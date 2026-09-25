"""Graph Service (Phase 5 Orchestrator).

Orchestrates Phase 4 DocLink knowledge ingestion into Phase 5 Neo4j graph database,
and exposes graph retrieval query interfaces for Phase 7 Hybrid RAG.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from ..core.config import get_settings
from ..doclink.service import DocLinkService
from .mapper import map_doclink_result_to_payload
from .models import (
    GraphHealthResponse,
    GraphNodeModel,
    GraphPayload,
    GraphQueryResult,
    GraphRelationshipModel,
)
from .repository import (
    MockNeo4jGraphStore,
    Neo4jGraphRepository,
    get_graph_repository,
)

log = logging.getLogger("gen-transform.graph.service")


class GraphService:
    """Orchestrates Neo4j knowledge graph operations."""

    def __init__(self, repository: Optional[Union[Neo4jGraphRepository, MockNeo4jGraphStore]] = None) -> None:
        self.repo = repository

    def _get_repo(self) -> Union[Neo4jGraphRepository, MockNeo4jGraphStore]:
        if self.repo is not None:
            return self.repo
        return get_graph_repository()

    def ingest_doclink_result(self, doclink_result: Any) -> GraphQueryResult:
        """Map and persist Phase 4 DocLink result into Neo4j graph database."""
        payload: GraphPayload = map_doclink_result_to_payload(doclink_result)
        repo = self._get_repo()

        log.info(
            "Ingesting DocLink graph payload into Neo4j: document=%s, nodes=%d, edges=%d",
            payload.document.document_id,
            len(payload.nodes),
            len(payload.relationships),
        )

        ok = repo.ingest_payload(payload)

        return GraphQueryResult(
            ok=ok,
            document_id=payload.document.document_id,
            nodes=[n.model_dump() for n in payload.nodes],
            relationships=[r.model_dump() for r in payload.relationships],
            node_count=len(payload.nodes),
            edge_count=len(payload.relationships),
        )

    def ingest_document(self, document_id: str, use_llm: bool = True) -> GraphQueryResult:
        """Fetch extracted document, run DocLink analysis, and persist graph to Neo4j."""
        doclink_svc = DocLinkService()
        doclink_res = doclink_svc.analyze_document(document_id=document_id, use_llm=use_llm)
        return self.ingest_doclink_result(doclink_res)

    def find_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find entity node by entity_id or canonical name."""
        repo = self._get_repo()
        node = repo.find_entity(entity_id)
        return node.model_dump() if node else None

    def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retrieve all relationships connected to entity_id."""
        repo = self._get_repo()
        rels = repo.get_entity_relationships(entity_id)
        return [r.model_dump() for r in rels]

    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Retrieve 1-hop or 2-hop neighbor nodes for entity_id."""
        repo = self._get_repo()
        neighbors = repo.get_neighbors(entity_id, limit=20)
        return [n.model_dump() for n in neighbors]

    def get_document_graph(self, document_id: str) -> GraphQueryResult:
        """Retrieve complete subgraph connected to a document."""
        repo = self._get_repo()
        return repo.get_document_graph(document_id)

    def search_entities(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search entity nodes by name or alias substring match."""
        repo = self._get_repo()
        nodes = repo.search_entities(query, limit=limit)
        return [n.model_dump() for n in nodes]

    def health_check(self) -> GraphHealthResponse:
        """Perform Neo4j connectivity and status health audit."""
        settings = get_settings()
        repo = self._get_repo()

        if getattr(repo, "is_mock", False):
            return GraphHealthResponse(
                ok=True,
                status="healthy",
                neo4j="mock_fallback",
                uri=settings.neo4j_uri,
                database=settings.neo4j_database,
                error=None,
            )

        try:
            adapter = getattr(repo, "adapter", None)
            if adapter and adapter.verify_connectivity():
                return GraphHealthResponse(
                    ok=True,
                    status="healthy",
                    neo4j="connected",
                    uri=settings.neo4j_uri,
                    database=settings.neo4j_database,
                )
            return GraphHealthResponse(
                ok=False,
                status="degraded",
                neo4j="disconnected",
                uri=settings.neo4j_uri,
                database=settings.neo4j_database,
                error="Neo4j connectivity verification failed.",
            )
        except Exception as exc:
            return GraphHealthResponse(
                ok=False,
                status="offline",
                neo4j="disconnected",
                uri=settings.neo4j_uri,
                database=settings.neo4j_database,
                error=str(exc),
            )


__all__ = ["GraphService"]
