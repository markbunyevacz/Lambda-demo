import asyncio
import sys
from pathlib import Path
import json

# This assumes the script is run from /app, which is the WORKDIR
# Adding /app to the path ensures modules are found
sys.path.append('/app')

from app.mcp_orchestrator.strategies import (
    PDFPlumberStrategy,
    PyMuPDFStrategy,
)
from app.mcp_orchestrator.models import ExtractionTask
from app.services.ai_service import AnalysisService


async def diagnose_pdf(pdf_path: Path):
    """
    Runs each basic extraction strategy on a single PDF and prints the results.
    """
    if not pdf_path.exists():
        print(f"❌ ERROR: File not found at {pdf_path}")
        return

    print(f"🔬 Starting diagnosis for: {pdf_path.name}\n")
    task = ExtractionTask(pdf_path=str(pdf_path), task_id="diagnosis_task")

    strategies_to_test = [
        ("PDFPlumber", PDFPlumberStrategy()),
        ("PyMuPDF", PyMuPDFStrategy()),
    ]

    for name, strategy in strategies_to_test:
        print(f"--- Testing Strategy: {name} ---")
        try:
            result = await strategy.extract(pdf_path, task)
            if result.success:
                text = result.extracted_data.get("raw_text", "")
                text_length = len(text)
                print(f"✅ SUCCESS: Extracted {text_length} characters.")
                if text_length > 0:
                    print("🔍 Preview (first 200 chars):")
                    print(f'"""{text[:200].strip()}..."""\n')
            else:
                print(f"⚠️ FAILED: {result.error_message}\n")
        except Exception as e:
            print(f"💥 CRITICAL ERROR during {name} execution: {e}\n")


if __name__ == "__main__":
    # Path to the problematic PDF inside the Docker container
    default_pdf = (
        "/app/src/downloads/rockwool_datasheets/Stroprock G termékadatlap.pdf"
    )
    
    pdf_to_test_path_str = sys.argv[1] if len(sys.argv) > 1 else default_pdf
    target_pdf_path = Path(pdf_to_test_path_str)
        
    asyncio.run(diagnose_pdf(target_pdf_path)) 