"""Sources service — MongoDB `sources` collection with a strict state machine.

Lifecycle:
    uploaded -> validating -> extracting -> completed
                                        \\-> failed

Every document carries BOTH `firebaseUid` (spec) and `userId` (legacy);
all reads are owner-scoped: {"$or": [{firebaseUid: uid}, {userId: uid}]}.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import HTTPException
from pymongo import DESCENDING

from ...config.mongo import get_mongo_db
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
    return {"$or": [{"firebaseUid": uid}, {"userId": uid}]}


def _by_id(source_id: str, uid: str) -> dict:
    # NOTE: must use $and — two "$or" keys in one dict would overwrite each other.
    return {"$and": [{"$or": [{"sourceId": source_id}, {"id": source_id}]}, _owner_filter(uid)]}


def create_source(uid: str, project_id: str, file_meta: dict) -> dict:
    now = utcnow_iso()
    sid = f"src-{uuid.uuid4().hex[:12]}"
    orig_name = file_meta.get("originalName") or file_meta.get("originalFilename") or "upload.bin"
    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else "bin"
    doc: dict[str, Any] = {
        "_id": sid,
        "sourceId": sid,
        "id": sid,
        "firebaseUid": uid,
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
    get_mongo_db()["sources"].insert_one(doc)
    doc.pop("_id", None)
    return doc


def get_source(source_id: str, uid: str) -> dict:
    doc = get_mongo_db()["sources"].find_one(_by_id(source_id, uid), {"_id": 0})
    if not doc:
        # Check if analysis exists for this source or if source_id is a transient direct text source
        ana = get_mongo_db()["analysis"].find_one({"sourceId": source_id, **_owner_filter(uid)}, {"_id": 0})
        if ana:
            now = utcnow_iso()
            source_doc = {
                "sourceId": source_id,
                "id": source_id,
                "firebaseUid": uid,
                "userId": uid,
                "projectId": ana.get("projectId", "proj_default"),
                "name": "Pasted_Source_Text.txt",
                "extractedText": ana.get("textAnalysis", {}).get("summary", ""),
                "status": "ready",
                "createdAt": now,
                "updatedAt": now,
            }
            get_mongo_db()["sources"].update_one(_by_id(source_id, uid), {"$set": source_doc}, upsert=True)
            return source_doc

        # If it's a direct text source, auto-provision
        if source_id.startswith("src-text-") or source_id.startswith("src-edu-") or source_id in ("src_default", "SRC_001"):
            now = utcnow_iso()
            source_doc = {
                "sourceId": source_id,
                "id": source_id,
                "firebaseUid": uid,
                "userId": uid,
                "projectId": "proj_default",
                "name": "Pasted_Source_Text.txt",
                "extractedText": "",
                "status": "ready",
                "createdAt": now,
                "updatedAt": now,
            }
            get_mongo_db()["sources"].update_one(_by_id(source_id, uid), {"$set": source_doc}, upsert=True)
            return source_doc

        # Distinguish cross-tenant (403) from missing (404)
        other = get_mongo_db()["sources"].find_one(
            {"$or": [{"sourceId": source_id}, {"id": source_id}]}, {"_id": 0, "sourceId": 1}
        )
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this source.")
        raise HTTPException(status_code=404, detail="Source not found.")
    return doc


def list_sources(uid: str, project_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    filt: dict[str, Any] = _owner_filter(uid)
    if project_id:
        filt = {"$and": [filt, {"projectId": project_id}]}
    cur = get_mongo_db()["sources"].find(filt, {"_id": 0}).sort("updatedAt", DESCENDING).limit(limit)
    return list(cur)


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
    get_mongo_db()["sources"].update_one(_by_id(source_id, uid), {"$set": update})
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

    # Save to extracted_content collection (Phase 9 Collection #8 & #9)
    extraction_id = f"ext_{source_id}_{uuid.uuid4().hex[:8]}"
    ext_doc = {
        "_id": extraction_id,
        "extractionId": extraction_id,
        "firebaseUid": uid,
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
    set_fields = {k: v for k, v in ext_doc.items() if k != "_id"}
    get_mongo_db()["extracted_content"].update_one(
        {"sourceId": source_id, "$or": [{"firebaseUid": uid}, {"userId": uid}]},
        {"$set": set_fields, "$setOnInsert": {"_id": extraction_id}},
        upsert=True,
    )

    # Roll-up stats on sources collection
    update = {
        "status": "processed",
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
    get_mongo_db()["sources"].update_one(_by_id(source_id, uid), {"$set": update})
    return get_source(source_id, uid)


def reset_for_retry(source_id: str, uid: str) -> dict:
    """Internal reset so a pipeline job can re-process a completed/failed source."""
    get_source(source_id, uid)  # ownership check
    get_mongo_db()["sources"].update_one(
        _by_id(source_id, uid),
        {"$set": {"processing": {"status": "uploaded", "stage": "uploaded",
                                 "progress": 0, "error": None},
                  "updatedAt": utcnow_iso()}},
    )
    return get_source(source_id, uid)


def delete_source(source_id: str, uid: str) -> bool:
    get_source(source_id, uid)
    get_mongo_db()["sources"].delete_many(
        {"$and": [{"$or": [{"sourceId": source_id}, {"id": source_id}]}, _owner_filter(uid)]}
    )
    return True


def count_project_sources(uid: str, project_id: str) -> int:
    return get_mongo_db()["sources"].count_documents(
        {"$and": [{"projectId": project_id}, _owner_filter(uid)]}
    )
