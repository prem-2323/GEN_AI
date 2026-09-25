"""DocLink (Phase 4) schemas - Entity / Fact / Relation structured knowledge contract.

DocLink converts the Phase 3 ``ExtractedDocument`` (human-readable text) into a
machine-readable knowledge representation::

    ExtractedDocument -> Entity / Fact / Relation extraction -> Normalization
        -> Deduplication -> Evidence references -> UCKR-compatible projection
        -> graph-ready nodes / edges

Phase 4 boundary: this module never talks to Neo4j. It only produces a
graph-ready structure that Phase 5 can persist.

Field naming follows the Phase 4 specification (snake_case: ``entity_id``,
``canonical_name``, ``fact_id``, ``source.text_span``) because this structure is
the explicit hand-off contract to the Phase 5 graph store.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..utils.helpers import utcnow_iso


# ---------------------------------------------------------------------------
# Controlled taxonomies
# ---------------------------------------------------------------------------
class EntityType(str, Enum):
    """Controlled entity taxonomy - deliberately small and extensible."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    TIME = "TIME"
    EVENT = "EVENT"
    PRODUCT = "PRODUCT"
    TECHNOLOGY = "TECHNOLOGY"
    DOCUMENT = "DOCUMENT"
    LAW = "LAW"
    POLICY = "POLICY"
    COUNTRY = "COUNTRY"
    CITY = "CITY"
    AMOUNT = "AMOUNT"
    IDENTIFIER = "IDENTIFIER"


class RelationType(str, Enum):
    """Controlled relation vocabulary - extensible, but always normalised to it."""
    WORKS_FOR = "WORKS_FOR"
    LOCATED_IN = "LOCATED_IN"
    PART_OF = "PART_OF"
    CREATED = "CREATED"
    DEVELOPED = "DEVELOPED"
    USES = "USES"
    OWNS = "OWNS"
    PRODUCED = "PRODUCED"
    ANNOUNCED = "ANNOUNCED"
    PARTNERED_WITH = "PARTNERED_WITH"
    RELATED_TO = "RELATED_TO"
    MENTIONS = "MENTIONS"
    OCCURRED_ON = "OCCURRED_ON"
    APPLIES_TO = "APPLIES_TO"


class FactType(str, Enum):
    """Controlled factual-statement taxonomy."""
    STATEMENT = "STATEMENT"
    EVENT = "EVENT"
    MEASUREMENT = "MEASUREMENT"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    ACTION = "ACTION"
    RISK = "RISK"
    DEFINITION = "DEFINITION"


ENTITY_TYPE_ALIASES: Dict[str, str] = {
    "org": "ORGANIZATION", "organisation": "ORGANIZATION", "organization": "ORGANIZATION",
    "company": "ORGANIZATION", "corporation": "ORGANIZATION", "business": "ORGANIZATION",
    "institution": "ORGANIZATION", "agency": "ORGANIZATION", "ngo": "ORGANIZATION",
    "norp": "ORGANIZATION", "group": "ORGANIZATION", "team": "ORGANIZATION",
    "person": "PERSON", "people": "PERSON", "human": "PERSON", "per": "PERSON",
    "location": "LOCATION", "loc": "LOCATION", "gpe": "LOCATION", "place": "LOCATION",
    "fac": "LOCATION", "address": "LOCATION", "region": "LOCATION",
    "country": "COUNTRY", "nation": "COUNTRY", "state": "COUNTRY",
    "city": "CITY", "town": "CITY", "municipality": "CITY",
    "date": "DATE", "datetime": "DATE", "day": "DATE", "year": "DATE", "month": "DATE",
    "time": "TIME", "timestamp": "TIME", "duration": "TIME",
    "event": "EVENT", "incident": "EVENT", "conference": "EVENT",
    "product": "PRODUCT", "service": "PRODUCT", "system": "TECHNOLOGY",
    "platform": "TECHNOLOGY", "technology": "TECHNOLOGY", "tech": "TECHNOLOGY",
    "software": "TECHNOLOGY", "tool": "TECHNOLOGY", "framework": "TECHNOLOGY",
    "model": "TECHNOLOGY",
    "document": "DOCUMENT", "doc": "DOCUMENT", "report": "DOCUMENT",
    "publication": "DOCUMENT",
    "law": "LAW", "legislation": "LAW", "act": "LAW", "regulation": "LAW",
    "policy": "POLICY", "standard": "POLICY",
    "amount": "AMOUNT", "money": "AMOUNT", "monetary": "AMOUNT", "quantity": "AMOUNT",
    "number": "AMOUNT", "percentage": "AMOUNT", "metric": "AMOUNT", "cardinal": "AMOUNT",
    "identifier": "IDENTIFIER", "id": "IDENTIFIER", "code": "IDENTIFIER",
    "cve": "IDENTIFIER", "cwe": "IDENTIFIER", "hash": "IDENTIFIER", "email": "IDENTIFIER",
    "url": "IDENTIFIER", "ip": "IDENTIFIER", "domain": "IDENTIFIER", "token": "IDENTIFIER",
}



