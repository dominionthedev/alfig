"""Alfig — Unified Config System."""

from alfig.core import Alfig, AlfigError
from alfig.schema import ValidationError, SchemaError

__all__ = ["Alfig", "AlfigError", "ValidationError", "SchemaError"]
__version__ = "0.1.0"
