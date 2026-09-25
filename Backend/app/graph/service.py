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
    GraphNodeCountsModel,
    GraphNodeModel,
    GraphPayload,
    GraphQueryResult,
    GraphRelationshipModel,
    GraphStatusResponse,
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
        backend_choice = (getattr(settings, "graph_backend", "neo4j") or "neo4j").strip().lower()

        try:
            repo = self._get_repo()
            if getattr(repo, "is_mock", False):
                mock_nodes = len(getattr(repo, "nodes", {})) + len(getattr(repo, "documents", {}))
                mock_rels = len(getattr(repo, "relationships", {})) if isinstance(getattr(repo, "relationships", None), dict) else len(getattr(repo, "relationships", []))
                return GraphHealthResponse(
                    ok=True,
                    status="healthy",
                    backend="mock",
                    connected=True,
                    database="in_memory_mock",
                    neo4j_version="mock",
                    node_count=mock_nodes,
                    relationship_count=mock_rels,
                    error=None,
                )

            adapter = getattr(repo, "adapter", None)
            if adapter and adapter.verify_connectivity():
                # Query actual counts from Neo4j
                count_res = adapter.execute_read("MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS rels")
                node_cnt = count_res[0]["nodes"] if count_res else 0
                rel_cnt = count_res[0]["rels"] if count_res else 0
                return GraphHealthResponse(
                    ok=True,
                    status="healthy",
                    backend="neo4j",
                    connected=True,
                    database=settings.neo4j_database,
                    neo4j_version="5.x",
                    node_count=node_cnt,
                    relationship_count=rel_cnt,
                    error=None,
                )
            return GraphHealthResponse(
                ok=False,
                status="degraded",
                backend=backend_choice,
                connected=False,
                database=settings.neo4j_database,
                error=f"Neo4j instance at {settings.neo4j_uri} unreachable.",
            )
        except Exception as exc:
            return GraphHealthResponse(
                ok=False,
                status="offline",
                backend=backend_choice,
                connected=False,
                database=settings.neo4j_database,
                error=str(exc),
            )

    def get_status(self) -> GraphStatusResponse:
        """Retrieve detailed database status and node breakdown across labels."""
        settings = get_settings()
        backend_choice = (getattr(settings, "graph_backend", "neo4j") or "neo4j").strip().lower()

        try:
            repo = self._get_repo()
            if getattr(repo, "is_mock", False):
                mock_nodes = getattr(repo, "nodes", {})
                mock_docs = getattr(repo, "documents", {})
                mock_rels = getattr(repo, "relationships", [])
                counts = GraphNodeCountsModel(
                    documents=len(mock_docs),
                    chunks=0,
                    entities=len(mock_nodes),
                    facts=0,
                    metrics=0,
                    concepts=0,
                )
                return GraphStatusResponse(
                    backend="mock",
                    connected=True,
                    schema_initialized=True,
                    nodes=counts,
                    relationships=len(mock_rels),
                    error=None,
                )

            adapter = getattr(repo, "adapter", None)
            if not adapter or not adapter.verify_connectivity():
                return GraphStatusResponse(
                    backend="neo4j",
                    connected=False,
                    schema_initialized=False,
                    nodes=GraphNodeCountsModel(),
                    relationships=0,
                    error=f"Neo4j instance at {settings.neo4j_uri} unreachable.",
                )

            counts_query = (
                "OPTIONAL MATCH (d:Document) WITH count(d) AS docs "
                "OPTIONAL MATCH (c:Chunk) WITH docs, count(c) AS chks "
                "OPTIONAL MATCH (e:Entity) WITH docs, chks, count(e) AS ents "
                "OPTIONAL MATCH (f:Fact) WITH docs, chks, ents, count(f) AS fcts "
                "OPTIONAL MATCH (m:Metric) WITH docs, chks, ents, fcts, count(m) AS mets "
                "OPTIONAL MATCH (cp:Concept) WITH docs, chks, ents, fcts, mets, count(cp) AS cncpts "
                "OPTIONAL MATCH ()-[r]->() "
                "RETURN docs, chks, ents, fcts, mets, cncpts, count(r) AS rels"
            )
            res = adapter.execute_read(counts_query)
            row = res[0] if res else {}
            counts = GraphNodeCountsModel(
                documents=row.get("docs", 0),
                chunks=row.get("chks", 0),
                entities=row.get("ents", 0),
                facts=row.get("fcts", 0),
                metrics=row.get("mets", 0),
                concepts=row.get("cncpts", 0),
            )
            return GraphStatusResponse(
                backend="neo4j",
                connected=True,
                schema_initialized=True,
                nodes=counts,
                relationships=row.get("rels", 0),
                error=None,
            )
        except Exception as exc:
            return GraphStatusResponse(
                backend=backend_choice,
                connected=False,
                schema_initialized=False,
                nodes=GraphNodeCountsModel(),
                relationships=0,
                error=str(exc),
            )


__all__ = ["GraphService"]
