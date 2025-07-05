"""
MCP Orchestrator - Advanced PDF Extraction System
=================================================

This module implements a rock-solid, AI-orchestrated PDF extraction system
that uses multiple parallel strategies and AI-powered validation to ensure
maximum accuracy and completeness.

Architecture:
- Multiple extraction strategies running in parallel
- AI-powered cross-validation and merging
- Confidence scoring for each extracted field
- Asynchronous processing with status tracking
"""

from .models import (
    ConfidenceLevel,
    ExtractionResult,
    ExtractionTask,
    FieldConfidence,
    GoldenRecord,
    StrategyType,
    TaskStatus,
)
from .strategies import (
    NativePDFStrategy,
    PDFPlumberStrategy,
    PyMuPDFStrategy,
)
from .validator import AIValidator
from .orchestrator import MCPOrchestrator
from .chroma_client import ChromaClient


__all__ = [
    "ConfidenceLevel",
    "ExtractionResult",
    "ExtractionTask",
    "FieldConfidence",
    "GoldenRecord",
    "StrategyType",
    "TaskStatus",
    "NativePDFStrategy",
    "PDFPlumberStrategy",
    "PyMuPDFStrategy",
    "AIValidator",
    "ChromaClient",
]