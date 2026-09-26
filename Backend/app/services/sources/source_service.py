"""Sources service — Database-independent repository with a strict state machine.

Lifecycle:
    uploaded -> validating -> extracting -> completed
                                        \-> failed
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import HTTPException
from ...storage.repository import get_repository
from ...utils.helpers import utcnow_iso

log = logging.getLogger("gen-transform.sources")

VALID_TRANSITIONS: dict[str, set[str]] = {
    "uploaded": {"validating", "failed"},
    "validating": {"extracting", "failed"},
    "extracting": {"completed", "failed"},
    "completed": set(),
    "failed": {"validating"},  # manual retry
}

TERMINAL = {"completed", "failed"}


def _owner_filter(uid: str) -> dict:
    if uid in ("local_dev_user", "anonymous", "local-workspace", "dev_user"):
        return {"$or": [{"userId": uid}, {"firebaseUid": uid}, {"userId": "local-workspace"}, {"userId": "local_dev_user"}, {"userId": "dev_user"}, {"userId": "anonymous"}]}
    return {"$or": [{"userId": uid}, {"firebaseUid": uid}]}


def _by_id(source_id: str, uid: str) -> dict:
    return {"$and": [{"$or": [{"sourceId": source_id}, {"id": source_id}]}, _owner_filter(uid)]}


def create_source(uid: str, project_id: str, file_meta: dict) -> dict:
    now = utcnow_iso()
    sid = file_meta.get("fileId") or f"src-{uuid.uuid4().hex[:12]}"
    orig_name = file_meta.get("originalName") or file_meta.get("originalFilename") or "upload.bin"
    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else "bin"
    doc: dict[str, Any] = {
        "sourceId": sid,
        "id": sid,
        "userId": uid,
        "userId": uid,
        "projectId": project_id,
        "fileId": file_meta.get("fileId", ""),
        "originalFilename": orig_name,
        "fileType": ext,
        "mimeType": file_meta.get("mimeType", "application/octet-stream"),
        "fileSize": file_meta.get("size", 0),
        "sha256": file_meta.get("sha256", ""),
        "status": "uploaded",
        "file": {
            "originalName": orig_name,
            "storedName": file_meta.get("storedName", ""),
            "mimeType": file_meta.get("mimeType", "application/octet-stream"),
            "size": file_meta.get("size", 0),
            "storagePath": file_meta.get("storagePath", ""),
            "fileId": file_meta.get("fileId", ""),
        },
        "processing": {"status": "uploaded", "stage": "uploaded", "progress": 0, "error": None},
        "extraction": {"textLength": 0, "pageCount": 0, "wordCount": 0, "chunkCount": 0, "imageCount": 0, "tableCount": 0},
        "createdAt": now,
        "updatedAt": now,
    }
    repo = get_repository("sources")
    repo.insert_one(doc)
    return doc


def get_source(source_id: str, uid: str) -> dict:
    repo = get_repository("sources")
    doc = repo.find_one(_by_id(source_id, uid), projection={"_id": 0})
    if not doc:
        # Check if analysis exists for this source or if source_id is a transient direct text source
        ana_repo = get_repository("analysis")
        ana = ana_repo.find_one({"sourceId": source_id, **_owner_filter(uid)}, projection={"_id": 0})
        if ana:
            now = utcnow_iso()
            source_doc = {
                "sourceId": source_id,
                "id": source_id,
                "userId": uid,
                "userId": uid,
                "projectId": ana.get("projectId", "proj_default"),
                "name": "Pasted_Source_Text.txt",
                "extractedText": ana.get("textAnalysis", {}).get("summary", ""),
                "status": "ready",
                "createdAt": now,
                "updatedAt": now,
            }
            repo.update_one(_by_id(source_id, uid), {"$set": source_doc}, upsert=True)
            return source_doc

        # If it's a direct text source, auto-provision
        if source_id.startswith("src-text-") or source_id.startswith("src-edu-") or source_id in ("src_default", "SRC_001"):
            now = utcnow_iso()
            source_doc = {
                "sourceId": source_id,
                "id": source_id,
                "userId": uid,
                "userId": uid,
                "projectId": "proj_default",
                "name": "Pasted_Source_Text.txt",
                "extractedText": "",
                "status": "ready",
                "createdAt": now,
                "updatedAt": now,
            }
            repo.update_one(_by_id(source_id, uid), {"$set": source_doc}, upsert=True)
            return source_doc

        # Distinguish cross-tenant (403) from missing (404)
        other = repo.find_one(
            {"$or": [{"sourceId": source_id}, {"id": source_id}]}, projection={"_id": 0}
        )
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this source.")
        raise HTTPException(status_code=404, detail="Source not found.")
    return doc


def list_sources(uid: str, project_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    filt: dict[str, Any] = _owner_filter(uid)
    if project_id:
        filt = {"$and": [filt, {"projectId": project_id}]}
    repo = get_repository("sources")
    return repo.find(filt, sort=[("updatedAt", -1)], limit=limit, projection={"_id": 0})


def set_stage(source_id: str, uid: str, stage: str, progress: int = 0, error: Optional[str] = None) -> dict:
    doc = get_source(source_id, uid)
    current = (doc.get("processing") or {}).get("stage", "uploaded")
    if stage not in VALID_TRANSITIONS.get(current, set()) and stage != current:
        raise HTTPException(status_code=409, detail=f"Illegal source transition {current} -> {stage}.")
    terminal = "completed" if stage == "completed" else ("failed" if stage == "failed" else "processing")
    update: dict[str, Any] = {
        "processing.status": terminal if stage in TERMINAL else "processing",
        "processing.stage": stage,
        "processing.progress": progress,
        "processing.error": error,
        "updatedAt": utcnow_iso(),
    }
    repo = get_repository("sources")
    repo.update_one(_by_id(source_id, uid), {"$set": update})
    return get_source(source_id, uid)


def store_extraction(source_id: str, uid: str, normalized: dict) -> dict:
    """Persist the normalized extraction result into extracted_content and roll-up stats on source."""
    src = get_source(source_id, uid)  # ownership check
    project_id = src.get("projectId", "proj_default")
    ext = normalized.get("extraction", normalized)
    pages = normalized.get("pages", [])
    images = normalized.get("images", [])
    tables = normalized.get("tables", [])
    text_content = normalized.get("text", {}).get("content", "")
    words = len(text_content.split())

    # Build structured chunks
    chunks = []
    paras = [p.strip() for p in text_content.split("\n\n") if p.strip()] or [text_content.strip()]
    for idx, p in enumerate(paras):
        chunks.append({
            "chunkId": f"chunk_{source_id}_{idx+1:03d}",
            "pageNumber": 1,
            "text": p,
        })

    extraction_id = f"ext_{source_id}_{uuid.uuid4().hex[:8]}"
    ext_doc = {
        "extractionId": extraction_id,
        "userId": uid,
        "userId": uid,
        "projectId": project_id,
        "sourceId": source_id,
        "document": {
            "title": normalized.get("document", {}).get("name", "Document"),
            "language": "en",
            "pageCount": len(pages) or 1,
        },
        "pages": pages,
        "chunks": chunks,
        "images": [
            {
                "imageId": img.get("imageId", f"img_{idx+1}"),
                "fileId": img.get("fileId", ""),
                "pageNumber": img.get("pageNumber", 1),
                "mimeType": img.get("mimeType", "image/png"),
                "path": img.get("path", ""),
            }
            for idx, img in enumerate(images)
        ],
        "createdAt": utcnow_iso(),
    }
    ext_repo = get_repository("extracted_content")
    ext_repo.update_one(
        {"sourceId": source_id, "$or": [{"userId": uid}, {"firebaseUid": uid}]},
        {"$set": ext_doc},
        upsert=True,
    )

    # Roll-up stats on sources collection
    update = {
        "status": "processed",
        "extractedText": text_content,
        "extraction": {
            "textLength": ext.get("textLength", len(text_content)),
            "wordCount": words,
            "pageCount": len(pages),
            "chunkCount": len(chunks),
            "imageCount": len(images),
            "tableCount": len(tables),
        },
        "normalized": normalized,
        "updatedAt": utcnow_iso(),
    }
    repo = get_repository("sources")
    repo.update_one(_by_id(source_id, uid), {"$set": update})
    return get_source(source_id, uid)


def reset_for_retry(source_id: str, uid: str) -> dict:
    """Internal reset so a pipeline job can re-process a completed/failed source."""
    get_source(source_id, uid)  # ownership check
    repo = get_repository("sources")
    repo.update_one(
        _by_id(source_id, uid),
        {"$set": {"processing": {"status": "uploaded", "stage": "uploaded",
                                 "progress": 0, "error": None},
                  "updatedAt": utcnow_iso()}},
    )
    return get_source(source_id, uid)


def delete_source(source_id: str, uid: str) -> bool:
    get_source(source_id, uid)
    repo = get_repository("sources")
    repo.delete_many(
        {"$and": [{"$or": [{"sourceId": source_id}, {"id": source_id}]}, _owner_filter(uid)]}
    )
    return True


def count_project_sources(uid: str, project_id: str) -> int:
    repo = get_repository("sources")
    return repo.count_documents(
        {"$and": [{"projectId": project_id}, _owner_filter(uid)]}
    )
