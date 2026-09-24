"""Main Consistency Engine Orchestrator and Regeneration Service (Phase 7)."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pymongo import DESCENDING

from ...config.mongo import get_mongo_db
from ...models.deliverable import DeliverableRecord, TransformationConfig
from ...models.validation import (
    DeliverableValidationResult,
    OverallValidationStatus,
    RegenerateRequest,
    ValidationRecord,
    ValidationRequest,
    ValidationScores,
)
from ...utils.helpers import utcnow_iso
from ..transformation.transformation_service import generate_single_deliverable
from .citation_checker import check_citation_consistency
from .date_checker import check_date_consistency
from .entity_checker import check_entity_consistency
from .fact_checker import check_fact_preservation
from .metric_checker import check_metric_consistency
from .score_calculator import calculate_validation_scores
from .unsupported_claim_detector import detect_unsupported_claims

log = logging.getLogger("gen-transform.consistency_service")


def _project_filter(project_id: str, user_uid: str) -> Dict[str, Any]:
    return {
        "$and": [
            {"$or": [{"_id": project_id}, {"id": project_id}, {"projectId": project_id}]},
            {"$or": [{"userId": user_uid}, {"firebaseUid": user_uid}]},
        ]
    }


def _flatten_content(content: Any) -> str:
    """Recursively flattens dict/list/string content into a single searchable text string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (int, float)):
        return str(content)
    if isinstance(content, list):
        return " ".join(_flatten_content(item) for item in content)
    if isinstance(content, dict):
        return " ".join(_flatten_content(v) for v in content.values())
    return ""


def validate_single_deliverable(
    uckr: Dict[str, Any],
    deliverable_doc: Dict[str, Any],
) -> DeliverableValidationResult:
    """Executes all 7 consistency checks against a single deliverable."""
    deliv_id = str(deliverable_doc.get("_id") or deliverable_doc.get("id", "deliv"))
    deliv_type = deliverable_doc.get("type", "unknown")
    content = deliverable_doc.get("content", {})
    deliv_text = _flatten_content(content)

    # 1. Run all modular checks
    checks = []
    checks.extend(check_date_consistency(uckr, deliv_text))
    checks.extend(check_metric_consistency(uckr, deliv_text))
    checks.extend(check_entity_consistency(uckr, deliv_text))
    checks.extend(check_fact_preservation(uckr, deliverable_doc, deliv_text))
    checks.extend(check_citation_consistency(uckr, deliverable_doc))

    # 2. Detect unsupported claims
    unsupported = detect_unsupported_claims(uckr, deliv_text)

    # 3. Determine single deliverable status
    contradictions = sum(1 for c in checks if c.status == "contradiction")
    if contradictions > 0 or len(unsupported) > 2:
        deliv_status: OverallValidationStatus = "FAIL"
    elif len(unsupported) > 0:
        deliv_status = "WARNING"
    else:
        deliv_status = "PASS"

    return DeliverableValidationResult(
        deliverableId=deliv_id,
        deliverableType=deliv_type,
        checks=checks,
        unsupportedClaims=unsupported,
        status=deliv_status,
    )


def validate_project_sources(
    project_id: str,
    source_id: str,
    req: ValidationRequest,
    user: Dict[str, Any],
) -> ValidationRecord:
    """Validates project deliverables against canonical UCKR."""
    db = get_mongo_db()
    user_uid = user.get("uid") or user.get("userId") or user.get("firebaseUid")
    if not user_uid:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # 1. Verify Project
    proj = None
    if db is not None:
        proj = db.projects.find_one(_project_filter(project_id, user_uid))
    if proj is None:
        raise HTTPException(status_code=403, detail="Project not found or access denied.")

    # 2. Load Canonical UCKR
    uckr_query: Dict[str, Any] = {"projectId": project_id, "sourceId": source_id}
    if req.uckrVersion:
        uckr_query["version"] = req.uckrVersion

    uckr_doc = None
    if db is not None:
        uckr_doc = db.uckr.find_one(uckr_query, sort=[("version", DESCENDING)])

    if not uckr_doc:
        raise HTTPException(status_code=404, detail="Canonical UCKR document not found.")

    # 3. Load Deliverables
    deliv_query: Dict[str, Any] = {"projectId": project_id}
    if req.deliverableIds:
        deliv_query["_id"] = {"$in": req.deliverableIds}

    deliverables = []
    if db is not None:
        deliverables = list(db.deliverables.find(deliv_query, sort=[("createdAt", DESCENDING)]))

    if not deliverables:
        raise HTTPException(status_code=404, detail="No deliverables found to validate.")

    # 4. Validate Each Deliverable
    results: List[DeliverableValidationResult] = []
    deliv_ids = []
    for d in deliverables:
        res = validate_single_deliverable(uckr_doc, d)
        results.append(res)
        deliv_ids.append(res.deliverableId)

    # 5. Compute Mathematical Scores
    scores, overall_status = calculate_validation_scores(results)

    val_id = f"val_{uuid.uuid4().hex[:8]}"
    now = utcnow_iso()

    doc = {
        "_id": val_id,
        "firebaseUid": user_uid,
        "projectId": project_id,
        "sourceId": source_id,
        "uckrId": str(uckr_doc.get("_id") or uckr_doc.get("id")),
        "uckrVersion": uckr_doc.get("version", 1),
        "deliverableIds": deliv_ids,
        "results": [r.model_dump() for r in results],
        "scores": scores.model_dump(),
        "overallStatus": overall_status,
        "status": "completed",
        "createdAt": now,
        "updatedAt": now,
    }

    if db is not None:
        try:
            db.validations.insert_one(doc)
            log.info("Persisted validation %s (status=%s, consistency=%s%%)", val_id, overall_status, scores.consistency)
        except Exception as exc:
            log.warning("Failed to persist validation to MongoDB: %s", exc)

    return ValidationRecord.model_validate(doc)