RELATION_TYPE_ALIASES: Dict[str, str] = {
    "works_for": "WORKS_FOR", "works at": "WORKS_FOR", "employed_by": "WORKS_FOR",
    "employee_of": "WORKS_FOR", "member_of": "WORKS_FOR", "staff_of": "WORKS_FOR",
    "located_in": "LOCATED_IN", "based_in": "LOCATED_IN", "headquartered_in": "LOCATED_IN",
    "in": "LOCATED_IN", "at": "LOCATED_IN", "resides_in": "LOCATED_IN",
    "part_of": "PART_OF", "belongs_to": "PART_OF", "subsidiary_of": "PART_OF",
    "created": "CREATED", "creates": "CREATED", "authored": "CREATED", "founded": "CREATED",
    "developed": "DEVELOPED", "develops": "DEVELOPED", "built": "DEVELOPED",
    "engineered": "DEVELOPED", "designed": "DEVELOPED",
    "uses": "USES", "use": "USES", "used": "USES", "used_by": "USES", "utilises": "USES",
    "utilizes": "USES", "relies_on": "USES", "depends_on": "USES", "leverages": "USES",
    "owns": "OWNS", "own": "OWNS", "acquired": "OWNS", "acquires": "OWNS", "has": "OWNS",
    "produced": "PRODUCED", "produces": "PRODUCED", "manufactured": "PRODUCED",
    "released": "PRODUCED", "releases": "PRODUCED", "published": "PRODUCED",
    "announced": "ANNOUNCED", "announce": "ANNOUNCED", "unveiled": "ANNOUNCED",
    "declared": "ANNOUNCED", "reported": "ANNOUNCED", "introduced": "ANNOUNCED",
    "partnered_with": "PARTNERED_WITH", "partnered": "PARTNERED_WITH",
    "partners_with": "PARTNERED_WITH", "collaborated_with": "PARTNERED_WITH",
    "allied_with": "PARTNERED_WITH",
    "related_to": "RELATED_TO", "relates_to": "RELATED_TO", "associated_with": "RELATED_TO",
    "connected_to": "RELATED_TO", "linked_to": "RELATED_TO", "affects": "RELATED_TO",
    "mentions": "MENTIONS", "mentioned_in": "MENTIONS", "references": "MENTIONS",
    "cites": "MENTIONS", "covers": "MENTIONS",
    "occurred_on": "OCCURRED_ON", "happened_on": "OCCURRED_ON", "dated": "OCCURRED_ON",
    "took_place_on": "OCCURRED_ON", "scheduled_for": "OCCURRED_ON",
    "applies_to": "APPLIES_TO", "applicable_to": "APPLIES_TO", "governs": "APPLIES_TO",
    "targets": "APPLIES_TO",
}


