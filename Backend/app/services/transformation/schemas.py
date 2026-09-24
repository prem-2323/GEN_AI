"""Output Schemas and JSON validation definitions for Phase 6 Deliverables."""
from __future__ import annotations

from typing import Any, Dict
from ...models.deliverable import (
    LinkedInContent,
    XThreadContent,
    ExecutiveSummaryContent,
    AdvisoryContent,
    InfographicContent,
    PresentationContent,
    VideoScriptContent,
)

DELIVERABLE_MODEL_MAP: Dict[str, Any] = {
    "linkedin": LinkedInContent,
    "x": XThreadContent,
    "executive_summary": ExecutiveSummaryContent,
    "advisory": AdvisoryContent,
    "infographic": InfographicContent,
    "presentation": PresentationContent,
    "video_script": VideoScriptContent,
}
