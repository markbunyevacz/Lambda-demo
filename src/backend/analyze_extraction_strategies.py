#!/usr/bin/env python3
"""
🔍 Extraction Strategy Analyzer

This script analyzes and compares two different PDF extraction strategies:
1. **Structured Extraction**: The current system's method (text/table 
   extraction + AI for structuring).
2. **Raw Haiku Extraction**: Feeding the raw PDF text directly to 
   Claude 3.5 Haiku and asking for a full JSON output.

The goal is to identify why some PDFs fail to process and to evaluate 
if a direct AI approach yields better results.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
from anthropic import Anthropic

# Ensure the correct paths are used for module imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.paths import ROCKWOOL_DATASHEETS_DIR  # noqa: E402
from real_pdf_processor import RealPDFProcessor, PDFExtractionResult  # noqa: E402
from app.database import SessionLocal  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
PDF_DIRECTORY = ROCKWOOL_DATASHEETS_DIR
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
REPORT_FILE = REPORTS_DIR / "extraction_comparison_report.json"
SUCCESSFUL_IDS_FILE = REPORTS_DIR / "db_product_ids.json"

# Check if the directory exists to provide a better error message
if not PDF_DIRECTORY.is_dir():
    raise FileNotFoundError(
        f"The specified PDF directory does not exist or is not a "
        f"directory: {PDF_DIRECTORY}\nPlease ensure the path is "
        "correct and the datasheets are downloaded."
    )


class RawHaikuExtractor:
    """
    🤖 RAW HAIKU EXTRACTOR
    
    Cél: PDF tartalom közvetlen átadása Claude 3.5 Haiku-nak
    - NINCS előfeldolgozás
    - NINCS strukturálás
    - ASIS PDF szöveg + táblázatok kinyerése
    - Tiszta AI-alapú megközelítés
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("❌ ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3.5-haiku-20241022"
        
        logger.info(f"🤖 Raw Haiku Extractor initialized: {self.model}")
    
    async def extract(self, pdf_text_content: str, filename: str) -> Dict[str, Any]:
        """
        RAW PDF SZÖVEG KINYERÉS - ASIS módszer
        
        Kéri a Haikutól:
        1. Szöveg tartalom AS-IS kinyerése
        2. Táblázatok AS-IS formában
        3. NINCS interpretáció vagy változtatás
        4. Minimális strukturálás csak JSON kimenethez
        """
        
        # KRITIKUS: AS-IS prompt - NINCS interpretáció!
        prompt = f"""
🎯 RAW PDF CONTENT EXTRACTION - AS-IS METHOD

📋 FELADAT: 
Nyerd ki a PDF tartalmat PONTOSAN úgy, ahogy van - SEMMI változtatás!

📄 DOKUMENTUM: {filename}
NYERS SZÖVEG TARTALOM:
{pdf_text_content[:120000]}  # Első 120K karakter

🔧 KINYERÉSI SZABÁLYOK:
1. **AS-IS SZÖVEG**: Minden szöveget pontosan úgy másolj, ahogy van
2. **AS-IS TÁBLÁZATOK**: Ha táblázat van, sorold fel pontosan úgy
3. **NINCS INTERPRETÁCIÓ**: Ne magyarázd, ne változtasd
4. **NINCS NORMALIZÁLÁS**: Hagyd az eredeti formátumokat
5. **MINIMÁLIS JSON**: Csak a kimenet legyen JSON

📤 KIMENETI FORMÁTUM:
{{
  "raw_text_extraction": {{
    "full_text": "TELJES szöveg AS-IS",
    "detected_tables": [
      "Táblázat 1 AS-IS",
      "Táblázat 2 AS-IS"
    ],
    "product_name_raw": "Ahogy a PDF-ben szerepel",
    "technical_data_raw": "Minden műszaki adat AS-IS"
  }},
  "extraction_metadata": {{
    "method": "raw_haiku_asis",
    "content_length": {len(pdf_text_content)},
    "filename": "{filename}",
    "confidence": "0.0-1.0"
  }}
}}

⚡ KRITIKUS: SEMMI előfeldolgozás! Csak másold ki AS-IS!
"""
        
        try:
            # Direct Claude API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.0,  # Zero creativity - exact extraction
                system="You are a precise text extraction tool. "
                       "Extract content exactly as it appears without any interpretation, "
                       "normalization, or changes. Preserve original formatting.",
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = response.content[0].text
            logger.info(f"✅ Raw Haiku extraction complete, length: {len(response_text)}")
            
            # Parse the response
            result = self._parse_raw_response(response_text, filename)
            return result
            
        except Exception as e:
            logger.error(f"❌ Raw Haiku extraction failed: {e}")
            return {
                "raw_text_extraction": {
                    "full_text": "",
                    "detected_tables": [],
                    "product_name_raw": "",
                    "technical_data_raw": ""
                },
                "extraction_metadata": {
                    "method": "raw_haiku_asis",
                    "error": str(e),
                    "confidence": 0.0
                }
            }
    
    def _parse_raw_response(self, response_text: str, filename: str) -> Dict[str, Any]:
        """Parse Claude's raw response"""
        
        # Try to find JSON in response
        import re
        import json
        
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Complete JSON
            r'```json\s*(\{.*?\})\s*```',         # JSON code block
            r'```\s*(\{.*?\})\s*```'              # Generic code block
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match)
                    logger.info("✅ Raw JSON parsed successfully")
                    
                    # Ensure required structure
                    if "raw_text_extraction" not in result:
                        result["raw_text_extraction"] = {}
                    if "extraction_metadata" not in result:
                        result["extraction_metadata"] = {}
                    
                    # Add metadata
                    result["extraction_metadata"].update({
                        "method": "raw_haiku_asis",
                        "filename": filename,
                        "response_length": len(response_text)
                    })
                    
                    return result
                    
                except json.JSONDecodeError:
                    continue
        
        # Fallback: manual text extraction
        logger.warning("⚠️ Failed to parse JSON, using text fallback")
        return {
            "raw_text_extraction": {
                "full_text": response_text,
                "detected_tables": [],
                "product_name_raw": "Parse failed",
                "technical_data_raw": response_text[:500]
            },
            "extraction_metadata": {
                "method": "raw_haiku_asis_fallback",
                "filename": filename,
                "confidence": 0.3,
                "parse_error": "JSON extraction failed"
            }
        }


