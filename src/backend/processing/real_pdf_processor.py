#!/usr/bin/env python3
"""
PDF Processing Orchestrator
Coordinates the services responsible for PDF extraction and analysis.

This module orchestrates the entire PDF processing workflow by coordinating
various specialized services. It follows the single responsibility principle
where each service handles a specific aspect of the processing pipeline.
"""

import asyncio
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to Python path for module resolution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Third-party imports
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Service imports - all required for operation
from app.services.ai_service import AnalysisService
from app.services.extraction_service import RealPDFExtractor
from app.services.ingestion_service import DataIngestionService
from processing.confidence_scorer import ConfidenceScorer
from processing.file_handler import FileHandler

# Database imports - required for data persistence
from app.database import SessionLocal

# Environment configuration
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Logging configuration
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
    """
    Orchestrates the PDF processing workflow using dependency injection.
    
    This class coordinates multiple specialized services to process PDF files:
    - FileHandler: File operations and hashing
    - RealPDFExtractor: PDF content extraction
    - AnalysisService: AI-powered content analysis
    - ConfidenceScorer: Quality assessment
    - DataIngestionService: Database persistence
    """

    def __init__(self, db_session: Session):
        """
        Initialize the processor with all required services.
        
        Args:
            db_session: Database session for data persistence
            
        Raises:
            ImportError: If any required service dependencies are missing
            RuntimeError: If service initialization fails
        """
        self.db_session = db_session
        
        # REFACTORING NOTE: Previously this was a monolithic class that handled
        # all operations internally. Now we use dependency injection to compose
        # specialized services, making the code more testable and maintainable.
        
        # Initialize all required services - fail fast if any are unavailable
        # This replaces the old try/except ImportError pattern with explicit
        # dependency requirements
        self.file_handler = FileHandler()  # Handles file ops & streaming hash
        self.extractor = RealPDFExtractor()  # PDF content extraction
        self.analyzer = AnalysisService()  # AI-powered analysis
        self.scorer = ConfidenceScorer()  # Multi-factor confidence calculation
        self.ingestor = DataIngestionService(db_session)  # Database persistence

        # Processing statistics - track success/failure rates
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped_duplicates": 0,  # Important for deduplication tracking
        }
        
        # Load existing processed file hashes for deduplication
        # This prevents reprocessing the same content multiple times
        self.processed_hashes = self.ingestor.load_processed_hashes()

    async def process_pdf(self, pdf_path: Path) -> Optional[PDFExtractionResult]:
        """
        Process a single PDF file through the complete pipeline.
        
        ARCHITECTURE NOTE: This method orchestrates the entire pipeline using
        the composed services. Each step is clearly separated and can be
        independently tested and modified.
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            PDFExtractionResult if successful, None if failed or skipped
            
        Raises:
            ValueError: If extraction fails or produces empty content
            Exception: For any other processing errors (logged but not re-raised)
        """
        logger.info(f"🚀 Starting processing for: {pdf_path.name}")
        start_time = datetime.now()
        
        # Step 1: File handling and deduplication check
        # OPTIMIZATION: Use streaming hash to handle large files efficiently
        file_hash = self.file_handler.calculate_file_hash(pdf_path)
        if file_hash in self.processed_hashes:
            logger.info(f"⏭️ Skipping duplicate file: {pdf_path.name}")
            self.processing_stats["skipped_duplicates"] += 1
            return None
        
        try:
            # Step 2: Extract content from PDF
            # PERFORMANCE: Run synchronous extraction in separate thread
            # to avoid blocking the async event loop
            text, tables, method = await asyncio.to_thread(
                self.extractor.extract_pdf_content, pdf_path
            )
            
            # VALIDATION: Ensure we got meaningful content
            if not text:
                raise ValueError("Text extraction failed, content is empty.")
            
            # Step 3: AI analysis of extracted content
            # ENHANCEMENT: Use specialized AI service with Hungarian language
            # support and construction industry terminology
            ai_analysis = await self.analyzer.analyze_pdf_content(
                text_content=text,
                tables_data=tables,
                filename=pdf_path.name,
            )

            # Step 4: Calculate confidence score
            # IMPROVEMENT: Multi-factor confidence scoring replaces simple
            # AI-only confidence with weighted assessment
            confidence = self.scorer.calculate_enhanced_confidence(
                text_content=text,
                tables=tables,
                ai_analysis=ai_analysis,
                extraction_method=method,
            )
            
            # Step 5: Create final result object
            # CONSOLIDATION: Combine all processing results into structured format
            result = self._consolidate_results(
                pdf_path, start_time, (text, tables, method), 
                ai_analysis, confidence
            )
            
            # Step 6: Persist to database
            # PERSISTENCE: Save to both PostgreSQL (structured) and ChromaDB (vectors)
            self.ingestor.ingest_data(result, file_hash)
            self.processed_hashes.add(file_hash)  # Update deduplication cache
            self.processing_stats["successful"] += 1
            
            logger.info(
                f"✅ Successfully processed: {pdf_path.name} "
                f"(confidence: {confidence:.2f})"
            )
            return result
            
        except Exception as e:
            # ERROR HANDLING: Log detailed error info but don't crash the batch
            logger.error(
                f"❌ Processing failed for {pdf_path.name}: {e}", 
                exc_info=True
            )
            self.processing_stats["failed"] += 1
            return None
        
    def _consolidate_results(
        self, 
        pdf_path: Path, 
        start_time: datetime, 
        content_tuple: tuple, 
        ai_analysis: Dict[str, Any], 
        confidence: float
    ) -> PDFExtractionResult:
        """
        Create the final PDFExtractionResult object from all processing steps.
        
        Args:
            pdf_path: Original PDF file path
            start_time: Processing start time
            content_tuple: (text, tables, method) from extraction
            ai_analysis: Structured data from AI analysis
            confidence: Calculated confidence score
            
        Returns:
            Complete PDFExtractionResult object
        """
        text, tables, method = content_tuple
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return PDFExtractionResult(
            product_name=ai_analysis.get("product_identification", {}).get(
                "product_name", "Unknown"
            ),
            extracted_text=text,
            technical_specs=ai_analysis.get("technical_specifications", {}),
            pricing_info=ai_analysis.get("pricing_information", {}),
            tables_data=tables,
            confidence_score=confidence,
            source_filename=pdf_path.name,
            processing_time=processing_time,
            extraction_method=method
        )

    async def process_directory(
        self, 
        pdf_directory: Path, 
        output_file: Optional[Path] = None
    ) -> List[PDFExtractionResult]:
        """
        Process all PDF files in a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            output_file: Optional output file for results
            
        Returns:
            List of successful extraction results
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

