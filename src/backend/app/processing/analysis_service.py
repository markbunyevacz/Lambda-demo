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

# REFACTOR: Import the new AnalysisService from the correct location
from app.services.ai_service import AnalysisService as ClaudeAIAnalyzer

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates the AI analysis of extracted PDF content."""

    def __init__(self):
        # The new ai_service.AnalysisService is now used here
        self.ai_analyzer = ClaudeAIAnalyzer()

    async def analyze_content(
        self, text_content: str, tables: List[Dict], pdf_name: str
    ) -> Dict[str, Any]:
        """
        Analyzes the extracted text and tables using the refactored AI service.
        """
        logger.info(f"Starting AI analysis for {pdf_name}...")
        try:
            # The new service has a unified method 'analyze_pdf_content'
            ai_analysis = await self.ai_analyzer.analyze_pdf_content(
                text_content=text_content,
                tables_data=tables,
                filename=pdf_name
            )
            logger.info(f"Successfully completed AI analysis for {pdf_name}.")
            return ai_analysis
        except Exception as e:
            logger.error(f"AI analysis failed for {pdf_name}: {e}")
            return {
                "error": str(e),
                "product_identification": {
                    "product_name": f"Analysis Failed: {pdf_name}"
                },
                "technical_specifications": {},
                "pricing_information": {},
                "extraction_metadata": {"confidence_score": 0.0},
            } 