def normalize_entity_type(raw: Optional[str]) -> Optional[str]:
    """Map a free-form entity type onto the controlled taxonomy (None if unmappable)."""
    if not raw:
        return None
    candidate = str(raw).strip()
    if not candidate:
        return None
    upper = candidate.upper().replace(" ", "_").replace("-", "_")
    if upper in EntityType.__members__:
        return upper
    lowered = candidate.lower().replace("-", "_").replace(" ", "_")
    return ENTITY_TYPE_ALIASES.get(lowered) or ENTITY_TYPE_ALIASES.get(candidate.lower())


def normalize_relation_type(raw: Optional[str]) -> str:
    """Map a free-form relation phrase onto the controlled relation vocabulary."""
    if not raw:
        return RelationType.RELATED_TO.value
    candidate = " ".join(str(raw).strip().replace("-", "_").split())
    upper = candidate.upper().replace(" ", "_")
    if upper in RelationType.__members__:
        return upper
    return RELATION_TYPE_ALIASES.get(candidate.lower(), RelationType.RELATED_TO.value)


def is_valid_entity_type(raw: Optional[str]) -> bool:
    """True when the value maps cleanly onto the controlled entity taxonomy."""
    return normalize_entity_type(raw) is not None


def is_valid_relation_type(raw: Optional[str]) -> bool:
    """True when the value is an exact member of the controlled relation vocabulary."""
    return bool(raw) and str(raw).upper().replace(" ", "_") in RelationType.__members__



# ---------------------------------------------------------------------------
# Evidence / source tracking
# ---------------------------------------------------------------------------
class SourceSpan(BaseModel):
    """Evidence pointer retained by every entity, fact and relation.

    Phase 4 captures references only. The full provenance / lineage engine
    (lineage graphs, citations, consistency proofs) belongs to Phase 14.
    """
    document_id: str = ""
    source_id: str = ""
    chunk_id: str = "chunk_001"
    page: int = 1
    paragraph: Optional[int] = None
    text_span: str = ""
    char_start: Optional[int] = None
    char_end: Optional[int] = None

    model_config = {"extra": "allow"}

    def key(self) -> tuple:
        return (self.document_id, self.chunk_id, self.page, self.text_span[:160])


# ---------------------------------------------------------------------------
# Canonical DocLink knowledge objects
# ---------------------------------------------------------------------------
class DocLinkEntity(BaseModel):
    """A normalised entity with surface forms, canonical name and evidence."""
    entity_id: str = Field(default_factory=lambda: "ent_001")
    text: str
    canonical_name: str
    surface_forms: List[str] = Field(default_factory=list)
    type: str = EntityType.ORGANIZATION.value
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    mentions: int = 1
    evidence: List[SourceSpan] = Field(default_factory=list)
    aliases_resolved: List[str] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class DocLinkFact(BaseModel):
    """A subject-predicate-object factual statement with time + evidence."""
    fact_id: str = Field(default_factory=lambda: "fact_001")
    statement: str
    subject: str = ""
    subject_id: Optional[str] = None
    predicate: str = ""
    object: str = ""
    object_id: Optional[str] = None
    time: Optional[str] = None
    fact_type: str = FactType.STATEMENT.value
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence: List[SourceSpan] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class DocLinkRelation(BaseModel):
    """A directed relation between two entities in the controlled vocabulary."""
    relation_id: str = Field(default_factory=lambda: "rel_001")
    source: str
    source_id: Optional[str] = None
    relation: str = RelationType.RELATED_TO.value
    target: str
    target_id: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence: List[SourceSpan] = Field(default_factory=list)

    model_config = {"extra": "allow"}



# ---------------------------------------------------------------------------
# Raw (model output) shapes - validated before becoming canonical objects
# ---------------------------------------------------------------------------
class RawEntity(BaseModel):
    """Loose shape accepted from an LLM or the deterministic extractor."""
    text: str = ""
    name: str = ""
    type: str = ""
    canonical_name: Optional[str] = None
    confidence: Optional[float] = None
    role: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    quote: Optional[str] = None

    model_config = {"extra": "allow", "populate_by_name": True}

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return None


