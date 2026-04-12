"""Backward-compatible patient router export.

The patient module now lives under app.modules.patients, following an
openhis-style module -> application service -> router split.
"""

from ..modules.patients.router import router

__all__ = ["router"]
