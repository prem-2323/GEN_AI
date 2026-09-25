"""Phase 7 RAG — Query Understanding Module.

Analyzes natural language queries to extract mentioned entities, intent, keywords,
graph search targets, semantic queries, and retrieval routing (SEMANTIC, GRAPH, HYBRID).
"""
from __future__ import annotations

import re
import logging
from typing import List, Set

from .schemas import QueryAnalysis, QueryTypeEnum

log = logging.getLogger("gen-transform.rag.query_analyzer")

# Common stop words for keyword extraction
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "can", "could", "should", "would", "may", "might", "must",
    "shall", "how", "where", "when", "why", "in", "on", "at", "by", "for", "with",
    "about", "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "to", "from", "up", "down", "in", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "just",
    "don", "shouldve", "now", "d", "ll", "m", "o", "re", "ve", "y", "does", "use",
    "uses", "used"
}

# Regex for capitalized proper nouns, technical terms, and acronyms
_ENTITY_REGEX = re.compile(
    r"\b([A-Z][a-zA-Z0-9\-_]{1,}(?:\s+[A-Z][a-zA-Z0-9\-_]{1,}){0,3})\b"
)

# Known technologies & domain terms matching (case-insensitive)
_TECH_PATTERNS = [
    "pytorch", "cuda", "openai", "nvidia", "transformer", "hbm3e", "gpu", "gpt",
    "gpt-4", "gemini", "gemma", "qwen", "neo4j", "python", "fastapi", "react",
    "docker", "kubernetes", "tensorflow", "scikit-learn", "langchain", "llama",
    "ollama", "redis", "mongodb", "postgresql", "cypher"
]

# Intent classification keywords
_TECH_INTENT_WORDS = {"technology", "technologies", "tech", "stack", "framework", "uses", "used", "tool", "tools", "library"}
_RELATION_INTENT_WORDS = {"connect", "connected", "connection", "relationship", "relate", "linked", "link", "hierarchy", "graph", "network", "node"}
_SUMMARY_INTENT_WORDS = {"summary", "summarize", "overview", "explain", "describe", "detail", "document", "about"}


class QueryAnalyzer:
    """Understands user query intent, entities, keywords, and routing strategy."""

    def analyze(self, query: str) -> QueryAnalysis:
        raw_query = (query or "").strip()
        if not raw_query:
            return QueryAnalysis(
                query="",
                entities=[],
                intent="general_qa",
                keywords=[],
                possible_graph_entities=[],
                semantic_query="",
                query_type=QueryTypeEnum.HYBRID,
            )

        # 1. Entity Extraction
        found_entities: List[str] = []
        # Capitalized sequences
        matches = _ENTITY_REGEX.findall(raw_query)
        for m in matches:
            if m.lower() not in _STOP_WORDS and len(m) > 1 and m not in found_entities:
                found_entities.append(m)

        # Tech keyword match
        query_lower = raw_query.lower()
        for tech in _TECH_PATTERNS:
            if tech in query_lower:
                # Find exact casing in raw query or capitalize
                idx = query_lower.find(tech)
                exact_sub = raw_query[idx : idx + len(tech)]
                if exact_sub and exact_sub not in found_entities:
                    found_entities.append(exact_sub)

        # 2. Keyword Extraction
        words = re.findall(r"\b[a-zA-Z0-9\-_]{2,}\b", query_lower)
        keywords = [w for w in words if w not in _STOP_WORDS]

        # 3. Intent Determination
        intent = "general_qa"
        if any(w in query_lower for w in _TECH_INTENT_WORDS):
            intent = "technology_usage"
        elif any(w in query_lower for w in _RELATION_INTENT_WORDS):
            intent = "structural_relationship"
        elif any(w in query_lower for w in _SUMMARY_INTENT_WORDS):
            intent = "semantic_summary"

        # 4. Routing Classification (SEMANTIC, GRAPH, HYBRID)
        query_type = QueryTypeEnum.HYBRID
        if any(w in query_lower for w in _RELATION_INTENT_WORDS) and not any(w in query_lower for w in _SUMMARY_INTENT_WORDS):
            query_type = QueryTypeEnum.GRAPH
        elif any(w in query_lower for w in _SUMMARY_INTENT_WORDS) and not found_entities:
            query_type = QueryTypeEnum.SEMANTIC

        # 5. Graph Entities
        possible_graph_entities = list(dict.fromkeys(found_entities + [k.capitalize() for k in keywords[:4]]))

        # 6. Semantic Query Refinement
        semantic_query = raw_query

        log.debug(
            "Query analyzed: query='%s', entities=%s, intent='%s', type='%s'",
            raw_query[:40],
            found_entities,
            intent,
            query_type.value,
        )

        return QueryAnalysis(
            query=raw_query,
            entities=found_entities,
            intent=intent,
            keywords=keywords,
            possible_graph_entities=possible_graph_entities,
            semantic_query=semantic_query,
            query_type=query_type,
        )


__all__ = ["QueryAnalyzer"]
