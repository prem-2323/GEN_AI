"""Phase 14 Provenance & Evidence Tracking — Pydantic Schemas.

Defines schemas for provenance records, evidence records, claim lineage, output lineage,
provenance metadata, integrity verification, lineage trees, and API payloads.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceTypeEnum(str, Enum):
    """Supported source artifact types for provenance lineage."""
    DOCUMENT = "DOCUMENT"
    PAGE = "PAGE"
    SECTION = "SECTION"
    CHUNK = "CHUNK"
    FACT = "FACT"
    ENTITY = "ENTITY"
    RELATION = "RELATION"
    VECTOR_EVIDENCE = "VECTOR_EVIDENCE"
    GRAPH_EVIDENCE = "GRAPH_EVIDENCE"
    RAG_EVIDENCE = "RAG_EVIDENCE"
    TRANSFORMATION_CLAIM = "TRANSFORMATION_CLAIM"


class ProvenanceRecord(BaseModel):
    """Represents a single directional provenance link between source and target artifacts."""
    provenance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    source_type: str
    target_type: str
    relationship: str  # e.g., DERIVED_FROM, SUPPORTED_BY, MAPPED_TO, CITES, GENERATED_BY
    document_id: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    evidence_id: Optional[str] = None
    citation_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceRecord(BaseModel):
    """Represents a trusted ground truth evidence artifact with exact source locations."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    source_type: str = SourceTypeEnum.RAG_EVIDENCE
    page: Optional[int] = None
    section: Optional[str] = None
    text_span: Optional[str] = None
    chunk_id: Optional[str] = None
    fact_id: Optional[str] = None
    entity_id: Optional[str] = None
    relation_id: Optional[str] = None
    content_hash: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClaimProvenance(BaseModel):
    """Connects a generated claim to its supporting evidence, document, and validation run."""
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    output_id: str
    claim_text: str
    evidence_ids: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    page_numbers: List[int] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    fact_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    relation_ids: List[str] = Field(default_factory=list)
    citation_ids: List[str] = Field(default_factory=list)
    validation_id: Optional[str] = None
    status: str = "RESOLVED"  # RESOLVED, UNRESOLVED, ORPHAN


class ProvenanceMetadata(BaseModel):
    """Comprehensive system metadata across Phases 7-13 preserving pipeline configuration."""
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    model_type: Optional[str] = None
    device: Optional[str] = None
    optimization_method: Optional[str] = None
    optimization_backend: Optional[str] = None
    optimization_id: Optional[str] = None
    distillation_model: Optional[str] = None
    distillation_version: Optional[str] = None
    active_parameter_strategy: Optional[str] = None
    active_parameter_count: Optional[int] = None
    validation_id: Optional[str] = None
    transformation_type: Optional[str] = None
    language: str = "en"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class OutputProvenance(BaseModel):
    """Complete provenance lineage wrapper for a generated deliverable artifact."""
    output_id: str
    document_ids: List[str] = Field(default_factory=list)
    claim_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    citation_ids: List[str] = Field(default_factory=list)
    validation_id: Optional[str] = None
    metadata: ProvenanceMetadata = Field(default_factory=ProvenanceMetadata)
    transformation_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    content_hash: str = ""


class IntegrityResult(BaseModel):
    """Structured response for content hash integrity verification."""
    valid: bool
    source_id: str
    expected_hash: str
    actual_hash: str
    checked_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    message: str = "INTEGRITY_VALID"


class LineageNode(BaseModel):
    """Tree node representing an artifact in the lineage graph."""
    node_id: str
    node_type: str
    label: str
    location: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    children: List[LineageNode] = Field(default_factory=list)


class LineageTree(BaseModel):
    """Hierarchical graph structure representing forward or reverse lineage."""
    root_id: str
    direction: str  # FORWARD or REVERSE
    tree: LineageNode
    total_nodes: int = 1
    depth: int = 1
    completeness_score: float = 1.0


class ProvenanceMetrics(BaseModel):
    """Measurable quality metrics for provenance completeness, linkage, and integrity."""
    total_outputs: int = 0
    total_claims: int = 0
    total_evidence_records: int = 0
    resolved_evidence: int = 0
    unresolved_evidence: int = 0
    provenance_completeness: float = 1.0
    orphan_records: int = 0
    broken_lineage_count: int = 0
    valid_hashes: int = 0
    invalid_hashes: int = 0
    citation_resolution_rate: float = 1.0
    validation_linkage_rate: float = 1.0
    average_lineage_depth: float = 0.0


class IntegrityVerifyRequest(BaseModel):
    """Payload for POST /api/provenance/verify endpoint."""
    artifact_id: str
    content: str
    expected_hash: Optional[str] = None
    artifact_type: str = "OUTPUT"


class ProvenanceRequest(BaseModel):
    """Payload for creating output provenance via service."""
    output_id: str
    content: str
    output_type: str = "SUMMARY"
    language: str = "en"
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    validation_result: Optional[Dict[str, Any]] = None
    pipeline_metadata: Optional[Dict[str, Any]] = None


__all__ = [
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
    "IntegrityVerifyRequest",
    "ProvenanceRequest",
]
