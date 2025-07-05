import pdfplumber
from pathlib import Path
import time
from .base_strategy import BaseExtractionStrategy
from ..models import ExtractionResult, StrategyType, ExtractionTask


class PDFPlumberStrategy(BaseExtractionStrategy):
    """An extraction strategy using the pdfplumber library."""
    def __init__(self):
        super().__init__(
            strategy_type=StrategyType.PDFPLUMBER, cost_tier=1
        )

    async def extract(
        self, pdf_path: Path, task: ExtractionTask
    ) -> ExtractionResult:
        start_time = time.time()
        try:
            text = ""
            tables = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                    
                    # Extract tables with default settings
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
            
            if not text and not tables:
                return ExtractionResult(
                    strategy_type=self.strategy_type,
                    success=False,
                    execution_time_seconds=time.time() - start_time,
                    error_message="No text or tables found by pdfplumber."
                )

            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=True,
                execution_time_seconds=time.time() - start_time,
                extracted_data={
                    "raw_text": text,
                    "tables_data": tables
                },
                confidence_score=0.7  # Base confidence for this reliable method
            )
        except Exception as e:
            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=False,
                execution_time_seconds=time.time() - start_time,
                error_message=str(e)
            )