async def analyze_strategies():
    """
    Main function to run the analysis of the two extraction strategies.
    """
    db_session = SessionLocal()
    structured_processor = RealPDFProcessor(db_session)
    raw_haiku_extractor = RawHaikuExtractor()

    # Get a list of all unique PDFs using a more robust method
    pdf_files = []
    for root, _, files in os.walk(PDF_DIRECTORY):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(Path(root) / file)
    logger.info(
        f"Found {len(pdf_files)} PDF files to analyze in {PDF_DIRECTORY}."
    )

    all_results = []

    for pdf_path in pdf_files:
        logger.info(f"--- Processing: {pdf_path.name} ---")
        comparison_data = {
            "pdf_filename": pdf_path.name,
            "structured_extraction": None,
            "raw_haiku_extraction": None,
        }

        # Strategy 1: Structured Extraction (current system)
        try:
            # We need the text content first
            text_content, _, _ = (
                structured_processor.extractor.extract_pdf_content(pdf_path)
            )
            
            if text_content:
                # This call simulates the processing without database saving
                structured_result = (
                    await structured_processor.process_single_pdf_for_analysis(
                        pdf_path
                    )
                )
                
                # Convert Pydantic model to dict for JSON serialization
                result_dict = (
                    structured_result.to_dict() if structured_result else {}
                )
                comparison_data["structured_extraction"] = result_dict
            else:
                comparison_data["structured_extraction"] = {
                    "error": "Failed to extract text content."
                }

        except Exception as e:
            logger.error(
                f"Error in structured extraction for {pdf_path.name}: {e}", 
                exc_info=True
            )
            comparison_data["structured_extraction"] = {"error": str(e)}

        # Strategy 2: Raw Haiku Extraction
        try:
            if 'text_content' in locals() and text_content:
                raw_result = await raw_haiku_extractor.extract(
                    text_content, pdf_path.name
                )
                comparison_data["raw_haiku_extraction"] = raw_result
            else:
                comparison_data["raw_haiku_extraction"] = {
                    "error": "Skipped due to text extraction failure."
                }
        
        except Exception as e:
            logger.error(
                f"Error in raw Haiku extraction for {pdf_path.name}: {e}", 
                exc_info=True
            )
            comparison_data["raw_haiku_extraction"] = {"error": str(e)}
        
        all_results.append(comparison_data)

    # Save the final report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)

    logger.info(f"✅ Analysis complete. Report saved to {REPORT_FILE}")
    db_session.close()


if __name__ == "__main__":
    # Add a method to RealPDFProcessor to bypass database saving for analysis
    async def process_single_pdf_for_analysis(
        self: RealPDFProcessor, pdf_path: Path
    ) -> PDFExtractionResult:
        # This is a simplified version of process_pdf for analysis purposes
        text, tables, method = self.extractor.extract_pdf_content(pdf_path)
        if not text:
            return None
        
        ai_analysis_result = await self.ai_analyzer.analyze_rockwool_pdf(
            text, tables, pdf_path.name
        )
        
        # Directly return the result without validation or saving
        return PDFExtractionResult(
            product_name=ai_analysis_result.get(
                "product_identification", {}
            ).get("name", pdf_path.stem),
            extracted_text=text,
            technical_specs=ai_analysis_result.get(
                "technical_specifications", {}
            ),
            pricing_info=ai_analysis_result.get("pricing_information", {}),
            tables_data=tables,
            confidence_score=ai_analysis_result.get(
                "extraction_metadata", {}
            ).get("confidence_score", 0.0),
            extraction_method=method,
            source_filename=pdf_path.name,
            processing_time=0.0
        )

    RealPDFProcessor.process_single_pdf_for_analysis = (
        process_single_pdf_for_analysis
    )
    
    asyncio.run(analyze_strategies()) 