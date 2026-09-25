"""Graph Module (Phase 5): Neo4j Knowledge Graph Integration.

Translates DocLink extracted knowledge into persistent Neo4j graph nodes, relationships,
document mentions, and evidence pointers.
"""
from __future__ import annotations

from .interface import GraphStoreInterface
from .mapper import map_doclink_result_to_payload
from .models import (
    DocumentNodeModel,
    GraphHealthResponse,
    GraphNodeModel,
    GraphPayload,
    GraphQueryResult,
    GraphRelationshipModel,
)
from .neo4j import Neo4jDriverAdapter
from .repository import (
    MockNeo4jGraphStore,
    Neo4jBoundaryRepository,
    Neo4jGraphRepository,
    get_graph_repository,
    reset_graph_repository,
    set_graph_repository,
)
from .service import GraphService

__all__ = [
    "GraphStoreInterface",
    "Neo4jBoundaryRepository",
    "Neo4jGraphRepository",
    "MockNeo4jGraphStore",
    "Neo4jDriverAdapter",
    "GraphService",
    "DocumentNodeModel",
    "GraphNodeModel",
    "GraphRelationshipModel",
    "GraphPayload",
    "GraphQueryResult",
    "GraphHealthResponse",
    "map_doclink_result_to_payload",
    "get_graph_repository",
    "set_graph_repository",
    "reset_graph_repository",
]
