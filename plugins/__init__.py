"""
OpenWebUI Custom Tools Package

This package contains custom tools for OpenWebUI integration
with the LaTeX compilation backend service.
"""

from .latex_compiler import (
    latex_compiler_tool,
    TOOL_SPECIFICATION,
    HELP_TEXT
)

__all__ = [
    "latex_compiler_tool",
    "TOOL_SPECIFICATION",
    "HELP_TEXT"
]