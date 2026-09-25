"""Phase 7 RAG — Graph Search Retriever.

Interfaces with Phase 5 Graph Service (Neo4j / Mock) to query entity relationships
and subgraphs, standardizing structured graph evidence into RetrievalResult format.
"""
from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from ..graph.service import GraphService
from .schemas import QueryAnalysis, RetrievalResult

log = logging.getLogger("gen-transform.rag.graph_retriever")

MAX_GRAPH_DEPTH = 2
MAX_GRAPH_RESULTS = 20


class GraphRetriever:
    """Retrieves structurally relevant entity relationships from Neo4j knowledge graph."""

    def __init__(self, service: Optional[GraphService] = None) -> None:
        self.service = service or GraphService()

    def retrieve(
        self,
        analysis: QueryAnalysis,
        graph_depth: int = 1,
        document_id: Optional[str] = None,
        top_k: int = 10,
    ) -> Tuple[List[RetrievalResult], float]:
        """Perform graph retrieval using query analysis entities and keywords."""
        t_start = time.time()
        effective_depth = min(max(1, graph_depth), MAX_GRAPH_DEPTH)
        max_results = min(top_k, MAX_GRAPH_RESULTS)

        target_entities: List[str] = list(
            dict.fromkeys(analysis.entities + analysis.possible_graph_entities + analysis.keywords)
        )

        log.debug(
            "Graph search starting for targets: %s (depth=%d, doc_id=%s)",
            target_entities[:5],
            effective_depth,
            document_id,
        )

        results: List[RetrievalResult] = []
        visited_rels: Set[str] = set()

        # Step 1: If target document_id is provided, try retrieving complete document subgraph
        if document_id:
            try:
                doc_graph = self.service.get_document_graph(document_id)
                if doc_graph and doc_graph.relationships:
                    for rel in doc_graph.relationships:
                        rel_id = rel.get("relation_id") or f"{rel.get('source_id')}_{rel.get('relation_type')}_{rel.get('target_id')}"
                        if rel_id in visited_rels:
                            continue
                        visited_rels.add(rel_id)

                        src = rel.get("source_id", "Entity")
                        r_type = rel.get("relation_type", "RELATED_TO")
                        tgt = rel.get("target_id", "Entity")
                        ev_text = rel.get("evidence_text", "")
                        score = float(rel.get("confidence", 0.9))

                        readable_text = f"{src} --[{r_type}]--> {tgt}"
                        if ev_text:
                            readable_text += f" (Evidence: {ev_text})"

                        results.append(
                            RetrievalResult(
                                source_type="graph",
                                source_id=rel_id,
                                document_id=rel.get("document_id") or document_id,
                                text=readable_text,
                                score=score,
                                metadata={
                                    "source": src,
                                    "relation": r_type,
                                    "target": tgt,
                                    "page": rel.get("page", 1),
                                },
                                evidence={
                                    "source": src,
                                    "relation": r_type,
                                    "target": tgt,
                                    "evidence_text": ev_text,
                                    "page": rel.get("page", 1),
                                    "document_id": rel.get("document_id") or document_id,
                                },
                            )
                        )
            except Exception as exc:
                log.warning("Document graph retrieval error for '%s': %s", document_id, exc)

        # Step 2: Entity match & relationship expansion
        for ent_name in target_entities:
            if len(results) >= max_results:
                break
            if not ent_name or len(ent_name) < 2:
                continue

            # Search entity nodes in graph
            matched_nodes = self.service.search_entities(query=ent_name, limit=5)
            if not matched_nodes and ent_name:
                found = self.service.find_entity(ent_name)
                if found:
                    matched_nodes = [found]

            for node in matched_nodes:
                if len(results) >= max_results:
                    break

                node_id = node.get("entity_id") or node.get("canonical_name") or ent_name
                # Fetch 1-hop relationships
                rels = self.service.get_entity_relationships(node_id)
                for r in rels:
                    if len(results) >= max_results:
                        break

                    rel_doc_id = r.get("document_id", "")
                    if document_id and rel_doc_id and rel_doc_id != document_id:
                        continue

                    rel_id = r.get("relation_id") or f"{r.get('source_id')}_{r.get('relation_type')}_{r.get('target_id')}"
                    if rel_id in visited_rels:
                        continue
                    visited_rels.add(rel_id)

                    src = r.get("source_id", node_id)
                    r_type = r.get("relation_type", "RELATED_TO")
                    tgt = r.get("target_id", "Entity")
                    ev_text = r.get("evidence_text", "")
                    conf = float(r.get("confidence", 0.9))

                    readable_text = f"{src} --[{r_type}]--> {tgt}"
                    if ev_text:
                        readable_text += f" (Evidence: {ev_text})"

                    results.append(
                        RetrievalResult(
                            source_type="graph",
                            source_id=rel_id,
                            document_id=rel_doc_id or document_id,
                            text=readable_text,
                            score=conf,
                            metadata={
                                "source": src,
                                "relation": r_type,
                                "target": tgt,
                                "page": r.get("page", 1),
                            },
                            evidence={
                                "source": src,
                                "relation": r_type,
                                "target": tgt,
                                "evidence_text": ev_text,
                                "page": r.get("page", 1),
                                "document_id": rel_doc_id or document_id,
                            },
                        )
                    )

                # Hop 2 traversal if graph_depth > 1
                if effective_depth > 1 and len(results) < max_results:
                    neighbors = self.service.get_neighbors(node_id, depth=1)
                    for nbr in neighbors:
                        if len(results) >= max_results:
                            break
                        nbr_id = nbr.get("entity_id") or nbr.get("canonical_name")
                        if not nbr_id or nbr_id == node_id:
                            continue
                        nbr_rels = self.service.get_entity_relationships(nbr_id)
                        for r in nbr_rels:
                            if len(results) >= max_results:
                                break

                            rel_doc_id = r.get("document_id", "")
                            if document_id and rel_doc_id and rel_doc_id != document_id:
                                continue

                            rel_id = r.get("relation_id") or f"{r.get('source_id')}_{r.get('relation_type')}_{r.get('target_id')}"
                            if rel_id in visited_rels:
                                continue
                            visited_rels.add(rel_id)

                            src = r.get("source_id", nbr_id)
                            r_type = r.get("relation_type", "CONNECTED_TO")
                            tgt = r.get("target_id", "Node")
                            ev_text = r.get("evidence_text", "")
                            conf = float(r.get("confidence", 0.85)) * 0.9  # depth decay

                            readable_text = f"{src} --[{r_type}]--> {tgt}"
                            if ev_text:
                                readable_text += f" (Evidence: {ev_text})"

                            results.append(
                                RetrievalResult(
                                    source_type="graph",
                                    source_id=rel_id,
                                    document_id=rel_doc_id or document_id,
                                    text=readable_text,
                                    score=conf,
                                    metadata={
                                        "source": src,
                                        "relation": r_type,
                                        "target": tgt,
                                        "page": r.get("page", 1),
                                    },
                                    evidence={
                                        "source": src,
                                        "relation": r_type,
                                        "target": tgt,
                                        "evidence_text": ev_text,
                                        "page": r.get("page", 1),
                                        "document_id": rel_doc_id or document_id,
                                    },
                                )
                            )

        # Sort graph results by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:max_results]

        latency_ms = round((time.time() - t_start) * 1000, 2)
        log.debug("Graph retriever returned %d items in %sms", len(results), latency_ms)
        return results, latency_ms


__all__ = ["GraphRetriever"]
