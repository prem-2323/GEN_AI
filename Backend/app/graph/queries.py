"""Centralized Cypher Queries for Neo4j (Phase 5).

No Cypher strings are hard-coded in API routes. All query templates live here.
"""
from __future__ import annotations

# Schema Uniqueness Constraints (Idempotent)
CREATE_ENTITY_ID_CONSTRAINT = (
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
    "FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE"
)

CREATE_DOCUMENT_ID_CONSTRAINT = (
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS "
    "FOR (d:Document) REQUIRE d.document_id IS UNIQUE"
)

CREATE_CHUNK_ID_CONSTRAINT = (
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS "
    "FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE"
)

CREATE_FACT_ID_CONSTRAINT = (
    "CREATE CONSTRAINT fact_id_unique IF NOT EXISTS "
    "FOR (f:Fact) REQUIRE f.fact_id IS UNIQUE"
)

CREATE_METRIC_ID_CONSTRAINT = (
    "CREATE CONSTRAINT metric_id_unique IF NOT EXISTS "
    "FOR (m:Metric) REQUIRE m.metric_id IS UNIQUE"
)

CREATE_CONCEPT_ID_CONSTRAINT = (
    "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS "
    "FOR (cp:Concept) REQUIRE cp.concept_id IS UNIQUE"
)

ALL_SCHEMA_CONSTRAINTS = [
    CREATE_DOCUMENT_ID_CONSTRAINT,
    CREATE_CHUNK_ID_CONSTRAINT,
    CREATE_ENTITY_ID_CONSTRAINT,
    CREATE_FACT_ID_CONSTRAINT,
    CREATE_METRIC_ID_CONSTRAINT,
    CREATE_CONCEPT_ID_CONSTRAINT,
]

# Ingestion / MERGE Queries
MERGE_DOCUMENT_QUERY = (
    "MERGE (d:Document {document_id: $document_id}) "
    "SET d.filename = $filename, d.file_type = $file_type, d.updated_at = datetime() "
    "RETURN d.document_id AS document_id"
)

