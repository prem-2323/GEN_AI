"""Phase 13 Validation Engine — Schemas & Data Models.

Defines strongly typed Pydantic models for validation requests, contexts, results,
issues, claims, coverage breakdown, and cross-output consistency.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IssueTypeEnum(str, Enum):
    """Controlled issue types for factual, numeric, entity, citation, and structural violations."""
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    FACT_MISMATCH = "FACT_MISMATCH"
    ENTITY_MISMATCH = "ENTITY_MISMATCH"
    RELATION_MISMATCH = "RELATION_MISMATCH"
    NUMBER_MISMATCH = "NUMBER_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    CITATION_INVALID = "CITATION_INVALID"
    CITATION_MISSING = "CITATION_MISSING"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    CONTRADICTION = "CONTRADICTION"
    STRUCTURE_INVALID = "STRUCTURE_INVALID"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    TRANSLATION_DRIFT = "TRANSLATION_DRIFT"
    OUTPUT_INCONSISTENCY = "OUTPUT_INCONSISTENCY"


class SeverityEnum(str, Enum):
    """Severity classification levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationDecisionEnum(str, Enum):
    """Overall validation result status decision."""
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


class FactSupportStatusEnum(str, Enum):
    """Support status classification for individual factual claims."""
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


class ClaimItem(BaseModel):
    """Extracted factual claim item from generated text."""
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object_val: Optional[str] = None
    date_val: Optional[str] = None
    number_val: Optional[str] = None
    location_val: Optional[str] = None
    citation_ids: List[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    """Individual validation issue/violation detail."""
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: str
    severity: str
    message: str
    generated_text: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    source_document_ids: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    confidence: float = 1.0


class EvidenceCoverageResult(BaseModel):
    """Breakdown of evidence coverage across extracted claims."""
    total_claims: int = 0
    supported_claims: int = 0
    partially_supported_claims: int = 0
    unsupported_claims: int = 0
    contradicted_claims: int = 0
    coverage_ratio: float = 1.0


class ValidationResult(BaseModel):
    """Structured result returned by ValidationService."""
    validation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transformation_id: Optional[str] = None
    status: str = "PASS"  # PASS, PASS_WITH_WARNINGS, FAIL
    passed: bool = True
    score: float = 1.0  # [0.0, 1.0]
    issues: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    errors: List[ValidationIssue] = Field(default_factory=list)
    checks_run: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    evidence_coverage: EvidenceCoverageResult = Field(default_factory=EvidenceCoverageResult)
    citation_validity: Dict[str, Any] = Field(default_factory=dict)
    consistency_score: float = 1.0
    validation_latency_ms: float = 0.0
    repaired_content: Optional[str] = None


class CrossOutputConsistencyResult(BaseModel):
    """Comparison result when verifying consistency across multiple generated outputs."""
    consistency_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    output_ids: List[str] = Field(default_factory=list)
    compared_fields: List[str] = Field(default_factory=list)
    consistent_fields: List[str] = Field(default_factory=list)
    inconsistent_fields: List[str] = Field(default_factory=list)
    contradictions: List[ValidationIssue] = Field(default_factory=list)
    consistency_score: float = 1.0


class ValidationContext(BaseModel):
    """Standardized internal validation context containing trusted ground truth and output."""
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_ids: List[str] = Field(default_factory=list)
    source_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    source_facts: List[Dict[str, Any]] = Field(default_factory=list)
    source_entities: List[Dict[str, Any]] = Field(default_factory=list)
    source_relations: List[Dict[str, Any]] = Field(default_factory=list)
    graph_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    transformation_output: str
    structured_output: Optional[Dict[str, Any]] = None
    output_type: str = "SUMMARY"
    language: str = "en"
    requested_constraints: Dict[str, Any] = Field(default_factory=dict)
    expected_structure: List[str] = Field(default_factory=list)


class ValidationRequest(BaseModel):
    """API payload request for Phase 13 Validation Engine."""
    transformation_output: str
    transformation_id: Optional[str] = None
    structured_output: Optional[Dict[str, Any]] = None
    output_type: str = "SUMMARY"
    language: str = "en"
    source_text: Optional[str] = None
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    policy: str = "FAIL_ON_CRITICAL"


__all__ = [
    "IssueTypeEnum",
    "SeverityEnum",
    "ValidationDecisionEnum",
    "FactSupportStatusEnum",
    "ClaimItem",
    "ValidationIssue",
    "EvidenceCoverageResult",
    "ValidationResult",
    "CrossOutputConsistencyResult",
    "ValidationContext",
    "ValidationRequest",
]