class RawFact(BaseModel):
    """Loose subject-predicate-object shape accepted from an extractor."""
    subject: str = ""
    predicate: str = ""
    object: str = ""
    time: Optional[str] = None
    statement: Optional[str] = None
    fact_type: Optional[str] = None
    confidence: Optional[float] = None
    quote: Optional[str] = None

    model_config = {"extra": "allow"}

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return None


class RawRelation(BaseModel):
    """Loose source-relation-target shape accepted from an extractor."""
    source: str = ""
    relation: str = ""
    target: str = ""
    confidence: Optional[float] = None
    quote: Optional[str] = None

    model_config = {"extra": "allow"}

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return None



# ---------------------------------------------------------------------------
# Chunking + extraction containers
# ---------------------------------------------------------------------------
class ExtractionChunk(BaseModel):
    """A logical section / page slice of the extracted document (Phase 4 chunking)."""
    chunk_id: str
    document_id: str = ""
    page: int = 1
    section: str = ""
    index: int = 1
    text: str = ""
    char_start: int = 0
    char_end: int = 0
    word_count: int = 0


class ChunkExtraction(BaseModel):
    """Per-chunk extraction output before global merge / dedup."""
    chunk_id: str
    page: int = 1
    provider: str = "deterministic"
    entities: List[RawEntity] = Field(default_factory=list)
    facts: List[RawFact] = Field(default_factory=list)
    relations: List[RawRelation] = Field(default_factory=list)
    rejected: List[str] = Field(default_factory=list)


class DocLinkStatistics(BaseModel):
    """Deterministic counters used for validation, UI and later graph readiness."""
    totalChunks: int = 0
    totalEntities: int = 0
    totalFacts: int = 0
    totalRelations: int = 0
    totalEvidence: int = 0
    mergedEntities: int = 0
    duplicateEntitiesRemoved: int = 0
    duplicateFactsRemoved: int = 0
    duplicateRelationsRemoved: int = 0
    rejectedItems: int = 0
    evidenceCoverage: float = 0.0
    entityTypes: Dict[str, int] = Field(default_factory=dict)
    relationTypes: Dict[str, int] = Field(default_factory=dict)


class DocLinkValidationReport(BaseModel):
    """Semantic validation report produced by validator.validate_doclink_result."""
    valid: bool = True
    status: str = "valid"  # valid | invalid
    documentId: str = ""
    stats: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    rejectedEntities: List[str] = Field(default_factory=list)
    rejectedFacts: List[str] = Field(default_factory=list)
    rejectedRelations: List[str] = Field(default_factory=list)
    orphanRelations: List[str] = Field(default_factory=list)
    duplicateIds: List[str] = Field(default_factory=list)
    invalidTypes: List[str] = Field(default_factory=list)
    missingEvidence: List[str] = Field(default_factory=list)
    evidenceCoverage: float = 0.0
    checks: Dict[str, bool] = Field(default_factory=dict)
    validated_at: str = Field(default_factory=utcnow_iso)



# ---------------------------------------------------------------------------
# Graph-ready structure (Phase 4 output - persisted only in Phase 5)
# ---------------------------------------------------------------------------
class GraphNode(BaseModel):
    id: str
    label: str
    name: str
    type: str = ""
    confidence: float = 0.9
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str = ""
    source: str
    type: str
    target: str
    confidence: float = 0.9
    properties: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[SourceSpan] = Field(default_factory=list)


class GraphReadyGraph(BaseModel):
    """Neo4j-ready nodes/edges - deliberately NOT written to Neo4j in Phase 4."""
    document_id: str = ""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    statistics: Dict[str, int] = Field(default_factory=dict)
    persisted: bool = False  # stays False until Phase 5


