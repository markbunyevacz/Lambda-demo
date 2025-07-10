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

# This must be at the very top to ensure the app module is found
# We resolve the path to be absolute to avoid any relative path issues.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import warnings
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Database and Model Imports
from app.database import SessionLocal
from app.models.product import Product  # Assuming these are needed by the script/main
from app.models.manufacturer import Manufacturer
from app.models.category import Category

# Service Imports
from app.services.extraction_service import RealPDFExtractor, AdvancedTableExtractor, TableExtractionResult
from app.services.ingestion_service import DataIngestionService
from app.processing.file_handler import FileHandler
from app.processing.analysis_service import AnalysisService
from app.processing.confidence_scorer import ConfidenceScorer

# Utility Imports
from app.utils import clean_utf8


# Load environment variables
load_dotenv()
load_dotenv(str(Path(__file__).resolve().parent.parent.parent / ".env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PDFExtractionResult:
    """A structured representation of the data extracted from a PDF."""
    product_name: str
    extracted_text: str
    technical_specs: Dict[str, Any]
    pricing_info: Dict[str, Any]
    tables_data: List[Dict[str, Any]]
    confidence_score: float
    source_filename: str
    processing_time: float
    extraction_method: str

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary."""
        return asdict(self)


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
            return None # Error handled in calculator
        
        if self.file_handler.is_duplicate(file_hash):
            logger.info(f"Skipping duplicate file: {pdf_path.name}")
            self.processing_stats["skipped_duplicates"] += 1
            return None
        
        # 2. Extract Content
        text, simple_tables, text_method = self.extraction_service.extract_pdf_content(pdf_path)
        
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
        
        logger.info(f"Successfully processed {pdf_path.name} in {processing_time:.2f} seconds.")
        return consolidated_result

    def _consolidate_results(
        self, pdf_path, start_time, text, text_method, table_result, ai_analysis
    ) -> PDFExtractionResult:
        """Consolidates all extracted data into the final result object."""
        
        tables = table_result.tables if table_result else []
        table_method = table_result.extraction_method if table_result else "none"

        # Calculate confidence score using the dedicated service
        confidence = self.confidence_scorer.calculate_enhanced_confidence(
            text_content=text,
            tables=tables,
            ai_analysis=ai_analysis,
            extraction_method=text_method
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        return PDFExtractionResult(
            product_name=ai_analysis.get("product_identification", {}).get("product_name", pdf_path.stem),
            extracted_text=clean_utf8(text),
            technical_specs=ai_analysis.get("technical_specifications", {}),
            pricing_info=ai_analysis.get("pricing_information", {}),
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
            f"Processing complete: {len(results)}/{len(pdf_files)} successful"
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
    
    # Initialize database session
    try:
        db = SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        print("❌ Database not available - cannot proceed")
        return
    
    try:
        # Initialize processor
        processor = RealPDFProcessor(db_session=db)
        
        # Define paths
        pdf_directory = Path("../../src/downloads/rockwool_datasheets")
        output_file = Path("real_pdf_results.json")
        
        # Try alternative paths if main path doesn't exist
        if not pdf_directory.exists():
            alternative_paths = [
                Path("../downloads/rockwool_datasheets"),
                Path("src/downloads/rockwool_datasheets"),
                Path("downloads/rockwool_datasheets")
            ]
            
            for alt_path in alternative_paths:
                if alt_path.exists():
                    pdf_directory = alt_path
                    logger.info(f"Using alternative path: {pdf_directory}")
                    break
                else:
                    logger.error("No valid PDF directory found")
                    return
        
        # Process PDFs
        results = await processor.process_directory(pdf_directory, output_file)
        
        # Display results
        if results:
            print(f"\n🎉 Processing complete! {len(results)} PDFs processed.")
            print("\n📋 Sample results:")
            for i, result in enumerate(results[:3], 1):
                print(
                    f"  {i}. {result.product_name} "
                    f"(confidence: {result.confidence_score:.2f})"
                )
        else:
            print("❌ No PDFs were successfully processed")
            
        # Show statistics
        stats = processor.get_processing_stats()
        print(f"\n📊 Statistics: {stats}")
    
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())

