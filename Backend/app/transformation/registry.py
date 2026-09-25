"""Phase 12 Transformation Engine — Transformation Registry.

Manages registration, lookup, validation, and retrieval of transformation profiles
for all supported output types.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from .schemas import TransformationProfile
from .templates import DEFAULT_PROFILES

log = logging.getLogger("gen-transform.transformation.registry")


class TransformationRegistry:
    """Registry maintaining active output type profiles."""

    def __init__(self) -> None:
        self._profiles: Dict[str, TransformationProfile] = {}
        # Load standard default profiles
        for key, profile in DEFAULT_PROFILES.items():
            self.register_profile(profile)

    def register_profile(self, profile: TransformationProfile) -> None:
        """Register or update a transformation profile."""
        key = profile.output_type.upper().strip()
        self._profiles[key] = profile
        log.debug("Registered transformation profile: %s", key)

    def get_profile(self, output_type: str) -> TransformationProfile:
        """Retrieve profile by output_type name."""
        key = output_type.upper().strip()
        if key not in self._profiles:
            # Fallback to SUMMARY if unknown, or raise KeyError if strict
            valid_keys = sorted(self._profiles.keys())
            raise KeyError(f"Unsupported output_type '{output_type}'. Valid types: {valid_keys}")
        return self._profiles[key]

    def list_profiles(self) -> List[TransformationProfile]:
        """List all registered profiles."""
        return list(self._profiles.values())

    def validate_output_type(self, output_type: str) -> bool:
        """Check whether an output_type is registered."""
        return output_type.upper().strip() in self._profiles

    def list_output_types(self) -> List[str]:
        """Return list of supported output type names."""
        return sorted(self._profiles.keys())


_REGISTRY_INSTANCE: Optional[TransformationRegistry] = None


def get_transformation_registry() -> TransformationRegistry:
    """Return singleton instance of TransformationRegistry."""
    global _REGISTRY_INSTANCE
    if _REGISTRY_INSTANCE is None:
        _REGISTRY_INSTANCE = TransformationRegistry()
    return _REGISTRY_INSTANCE


def reset_transformation_registry() -> None:
    """Reset singleton instance of TransformationRegistry."""
    global _REGISTRY_INSTANCE
    _REGISTRY_INSTANCE = None


__all__ = [
    "TransformationRegistry",
    "get_transformation_registry",
    "reset_transformation_registry",
]
