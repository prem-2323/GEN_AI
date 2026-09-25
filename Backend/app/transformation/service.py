"""Transformation module boundary wrapping existing transformation engines."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..core.logging import get_logger

log = get_logger("transformation.service")


class TransformationService:
    """Architectural boundary for document transformation engine."""

    @staticmethod
    def generate_deliverable(
        project_id: str,
        uid: str,
        deliverable_type: str,
        uckr_id: Optional[str] = None,
        uckr_version: Optional[int] = None,
        custom_instructions: str = "",
    ) -> Dict[str, Any]:
        """Generate deliverable via existing transformation service."""
        from ..services.transformation.transformation_service import generate_single_deliverable
        return generate_single_deliverable(
            project_id=project_id,
            uid=uid,
            deliverable_type=deliverable_type,
            uckr_id=uckr_id,
            uckr_version=uckr_version,
            custom_instructions=custom_instructions,
        )

    @staticmethod
    def run_batch_transformation(
        project_id: str,
        uid: str,
        deliverable_types: Optional[List[str]] = None,
        uckr_id: Optional[str] = None,
        uckr_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate all standard deliverables for a project."""
        from ..services.transformation.transformation_service import generate_all_deliverables
        return generate_all_deliverables(
            project_id=project_id,
            uid=uid,
            deliverable_types=deliverable_types,
            uckr_id=uckr_id,
            uckr_version=uckr_version,
        )


transformation_service = TransformationService()
