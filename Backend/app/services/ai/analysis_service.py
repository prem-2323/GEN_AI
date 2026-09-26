"""Analysis Service — manages storage, deduplication, and execution lifecycle."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException

from ...storage.repository import get_repository
from ...storage.service import read_file_bytes
from ...models.analysis import AnalysisRecord
from .orchestrator import orchestrate_source_analysis, compute_content_hash
from ..projects.project_service import get_project
from ..sources import source_service

log = logging.getLogger("gen-transform.analysis_service")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def analyze_source(
    project_id: str,
    source_id: str,
    user_id: str,
    extracted_text: Optional[str] = None,
    extracted_images: Optional[list] = None,
    force_refresh: bool = False,
) -> AnalysisRecord:
    """Run or retrieve source analysis with SHA-256 deduplication and repository persistence."""
    # 1. Verify project ownership (raises 404 or 403)
    project = get_project(project_id, uid=user_id)

    # 2. Resolve content from the requested source, not the project's latest source.
    source_obj = source_service.get_source(source_id, user_id)
    if source_obj.get("projectId") != project_id:
        raise HTTPException(status_code=400, detail="Source does not belong to this project.")

    if not extracted_text:
        extracted_text = source_obj.get("extractedText") or (source_obj.get("normalized", {}).get("text") or {}).get("content", "")

        if not extracted_text:
            ext_repo = get_repository("extracted_content")
            ext_doc = ext_repo.find_one({"sourceId": source_id}, projection={"_id": 0})
            if ext_doc:
                if ext_doc.get("text"):
                    extracted_text = ext_doc["text"]
                elif ext_doc.get("chunks"):
                    extracted_text = "\n\n".join(c.get("text", "") for c in ext_doc.get("chunks", []))
                elif ext_doc.get("pages"):
                    extracted_text = "\n\n".join(p.get("text", "") for p in ext_doc.get("pages", []))

        if not extracted_text:
            extracted_text = project.get("description") or project.get("title") or ""

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Source contains no extracted text to analyze.")

    if extracted_images is None:
        extracted_images = []
        for image in (source_obj.get("normalized") or {}).get("images", []):
            path = image.get("path")
            if not path:
                continue
            try:
                image_bytes, _ = read_file_bytes(path, uid=user_id)
            except Exception as exc:
                log.warning("Could not load source image %s: %s", image.get("imageId", ""), exc)
                continue
            extracted_images.append({
                "id": image.get("imageId") or image.get("filename") or path,
                "page": image.get("pageNumber"),
                "bytes": image_bytes,
            })

    # 3. Check deduplication hash in repository
    c_hash = compute_content_hash(extracted_text)
    analysis_repo = get_repository("analysis")

    if not force_refresh:
        existing = analysis_repo.find_one(
            {"projectId": project_id, "sourceId": source_id, "contentHash": c_hash},
            projection={"_id": 0},
        )
        if existing:
            log.info("Reusing cached analysis for source %s (hash=%s)", source_id, c_hash[:8])
            return AnalysisRecord(**existing)

    # 4. Run AI Orchestration (Qwen + Gemma)
    record = orchestrate_source_analysis(
        project_id=project_id,
        source_id=source_id,
        user_id=user_id,
        extracted_text=extracted_text,
        extracted_images=extracted_images,
    )

    # 5. Save to analysis repository
    doc_data = record.model_dump()
    analysis_repo.update_one(
        {"id": record.id},
        {"$set": doc_data},
        upsert=True,
    )

    # 6. Also sync summary to project document
    try:
        proj_repo = get_repository("projects")
        proj_repo.update_one(
            {"id": project_id},
            {
                "$set": {
                    "analysis": {
                        "analysisId": record.id,
                        "summary": record.textAnalysis.summary,
                        "factsCount": len(record.textAnalysis.facts),
                        "entitiesCount": len(record.textAnalysis.entities),
                        "eventsCount": len(record.textAnalysis.events),
                        "metricsCount": len(record.textAnalysis.metrics),
                        "updatedAt": _now(),
                    }
                }
            },
        )
    except Exception as exc:
        log.warning("Could not update project analysis summary: %s", exc)

    return record


def analyze_source_sync(project_id: str, source_id: str, user_id: str) -> AnalysisRecord:
    """Compatibility entry point for synchronous UCKR construction flows."""
    return analyze_source(project_id, source_id, user_id)


def get_analysis(project_id: str, source_id: str, user_id: str) -> AnalysisRecord:
    """Retrieve saved analysis, enforcing ownership."""
    get_project(project_id, uid=user_id)

    analysis_repo = get_repository("analysis")
    doc = analysis_repo.find_one(
        {"projectId": project_id, "sourceId": source_id},
        projection={"_id": 0},
    )
    if not doc:
        # If not analyzed yet, run initial analysis automatically
        return analyze_source(project_id, source_id, user_id)

    owner_uid = doc.get("userId") or doc.get("firebaseUid")
    if owner_uid and owner_uid != user_id:
        raise HTTPException(status_code=403, detail="Access denied to this analysis record.")

    return AnalysisRecord(**doc)


def get_analysis_status(project_id: str, source_id: str, user_id: str) -> Dict[str, Any]:
    """Check processing status and progress."""
    get_project(project_id, uid=user_id)
    analysis_repo = get_repository("analysis")
    doc = analysis_repo.find_one(
        {"projectId": project_id, "sourceId": source_id},
        projection={"_id": 0},
    )
    if not doc:
        return {"status": "not_started", "stage": "idle", "progress": 0}
    return {
        "status": doc.get("status"),
        "stage": doc.get("stage"),
        "progress": doc.get("progress", 0),
        "updatedAt": doc.get("updatedAt"),
    }

