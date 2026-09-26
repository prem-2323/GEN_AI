from app.models.uckr import TimelineNode
from app.services.ai.qwen_service import (
    _deterministic_extractive_analysis,
    _extract_timeline_deterministic,
)
from app.services.ai.pipeline_orchestrator import _extractive_analysis
from app.services.uckr.uckr_builder import build_uckr_from_analysis
from app.services.uckr.pipeline_uckr import build_uckr
from app.services.uckr.uckr_validator import validate_timeline


SAMPLE_TEXT = (
    "The implementation is estimated to take 12 months. "
    "The first three months will focus on requirements and system design, "
    "followed by six months of development and testing. "
    "The final three months will be used for pilot deployment, staff training, and improvements."
)


def test_timeline_extraction_builds_grounded_uckr_nodes():
    timeline = _extract_timeline_deterministic(SAMPLE_TEXT)

    assert [node["description"] for node in timeline] == [
        "Total implementation",
        "Requirements and system design",
        "Development and testing",
        "Pilot deployment, staff training, and improvements",
    ]
    assert [node["duration_value"] for node in timeline] == [12, 3, 6, 3]
    assert [node["sequence"] for node in timeline] == [1, 2, 3, 4]

    analysis = _deterministic_extractive_analysis(SAMPLE_TEXT)
    record = build_uckr_from_analysis(
        analysis,
        {"name": "timeline-sample", "extractedText": SAMPLE_TEXT},
        uid="test-user",
        project_id="test-project",
        source_id="test-source",
    )
    persisted = record.model_dump(mode="json")

    assert len(persisted["timeline"]) == 4
    assert all(node["sourceFactId"] for node in persisted["timeline"])
    assert all(node["sourceText"] in SAMPLE_TEXT for node in persisted["timeline"])
    assert persisted["statistics"]["totalTimelineNodes"] == 4
    assert persisted["statistics"]["timelineConsistent"] is True
    assert persisted["validation"]["timelineConsistency"]["calculated_total"] == 12
    assert persisted["validation"]["checks"]["timeline_grounding"] is True


def test_timeline_validation_detects_mismatch_and_unknown_units():
    mismatched = [
        TimelineNode(id="T-1", description="Total implementation", duration_value=12, duration_unit="months", kind="total"),
        TimelineNode(id="T-2", description="Phase one", duration_value=3, duration_unit="months"),
        TimelineNode(id="T-3", description="Phase two", duration_value=6, duration_unit="months"),
    ]
    assert validate_timeline(mismatched)["consistent"] is False

    incomparable = [
        TimelineNode(id="T-1", description="Total implementation", duration_value=1, duration_unit="years", kind="total"),
        TimelineNode(id="T-2", description="Phase one", duration_value=6, duration_unit="months"),
    ]
    assert validate_timeline(incomparable)["consistent"] is None

    incomplete = [
        TimelineNode(id="T-1", description="Total implementation", duration_value=12, duration_unit="months", kind="total"),
        TimelineNode(id="T-2", description="Phase one", duration_value=3, duration_unit="months"),
        TimelineNode(id="T-3", description="Phase two"),
    ]
    assert validate_timeline(incomplete)["consistent"] is None
    assert validate_timeline(incomplete)["phase_count"] == 2


def test_active_analyze_pipeline_persists_timeline_validation():
    analysis = _extractive_analysis(SAMPLE_TEXT)
    uckr = build_uckr(
        {"text": {"content": SAMPLE_TEXT}},
        analysis,
        uid="test-user",
        project_id="test-project",
        source_id="test-source",
    )

    assert len(uckr["timeline"]) == 4
    assert uckr["stats"]["timelineConsistent"] is True
    assert uckr["stats"]["timelineTotalDuration"] == 12
    assert uckr["stats"]["timelinePhaseCount"] == 3
    assert uckr["validation"]["checks"]["timeline_grounding"] is True