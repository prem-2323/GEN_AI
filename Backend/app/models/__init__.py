"""PyTorch / AI Model Layer module boundary.

Note: Deep learning model architectures, PyTorch modules, tensor operations,
and model inference pipelines will be implemented in Phase 9.

Application/database data schemas have been organized under `app.domain_models`.
For backward compatibility during migration, domain schemas are also re-exported here.
"""
from __future__ import annotations

# Re-export domain models for backward compatibility
from ..domain_models import *
from ..domain_models import __all__ as _domain_all

__all__ = list(_domain_all)
