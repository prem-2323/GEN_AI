"""Phase 14 Provenance & Evidence Tracking — Configuration Settings.

Defines configuration settings for provenance record creation, evidence resolution,
lineage caching, hash verification, and repository paths.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

log = logging.getLogger("gen-transform.provenance.config")


class ProvenanceSettings(BaseSettings):
    """Configuration settings for Phase 14 Provenance Engine."""

    enabled: bool = Field(default=True, description="Enable Provenance & Evidence Tracking Engine")
    storage_dir: str = Field(default="data/provenance", description="Directory for provenance JSON storage")
    hash_algorithm: str = Field(default="sha256", description="Cryptographic hashing algorithm for content integrity")
    enable_integrity_verification: bool = Field(default=True, description="Enable hash integrity checks")
    strict_lineage: bool = Field(default=False, description="Raise error if lineage resolution fails")
    cache_lineage_trees: bool = Field(default=True, description="Cache constructed lineage trees in memory")
    max_lineage_depth: int = Field(default=10, description="Maximum tree traversal depth for lineage resolution")

    model_config = {
        "env_prefix": "PROVENANCE_",
        "extra": "ignore",
    }


def get_provenance_settings() -> ProvenanceSettings:
    """Instantiate and return ProvenanceSettings."""
    return ProvenanceSettings()


__all__ = ["ProvenanceSettings", "get_provenance_settings"]
