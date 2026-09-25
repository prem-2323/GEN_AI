"""Phase 12 Transformation Engine — Data Schemas & Models.

Defines strongly typed models for transformation requests, responses,
profiles, contexts, citations, evidence items, and structured outputs.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OutputTypeEnum(str, Enum):
    """Supported transformation output types."""
    SUMMARY = "SUMMARY"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    QUICK_READ = "QUICK_READ"
    DETAILED_REPORT = "DETAILED_REPORT"
    LINKEDIN_POST = "LINKEDIN_POST"
    X_POST = "X_POST"
    ADVISORY = "ADVISORY"
    POLICY_BRIEF = "POLICY_BRIEF"
    MEMO = "MEMO"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    VIDEO_SCRIPT = "VIDEO_SCRIPT"
    PRESENTATION_OUTLINE = "PRESENTATION_OUTLINE"
    INFOGRAPHIC_SPEC = "INFOGRAPHIC_SPEC"
    FAQ = "FAQ"
    TRANSLATION = "TRANSLATION"
    EMAIL_COMMUNICATION = "EMAIL_COMMUNICATION"
    STRUCTURED_REPORT = "STRUCTURED_REPORT"


class AudienceEnum(str, Enum):
    """Supported audience profiles."""
    GENERAL_PUBLIC = "GENERAL_PUBLIC"
    TECHNICAL_AUDIENCE = "TECHNICAL_AUDIENCE"
    EXECUTIVES = "EXECUTIVES"
    POLICYMAKERS = "POLICYMAKERS"
    RESEARCHERS = "RESEARCHERS"
    DEVELOPERS = "DEVELOPERS"
    STUDENTS = "STUDENTS"
    SECURITY_PROFESSIONALS = "SECURITY_PROFESSIONALS"


class ToneEnum(str, Enum):
    """Supported presentation tones."""
    NEUTRAL = "NEUTRAL"
    PROFESSIONAL = "PROFESSIONAL"
    FORMAL = "FORMAL"
    TECHNICAL = "TECHNICAL"
    CONCISE = "CONCISE"
    EDUCATIONAL = "EDUCATIONAL"
    CONVERSATIONAL = "CONVERSATIONAL"
    EXECUTIVE = "EXECUTIVE"


class DetailLevelEnum(str, Enum):
    """Supported detail levels."""
    CONCISE = "CONCISE"
    MEDIUM = "MEDIUM"
    COMPREHENSIVE = "COMPREHENSIVE"


class CitationModeEnum(str, Enum):
    """Supported citation formatting modes."""
    INLINE = "INLINE"
    FOOTNOTE = "FOOTNOTE"
    NONE = "NONE"
    STRICT = "STRICT"


class EvidenceItem(BaseModel):
    """Single evidence chunk with metadata."""
    evidence_id: str
    document_id: Optional[str] = None
    content: str
    score: float = 1.0
    source: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CitationReference(BaseModel):
    """Citation mapping link from output reference to evidence item."""
    citation_id: str  # e.g., "[1]"
    evidence_id: str
    document_id: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    text_snippet: Optional[str] = None


class FactItem(BaseModel):
    """Extracted factual tuple."""
    fact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    predicate: str
    object_val: str
    confidence: float = 1.0


class EntityItem(BaseModel):
    """Extracted entity."""
    entity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    entity_type: str


class RelationItem(BaseModel):
    """Extracted relation between entities."""
    source_entity: str
    target_entity: str
    relation_type: str


class TransformationProfile(BaseModel):
    """Defines structural and formatting requirements for a specific output type."""
    output_type: str
    name: str
    purpose: str
    expected_structure: List[str]
    required_sections: List[str]
    target_length: str
    default_tone: str
    default_audience: str
    formatting_requirements: List[str]
    citation_requirements: str
    validation_rules: List[str]
    structured_json: bool = False


class TransformationRequest(BaseModel):
    """Strongly typed input request for document transformation."""
    transformation_id: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)
    source_text: Optional[str] = None
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    output_type: str = Field(default="SUMMARY", description="Requested output type profile")
    audience: str = Field(default="GENERAL_PUBLIC", description="Target audience")
    tone: str = Field(default="PROFESSIONAL", description="Desired presentation tone")
    language: str = Field(default="en", description="Source language")
    target_language: Optional[str] = Field(default=None, description="Target language (for TRANSLATION)")
    detail_level: str = Field(default="MEDIUM", description="Detail level: CONCISE, MEDIUM, COMPREHENSIVE")
    objective: Optional[str] = Field(default=None, description="Specific goal or emphasis")
    title: Optional[str] = Field(default=None, description="Optional custom title")
    instructions: Optional[str] = Field(default=None, description="Custom prompt instructions")
    citation_mode: str = Field(default="INLINE", description="Citation mode: INLINE, FOOTNOTE, NONE, STRICT")
    include_evidence: bool = True
    include_metadata: bool = True
    model_id: Optional[str] = Field(default=None, description="PyTorch or registered model ID")
    model_type: str = Field(default="standard", description="Model type: standard, distilled, pytorch, external")
    active_parameter_config: Optional[Dict[str, Any]] = Field(default=None, description="Phase 11 active parameter configuration")


class TransformationContext(BaseModel):
    """Standardized internal context compiled for prompt builder and model inference."""
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_ids: List[str] = Field(default_factory=list)
    source_content: str
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    graph_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    facts: List[FactItem] = Field(default_factory=list)
    entities: List[EntityItem] = Field(default_factory=list)
    relations: List[RelationItem] = Field(default_factory=list)
    citations: List[CitationReference] = Field(default_factory=list)
    requested_output: str
    audience: str
    tone: str
    language: str
    target_language: Optional[str] = None
    detail_level: str
    objective: Optional[str] = None
    instructions: Optional[str] = None
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    insufficient_evidence: bool = False


class StructuredSection(BaseModel):
    """Individual section in structured output."""
    section_name: str
    title: str
    content: str
    evidence_ids: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class StructuredContent(BaseModel):
    """Parsed structured representation of generated content."""
    title: str
    summary: Optional[str] = None
    sections: List[StructuredSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransformationResponse(BaseModel):
    """Structured response output from TransformationEngine."""
    transformation_id: str
    document_ids: List[str] = Field(default_factory=list)
    output_type: str
    title: str
    content: str
    structured_content: Optional[StructuredContent] = None
    language: str
    audience: str
    tone: str
    detail_level: str
    model_id: str
    model_type: str
    citations: List[CitationReference] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    transformation_metadata: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    status: str = "completed"  # completed, failed, insufficient_evidence
    warnings: List[str] = Field(default_factory=list)
    insufficient_evidence: bool = False


class TransformationPreviewResponse(BaseModel):
    """Response model for preview mode execution."""
    output_type: str
    profile: TransformationProfile
    expected_structure: List[str]
    model_selection: Dict[str, Any]
    active_parameter_metadata: Dict[str, Any]
    estimated_constraints: Dict[str, Any]


__all__ = [
    "OutputTypeEnum",
    "AudienceEnum",
    "ToneEnum",
    "DetailLevelEnum",
    "CitationModeEnum",
    "EvidenceItem",
    "CitationReference",
    "FactItem",
    "EntityItem",
    "RelationItem",
    "TransformationProfile",
    "TransformationRequest",
    "TransformationContext",
    "StructuredSection",
    "StructuredContent",
    "TransformationResponse",
    "TransformationPreviewResponse",
]