def get_latest_validation(project_id: str, source_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieves the latest validation audit report for a project source."""
    db = get_mongo_db()
    user_uid = user.get("uid") or user.get("userId") or user.get("firebaseUid")
    if not user_uid:
        raise HTTPException(status_code=401, detail="Authentication required.")

    if db is not None:
        proj = db.projects.find_one(_project_filter(project_id, user_uid))
        if proj is None:
            raise HTTPException(status_code=403, detail="Project not found or access denied.")

        doc = db.validations.find_one({"projectId": project_id, "sourceId": source_id}, sort=[("createdAt", DESCENDING)])
        if not doc:
            raise HTTPException(status_code=404, detail="No validation record found for this source.")
        doc["id"] = str(doc.get("_id"))
        return doc

    raise HTTPException(status_code=404, detail="No validation record found.")


def regenerate_deliverable_with_feedback(
    project_id: str,
    deliverable_id: str,
    req: RegenerateRequest,
    user: Dict[str, Any],
) -> Dict[str, Any]:
    """Regenerates a deliverable incorporating validation error feedback and re-validates."""
    db = get_mongo_db()
    user_uid = user.get("uid") or user.get("userId") or user.get("firebaseUid")
    if not user_uid:
        raise HTTPException(status_code=401, detail="Authentication required.")

    if db is None:
        raise HTTPException(status_code=500, detail="Database connection unavailable.")

    proj = db.projects.find_one(_project_filter(project_id, user_uid))
    if proj is None:
        raise HTTPException(status_code=403, detail="Project not found or access denied.")

    old_deliv = db.deliverables.find_one({"_id": deliverable_id, "projectId": project_id})
    if not old_deliv:
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    source_id = old_deliv.get("sourceId")
    uckr_version = old_deliv.get("uckrVersion", 1)
    uckr_doc = db.uckr.find_one({"projectId": project_id, "sourceId": source_id, "version": uckr_version})
    if not uckr_doc:
        raise HTTPException(status_code=404, detail="Canonical UCKR not found for regeneration.")

    cfg_dict = req.configuration or old_deliv.get("configuration") or {}
    cfg = TransformationConfig.model_validate(cfg_dict)

    # Regenerate deliverable strictly from UCKR
    dtype = old_deliv.get("type", "linkedin")
    new_deliv = generate_single_deliverable(
        dtype=dtype,
        uckr=uckr_doc,
        cfg=cfg,
        user_uid=user_uid,
        project_id=project_id,
        source_id=source_id,
    )

    # Re-validate the newly generated deliverable
    val_res = validate_single_deliverable(uckr_doc, new_deliv.model_dump(by_alias=True))

    # Update existing deliverable in MongoDB
    db.deliverables.update_one(
        {"_id": deliverable_id},
        {"$set": {
            "content": new_deliv.content,
            "usedFactIds": new_deliv.usedFactIds,
            "citations": new_deliv.citations,
            "status": "completed" if val_res.status == "PASS" else "completed",
            "validation": val_res.model_dump(),
            "updatedAt": utcnow_iso(),
        }},
    )

    return {
        "ok": True,
        "deliverableId": deliverable_id,
        "type": dtype,
        "content": new_deliv.content,
        "validation": val_res.model_dump(),
    }
