"""Validation module boundary wrapping existing consistency and validation engines."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..core.logging import get_logger

log = get_logger("validation.service")


class ValidationService:
    """Architectural boundary for deliverable consistency and validation checks."""

    @staticmethod
    def validate_deliverable(
        project_id: str,
        deliverable_id: str,
        uid: str,
    ) -> Dict[str, Any]:
        """Validate deliverable against UCKR ground truth."""
        from ..services.consistency.consistency_service import validate_deliverable_consistency
        return validate_deliverable_consistency(
            project_id=project_id,
            deliverable_id=deliverable_id,
            uid=uid,
        )

    @staticmethod
    def run_full_validation_suite(
        project_id: str,
        uid: str,
    ) -> Dict[str, Any]:
        """Run complete consistency validation across all project deliverables."""
        from ..services.consistency.consistency_service import validate_all_project_deliverables
        return validate_all_project_deliverables(
            project_id=project_id,
            uid=uid,
        )


validation_service = ValidationService()
