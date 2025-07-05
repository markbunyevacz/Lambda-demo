"""
Data Models for MCP Orchestrator
===============================

Defines the core data structures used throughout the orchestration system.
"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


# --- Enums ---

class TaskStatus(Enum):
    """Status of an extraction task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StrategyType(Enum):
    """The type of extraction strategy used"""
    PDFPLUMBER = "pdfplumber"
    PYMUPDF = "pymupdf"
    OCR = "ocr"
    NATIVE_PDF = "native_pdf"
    UNKNOWN = "unknown"

class ConfidenceLevel(Enum):
    """Categorical confidence levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# --- Core Data Models ---


class ExtractionTask(BaseModel):
    """Defines a task for the MCP Orchestrator to process a single PDF."""
    pdf_path: str
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    input_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class ExtractionResult:
    """The output from a single extraction strategy."""
    strategy_type: StrategyType
    success: bool
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None


@dataclass
class FieldConfidence:
    """Confidence information for a specific extracted field"""
    field_name: str
    value: Any
    confidence_score: float
    strategy_used: StrategyType
    conflicting_values: List[Any] = field(default_factory=list)


@dataclass
class GoldenRecord:
    """The final, merged, and validated extraction result"""
    
    # Link to the original task
    task: Optional[ExtractionTask] = None

    # Core data
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    
    # Confidence scores
    field_confidences: Dict[str, "FieldConfidence"] = field(
        default_factory=dict
    )
    overall_confidence: float = 0.0

    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Validation info
    requires_human_review: bool = False
    ai_adjudication_notes: Optional[str] = None
    
    def get_modality(self, key: str, default: Any = None) -> Any:
        """Safely get a data modality from the extracted_data dictionary."""
        return self.extracted_data.get(key, default) 