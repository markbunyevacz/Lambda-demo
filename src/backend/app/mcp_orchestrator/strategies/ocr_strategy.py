import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
import time
from .base_strategy import BaseExtractionStrategy
from ..models import ExtractionResult, StrategyType, ExtractionTask


class OCRStrategy(BaseExtractionStrategy):
    """
    An extraction strategy that uses Optical Character Recognition (OCR)
    to extract text from image-based PDFs.
    """
    def __init__(self):
        super().__init__(strategy_type=StrategyType.OCR, cost_tier=3)

    async def extract(
        self, pdf_path: Path, task: ExtractionTask
    ) -> ExtractionResult:
        start_time = time.time()
        try:
            images = convert_from_path(pdf_path)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(
                    img, lang='hun+eng'
                ) + "\n\n"

            if not text.strip():
                return ExtractionResult(
                    strategy_type=self.strategy_type,
                    success=False,
                    execution_time_seconds=time.time() - start_time,
                    error_message="OCR processing yielded no text."
                )

            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=True,
                execution_time_seconds=time.time() - start_time,
                extracted_data={"raw_text": text},
                confidence_score=0.4  # OCR is less reliable
            )
        except Exception as e:
            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=False,
                execution_time_seconds=time.time() - start_time,
                error_message=f"OCR Error: {e}"
            ) 