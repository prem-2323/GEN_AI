"""Strict Pydantic schemas for Phase 5 Real UCKR Engine."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    sourceId: str
    chunkId: str = "chunk_001"
    pageNumber: int = 1
    paragraph: Optional[int] = None
    line: Optional[int] = None
    textQuote: Optional[str] = None


class Fact(BaseModel):
    factId: str = Field(default_factory=lambda: "fact_001")
    id: Optional[str] = None
    statement: str
    value: Optional[str] = None
    text: Optional[str] = None
    type: str = "event_fact"  # event_fact, metric_fact, proposition, risk_fact, action_fact, entity_fact
    confidence: float = Field(default=0.98, ge=0.0, le=1.0)
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)
    sourceDoc: str = "source"
    page: int = 1
    chunkId: str = "chunk_001"
    quote: str = ""
    usedInDeliverables: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.factId
        if not self.value:
            self.value = self.statement
        if not self.text:
            self.text = self.statement
        if not self.quote:
            self.quote = self.statement


class Entity(BaseModel):
    entityId: str = Field(default_factory=lambda: "entity_001")
    id: Optional[str] = None
    canonicalName: str
    name: Optional[str] = None
    type: str = "ORGANIZATION"  # PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, THREAT_ACTOR, PRODUCT, MALWARE, COUNTRY, SYSTEM, VULNERABILITY
    category: str = "Actor / Stakeholder"
    aliases: List[str] = Field(default_factory=list)
    mentions: int = 1
    role: str = ""
    confidence: float = Field(default=0.99, ge=0.0, le=1.0)
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.entityId
        if not self.name:
            self.name = self.canonicalName


class Event(BaseModel):
    eventId: str = Field(default_factory=lambda: "event_001")
    id: Optional[str] = None
    eventType: str = "INCIDENT"  # CYBER_ATTACK, DISCOVERY, ANNOUNCEMENT, INCIDENT, LAUNCH, ACQUISITION, POLICY_CHANGE, MEETING, RESEARCH, DETECTION, RESPONSE
    description: str
    name: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    timestamp: Optional[str] = None
    location: Optional[str] = None
    impact: str = ""
    actors: List[str] = Field(default_factory=list)
    participants: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.eventId
        if not self.name:
            self.name = self.description
        if not self.title:
            self.title = self.description
        if not self.date and self.timestamp:
            self.date = self.timestamp
        elif not self.timestamp and self.date:
            self.timestamp = self.date
        if not self.actors and self.participants:
            self.actors = self.participants
        elif not self.participants and self.actors:
            self.participants = self.actors


class Metric(BaseModel):
    metricId: str = Field(default_factory=lambda: "metric_001")
    id: Optional[str] = None
    name: str = "Metric"
    value: Any
    unit: str = ""
    context: str = ""
    date: Optional[str] = None
    confidence: float = Field(default=0.98, ge=0.0, le=1.0)
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.metricId


class Claim(BaseModel):
    claimId: str = Field(default_factory=lambda: "claim_001")
    id: Optional[str] = None
    statement: str
    text: Optional[str] = None
    claimType: str = "SOURCE_ASSERTION"  # SOURCE_ASSERTION, IMPACT, FINDING, HYPOTHESIS
    attribution: str = ""
    confidence: float = Field(default=0.92, ge=0.0, le=1.0)
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.claimId
        if not self.text:
            self.text = self.statement


class Action(BaseModel):
    actionId: str = Field(default_factory=lambda: "action_001")
    id: Optional[str] = None
    action: str
    text: Optional[str] = None
    actor: str = ""
    status: str = "RECOMMENDED"  # RECOMMENDED, MANDATORY, COMPLETED, IN_PROGRESS
    priority: str = "P1 High"  # P0 Immediate, P1 High, P2 Medium
    timeframe: str = ""
    owner: str = ""
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.actionId
        if not self.text:
            self.text = self.action
        if not self.owner and self.actor:
            self.owner = self.actor
        elif not self.actor and self.owner:
            self.actor = self.owner


class Relationship(BaseModel):
    relationshipId: str = Field(default_factory=lambda: "rel_001")
    id: Optional[str] = None
    sourceEntityId: str
    source: Optional[str] = None
    relationshipType: str = "RELATED_TO"  # CONDUCTED, TARGETED, LOCATED_IN, OWNED_BY, USED, PRODUCED, AFFECTED, CAUSED, PART_OF, RELATED_TO, ANNOUNCED, OPERATED_BY
    relation: Optional[str] = None
    targetEntityId: str
    target: Optional[str] = None
    confidence: float = Field(default=0.92, ge=0.0, le=1.0)
    sourceRefs: List[Union[SourceRef, Dict[str, Any], str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.relationshipId
        if not self.source:
            self.source = self.sourceEntityId
        if not self.target:
            self.target = self.targetEntityId
        if not self.relation:
            self.relation = self.relationshipType


class Topic(BaseModel):
    topicId: str = Field(default_factory=lambda: "topic_001")
    id: Optional[str] = None
    name: str
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.topicId


class Citation(BaseModel):
    citationId: str = Field(default_factory=lambda: "citation_001")
    id: Optional[str] = None
    factId: Optional[str] = None
    sourceId: str
    chunkId: str = "chunk_001"
    pageNumber: int = 1
    page: Optional[int] = None
    textQuote: str = ""
    excerpt: Optional[str] = None
    quote: Optional[str] = None
    sourceDoc: str = "source"
    type: str = "text"  # text, image, table, diagram
    imageId: Optional[str] = None
    description: Optional[str] = None
    location: Dict[str, Any] = Field(default_factory=lambda: {"page": 1})

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.citationId
        if not self.page:
            self.page = self.pageNumber
        elif not self.pageNumber and self.page:
            self.pageNumber = self.page
        if not self.excerpt and self.textQuote:
            self.excerpt = self.textQuote
        elif not self.textQuote and self.excerpt:
            self.textQuote = self.excerpt
        if not self.quote:
            self.quote = self.textQuote or self.excerpt or ""


class UCKRStatistics(BaseModel):
    totalFacts: int = 0
    totalEntities: int = 0
    totalEvents: int = 0
    totalMetrics: int = 0
    totalActions: int = 0
    totalClaims: int = 0
    totalRelationships: int = 0
    totalCitations: int = 0
    totalTopics: int = 0
    totalSources: int = 1
    coverage: float = 0.0
    grounding: float = 100.0
    groundingCoverage: float = 100.0
    readiness: float = 95.0

    # UI aliases
    facts: Optional[int] = None
    entities: Optional[int] = None
    events: Optional[int] = None
    metrics: Optional[int] = None
    claims: Optional[int] = None
    actions: Optional[int] = None
    relationships: Optional[int] = None
    citations: Optional[int] = None
    factCount: Optional[int] = None
    entityCount: Optional[int] = None
    eventCount: Optional[int] = None
    metricCount: Optional[int] = None
    citationCount: Optional[int] = None

    def model_post_init(self, __context: Any) -> None:
        self.facts = self.totalFacts
        self.entities = self.totalEntities
        self.events = self.totalEvents
        self.metrics = self.totalMetrics
        self.claims = self.totalClaims
        self.actions = self.totalActions
        self.relationships = self.totalRelationships
        self.citations = self.totalCitations

        self.factCount = self.totalFacts
        self.entityCount = self.totalEntities
        self.eventCount = self.totalEvents
        self.metricCount = self.totalMetrics
        self.citationCount = self.totalCitations
        self.groundingCoverage = self.grounding


class UCKRValidationResult(BaseModel):
    valid: bool = True
    status: str = "valid"  # valid | invalid
    uckrId: str = ""
    version: int = 1
    stats: Dict[str, int] = Field(default_factory=dict)
    citationCoverage: float = 100.0
    groundingCoverage: float = 100.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks: Dict[str, bool] = Field(default_factory=dict)
    brokenReferences: List[str] = Field(default_factory=list)
    missingCitations: List[str] = Field(default_factory=list)
    duplicateIds: List[str] = Field(default_factory=list)
    orphanRelationships: List[str] = Field(default_factory=list)
    validatedAt: str = ""


class UCKRRecord(BaseModel):
    id: Optional[str] = None
    uckrId: str
    projectId: str
    sourceId: str
    firebaseUid: str
    userId: str
    version: int = 1
    previousVersion: Optional[int] = None
    title: str = "Source Knowledge Base"
    summary: str = ""
    status: str = "valid"  # draft, building, validating, valid, invalid, failed

    facts: List[Fact] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    topics: List[Topic] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)

    validation: Optional[Dict[str, Any]] = None
    statistics: UCKRStatistics = Field(default_factory=UCKRStatistics)
    stats: Optional[Dict[str, Any]] = None
    provider: str = "qwen3:4b + gemma3:4b"
    createdAt: str = ""
    updatedAt: str = ""

    model_config = {"extra": "allow"}


# Legacy aliases
UckrModel = UCKRRecord
