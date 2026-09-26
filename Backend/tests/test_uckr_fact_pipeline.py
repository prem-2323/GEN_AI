"""Unit tests for sentence-level UCKR fact extraction, boundary repair, and quality metrics."""
from __future__ import annotations

import pytest
from app.services.uckr.fact_service import (
    split_into_sentences,
    merge_and_repair_facts,
    validate_fact,
    process_and_deduplicate_facts,
)
from app.services.uckr.uckr_validator import validate_uckr
from app.models.uckr import UCKRRecord, Fact, Entity, Metric, Citation, TimelineNode


def test_sentence_boundary_detection():
    sample_text = (
        "Artificial Intelligence (AI) is changing the way students learn and teachers teach.\n"
        "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.\n"
        "They can also help students understand difficult topics, answer questions, and practice lessons.\n"
        "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.\n"
        "AI can save time and make education more accessible.\n"
        "However, AI should be used responsibly.\n"
        "Students should not depend completely on AI for their studies.\n"
        "Human teachers, critical thinking, creativity, and communication skills remain important."
    )

    sentences = split_into_sentences(sample_text)
    assert len(sentences) == 8, f"Expected 8 sentences, got {len(sentences)}"
    assert sentences[0] == "Artificial Intelligence (AI) is changing the way students learn and teachers teach."
    assert "and teachers teach" in sentences[0]


def test_fact_merge_and_repair():
    source_text = (
        "Artificial Intelligence (AI) is changing the way students learn and teachers teach. "
        "AI can save time and make education more accessible."
    )
    
    # Fragmented facts simulating over-aggressive splitting
    fragmented_facts = [
        {"text": "Artificial Intelligence (AI) is changing the way students learn"},
        {"text": "teachers teach."},
        {"text": "AI can save time"},
        {"text": "and make education more accessible."},
    ]

    repaired = merge_and_repair_facts(fragmented_facts, source_text)
    assert len(repaired) == 2, f"Expected 2 merged facts, got {len(repaired)}"
    assert "Artificial Intelligence (AI) is changing the way students learn and teachers teach" in repaired[0]["statement"]
    assert "AI can save time and make education more accessible" in repaired[1]["statement"]


def test_validate_fact_grounding():
    source_text = "Artificial Intelligence is changing the way students learn and teachers teach."
    assert validate_fact("Artificial Intelligence is changing the way students learn and teachers teach.", source_text) is True
    assert validate_fact("Students learn through Artificial Intelligence.", source_text) is True
    assert validate_fact("Completely unrelated quantum mechanics claim.", source_text) is False


def test_uckr_quality_score_card():
    facts = [
        Fact(
            factId=f"fact_{i:03d}",
            statement=stmt,
            sourceDoc="source",
            page=1,
            quote=stmt,
        )
        for i, stmt in enumerate([
            "Artificial Intelligence is changing the way students learn and teachers teach.",
            "AI-powered tools provide personalized learning experiences.",
            "Human teachers and critical thinking remain essential.",
        ], start=1)
    ]

    entities = [
        Entity(entityId="entity_001", canonicalName="Artificial Intelligence"),
        Entity(entityId="entity_002", canonicalName="Teachers"),
    ]

    record = UCKRRecord(
        uckrId="uckr_test_001",
        projectId="proj_test",
        sourceId="src_test",
        userId="user_test",
        facts=facts,
        entities=entities,
        citations=[Citation(citationId=f"cit_{i:03d}", sourceId="src_test", factId=f.factId, quote=f.statement) for i, f in enumerate(facts, 1)],
    )

    result = validate_uckr(record)
    assert result.valid is True
    assert result.groundingIndex == 100.0
    assert result.factCompleteness >= 90.0
    assert result.factConsistency == 100.0
    assert result.entityConsistency == 100.0
    assert result.numberConsistency == 100.0
    assert result.dateConsistency == 100.0
