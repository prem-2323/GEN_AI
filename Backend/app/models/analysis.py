"""Pydantic schemas for Phase 3 AI Content Understanding and Analysis."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    page: Optional[int] = None
    paragraph: Optional[int] = None
    line: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None


class ExtractedFact(BaseModel):
    id: str = Field(default_factory=lambda: "fact_001")
    text: str
    confidence: float = 0.98
    type: str = "Proposition"  # Proposition, Metric, Entity Finding, Timeline, Action Mandate, Risk
    source: Optional[SourceLocation] = None


class ExtractedEntity(BaseModel):
    id: str = Field(default_factory=lambda: "entity_001")
    name: str
    type: str = "organization"  # organization, person, technology, vulnerability, infrastructure, location
    role: Optional[str] = ""
    confidence: float = 0.99
    source: Optional[SourceLocation] = None


class ExtractedEvent(BaseModel):
    id: str = Field(default_factory=lambda: "event_001")
    event: str
    date: Optional[str] = None
    impact: Optional[str] = None
    actors: List[str] = Field(default_factory=list)
    confidence: float = 0.95
    source: Optional[SourceLocation] = None


class ExtractedMetric(BaseModel):
    id: str = Field(default_factory=lambda: "metric_001")
    name: Optional[str] = ""
    value: Any
    unit: Optional[str] = ""
    context: Optional[str] = ""
    confidence: float = 0.98
    source: Optional[SourceLocation] = None


class ExtractedClaim(BaseModel):
    id: str = Field(default_factory=lambda: "claim_001")
    claim: str
    evidence: Optional[str] = ""
    confidence: float = 0.95
    source: Optional[SourceLocation] = None


class ExtractedAction(BaseModel):
    id: str = Field(default_factory=lambda: "action_001")
    action: str
    priority: str = "P1 High"  # P0 Immediate, P1 High, P2 Medium
    timeframe: Optional[str] = ""
    owner: Optional[str] = ""
    confidence: float = 0.95
    source: Optional[SourceLocation] = None


class ExtractedTopic(BaseModel):
    id: str = Field(default_factory=lambda: "topic_001")
    topic: str
    relevance: float = 0.95
    source: Optional[SourceLocation] = None


class ExtractedRelationship(BaseModel):
    id: str = Field(default_factory=lambda: "rel_001")
    source: str
    relation: str
    target: str
    confidence: float = 0.95


class VisualEvidence(BaseModel):
    imageId: str
    type: str = "chart"  # chart, table, diagram, screenshot, logo, graph, visual_entity
    description: str = ""
    textDetected: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.92
    source: Optional[SourceLocation] = None


class TextAnalysis(BaseModel):
    summary: str = ""
    facts: List[ExtractedFact] = Field(default_factory=list)
    entities: List[ExtractedEntity] = Field(default_factory=list)
    events: List[ExtractedEvent] = Field(default_factory=list)
    metrics: List[ExtractedMetric] = Field(default_factory=list)
    claims: List[ExtractedClaim] = Field(default_factory=list)
    actions: List[ExtractedAction] = Field(default_factory=list)
    topics: List[ExtractedTopic] = Field(default_factory=list)
    relationships: List[ExtractedRelationship] = Field(default_factory=list)


class AnalysisRecord(BaseModel):
    id: str
    analysisId: str
    projectId: str
    sourceId: str
    userId: str
    contentHash: str = ""
    textAnalysis: TextAnalysis = Field(default_factory=TextAnalysis)
    visualAnalysis: List[VisualEvidence] = Field(default_factory=list)
    modelInfo: Dict[str, str] = Field(default_factory=lambda: {"textModel": "qwen3:4b", "visionModel": "gemma3:4b"})
    analysisMode: str = "deterministic"  # local_llm, deterministic, hybrid
    status: str = "completed"  # queued, loading_source, analyzing_text, analyzing_images, merging_analysis, validating_analysis, completed, failed
    stage: str = "completed"
    progress: int = 100
    errorMessage: Optional[str] = None
    createdAt: str = ""
    updatedAt: str = ""

    model_config = {"extra": "allow"}
