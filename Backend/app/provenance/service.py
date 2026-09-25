"""Phase 14 Provenance & Evidence Tracking Engine — Service Implementation.

Main service orchestrating provenance record creation, evidence resolution,
lineage graph construction, content hash verification, and repository persistence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from .config import ProvenanceSettings, get_provenance_settings
from .schemas import (
    ClaimProvenance,
    EvidenceRecord,
    IntegrityResult,
    LineageTree,
    OutputProvenance,
    ProvenanceMetrics,
    ProvenanceRequest,
)
from .builder import ProvenanceBuilder
from .citation_mapper import CitationMapper
from .hashing import ProvenanceHasher
from .lineage import LineageService
from .metrics import ProvenanceMetricsCalculator
from .repository import ProvenanceRepository
from .resolver import EvidenceResolver

log = logging.getLogger("gen-transform.provenance.service")


class ProvenanceService:
    """Core operational service for Phase 14 Provenance & Evidence Tracking."""

    def __init__(
        self,
        config: Optional[ProvenanceSettings] = None,
        repository: Optional[ProvenanceRepository] = None,
        resolver: Optional[EvidenceResolver] = None,
    ) -> None:
        self.config = config or get_provenance_settings()
        self.repository = repository or ProvenanceRepository(storage_dir=self.config.storage_dir)
        self.resolver = resolver or EvidenceResolver()
        self.builder = ProvenanceBuilder(resolver=self.resolver)
        self.citation_mapper = CitationMapper(resolver=self.resolver)
        self.lineage_service = LineageService(repository=self.repository, resolver=self.resolver)

    def create_output_provenance(self, request: ProvenanceRequest) -> OutputProvenance:
        """Create and store complete OutputProvenance, ClaimProvenance, EvidenceRecords, and links."""
        output_prov, claims, evidence_list, links = self.builder.build_output_provenance(
            output_id=request.output_id,
            content=request.content,
            claims_input=request.claims,
            evidence_input=request.evidence_items,
            citations_input=request.citations,
            validation_result=request.validation_result,
            pipeline_metadata=request.pipeline_metadata,
        )

        # Persist to append-oriented repository
        self.repository.save_output_provenance(output_prov)
        self.repository.save_claims(claims)
        self.repository.save_evidence(evidence_list)
        self.repository.save_records(links)

        log.info(
            f"Successfully stored OutputProvenance for output '{request.output_id}' "
            f"({len(claims)} claims, {len(evidence_list)} evidence items)."
        )
        return output_prov

    def get_output_provenance(self, output_id: str) -> Optional[OutputProvenance]:
        """Retrieve stored OutputProvenance by output_id."""
        return self.repository.get_output(output_id)

    def get_claim_provenance(self, claim_id: str) -> Optional[ClaimProvenance]:
        """Retrieve stored ClaimProvenance by claim_id."""
        return self.repository.get_claim(claim_id)

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """Retrieve stored EvidenceRecord or resolve it."""
        return self.repository.get_evidence(evidence_id) or self.resolver.resolve_evidence(evidence_id)

    def get_citation_provenance(self, citation_id: str) -> Dict[str, Any]:
        """Retrieve citation mapping details."""
        return self.citation_mapper.resolve_citation({"citation_id": citation_id})

    def get_lineage(self, output_id: str) -> LineageTree:
        """Get forward lineage tree for output_id."""
        return self.lineage_service.get_forward_lineage(output_id)

    def get_reverse_lineage(self, document_id: str) -> LineageTree:
        """Get reverse lineage tree for document_id."""
        return self.lineage_service.get_reverse_lineage(document_id)

    def verify_integrity(
        self, artifact_id: str, content: str, expected_hash: Optional[str] = None
    ) -> IntegrityResult:
        """Verify content SHA-256 hash integrity against expected hash or stored output hash."""
        if not expected_hash:
            stored = self.get_output_provenance(artifact_id)
            if stored and stored.content_hash:
                expected_hash = stored.content_hash

        return ProvenanceHasher.verify_integrity(
            artifact_id=artifact_id, content=content, expected_hash=expected_hash
        )

    def get_metrics(self) -> ProvenanceMetrics:
        """Calculate system-wide provenance health and completeness metrics."""
        return ProvenanceMetricsCalculator.calculate_repository_metrics(self.repository)


_PROVENANCE_SERVICE_INSTANCE: Optional[ProvenanceService] = None


def get_provenance_service() -> ProvenanceService:
    """Singleton getter for ProvenanceService instance."""
    global _PROVENANCE_SERVICE_INSTANCE
    if _PROVENANCE_SERVICE_INSTANCE is None:
        _PROVENANCE_SERVICE_INSTANCE = ProvenanceService()
    return _PROVENANCE_SERVICE_INSTANCE


__all__ = ["ProvenanceService", "get_provenance_service"]
