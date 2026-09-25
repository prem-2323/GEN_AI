"""Centralized Cypher Queries for Neo4j (Phase 5).

No Cypher strings are hard-coded in API routes. All query templates live here.
"""
from __future__ import annotations

# Schema Uniqueness Constraints
CREATE_ENTITY_ID_CONSTRAINT = (
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
    "FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE"
)

CREATE_DOCUMENT_ID_CONSTRAINT = (
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS "
    "FOR (d:Document) REQUIRE d.document_id IS UNIQUE"
)

# Ingestion / Merge Queries
MERGE_DOCUMENT_QUERY = (
    "MERGE (d:Document {document_id: $document_id}) "
    "SET d.filename = $filename, d.file_type = $file_type, d.updated_at = $created_at "
    "RETURN d.document_id AS document_id"
)

MERGE_ENTITY_QUERY = (
    "MERGE (e:Entity {entity_id: $entity_id}) "
    "SET e.canonical_name = $canonical_name, "
    "    e.entity_type = $entity_type, "
    "    e.surface_forms = $surface_forms, "
    "    e.confidence = $confidence, "
    "    e.updated_at = datetime() "
    "RETURN e.entity_id AS entity_id"
)

MERGE_MENTIONS_QUERY = (
    "MATCH (d:Document {document_id: $document_id}), (e:Entity {entity_id: $entity_id}) "
    "MERGE (d)-[r:MENTIONS]->(e) "
    "SET r.created_at = $created_at "
    "RETURN type(r) AS rel_type"
)


def build_merge_relation_query(rel_type: str) -> str:
    """Safely format MERGE query for a specific directed relationship type."""
    # Sanitize relation type label to valid Cypher identifier
    safe_rel_type = "".join(c if c.isalnum() or c == "_" else "_" for c in (rel_type or "RELATED_TO")).upper()
    return (
        f"MATCH (s:Entity {{entity_id: $source_id}}), (t:Entity {{entity_id: $target_id}}) "
        f"MERGE (s)-[r:{safe_rel_type} {{relation_id: $relation_id}}]->(t) "
        f"SET r.confidence = $confidence, "
        f"    r.document_id = $document_id, "
        f"    r.page = $page, "
        f"    r.evidence_text = $evidence_text, "
        f"    r.created_at = $created_at "
        f"RETURN r.relation_id AS relation_id"
    )


# Graph Retrieval Queries
FIND_ENTITY_QUERY = (
    "MATCH (e:Entity) "
    "WHERE e.entity_id = $entity_id OR toLower(e.canonical_name) = toLower($name) "
    "RETURN e.entity_id AS id, e.canonical_name AS canonical_name, e.entity_type AS entity_type, "
    "       e.surface_forms AS surface_forms, e.confidence AS confidence"
)

GET_ENTITY_RELATIONSHIPS_QUERY = (
    "MATCH (e:Entity {entity_id: $entity_id})-[r]-(target:Entity) "
    "RETURN e.entity_id AS source_id, e.canonical_name AS source_name, "
    "       type(r) AS relation, r.confidence AS confidence, r.document_id AS document_id, "
    "       r.evidence_text AS evidence_text, target.entity_id AS target_id, target.canonical_name AS target_name"
)

GET_NEIGHBORS_QUERY = (
    "MATCH (e:Entity {entity_id: $entity_id})-[r]-(neighbor:Entity) "
    "RETURN neighbor.entity_id AS id, neighbor.canonical_name AS canonical_name, "
    "       neighbor.entity_type AS entity_type, type(r) AS relation_type "
    "LIMIT $limit"
)

GET_DOCUMENT_GRAPH_QUERY = (
    "MATCH (d:Document {document_id: $document_id})-[m:MENTIONS]->(e:Entity) "
    "OPTIONAL MATCH (e)-[r]->(t:Entity) "
    "WHERE r.document_id = $document_id "
    "RETURN d.document_id AS document_id, e.entity_id AS source_id, e.canonical_name AS source_name, "
    "       type(r) AS relation, t.entity_id AS target_id, t.canonical_name AS target_name"
)

SEARCH_ENTITIES_QUERY = (
    "MATCH (e:Entity) "
    "WHERE toLower(e.canonical_name) CONTAINS toLower($query) "
    "   OR any(sf IN e.surface_forms WHERE toLower(sf) CONTAINS toLower($query)) "
    "RETURN e.entity_id AS id, e.canonical_name AS canonical_name, e.entity_type AS entity_type, e.confidence AS confidence "
    "LIMIT $limit"
)

__all__ = [
    "CREATE_ENTITY_ID_CONSTRAINT",
    "CREATE_DOCUMENT_ID_CONSTRAINT",
    "MERGE_DOCUMENT_QUERY",
    "MERGE_ENTITY_QUERY",
    "MERGE_MENTIONS_QUERY",
    "build_merge_relation_query",
    "FIND_ENTITY_QUERY",
    "GET_ENTITY_RELATIONSHIPS_QUERY",
    "GET_NEIGHBORS_QUERY",
    "GET_DOCUMENT_GRAPH_QUERY",
    "SEARCH_ENTITIES_QUERY",
]
