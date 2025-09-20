# utils/__init__.py
"""
Utility modules for the LLM SQL Agent.

This package contains:
- gemini_config: Gemini model management and selection
- helpers: Query validation and formatting utilities  
- logging_config: Structured logging setup
"""

__version__ = "1.0.0"
__author__ = "bitphonix"

# Make key classes easily importable
from .logging_config import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]