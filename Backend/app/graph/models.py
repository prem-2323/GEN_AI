"""Neo4j Knowledge Graph Models (Phase 5).

Data contracts for Document nodes, Entity nodes, Relationships, and Graph Query responses.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..utils.helpers import utcnow_iso


class DocumentNodeModel(BaseModel):
    """Neo4j Document Node contract (:Document)."""
    document_id: str
    filename: str = ""
    file_type: str = "pdf"
    created_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


class GraphNodeModel(BaseModel):
    """Neo4j Entity Node contract (:Entity)."""
    entity_id: str
    label: str = "Entity"
    canonical_name: str
    entity_type: str
    surface_forms: List[str] = Field(default_factory=list)
    confidence: float = 0.9
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class GraphRelationshipModel(BaseModel):
    """Neo4j Relationship contract (Source)-[RELATION_TYPE]->(Target)."""
    relation_id: str = Field(default_factory=lambda: "rel_001")
    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 0.9
    document_id: str = ""
    page: int = 1
    evidence_text: str = ""
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


class GraphPayload(BaseModel):
    """Bundle representing a complete document knowledge graph ready for transactional ingestion."""
    document: DocumentNodeModel
    nodes: List[GraphNodeModel] = Field(default_factory=list)
    relationships: List[GraphRelationshipModel] = Field(default_factory=list)


class GraphQueryResult(BaseModel):
    """Response contract for entity, relationship, or neighbor graph queries."""
    ok: bool = True
    entity_id: Optional[str] = None
    document_id: Optional[str] = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    neighbors: List[Dict[str, Any]] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


class GraphHealthResponse(BaseModel):
    """Neo4j health check contract."""
    ok: bool = True
    status: str = "healthy"  # healthy | degraded | offline
    neo4j: str = "connected"  # connected | disconnected | mock_fallback
    uri: str = ""
    database: str = ""
    error: Optional[str] = None


__all__ = [
    "DocumentNodeModel",
    "GraphNodeModel",
    "GraphRelationshipModel",
    "GraphPayload",
    "GraphQueryResult",
    "GraphHealthResponse",
]
