"""Alfig — Unified Config System."""

from alfig.core import Alfig, AlfigError
from alfig.schema import ValidationError, SchemaError, Schema

__all__ = ["Alfig", "AlfigError", "ValidationError", "SchemaError", "Schema"]
__version__ = "0.1.0"
