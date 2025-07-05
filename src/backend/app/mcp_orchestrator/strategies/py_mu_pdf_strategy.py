import fitz  # PyMuPDF
from pathlib import Path
import time
from .base_strategy import BaseExtractionStrategy
from ..models import ExtractionResult, StrategyType, ExtractionTask


class PyMuPDFStrategy(BaseExtractionStrategy):
    """An extraction strategy using the PyMuPDF (fitz) library."""
    def __init__(self):
        super().__init__(strategy_type=StrategyType.PYMUPDF, cost_tier=1)

    async def extract(
        self, pdf_path: Path, task: ExtractionTask
    ) -> ExtractionResult:
        start_time = time.time()
        try:
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text() + "\n\n"
            
            if not text.strip():
                return ExtractionResult(
                    strategy_type=self.strategy_type,
                    success=False,
                    execution_time_seconds=time.time() - start_time,
                    error_message="No text found by PyMuPDF."
                )

            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=True,
                execution_time_seconds=time.time() - start_time,
                extracted_data={"raw_text": text},
                # PyMuPDF doesn't handle tables as well, so lower confidence
                confidence_score=0.6
            )
        except Exception as e:
            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=False,
                execution_time_seconds=time.time() - start_time,
                error_message=str(e)
            ) 