# ---------------------------------------------------------------------------
# UCKR-compatible projection (Phase 4 -> UCKR contract)
# ---------------------------------------------------------------------------
class UCKRProjection(BaseModel):
    """Structured, deterministic UCKR-compatible representation of DocLink output."""
    document_id: str = ""
    documentId: str = ""
    sourceId: str = ""
    projectId: str = ""
    phase: str = "phase_4_doclink"
    provider: str = "deterministic"
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    statistics: DocLinkStatistics = Field(default_factory=DocLinkStatistics)
    generated_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}



# ---------------------------------------------------------------------------
# Top-level DocLink result
# ---------------------------------------------------------------------------
class DocLinkResult(BaseModel):
    """Complete Phase 4 knowledge representation for one extracted document."""
    document_id: str
    documentId: str = ""
    sourceId: str = ""
    projectId: str = ""
    document_name: str = ""
    version: int = 1
    status: str = "completed"  # completed | partial | failed
    provider: str = "deterministic"
    chunked: bool = False
    chunks: List[ExtractionChunk] = Field(default_factory=list)
    entities: List[DocLinkEntity] = Field(default_factory=list)
    facts: List[DocLinkFact] = Field(default_factory=list)
    relations: List[DocLinkRelation] = Field(default_factory=list)
    statistics: DocLinkStatistics = Field(default_factory=DocLinkStatistics)
    validation: Optional[DocLinkValidationReport] = None
    graph: GraphReadyGraph = Field(default_factory=GraphReadyGraph)
    uckr: UCKRProjection = Field(default_factory=UCKRProjection)
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# API request / response contracts
# ---------------------------------------------------------------------------
class DocLinkAnalyzeRequest(BaseModel):
    """Request body for POST /doclink/analyze."""
    document_id: Optional[str] = None
    documentId: Optional[str] = None
    sourceId: Optional[str] = None
    projectId: Optional[str] = None
    force: bool = False
    useLlm: bool = True
    chunk_size: int = 1800

    model_config = {"extra": "allow", "populate_by_name": True}

    def resolved_document_id(self) -> str:
        return (self.document_id or self.documentId or self.sourceId or "").strip()


class DocLinkTextRequest(BaseModel):
    """Request body for POST /doclink/analyze-text (ad-hoc text analysis)."""
    text: str
    document_id: str = "doc_inline"
    name: str = "inline-text"
    useLlm: bool = True
    chunk_size: int = 1800

    model_config = {"extra": "allow"}


class DocLinkAnalyzeResponse(BaseModel):
    """Phase 4 API response (mirrors the specification shape + explicit extras)."""
    document_id: str
    documentId: str = ""
    status: str = "completed"
    provider: str = ""
    entities: List[DocLinkEntity] = Field(default_factory=list)
    facts: List[DocLinkFact] = Field(default_factory=list)
    relations: List[DocLinkRelation] = Field(default_factory=list)
    statistics: DocLinkStatistics = Field(default_factory=DocLinkStatistics)
    validation: Optional[DocLinkValidationReport] = None
    graph: Optional[GraphReadyGraph] = None
    uckr: Optional[UCKRProjection] = None

    model_config = {"extra": "allow"}


__all__ = [
    "EntityType", "RelationType", "FactType",
    "ENTITY_TYPE_ALIASES", "RELATION_TYPE_ALIASES",
    "normalize_entity_type", "normalize_relation_type",
    "is_valid_entity_type", "is_valid_relation_type",
    "SourceSpan",
    "DocLinkEntity", "DocLinkFact", "DocLinkRelation",
    "RawEntity", "RawFact", "RawRelation",
    "ExtractionChunk", "ChunkExtraction",
    "DocLinkStatistics", "DocLinkValidationReport",
    "GraphNode", "GraphEdge", "GraphReadyGraph",
    "UCKRProjection", "DocLinkResult",
    "DocLinkAnalyzeRequest", "DocLinkTextRequest", "DocLinkAnalyzeResponse",
]

