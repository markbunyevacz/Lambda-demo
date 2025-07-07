import time
from pathlib import Path
from .base_strategy import BaseExtractionStrategy
from ..models import ExtractionResult, StrategyType, ExtractionTask
# Correctly import from the absolute path within the /app directory
from backend.real_pdf_processor import ClaudeAIAnalyzer


class NativePDFStrategy(BaseExtractionStrategy):
    """
    A 'meta-strategy' that uses an AI model (Claude) to analyze and structure
    the text and tables extracted by other, simpler strategies.
    """
    def __init__(self):
        super().__init__(strategy_type=StrategyType.NATIVE_PDF, cost_tier=4)
        self.ai_analyzer = ClaudeAIAnalyzer()

    async def extract(
        self, pdf_path: Path, task: ExtractionTask
    ) -> ExtractionResult:
        start_time = time.time()
        
        # This strategy REQUIRES text from a previous strategy.
        if not task.input_data or not task.input_data.get("raw_text"):
            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=False,
                execution_time_seconds=time.time() - start_time,
                error_message="NativePDFStrategy requires 'raw_text' in input."
            )
            
        raw_text = task.input_data.get("raw_text")
        tables = task.input_data.get("tables_data", [])

        try:
            ai_analysis = self.ai_analyzer.analyze_rockwool_pdf(
                text_content=raw_text,
                tables=tables,
                filename=pdf_path.name
            )

            # Flatten the AI analysis to match the expected structure
            product_id_data = ai_analysis.get("product_identification", {})
            extracted_data = {
                "product_name": product_id_data.get("name"),
                "sku": product_id_data.get("sku"),
                "description": ai_analysis.get("description"),
                "technical_specifications": ai_analysis.get(
                    "technical_specifications"
                ),
                "application_areas": ai_analysis.get("application_areas"),
                "pricing_information": ai_analysis.get("pricing_information"),
                "raw_text": raw_text  # Pass through the raw text
            }
            confidence = ai_analysis.get("confidence_assessment", {}).get(
                "overall_confidence", 0.0
            )

            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=True,
                execution_time_seconds=time.time() - start_time,
                extracted_data=extracted_data,
                confidence_score=float(confidence)
            )
        except Exception as e:
            return ExtractionResult(
                strategy_type=self.strategy_type,
                success=False,
                execution_time_seconds=time.time() - start_time,
                error_message=f"Claude AI analysis failed: {e}"
            ) 