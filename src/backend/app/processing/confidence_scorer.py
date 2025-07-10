"""
Confidence Scoring Service for the PDF Processing Pipeline
----------------------------------------------------------
Responsibilities:
- Calculating a robust confidence score for the extracted data.
- Assessing the quality of extracted text and tables.
- Cross-validating data from different extraction sources
  (e.g., AI vs. direct parsing).
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculates a confidence score for the PDF extraction results."""

    def calculate_enhanced_confidence(
        self,
        text_content: str,
        tables: List[Dict],
        ai_analysis: Dict[str, Any],
        extraction_method: str
    ) -> float:
        """
        Calculates an enhanced confidence score based on multiple quality
        factors.

        Args:
            text_content: The raw text extracted from the PDF.
            tables: A list of tables extracted from the PDF.
            ai_analysis: The structured data returned by the AI.
            extraction_method: The primary method used for PDF content
                extraction.

        Returns:
            A confidence score between 0.0 and 1.0.
        """
        try:
            # 1. Assess base quality of text and tables
            text_quality = self._assess_text_quality(text_content)
            table_quality = self._assess_table_quality(tables)
            
            # 2. Assess AI analysis quality
            ai_confidence = ai_analysis.get("extraction_metadata", {})\
                .get("confidence_score", 0.0)

            # 3. Combine scores with weighting
            # Weighting: AI analysis is most important, then tables, and
            # finally text.
            base_confidence = (
                (ai_confidence * 0.6) + (table_quality * 0.3) + (text_quality * 0.1)
            )

            # 4. Apply adjustments based on content type and source reliability
            final_confidence = self._apply_content_type_adjustments(
                base_confidence, ai_analysis, extraction_method
            )
            
            logger.info(f"Calculated confidence score: {final_confidence:.2f}")
            return round(final_confidence, 4)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    def _assess_text_quality(self, text_content: str) -> float:
        """Assess the quality of the extracted text."""
        if not text_content or len(text_content) < 100:
            return 0.0  # Very little or no text
        
        # Simple metric: ratio of alphanumeric characters to total length
        alnum_chars = sum(1 for char in text_content if char.isalnum())
        quality = alnum_chars / len(text_content)
        
        # Penalize for common extraction errors
        # (e.g., excessive weird spacing)
        if "  " in text_content:
            quality *= 0.9
            
        return min(quality, 1.0)

    def _assess_table_quality(self, tables: List[Dict]) -> float:
        """Assess the quality of the extracted tables."""
        if not tables:
            return 0.1  # No tables might be okay, but it's less certain

        total_cells = 0
        filled_cells = 0
        for table in tables:
            if isinstance(table, dict) and 'data' in table and \
               isinstance(table['data'], list):
                for row in table['data']:
                    if isinstance(row, list):
                        total_cells += len(row)
                        filled_cells += sum(
                            1 for cell in row if cell and str(cell).strip()
                        )

        if total_cells == 0:
            return 0.1

        quality = filled_cells / total_cells
        return quality

    def _apply_content_type_adjustments(
        self,
        base_confidence: float,
        ai_analysis: Dict[str, Any],
        extraction_method: str
    ) -> float:
        """Apply adjustments based on content type and source reliability."""
        
        # If it's a known high-quality document type, boost confidence
        filename = ai_analysis.get("source_filename", "").lower()
        if "termékadatlap" in filename:
            base_confidence += 0.05
        
        # If a reliable extraction method was used, boost confidence
        if extraction_method in ["pdfplumber", "PyMuPDF"]:
            base_confidence += 0.05

        # Ensure score stays within bounds
        return min(max(base_confidence, 0.0), 1.0) 