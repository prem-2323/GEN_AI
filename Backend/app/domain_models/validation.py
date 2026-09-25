"""Validation and Consistency Models (Phase 7)."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

CheckCategory = Literal[
    "fact",
    "date",
    "metric",
    "entity",
    "event",
    "claim",
    "relationship",
    "citation",
    "unsupported_claim",
]

CheckStatus = Literal[
    "consistent",
    "contradiction",
    "unsupported",
    "warning",
    "not_checked",
]

OverallValidationStatus = Literal["PASS", "WARNING", "FAIL"]


class CheckItem(BaseModel):
    """Individual verification check result."""
    category: CheckCategory
    factId: Optional[str] = None
    entityId: Optional[str] = None
    expected: Any = None
    found: Any = None
    status: CheckStatus = "consistent"
    message: str = ""
    sourceSnippet: Optional[str] = None


class DeliverableValidationResult(BaseModel):
    """Validation report for a single deliverable."""
    deliverableId: str
    deliverableType: str
    checks: List[CheckItem] = Field(default_factory=list)
    unsupportedClaims: List[str] = Field(default_factory=list)
    status: OverallValidationStatus = "PASS"


class ValidationScores(BaseModel):
    """Dynamically computed consistency scores."""
    consistency: float = 100.0          # (consistent_checks / total_applicable) * 100
    factPreservation: float = 100.0     # (preserved_referenced_facts / total_referenced) * 100
    citationCoverage: float = 100.0     # (cited_facts / total_referenced) * 100
    unsupportedClaims: int = 0          # Count of unsupported assertions


class ValidationRequest(BaseModel):
    """Request payload to validate deliverables against UCKR."""
    uckrVersion: Optional[int] = None
    deliverableIds: Optional[List[str]] = None


class RegenerateRequest(BaseModel):
    """Request payload to regenerate a deliverable with validation error constraints."""
    configuration: Optional[Dict[str, Any]] = None
    validationFeedback: Optional[List[str]] = None


class ValidationRecord(BaseModel):
    """Local repository record for a validation."""
    id: str = Field(alias="_id")
    userId: str
    projectId: str
    sourceId: str
    uckrId: str
    uckrVersion: int
    deliverableIds: List[str] = Field(default_factory=list)
    results: List[DeliverableValidationResult] = Field(default_factory=list)
    scores: ValidationScores = Field(default_factory=ValidationScores)
    overallStatus: OverallValidationStatus = "PASS"
    status: Literal["completed", "failed", "in_progress"] = "completed"
    createdAt: str
    updatedAt: str

    model_config = {"populate_by_name": True}
