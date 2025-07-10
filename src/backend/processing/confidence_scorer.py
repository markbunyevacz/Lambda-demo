#!/usr/bin/env python3
"""
Confidence Scorer Service
-------------------------
Centralised logic for turning a collection of *quality indicators* into
one scalar confidence_score ∈ [0,1].  The weighting scheme (60-20-20)
was chosen after empirical experiments – raw AI confidence proved to be
a strong predictor, but pure extraction quality still mattered.

Tuning guidelines (for future maintainers):
• If Claude becomes significantly more accurate, raise AI weight.
• If table extraction is upgraded (Camelot improvements), raise table
  weight.
• Keep the sum of weights = 1.0.
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Calculates an enhanced confidence score based on multiple factors
    from the PDF extraction process.
    """

    def calculate_enhanced_confidence(
        self,
        text_content: str,
        tables: List[Dict],
        ai_analysis: Dict[str, Any],
        extraction_method: str,
    ) -> float:
        """
        Calculates a final confidence score by weighting different quality metrics.
        
        ALGORITHM EXPLANATION:
        - 60% weight to AI confidence (Claude's self-assessment)
        - 20% weight to text quality (length, structure)
        - 20% weight to table quality (meaningful tabular data)
        
        This weighting was determined empirically - AI confidence proved to be
        the strongest predictor of extraction quality, but raw content quality
        still provides valuable validation.
        """
        try:
            # Base confidence from the AI's own assessment
            # Claude 3.5 Haiku provides reliable self-assessment scores
            base_confidence = ai_analysis.get("extraction_metadata", {}).get(
                "confidence_score", 0.0
            )

            # Assess the quality of the raw extracted text and tables
            # These provide independent validation of the extraction process
            text_quality = self._assess_text_quality(text_content)
            table_quality = self._assess_table_quality(tables)

            # Cross-validate AI results with patterns if available
            # (In this refactor, we rely more on AI but keep validation hooks)
            validation_factor = 1.0

            # CORE ALGORITHM: Weighted combination of quality metrics
            # 60% AI + 20% text + 20% table = balanced assessment
            final_confidence = (
                (base_confidence * 0.6)      # Primary: AI self-assessment
                + (text_quality * 0.2)       # Secondary: Content length/structure
                + (table_quality * 0.2)      # Secondary: Tabular data quality
            ) * validation_factor             # Future: Pattern validation

            logger.info(
                "Confidence: AI=%.2f, TextQ=%.2f, TableQ=%.2f -> Final=%.2f",
                base_confidence,
                text_quality,
                table_quality,
                final_confidence,
            )

            return min(final_confidence, 1.0)  # Cap at 1.0 for safety
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0  # Conservative fallback

    def _assess_text_quality(self, text_content: str) -> float:
        """
        Assesses the quality of the extracted text based on length and characters.
        
        BUSINESS LOGIC: Construction industry PDFs typically contain substantial
        technical content. Short extractions usually indicate parsing failures.
        
        Returns a score between 0.0 and 1.0.
        """
        if not text_content or len(text_content) < 200:
            return 0.0  # Not enough text to be meaningful for technical docs

        # HEURISTIC: Longer text generally indicates successful extraction
        # These thresholds are based on typical Rockwool datasheet lengths
        if len(text_content) > 1000:
            return 1.0    # Comprehensive extraction
        elif len(text_content) > 500:
            return 0.8    # Good extraction
        else:
            return 0.5    # Minimal but usable extraction

    def _assess_table_quality(self, tables: List[Dict]) -> float:
        """
        Assesses the quality of extracted tables based on structure.
        
        BUSINESS LOGIC: Technical specifications in construction PDFs are often
        presented in tabular format. Quality tables have multiple columns and
        meaningful data rows.
        
        Returns a score between 0.0 and 1.0.
        """
        if not tables:
            # NEUTRAL SCORE: Some docs don't have tables (e.g., overview docs)
            return 0.5

        meaningful_tables = 0
        for table in tables:
            # QUALITY CRITERIA: A meaningful table has structure and content
            headers = table.get("headers", [])
            data = table.get("data", [])
            
            # Minimum requirements: 2+ columns, 1+ data row
            if len(headers) >= 2 and len(data) >= 1:
                meaningful_tables += 1

        if meaningful_tables > 0:
            return 1.0  # High quality if we have at least one structured table
        else:
            # LOW QUALITY: Tables exist but seem empty/malformed
            return 0.2 