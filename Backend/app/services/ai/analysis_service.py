"""Analysis Service — manages storage, deduplication, and execution lifecycle in MongoDB."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException

from ...config.mongo import get_mongo_db
from ...models.analysis import AnalysisRecord
from .orchestrator import orchestrate_source_analysis, compute_content_hash
from ..project_service import get_project

log = logging.getLogger("gen-transform.analysis_service")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def analyze_source(
    project_id: str,
    source_id: str,
    firebase_uid: str,
    extracted_text: Optional[str] = None,
    extracted_images: Optional[list] = None,
    force_refresh: bool = False,
) -> AnalysisRecord:
    """Run or retrieve source analysis with SHA-256 deduplication and MongoDB persistence."""
    # 1. Verify project ownership (raises 404 or 403)
    project = get_project(project_id, uid=firebase_uid)

    # 2. Extract text from project source if not passed directly
    if not extracted_text:
        source_obj = project.get("source") or project.get("sourceFile") or {}
        extracted_text = source_obj.get("extractedText") or project.get("description") or project.get("title") or ""

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Source contains no extracted text to analyze.")

    # 3. Check deduplication hash in MongoDB
    c_hash = compute_content_hash(extracted_text)
    mongo_db = get_mongo_db()
    analysis_col = mongo_db["analysis"]

    if not force_refresh:
        existing = analysis_col.find_one(
            {"projectId": project_id, "sourceId": source_id, "contentHash": c_hash},
            {"_id": 0},
        )
        if existing:
            log.info("Reusing cached analysis for source %s (hash=%s)", source_id, c_hash[:8])
            return AnalysisRecord(**existing)

    # 4. Run AI Orchestration (Qwen + Gemma)
    record = orchestrate_source_analysis(
        project_id=project_id,
        source_id=source_id,
        firebase_uid=firebase_uid,
        extracted_text=extracted_text,
        extracted_images=extracted_images,
    )

    # 5. Save to MongoDB analysis collection
    doc_data = record.model_dump()
    analysis_col.update_one(
        {"id": record.id},
        {"$set": doc_data},
        upsert=True,
    )

    # 6. Also sync summary to project document
    try:
        mongo_db["projects"].update_one(
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


def get_analysis(project_id: str, source_id: str, firebase_uid: str) -> AnalysisRecord:
    """Retrieve saved analysis, enforcing ownership."""
    get_project(project_id, uid=firebase_uid)

    mongo_db = get_mongo_db()
    doc = mongo_db["analysis"].find_one(
        {"projectId": project_id, "sourceId": source_id},
        {"_id": 0},
    )
    if not doc:
        # If not analyzed yet, run initial analysis automatically
        return analyze_source(project_id, source_id, firebase_uid)

    if doc.get("firebaseUid") != firebase_uid:
        raise HTTPException(status_code=403, detail="Access denied to this analysis record.")

    return AnalysisRecord(**doc)


def get_analysis_status(project_id: str, source_id: str, firebase_uid: str) -> Dict[str, Any]:
    """Check processing status and progress."""
    get_project(project_id, uid=firebase_uid)
    mongo_db = get_mongo_db()
    doc = mongo_db["analysis"].find_one(
        {"projectId": project_id, "sourceId": source_id},
        {"_id": 0, "status": 1, "stage": 1, "progress": 1, "updatedAt": 1},
    )
    if not doc:
        return {"status": "not_started", "stage": "idle", "progress": 0}
    return doc