MERGE_CHUNK_QUERY = (
    "MERGE (c:Chunk {chunk_id: $chunk_id}) "
    "SET c.text = $text, c.page = $page, c.section = $section, c.document_id = $document_id, c.updated_at = datetime() "
    "RETURN c.chunk_id AS chunk_id"
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

MERGE_FACT_QUERY = (
    "MERGE (f:Fact {fact_id: $fact_id}) "
    "SET f.statement = $statement, f.confidence = $confidence, f.document_id = $document_id, f.updated_at = datetime() "
    "RETURN f.fact_id AS fact_id"
)

MERGE_METRIC_QUERY = (
    "MERGE (m:Metric {metric_id: $metric_id}) "
    "SET m.name = $name, m.value = $value, m.context = $context, m.document_id = $document_id, m.updated_at = datetime() "
    "RETURN m.metric_id AS metric_id"
)

MERGE_CONCEPT_QUERY = (
    "MERGE (cp:Concept {concept_id: $concept_id}) "
    "SET cp.name = $name, cp.description = $description, cp.document_id = $document_id, cp.updated_at = datetime() "
    "RETURN cp.concept_id AS concept_id"
)

# Relationship MERGE Queries
MERGE_HAS_CHUNK_QUERY = (
    "MATCH (d:Document {document_id: $document_id}), (c:Chunk {chunk_id: $chunk_id}) "
    "MERGE (d)-[r:HAS_CHUNK]->(c) "
    "RETURN type(r) AS rel_type"
)

MERGE_CHUNK_MENTIONS_ENTITY_QUERY = (
    "MATCH (c:Chunk {chunk_id: $chunk_id}), (e:Entity {entity_id: $entity_id}) "
    "MERGE (c)-[r:MENTIONS]->(e) "
    "RETURN type(r) AS rel_type"
)

MERGE_CHUNK_SUPPORTS_FACT_QUERY = (
    "MATCH (c:Chunk {chunk_id: $chunk_id}), (f:Fact {fact_id: $fact_id}) "
    "MERGE (c)-[r:SUPPORTS]->(f) "
    "RETURN type(r) AS rel_type"
)

MERGE_CHUNK_CONTAINS_METRIC_QUERY = (
    "MATCH (c:Chunk {chunk_id: $chunk_id}), (m:Metric {metric_id: $metric_id}) "
    "MERGE (c)-[r:CONTAINS_METRIC]->(m) "
    "RETURN type(r) AS rel_type"
)

MERGE_FACT_ABOUT_ENTITY_QUERY = (
    "MATCH (f:Fact {fact_id: $fact_id}), (e:Entity {entity_id: $entity_id}) "
    "MERGE (f)-[r:ABOUT]->(e) "
    "RETURN type(r) AS rel_type"
)

MERGE_MENTIONS_QUERY = (
    "MATCH (d:Document {document_id: $document_id}), (e:Entity {entity_id: $entity_id}) "
    "MERGE (d)-[r:MENTIONS]->(e) "
    "SET r.created_at = datetime() "
    "RETURN type(r) AS rel_type"
)

def build_merge_relation_query(rel_type: str) -> str:
    """Safely format MERGE query for a specific directed relationship type."""
    safe_rel_type = "".join(c if c.isalnum() or c == "_" else "_" for c in (rel_type or "RELATED_TO")).upper()
    return (
        f"MATCH (s:Entity {{entity_id: $source_id}}), (t:Entity {{entity_id: $target_id}}) "
        f"MERGE (s)-[r:{safe_rel_type} {{relation_id: $relation_id}}]->(t) "
        f"SET r.confidence = $confidence, "
        f"    r.document_id = $document_id, "
        f"    r.page = $page, "
        f"    r.evidence_text = $evidence_text, "
        f"    r.updated_at = datetime() "
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

FIND_DOCUMENT_FACTS_QUERY = (
    "MATCH (f:Fact) "
    "WHERE f.document_id = $document_id "
    "RETURN f.fact_id AS fact_id, f.statement AS statement, f.confidence AS confidence"
)

FIND_SUPPORTING_CHUNKS_QUERY = (
    "MATCH (c:Chunk)-[:SUPPORTS]->(f:Fact {fact_id: $fact_id}) "
    "RETURN c.chunk_id AS chunk_id, c.text AS text, c.page AS page"
)

SEARCH_ENTITIES_QUERY = (
    "MATCH (e:Entity) "
    "WHERE toLower(e.canonical_name) CONTAINS toLower($query) "
    "   OR any(sf IN e.surface_forms WHERE toLower(sf) CONTAINS toLower($query)) "
    "RETURN e.entity_id AS id, e.canonical_name AS canonical_name, e.entity_type AS entity_type, e.confidence AS confidence "
    "LIMIT $limit"
)

COUNT_ALL_NODES_AND_RELATIONS_QUERY = (
    "MATCH (n) WITH count(n) AS nodeCount MATCH ()-[r]->() RETURN nodeCount, count(r) AS relCount"
)

GET_NODE_COUNTS_BY_LABEL_QUERY = (
    "CALL { MATCH (d:Document) RETURN count(d) AS documents } "
    "CALL { MATCH (c:Chunk) RETURN count(c) AS chunks } "
    "CALL { MATCH (e:Entity) RETURN count(e) AS entities } "
    "CALL { MATCH (f:Fact) RETURN count(f) AS facts } "
    "CALL { MATCH (m:Metric) RETURN count(m) AS metrics } "
    "CALL { MATCH (cp:Concept) RETURN count(cp) AS concepts } "
    "RETURN documents, chunks, entities, facts, metrics, concepts"
)

__all__ = [
    "CREATE_ENTITY_ID_CONSTRAINT",
    "CREATE_DOCUMENT_ID_CONSTRAINT",
    "CREATE_CHUNK_ID_CONSTRAINT",
    "CREATE_FACT_ID_CONSTRAINT",
    "CREATE_METRIC_ID_CONSTRAINT",
    "CREATE_CONCEPT_ID_CONSTRAINT",
    "ALL_SCHEMA_CONSTRAINTS",
    "MERGE_DOCUMENT_QUERY",
    "MERGE_CHUNK_QUERY",
    "MERGE_ENTITY_QUERY",
    "MERGE_FACT_QUERY",
    "MERGE_METRIC_QUERY",
    "MERGE_CONCEPT_QUERY",
    "MERGE_HAS_CHUNK_QUERY",
    "MERGE_CHUNK_MENTIONS_ENTITY_QUERY",
    "MERGE_CHUNK_SUPPORTS_FACT_QUERY",
    "MERGE_CHUNK_CONTAINS_METRIC_QUERY",
    "MERGE_FACT_ABOUT_ENTITY_QUERY",
    "MERGE_MENTIONS_QUERY",
    "build_merge_relation_query",
    "FIND_ENTITY_QUERY",
    "GET_ENTITY_RELATIONSHIPS_QUERY",
    "GET_NEIGHBORS_QUERY",
    "GET_DOCUMENT_GRAPH_QUERY",
    "FIND_DOCUMENT_FACTS_QUERY",
    "FIND_SUPPORTING_CHUNKS_QUERY",
    "SEARCH_ENTITIES_QUERY",
    "COUNT_ALL_NODES_AND_RELATIONS_QUERY",
    "GET_NODE_COUNTS_BY_LABEL_QUERY",
]
