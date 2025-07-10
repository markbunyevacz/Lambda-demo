"""
AI Analysis Service for the PDF Processing Pipeline
-------------------------------------------------
Responsibilities:
- Interacting with the Claude AI model.
- Using specialized prompts for content analysis.
- Structuring the AI's response.
"""
import logging
from typing import Dict, List, Any

from app.services.ai_service import ClaudeAIAnalyzer

logger = logging.getLogger(__name__)

class AnalysisService:
    """Orchestrates the AI analysis of extracted PDF content."""

    def __init__(self):
        self.ai_analyzer = ClaudeAIAnalyzer()

    async def analyze_content(self, text_content: str, tables: List[Dict], pdf_name: str) -> Dict[str, Any]:
        """
        Analyzes the extracted text and tables using the Claude AI.

        Args:
            text_content: The raw text extracted from the PDF.
            tables: A list of tables extracted from the PDF.
            pdf_name: The name of the source PDF file.

        Returns:
            A dictionary containing the structured data returned by the AI.
        """
        logger.info(f"Starting AI analysis for {pdf_name}...")
        try:
            ai_analysis = await self.ai_analyzer.analyze_rockwool_pdf(
                text=text_content,
                tables=tables,
                filename=pdf_name
            )
            logger.info(f"Successfully completed AI analysis for {pdf_name}.")
            return ai_analysis
        except Exception as e:
            logger.error(f"AI analysis failed for {pdf_name}: {e}")
            # Return a default error structure
            return {
                "error": str(e),
                "product_identification": {"product_name": f"Analysis Failed: {pdf_name}"},
                "technical_specifications": {},
                "pricing_information": {},
                "extraction_metadata": {"confidence_score": 0.0},
            } 