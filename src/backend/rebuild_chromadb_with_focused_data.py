import os
import sys
from sqlalchemy.orm import Session
import asyncio
from pathlib import Path

# Add project root to path to resolve sibling imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, get_db
from app.models.product import Product

# Import MCP Orchestrator components
from app.mcp_orchestrator.orchestrator import MCPOrchestrator
from app.mcp_orchestrator.models import ExtractionTask


async def rebuild_database_with_orchestrator():
    """
    Wipes and rebuilds both PostgreSQL and ChromaDB using the MCP Orchestrator
    to ensure high-quality, validated data extraction.
    """
    print("🚀 Starting database rebuild process with MCP Orchestrator...")
    
    # --- Database Connection ---
    db: Session = next(get_db())
    # The orchestrator itself does not take a session, but the data saving logic will.
    # The session 'db' will be used later when saving the golden record.
    orchestrator = MCPOrchestrator()

    print("✅ Connected to databases and initialized Orchestrator.")

    # --- Step 1: Clear existing data ---
    print("🔥 Deleting existing product data from PostgreSQL and ChromaDB...")
    orchestrator.wipe_and_reset_databases()
    print("✅ Databases have been cleared.")

    # --- Step 2: Define PDF source directory ---
    # We assume the script is run from src/backend
    pdf_directory = Path("/app/src/downloads/rockwool_datasheets")
    if not pdf_directory.exists():
        # Fallback for local execution if needed
        pdf_directory = Path(__file__).resolve().parent / "src" / "downloads" / "rockwool_datasheets"
        if not pdf_directory.exists():
            raise FileNotFoundError(f"PDF directory not found in standard paths.")
    
    pdf_files = list(pdf_directory.glob("*.pdf"))
    print(f"📂 Found {len(pdf_files)} PDF files to process in {pdf_directory}.")

    # --- Step 3: Process each PDF with the Orchestrator ---
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n--- Processing file {i+1}/{len(pdf_files)}: {pdf_path.name} ---")
        task = ExtractionTask(pdf_path=str(pdf_path), task_id=pdf_path.stem)
        
        # The orchestrator will run its pipeline (extract, validate, store)
        golden_record = await orchestrator.process_task(task)
        
        # A task is successful if it does NOT require human review
        if golden_record and not golden_record.requires_human_review:
            print(f"✅ SUCCESS: Golden Record created for {pdf_path.name} with confidence {golden_record.overall_confidence:.2f}")
        else:
            print(f"❌ FAILED: Could not create Golden Record for {pdf_path.name}")

    print("\n\n🎉 Orchestrated database rebuild complete!")
    final_product_count = db.query(Product).count()
    final_chroma_count = orchestrator.get_chroma_collection().count()
    print(f"📊 PostgreSQL now contains {final_product_count} products.")
    print(f"📊 ChromaDB now contains {final_chroma_count} searchable documents.")


if __name__ == "__main__":
    # To run the async function
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(rebuild_database_with_orchestrator()) 