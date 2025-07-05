import asyncio
import json
import sys
from pathlib import Path

sys.path.append('/app')

from app.mcp_orchestrator.strategies import PyMuPDFStrategy
from app.mcp_orchestrator.models import ExtractionTask
from real_pdf_processor import ClaudeAIAnalyzer


async def debug_ai_analysis(pdf_path: Path):
    """
    Isolates and tests the ClaudeAIAnalyzer by feeding it text from a
    known-working strategy (PyMuPDF) and printing the raw AI response.
    """
    if not pdf_path.exists():
        print(f"❌ ERROR: File not found at {pdf_path}")
        return

    print(f"🔬 Starting AI analysis debug for: {pdf_path.name}")

    # --- Step 1: Extract text using a reliable strategy ---
    print("--- Running PyMuPDF to get clean text ---")
    task = ExtractionTask(pdf_path=str(pdf_path), task_id="ai_debug_task")
    pdf_strategy = PyMuPDFStrategy()
    text_result = await pdf_strategy.extract(pdf_path, task)
    
    if not text_result.success or not text_result.extracted_data.get("raw_text"):
        print(
            "❌ FAILED: Could not extract text with PyMuPDF. Cannot proceed."
        )
        return
    
    raw_text = text_result.extracted_data.get("raw_text")
    print(f"✅ Successfully extracted {len(raw_text)} characters of text.\n")

    # --- Step 2: Feed the extracted text to the AI analyzer ---
    print("--- Calling ClaudeAIAnalyzer with the extracted text ---")
    ai_analyzer = ClaudeAIAnalyzer()
    
    try:
        ai_response = ai_analyzer.analyze_rockwool_pdf(
            text_content=raw_text,
            tables=[],  # We focus only on text for this debug
            filename=pdf_path.name
        )
        print("✅ AI analysis completed.\n")
        
        # --- Step 3: Print the RAW, unformatted AI response ---
        print("--- 🤖 Raw AI Response (JSON) ---")
        print(json.dumps(ai_response, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR during AI analysis: {e}")


if __name__ == "__main__":
    default_pdf = (
        "/app/src/downloads/rockwool_datasheets/Stroprock G termékadatlap.pdf"
    )
    pdf_to_test_path_str = sys.argv[1] if len(sys.argv) > 1 else default_pdf
    target_pdf_path = Path(pdf_to_test_path_str)
        
    asyncio.run(debug_ai_analysis(target_pdf_path)) 