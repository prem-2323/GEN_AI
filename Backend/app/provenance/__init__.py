"""Phase 14 — Provenance & Evidence Tracking Package.

Provides complete forward and reverse lineage traceability, cryptographic content hashing,
append-oriented storage, evidence resolution, and lineage graph traversal.
"""

from __future__ import annotations

from .config import ProvenanceSettings, get_provenance_settings
from .schemas import (
    ClaimProvenance,
    EvidenceRecord,
    IntegrityResult,
    LineageNode,
    LineageTree,
    OutputProvenance,
    ProvenanceMetadata,
    ProvenanceMetrics,
    ProvenanceRecord,
    ProvenanceRequest,
    SourceTypeEnum,
)
from .builder import ProvenanceBuilder
from .citation_mapper import CitationMapper
from .hashing import ProvenanceHasher
from .lineage import LineageService
from .metrics import ProvenanceMetricsCalculator
from .repository import ProvenanceRepository
from .resolver import EvidenceResolver
from .service import ProvenanceService, get_provenance_service

__all__ = [
    "ProvenanceSettings",
    "get_provenance_settings",
    "SourceTypeEnum",
    "ProvenanceRecord",
    "EvidenceRecord",
    "ClaimProvenance",
    "OutputProvenance",
    "ProvenanceMetadata",
    "IntegrityResult",
    "LineageNode",
    "LineageTree",
    "ProvenanceMetrics",
    "ProvenanceRequest",
    "ProvenanceBuilder",
    "CitationMapper",
    "ProvenanceHasher",
    "LineageService",
    "ProvenanceMetricsCalculator",
    "ProvenanceRepository",
    "EvidenceResolver",
    "ProvenanceService",
    "get_provenance_service",
]
