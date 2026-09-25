"""Phase 14 Provenance Engine — API Endpoints.

Provides RESTful HTTP endpoints for creating and querying deliverable provenance records,
claim lineage, evidence resolution, citation mapping, forward/reverse lineage trees,
and content hash integrity verification.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.provenance.schemas import (
    ClaimProvenance,
    EvidenceRecord,
    IntegrityResult,
    IntegrityVerifyRequest,
    LineageTree,
    OutputProvenance,
    ProvenanceMetrics,
    ProvenanceRequest,
)
from app.provenance.service import ProvenanceService, get_provenance_service

log = logging.getLogger("gen-transform.api.provenance")

router = APIRouter(prefix="/api/provenance", tags=["Provenance & Evidence Tracking"])


@router.post("/create", response_model=OutputProvenance, status_code=status.HTTP_201_CREATED)
def create_output_provenance(
    request: ProvenanceRequest,
    service: ProvenanceService = Depends(get_provenance_service),
) -> OutputProvenance:
    """Create and persist full output provenance for a generated deliverable."""
    try:
        return service.create_output_provenance(request)
    except Exception as e:
        log.error(f"Error creating provenance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provenance creation failed: {str(e)}",
        )


@router.get("/output/{output_id}", response_model=OutputProvenance)
def get_output_provenance(
    output_id: str,
    service: ProvenanceService = Depends(get_provenance_service),
) -> OutputProvenance:
    """Get stored OutputProvenance by output_id."""
    prov = service.get_output_provenance(output_id)
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output provenance for '{output_id}' not found.",
        )
    return prov


@router.get("/output/{output_id}/lineage", response_model=LineageTree)
def get_output_lineage(
    output_id: str,
    service: ProvenanceService = Depends(get_provenance_service),
) -> LineageTree:
    """Get forward lineage tree for output_id down to source documents."""
    return service.get_lineage(output_id)


@router.get("/document/{document_id}/lineage", response_model=LineageTree)
def get_document_lineage(
    document_id: str,
    service: ProvenanceService = Depends(get_provenance_service),
) -> LineageTree:
    """Get reverse lineage tree for document_id up to generated deliverables."""
    return service.get_reverse_lineage(document_id)


@router.get("/claim/{claim_id}", response_model=ClaimProvenance)
def get_claim_provenance(
    claim_id: str,
    service: ProvenanceService = Depends(get_provenance_service),
) -> ClaimProvenance:
    """Get stored ClaimProvenance by claim_id."""
    claim_prov = service.get_claim_provenance(claim_id)
    if not claim_prov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim provenance for '{claim_id}' not found.",
        )
    return claim_prov


@router.get("/evidence/{evidence_id}", response_model=EvidenceRecord)
def get_evidence(
    evidence_id: str,
    service: ProvenanceService = Depends(get_provenance_service),
) -> EvidenceRecord:
    """Get EvidenceRecord by evidence_id."""
    rec = service.get_evidence(evidence_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence record for '{evidence_id}' not found.",
        )
    return rec


@router.get("/citation/{citation_id}")
def get_citation_provenance(
    citation_id: str,
    service: ProvenanceService = Depends(get_provenance_service),
) -> Dict[str, Any]:
    """Get citation resolution mapping."""
    return service.get_citation_provenance(citation_id)


@router.post("/verify", response_model=IntegrityResult)
def verify_integrity(
    request: IntegrityVerifyRequest,
    service: ProvenanceService = Depends(get_provenance_service),
) -> IntegrityResult:
    """Verify SHA-256 content hash integrity for an artifact."""
    return service.verify_integrity(
        artifact_id=request.artifact_id,
        content=request.content,
        expected_hash=request.expected_hash,
    )


@router.get("/metrics", response_model=ProvenanceMetrics)
def get_provenance_metrics(
    service: ProvenanceService = Depends(get_provenance_service),
) -> ProvenanceMetrics:
    """Get system-wide provenance health and completeness metrics."""
    return service.get_metrics()


__all__ = ["router"]
