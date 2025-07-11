#!/usr/bin/env python3
"""
PDF Processing Orchestrator
Coordinates the services responsible for PDF extraction and analysis.

This module orchestrates the entire PDF processing workflow by coordinating
various specialized services. It follows the single responsibility principle
where each service handles a specific aspect of the processing pipeline.
"""

import sys
from pathlib import Path

# -- Path Setup --
_current_dir = Path(__file__).parent
_backend_root = (_current_dir / "..").resolve()
sys.path.insert(0, str(_backend_root))

# Standard Library Imports
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

# Third-Party Imports
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Local Application Imports
from app.database import SessionLocal
from app.models.processing_models import PDFExtractionResult
from app.services.extraction_service import (
    RealPDFExtractor, AdvancedTableExtractor
)
from app.services.ingestion_service import DataIngestionService
from app.processing.file_handler import FileHandler
from app.processing.analysis_service import AnalysisService
from app.processing.confidence_scorer import ConfidenceScorer
from app.utils import clean_utf8

# -- Environment and Logging Configuration --
load_dotenv()
project_root_env = _backend_root.parent.parent / '.env'
if project_root_env.exists():
    load_dotenv(dotenv_path=project_root_env)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealPDFProcessor:
    """Orchestrates the PDF processing pipeline using dedicated services."""

    def __init__(self, db_session: Session, enable_ai_analysis: bool = True):
        """Initialize with dedicated services."""
        self.db_session = db_session
        self.enable_ai_analysis = enable_ai_analysis

        # Initialize services
        self.file_handler = FileHandler(db_session)
        self.extraction_service = RealPDFExtractor()
        self.table_extractor = AdvancedTableExtractor()
        self.analysis_service = AnalysisService()
        self.confidence_scorer = ConfidenceScorer()
        self.ingestion_service = DataIngestionService(db_session)

        # Processing stats
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped_duplicates": 0,
            "total_extraction_time": 0.0,
        }

    async def process_pdf(self, pdf_path: Path) -> Optional[PDFExtractionResult]:
        """
        Processes a single PDF file using a pipeline of dedicated services.
        """
        start_time = datetime.now()
        logger.info(f"Starting processing for: {pdf_path.name}")

        # 1. Handle File & Duplicates
        file_hash = self.file_handler.calculate_file_hash(pdf_path)
        if not file_hash:
            return None  # Error handled in calculator

        if self.file_handler.is_duplicate(file_hash):
            logger.info(f"Skipping duplicate file: {pdf_path.name}")
            self.processing_stats["skipped_duplicates"] += 1
            return None

        # 2. Extract Content
        text, simple_tables, text_method = (
            self.extraction_service.extract_pdf_content(pdf_path)
        )

        # 3. Extract Tables using Advanced Method
        table_result = self.table_extractor.extract_tables_hybrid(pdf_path)

        # 4. Analyze with AI
        ai_analysis = {}
        if self.enable_ai_analysis:
            ai_analysis = await self.analysis_service.analyze_content(
                text_content=text,
                tables=table_result.tables if table_result else simple_tables,
                pdf_name=pdf_path.name
            )

        # 5. Consolidate and Score
        consolidated_result = self._consolidate_results(
            pdf_path, start_time, text, text_method, table_result, ai_analysis
        )

        # 6. Ingest Data
        self.ingestion_service.ingest_data(consolidated_result, file_hash)

        # 7. Update logs and stats
        self.file_handler.add_hash_to_log(file_hash)
        self.processing_stats["successful"] += 1
        self.processing_stats["total_processed"] += 1
        processing_time = (datetime.now() - start_time).total_seconds()
        self.processing_stats["total_extraction_time"] += processing_time

        logger.info(
            f"Successfully processed {pdf_path.name} in {processing_time:.2f}s"
        )
        return consolidated_result

    def _consolidate_results(
        self, pdf_path, start_time, text, text_method, table_result, ai_analysis
    ) -> PDFExtractionResult:
        """
        Consolidates all extracted data into the final result object,
        ensuring it's always well-formed.
        """
        tables = table_result.tables if table_result else []
        table_method = table_result.extraction_method if table_result else "none"

        # Ensure ai_analysis is a dict even on failure
        if not isinstance(ai_analysis, dict):
            ai_analysis = {}

        # Calculate confidence score
        confidence = self.confidence_scorer.calculate_enhanced_confidence(
            text_content=text,
            tables=tables,
            ai_analysis=ai_analysis,
            extraction_method=text_method
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        product_name = ai_analysis.get("product_identification", {}).get(
            "product_name", pdf_path.stem
        )
        
        # This now includes the guaranteed 'extraction_metadata' field
        return PDFExtractionResult(
            product_name=product_name,
            extracted_text=clean_utf8(text),
            technical_specs=ai_analysis.get("technical_specifications", {}),
            pricing_info=ai_analysis.get("pricing_information", {}),
            extraction_metadata=ai_analysis.get("extraction_metadata", {}),
            tables_data=tables,
            confidence_score=confidence,
            source_filename=pdf_path.name,
            processing_time=processing_time,
            extraction_method=text_method,
            table_extraction_method=table_method,
            table_quality_score=table_result.quality_score if table_result else 0.0,
            advanced_tables_used=bool(table_result),
        )

    async def process_directory(
        self, pdf_directory: Path, output_file: Optional[Path] = None
    ) -> List[PDFExtractionResult]:
        """
        Processes all PDF files in a given directory concurrently.
        """
        if not pdf_directory.exists():
            raise FileNotFoundError(f"Directory not found: {pdf_directory}")

        pdf_files = list(pdf_directory.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files to process")
        results = []

        for pdf_path in pdf_files:
            result = await self.process_pdf(pdf_path)
            if result:
                results.append(result)

        logger.info(
            "Processing complete: %d/%d successful",
            len(results),
            len(pdf_files)
        )

        # Save results if output file specified
        if output_file and results:
            self._save_results(results, output_file)

        return results

    def _save_results(
        self, results: List[PDFExtractionResult], output_file: Path
    ):
        """Save processing results to JSON file."""
        import json

        results_data = [result.to_dict() for result in results]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")

    def get_processing_stats(self) -> Dict[str, int]:
        """Get current processing statistics."""
        return self.processing_stats.copy()


async def main():
    """Main function for testing the PDF processor."""
    logger.info("🚀 Starting the data ingestion process...")
    db_session = None
    try:
        db_session = SessionLocal()
        logger.info("✅ Database session created successfully.")

        processor = RealPDFProcessor(db_session=db_session)
        logger.info("✅ RealPDFProcessor initialized.")

        # Correctly define the project root and PDF directory path
        project_root = _backend_root.parent
        pdf_directory = project_root / "downloads" / "rockwool_datasheets"
        output_file = project_root / "real_pdf_results.json"

        logger.info(f"📁 Target PDF directory: {pdf_directory}")

        if not pdf_directory.exists():
            logger.error(
                "❌ CRITICAL: PDF directory not found at the specified path: %s",
                pdf_directory
            )
            return

        await processor.process_directory(pdf_directory, output_file)

        stats = processor.get_processing_stats()
        logger.info("🎉 Ingestion process finished.")
        logger.info(f"📊 Final Statistics: {stats}")

    except Exception as e:
        logger.error(
            "An unexpected error occurred during the ingestion process: %s",
            e, exc_info=True
        )
    finally:
        if db_session:
            db_session.close()
            logger.info("✅ Database session closed.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

