import asyncio
import json
import sys
from pathlib import Path

# This must be at the very top to ensure the app module is found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ai_service import AnalysisService
from app.services.extraction_service import RealPDFExtractor


async def debug_ai(pdf_path: Path):
    """
    Isolates and tests the AnalysisService by feeding it text from a
    real PDF document.
    """
    if not pdf_path.exists():
        print(f"💥 ERROR: PDF file not found at {pdf_path}")
        return
    
    print(f"---  एनालाइजिंग: {pdf_path.name} ---")

    try:
        # --- Step 1: Extract text using RealPDFExtractor ---
        print("--- Running RealPDFExtractor to get clean text ---")
        extractor = RealPDFExtractor()
        # Note: extract_pdf_content is synchronous in the original service
        # We will call it directly. If it were async, we would await it.
        text, tables, method = extractor.extract_pdf_content(pdf_path)

        if not text:
            print("Extraction failed. No text to analyze.")
            return

    # --- Step 2: Feed the extracted text to the AI analyzer ---
        print("--- Calling AnalysisService with the extracted text ---")
        analyzer = AnalysisService()
        result = await analyzer.analyze_pdf_content(text, tables, pdf_path.name)
        
        # --- Step 3: Print the RAW, unformatted AI response ---
        print("\n--- AI Analysis Result ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"An error occurred during the debug process: {e}")


if __name__ == "__main__":
    default_pdf = (
        "/app/src/downloads/rockwool_datasheets/Stroprock G termékadatlap.pdf"
    )
    pdf_to_test_path_str = sys.argv[1] if len(sys.argv) > 1 else default_pdf
    target_pdf_path = Path(pdf_to_test_path_str)
        
    asyncio.run(debug_ai(target_pdf_path)) 