"""Neo4j Graph Repository & Mock Fallback (Phase 5).

Provides graph persistence, query retrieval, MERGE upserts, uniqueness constraints,
and in-memory mock fallback when no live Neo4j daemon is reachable.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.config import get_settings
from .interface import GraphStoreInterface
from .models import (
    DocumentNodeModel,
    GraphNodeModel,
    GraphPayload,
    GraphQueryResult,
    GraphRelationshipModel,
)
from .neo4j import Neo4jDriverAdapter
from .queries import (
    CREATE_DOCUMENT_ID_CONSTRAINT,
    CREATE_ENTITY_ID_CONSTRAINT,
    FIND_ENTITY_QUERY,
    GET_DOCUMENT_GRAPH_QUERY,
    GET_ENTITY_RELATIONSHIPS_QUERY,
    GET_NEIGHBORS_QUERY,
    MERGE_DOCUMENT_QUERY,
    MERGE_ENTITY_QUERY,
    MERGE_MENTIONS_QUERY,
    SEARCH_ENTITIES_QUERY,
    build_merge_relation_query,
)

log = logging.getLogger("gen-transform.graph.repository")


class MockNeo4jGraphStore(GraphStoreInterface):
    """In-memory Graph Store providing full Phase 5 functionality when Neo4j is offline."""

    def __init__(self) -> None:
        self.documents: Dict[str, DocumentNodeModel] = {}
        self.nodes: Dict[str, GraphNodeModel] = {}
        self.mentions: List[Tuple[str, str]] = []  # (document_id, entity_id)
        self.relationships: List[GraphRelationshipModel] = []
        self.is_mock = True

    def init_constraints(self) -> bool:
        log.debug("MockNeo4jGraphStore initialized mock constraints.")
        return True

    def add_entity(self, entity_id: str, label: str, properties: Dict[str, Any]) -> bool:
        cname = properties.get("canonical_name") or properties.get("name") or entity_id
        etype = properties.get("entity_type") or label
        surfaces = properties.get("surface_forms") or [cname]
        conf = float(properties.get("confidence", 0.9))

        target_id = entity_id
        cname_lower = cname.lower()
        for eid, node in self.nodes.items():
            if (
                eid == entity_id
                or node.canonical_name.lower() == cname_lower
                or cname_lower in [s.lower() for s in node.surface_forms]
            ):
                target_id = eid
                break

        if target_id in self.nodes:
            existing = self.nodes[target_id]
            existing.canonical_name = cname
            existing.entity_type = etype
            for s in surfaces:
                if s not in existing.surface_forms:
                    existing.surface_forms.append(s)
        else:
            self.nodes[entity_id] = GraphNodeModel(
                entity_id=entity_id,
                label=label,
                canonical_name=cname,
                entity_type=etype,
                surface_forms=surfaces,
                confidence=conf,
            )
        return True

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        props = properties or {}
        rid = props.get("relation_id") or f"rel_{len(self.relationships)+1:03d}"
        doc_id = props.get("document_id", "")
        page = int(props.get("page", 1))
        ev_text = str(props.get("evidence_text", ""))
        conf = float(props.get("confidence", 0.9))

        # MERGE check: avoid duplicate identical relationships
        for r in self.relationships:
            if r.source_id == source_id and r.target_id == target_id and r.relation_type == rel_type:
                r.confidence = max(r.confidence, conf)
                if ev_text and not r.evidence_text:
                    r.evidence_text = ev_text
                return True

        self.relationships.append(
            GraphRelationshipModel(
                relation_id=rid,
                source_id=source_id,
                target_id=target_id,
                relation_type=rel_type,
                confidence=conf,
                document_id=doc_id,
                page=page,
                evidence_text=ev_text,
            )
        )
        return True

    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        log.debug("Mock query executed: %s (params: %s)", cypher[:60], params)
        return []

    def ingest_payload(self, payload: GraphPayload) -> bool:
        """In-memory transactional ingestion of document graph payload."""
        # 1. Document Node
        self.documents[payload.document.document_id] = payload.document

        # 2. Entity Nodes & Mentions
        for node in payload.nodes:
            self.add_entity(
                entity_id=node.entity_id,
                label=node.entity_type,
                properties={
                    "canonical_name": node.canonical_name,
                    "entity_type": node.entity_type,
                    "surface_forms": node.surface_forms,
                    "confidence": node.confidence,
                },
            )
            mention_key = (payload.document.document_id, node.entity_id)
            if mention_key not in self.mentions:
                self.mentions.append(mention_key)

        # 3. Relationships with evidence
        for rel in payload.relationships:
            self.add_relationship(
                source_id=rel.source_id,
                target_id=rel.target_id,
                rel_type=rel.relation_type,
                properties={
                    "relation_id": rel.relation_id,
                    "confidence": rel.confidence,
                    "document_id": rel.document_id or payload.document.document_id,
                    "page": rel.page,
                    "evidence_text": rel.evidence_text,
                },
            )
        return True

    def find_entity(self, entity_id: str) -> Optional[GraphNodeModel]:
        if entity_id in self.nodes:
            return self.nodes[entity_id]
        eid_lower = entity_id.lower()
        for node in self.nodes.values():
            if node.canonical_name.lower() == eid_lower or eid_lower in [s.lower() for s in node.surface_forms]:
                return node
        return None

    def get_entity_relationships(self, entity_id: str) -> List[GraphRelationshipModel]:
        matched = []
        for r in self.relationships:
            if r.source_id == entity_id or r.target_id == entity_id:
                matched.append(r)
        return matched

    def get_neighbors(self, entity_id: str, depth: int = 1, limit: int = 20) -> List[GraphNodeModel]:
        neighbor_ids = set()
        for r in self.relationships:
            if r.source_id == entity_id:
                neighbor_ids.add(r.target_id)
            elif r.target_id == entity_id:
                neighbor_ids.add(r.source_id)

        result = []
        for nid in neighbor_ids:
            if nid in self.nodes:
                result.append(self.nodes[nid])
        return result

    def get_document_graph(self, document_id: str) -> GraphQueryResult:
        doc = self.documents.get(document_id)
        if not doc:
            return GraphQueryResult(ok=False, document_id=document_id, node_count=0, edge_count=0)

        mentioned_eids = {eid for did, eid in self.mentions if did == document_id}
        doc_nodes = [self.nodes[eid].model_dump() for eid in mentioned_eids if eid in self.nodes]
        doc_rels = [r.model_dump() for r in self.relationships if r.document_id == document_id]

        return GraphQueryResult(
            ok=True,
            document_id=document_id,
            nodes=doc_nodes,
            relationships=doc_rels,
            node_count=len(doc_nodes),
            edge_count=len(doc_rels),
        )

    def search_entities(self, query_str: str, limit: int = 20) -> List[GraphNodeModel]:
        q = (query_str or "").lower().strip()
        matched = []
        for node in self.nodes.values():
            if q in node.canonical_name.lower() or any(q in s.lower() for s in node.surface_forms):
                matched.append(node)
                if len(matched) >= limit:
                    break
        return matched


class Neo4jGraphRepository(GraphStoreInterface):
    """Production Neo4j Repository implementation executing Cypher against live Neo4j."""

    def __init__(self, adapter: Optional[Neo4jDriverAdapter] = None) -> None:
        self.adapter = adapter or Neo4jDriverAdapter()
        self.is_mock = False

    def init_constraints(self) -> bool:
        """Create uniqueness constraints for Entity entity_id and Document document_id."""
        try:
            self.adapter.execute_query(CREATE_ENTITY_ID_CONSTRAINT)
            self.adapter.execute_query(CREATE_DOCUMENT_ID_CONSTRAINT)
            log.info("Neo4j uniqueness constraints initialized successfully.")
            return True
        except Exception as exc:
            log.warning("Failed to initialize Neo4j constraints: %s", exc)
            return False

    def add_entity(self, entity_id: str, label: str, properties: Dict[str, Any]) -> bool:
        cname = properties.get("canonical_name") or properties.get("name") or entity_id
        etype = properties.get("entity_type") or label
        surfaces = properties.get("surface_forms") or [cname]
        conf = float(properties.get("confidence", 0.9))

        params = {
            "entity_id": entity_id,
            "canonical_name": cname,
            "entity_type": etype,
            "surface_forms": surfaces,
            "confidence": conf,
        }
        try:
            self.adapter.execute_query(MERGE_ENTITY_QUERY, params)
            return True
        except Exception as exc:
            log.error("Neo4j add_entity failed (%s): %s", entity_id, exc)
            return False

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        props = properties or {}
        rid = props.get("relation_id") or f"rel_001"
        doc_id = props.get("document_id", "")
        page = int(props.get("page", 1))
        ev_text = str(props.get("evidence_text", ""))
        conf = float(props.get("confidence", 0.9))

        query_str = build_merge_relation_query(rel_type)
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "relation_id": rid,
            "confidence": conf,
            "document_id": doc_id,
            "page": page,
            "evidence_text": ev_text,
            "created_at": props.get("created_at", ""),
        }
        try:
            self.adapter.execute_query(query_str, params)
            return True
        except Exception as exc:
            log.error("Neo4j add_relationship failed (%s-[%s]->%s): %s", source_id, rel_type, target_id, exc)
            return False

    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.adapter.execute_query(cypher, params)

    def ingest_payload(self, payload: GraphPayload) -> bool:
        """Transactional batch insertion of complete Document GraphPayload into Neo4j."""

        def _transaction_work(tx: Any) -> bool:
            # 1. Document MERGE
            doc_p = payload.document.model_dump()
            tx.run(MERGE_DOCUMENT_QUERY, doc_p)

            # 2. Entity MERGE & Document MENTIONS
            for node in payload.nodes:
                e_params = {
                    "entity_id": node.entity_id,
                    "canonical_name": node.canonical_name,
                    "entity_type": node.entity_type,
                    "surface_forms": node.surface_forms,
                    "confidence": node.confidence,
                }
                tx.run(MERGE_ENTITY_QUERY, e_params)
                tx.run(
                    MERGE_MENTIONS_QUERY,
                    {"document_id": payload.document.document_id, "entity_id": node.entity_id, "created_at": doc_p["created_at"]},
                )

            # 3. Relationship MERGE
            for rel in payload.relationships:
                r_cypher = build_merge_relation_query(rel.relation_type)
                r_params = {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "relation_id": rel.relation_id,
                    "confidence": rel.confidence,
                    "document_id": rel.document_id or payload.document.document_id,
                    "page": rel.page,
                    "evidence_text": rel.evidence_text,
                    "created_at": rel.created_at,
                }
                tx.run(r_cypher, r_params)

            return True

        try:
            return self.adapter.execute_transaction(_transaction_work)
        except Exception as exc:
            log.error("Neo4j transaction ingest failed for document %s: %s", payload.document.document_id, exc)
            raise RuntimeError(f"Neo4j transaction failed: {exc}") from exc

    def find_entity(self, entity_id: str) -> Optional[GraphNodeModel]:
        rows = self.adapter.execute_query(FIND_ENTITY_QUERY, {"entity_id": entity_id, "name": entity_id})
        if not rows:
            return None
        row = rows[0]
        return GraphNodeModel(
            entity_id=row["id"],
            canonical_name=row["canonical_name"],
            entity_type=row["entity_type"],
            surface_forms=row.get("surface_forms") or [],
            confidence=float(row.get("confidence", 0.9)),
        )

    def get_entity_relationships(self, entity_id: str) -> List[GraphRelationshipModel]:
        rows = self.adapter.execute_query(GET_ENTITY_RELATIONSHIPS_QUERY, {"entity_id": entity_id})
        rels = []
        for idx, row in enumerate(rows, start=1):
            rels.append(
                GraphRelationshipModel(
                    relation_id=f"rel_{idx:03d}",
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relation_type=row["relation"],
                    confidence=float(row.get("confidence", 0.9)),
                    document_id=row.get("document_id", ""),
                    evidence_text=row.get("evidence_text", ""),
                )
            )
        return rels

    def get_neighbors(self, entity_id: str, limit: int = 20) -> List[GraphNodeModel]:
        rows = self.adapter.execute_query(GET_NEIGHBORS_QUERY, {"entity_id": entity_id, "limit": limit})
        nodes = []
        for row in rows:
            nodes.append(
                GraphNodeModel(
                    entity_id=row["id"],
                    canonical_name=row["canonical_name"],
                    entity_type=row["entity_type"],
                )
            )
        return nodes

    def get_document_graph(self, document_id: str) -> GraphQueryResult:
        rows = self.adapter.execute_query(GET_DOCUMENT_GRAPH_QUERY, {"document_id": document_id})
        nodes_dict = {}
        rels = []

        for idx, row in enumerate(rows, start=1):
            src_id = row.get("source_id")
            src_name = row.get("source_name")
            tgt_id = row.get("target_id")
            tgt_name = row.get("target_name")

            if src_id and src_id not in nodes_dict:
                nodes_dict[src_id] = {"id": src_id, "canonical_name": src_name}
            if tgt_id and tgt_id not in nodes_dict:
                nodes_dict[tgt_id] = {"id": tgt_id, "canonical_name": tgt_name}

            if row.get("relation") and src_id and tgt_id:
                rels.append(
                    {
                        "relation_id": f"rel_{idx:03d}",
                        "source_id": src_id,
                        "relation_type": row["relation"],
                        "target_id": tgt_id,
                    }
                )

        nodes_list = list(nodes_dict.values())
        return GraphQueryResult(
            ok=True,
            document_id=document_id,
            nodes=nodes_list,
            relationships=rels,
            node_count=len(nodes_list),
            edge_count=len(rels),
        )

    def search_entities(self, query_str: str, limit: int = 20) -> List[GraphNodeModel]:
        rows = self.adapter.execute_query(SEARCH_ENTITIES_QUERY, {"query": query_str, "limit": limit})
        nodes = []
        for row in rows:
            nodes.append(
                GraphNodeModel(
                    entity_id=row["id"],
                    canonical_name=row["canonical_name"],
                    entity_type=row["entity_type"],
                    confidence=float(row.get("confidence", 0.9)),
                )
            )
        return nodes


_GLOBAL_GRAPH_REPO: Optional[Union[Neo4jGraphRepository, MockNeo4jGraphStore]] = None


def get_graph_repository() -> Union[Neo4jGraphRepository, MockNeo4jGraphStore]:
    """Resolve Neo4j repository singleton: returns real Neo4j repository if reachable, mock store otherwise."""
    global _GLOBAL_GRAPH_REPO
    if _GLOBAL_GRAPH_REPO is not None:
        return _GLOBAL_GRAPH_REPO

    settings = get_settings()
    if settings.neo4j_enabled:
        adapter = Neo4jDriverAdapter()
        if adapter.verify_connectivity():
            repo = Neo4jGraphRepository(adapter)
            repo.init_constraints()
            _GLOBAL_GRAPH_REPO = repo
            return repo

    log.info("Neo4j daemon unreachable; initializing MockNeo4jGraphStore fallback.")
    mock_repo = MockNeo4jGraphStore()
    _GLOBAL_GRAPH_REPO = mock_repo
    return mock_repo


def set_graph_repository(repo: Union[Neo4jGraphRepository, MockNeo4jGraphStore]) -> None:
    """Inject a specific graph repository instance (for testing / mocking)."""
    global _GLOBAL_GRAPH_REPO
    _GLOBAL_GRAPH_REPO = repo


def reset_graph_repository() -> None:
    """Clear cached graph repository singleton."""
    global _GLOBAL_GRAPH_REPO
    _GLOBAL_GRAPH_REPO = None


Neo4jBoundaryRepository = Neo4jGraphRepository

__all__ = [
    "Neo4jGraphRepository",
    "Neo4jBoundaryRepository",
    "MockNeo4jGraphStore",
    "get_graph_repository",
    "set_graph_repository",
    "reset_graph_repository",
]
