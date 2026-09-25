"""Phase 12 Transformation Engine Module.

Provides modular transformation capabilities for converting validated source knowledge
and optimized evidence into structured communication deliverables.
"""

from .config import TransformationSettings, get_transformation_settings
from .formatters import TransformationFormatter
from .input_adapter import TransformationInputAdapter
from .output_parser import TransformationOutputParser
from .prompt_builder import TransformationPromptBuilder
from .registry import TransformationRegistry, get_transformation_registry, reset_transformation_registry
from .schemas import (
    AudienceEnum,
    CitationModeEnum,
    CitationReference,
    DetailLevelEnum,
    EntityItem,
    EvidenceItem,
    FactItem,
    OutputTypeEnum,
    RelationItem,
    StructuredContent,
    StructuredSection,
    ToneEnum,
    TransformationContext,
    TransformationPreviewResponse,
    TransformationProfile,
    TransformationRequest,
    TransformationResponse,
)
from .service import (
    FallbackGenerationProvider,
    PyTorchGenerationProvider,
    TransformationService,
    get_transformation_service,
    reset_transformation_service,
)

__all__ = [
    "TransformationSettings",
    "get_transformation_settings",
    "TransformationRegistry",
    "get_transformation_registry",
    "reset_transformation_registry",
    "TransformationInputAdapter",
    "TransformationPromptBuilder",
    "TransformationOutputParser",
    "TransformationFormatter",
    "TransformationService",
    "get_transformation_service",
    "reset_transformation_service",
    "FallbackGenerationProvider",
    "PyTorchGenerationProvider",
    "OutputTypeEnum",
    "AudienceEnum",
    "ToneEnum",
    "DetailLevelEnum",
    "CitationModeEnum",
    "EvidenceItem",
    "CitationReference",
    "FactItem",
    "EntityItem",
    "RelationItem",
    "TransformationProfile",
    "TransformationRequest",
    "TransformationContext",
    "StructuredSection",
    "StructuredContent",
    "TransformationResponse",
    "TransformationPreviewResponse",
]
