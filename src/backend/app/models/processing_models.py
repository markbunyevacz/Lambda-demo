from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any


@dataclass
class PDFExtractionResult:
    """A structured representation of the data extracted from a PDF."""
    product_name: str
    extracted_text: str
    technical_specs: Dict[str, Any]
    pricing_info: Dict[str, Any]
    tables_data: List[Dict[str, Any]]
    confidence_score: float
    source_filename: str
    processing_time: float
    extraction_method: str
    table_extraction_method: str
    table_quality_score: float
    advanced_tables_used: bool
    # This field is now guaranteed to exist.
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary."""
        return asdict(self) 