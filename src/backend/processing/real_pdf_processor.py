#!/usr/bin/env python3
"""
Lambda.hu Real PDF Processor
NO SIMULATIONS - Real AI-powered PDF content extraction

Uses:
- PyPDF2/pdfplumber for actual PDF text extraction
- Claude 3.5 Haiku for intelligent content analysis
- Structured data extraction for product specs and prices
"""

import sys
from pathlib import Path

# This must be at the very top to ensure the app module is found
# We resolve the path to be absolute to avoid any relative path issues.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import hashlib
import logging
import warnings
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add the project root to the Python path to resolve imports
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) # This line is now redundant due to the new_code, but keeping it as per instructions.


from sqlalchemy.orm import Session

# Environment
from dotenv import load_dotenv

# Database Integration
try:
    from app.database import SessionLocal
    from models.processed_file_log import ProcessedFileLog
    from app.models.product import Product
    from app.models.manufacturer import Manufacturer
    from app.models.category import Category
except ImportError:
    # Alternative imports for current structure
    SessionLocal = None
    ProcessedFileLog = None
    Product = None
    Manufacturer = None
    Category = None

# ✅ NEW: Import our new extraction service
try:
    from app.services.extraction_service import (
        RealPDFExtractor, AdvancedTableExtractor, TableExtractionResult
    )
except ImportError:
    # This might happen if the script is run from a different context
    # In a real app structure, this path would be consistent.
    # For now, let's assume it might fail and define dummy classes.
    class RealPDFExtractor:
        pass

    class AdvancedTableExtractor:
        pass

    @dataclass
    class TableExtractionResult:
        tables: List[Dict[str, Any]]
        extraction_method: str
        quality_score: float
        confidence: float
        processing_time: float

# ✅ NEW: Import our new AI service
try:
    from app.services.ai_service import ClaudeAIAnalyzer
except ImportError:
    class ClaudeAIAnalyzer:
        pass

# ✅ NEW: Import our new Ingestion service
try:
    from app.services.ingestion_service import DataIngestionService
except ImportError:
    class DataIngestionService:
        pass

# ✅ NEW: Import the UTF-8 cleaning utility
from app.utils import clean_utf8

# Load environment variables
load_dotenv()  # Current directory first
load_dotenv("../../.env")  # Fallback to root directory

# ✅ ENHANCED: Configure logging to ERROR level to hide all WARNING messages
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ✅ Set our own logger to INFO level for our messages
# logger.setLevel(logging.INFO) # This is now redundant

# ✅ CRITICAL: Silence all external library loggers that cause WARNING messages
external_loggers = [
    'tabula', 'jpype', 'jpype1', 'camelot', 'chromadb', 
    'pdfplumber', 'PyPDF2', 'fitz', 'urllib3', 'requests'
]
for lib_logger in external_loggers:
    logging.getLogger(lib_logger).setLevel(logging.CRITICAL)

# ✅ FIX: Suppress external library warnings
warnings.filterwarnings(
    "ignore", message="Failed to import jpype dependencies.*"
)
warnings.filterwarnings("ignore", message="No module named 'jpype'")
warnings.filterwarnings("ignore", category=UserWarning, module="camelot.*")
warnings.filterwarnings(
    "ignore", message="No tables found in table area.*"
)
# ✅ NEW: Suppress ChromaDB telemetry errors
warnings.filterwarnings(
    "ignore", message="Failed to send telemetry event.*"
)
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb.*")


@dataclass
class PDFExtractionResult:
    """Real PDF extraction result - no simulations"""
    product_name: str
    extracted_text: str
    technical_specs: Dict[str, Any]
    pricing_info: Dict[str, Any]
    tables_data: List[Dict[str, Any]]
    confidence_score: float
    extraction_method: str
    source_filename: str
    processing_time: float
    
    # ✅ NEW: Detailed extraction tracking
    extraction_metadata: Dict[str, Any] = None
    text_extraction_method: str = "unknown"
    table_extraction_method: str = "unknown"
    ai_analysis_method: str = "claude-3-5-haiku"
    extraction_timestamp: str = None
    table_quality_score: float = 0.0
    advanced_tables_used: bool = False
    extraction_attempts: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.extraction_metadata is None:
            self.extraction_metadata = {}
        if self.extraction_attempts is None:
            self.extraction_attempts = []
        if self.extraction_timestamp is None:
            from datetime import datetime
            self.extraction_timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary."""
        return asdict(self)


class RealPDFProcessor:
    """Complete AI-powered PDF processing system for construction materials"""

    def __init__(self, db_session: Session = None, enable_ai_analysis: bool = True):
        """Initialize with optional database session and AI analysis"""
        self.enable_ai_analysis = enable_ai_analysis
        self.db_session = db_session
        
        # ✅ Initialize processing stats
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped_duplicates": 0,
            "total_extraction_time": 0.0
        }
        
        # ✅ Initialize parameter mapping for table extraction
        self.parameter_map = {
            "hővezetési tényező": "thermal_conductivity",
            "lambda érték": "thermal_conductivity",
            "λ érték": "thermal_conductivity",
            "tűzvédelmi osztály": "fire_classification",
            "nyomószilárdság": "compressive_strength",
            "sűrűség": "density",
            "vastagság": "thickness",
            "méret": "dimensions",
            "alkalmazási terület": "application_area"
        }
        
        # ✅ Initialize extractors
        self.extractor = RealPDFExtractor()
        self.advanced_table_extractor = AdvancedTableExtractor()
        
        if self.enable_ai_analysis:
            try:
                self.ai_analyzer = ClaudeAIAnalyzer()
                logger.info("✅ Claude AI Analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ AI Analyzer initialization failed: {e}")
                self.ai_analyzer = None
        else:
            self.ai_analyzer = None
            
        # ✅ NEW: Use the DataIngestionService for all DB operations
        if self.db_session:
            self.ingestion_service = DataIngestionService(self.db_session)
            self.processed_file_hashes = (
                self.ingestion_service.load_processed_hashes()
            )
        else:
            self.ingestion_service = None
            self.processed_file_hashes = set()
            
        logger.info(
            f"🚀 RealPDFProcessor initialized (AI: {self.enable_ai_analysis})"
        )

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculates the SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _extract_specs_from_tables(
        self, tables: List[Dict]
    ) -> Dict[str, Any]:
        """
        Extracts technical specifications directly from parsed table data.
        """
        specs = {}
        found_keys = set()
        for table in tables:
            for row in table.get("data", []):
                if not row or len(row) < 2:
                    continue
                key_cell = str(row[0]) if row[0] is not None else ""
                key_normalized = key_cell.lower().strip().replace(":", "")
                if key_normalized in self.parameter_map:
                    standard_key = self.parameter_map[key_normalized]
                    if standard_key not in found_keys:
                        value = str(row[1]).strip()
                        specs[standard_key] = value
                        found_keys.add(standard_key)
        if specs:
            logger.info(f"🔍 Found {len(specs)} specs via table parsing.")
        return specs

    def _create_document_text(self, result: PDFExtractionResult) -> str:
        """Helper to create a single text document from the extraction result."""
        text_parts = [
            f"Termék: {result.product_name}",
            f"Gyártó: {result.extraction_metadata.get('manufacturer', 'Ismeretlen')}",
            f"Forrás PDF: {result.source_filename}",
        ]
        if result.technical_specs:
            specs_str = ", ".join(
                f"{k}: {v}" for k, v in result.technical_specs.items()
            )
            text_parts.append(f"Műszaki adatok: {specs_str}")
        if result.extracted_text:
            text_parts.append(
                f"\n--- Kivonatolt szöveg ---\n{result.extracted_text[:2000]}"
            )

        return "\n\n".join(text_parts)

    def _calculate_enhanced_confidence(
        self, 
        text_content: str, 
        tables: List[Dict], 
        pattern_specs: Dict[str, Any], 
        ai_analysis: Dict[str, Any], 
        extraction_method: str
    ) -> float:
        """Calculate dynamic confidence score based on content quality."""
        
        confidence_factors = []
        
        extraction_metadata = ai_analysis.get("extraction_metadata", {})
        ai_confidence = extraction_metadata.get("confidence_score", 0.5)
        data_completeness = extraction_metadata.get("data_completeness", 0.0)
        
        if isinstance(ai_confidence, (int, float)):
            confidence_factors.append(
                ("ai_confidence", float(ai_confidence), 0.35)
            )
        
        if isinstance(data_completeness, (int, float)):
            confidence_factors.append(
                ("data_completeness", float(data_completeness), 0.25)
            )
        
        text_quality = self._assess_text_quality(text_content)
        confidence_factors.append(("text_quality", text_quality, 0.15))
        
        table_quality = self._assess_table_quality(tables)
        confidence_factors.append(("table_quality", table_quality, 0.15))
        
        validation_score = self._cross_validate_extractions(
            pattern_specs, ai_analysis
        )
        confidence_factors.append(("validation_score", validation_score, 0.1))
        
        total_score = sum(score * weight for _, score, weight in confidence_factors)
        total_weight = sum(weight for _, _, weight in confidence_factors)
        
        final_confidence = total_score / total_weight if total_weight > 0 else 0.0
        
        final_confidence = self._apply_content_type_adjustments(
            final_confidence, ai_analysis, extraction_method
        )
        
        logger.debug(f"Dynamic confidence breakdown: {confidence_factors}")
        logger.debug(f"Final confidence: {final_confidence:.3f}")
        
        return round(final_confidence, 3)
    
    def _assess_text_quality(self, text_content: str) -> float:
        """Assess text quality based on content characteristics."""
        if not text_content:
            return 0.0
        
        quality_indicators = [
            ('length', len(text_content) > 500, 0.3),
            ('technical_terms', any(term in text_content.lower() for term in 
             ['hővezetési', 'thermal', 'rockwool', 'szigetelés']), 0.4),
            ('structured_data', ':' in text_content and '\n' in text_content, 0.3)
        ]
        
        score = sum(weight for _, present, weight in quality_indicators if present)
        return min(1.0, score)
    
    def _assess_table_quality(self, tables: List[Dict]) -> float:
        """Assess table quality based on structure and content."""
        if not tables:
            return 0.0
        
        total_quality = 0.0
        for table in tables:
            table_score = 0.0
            
            headers = table.get('headers', [])
            if headers and len(headers) > 1:
                table_score += 0.4
            
            data = table.get('data', [])
            if data and len(data) > 1:
                table_score += 0.4
            
            table_text = str(table).lower()
            if any(term in table_text for term in ['λ', 'w/mk', 'kg/m³', 'kpa']):
                table_score += 0.2
            
            total_quality += table_score
        
        return min(1.0, total_quality / len(tables))
    
    def _cross_validate_extractions(self, pattern_specs: Dict[str, Any], 
                                   ai_analysis: Dict[str, Any]) -> float:
        """Cross-validate pattern-based and AI extractions."""
        if not pattern_specs and not ai_analysis.get("technical_specifications"):
            return 0.0
        
        ai_specs = ai_analysis.get("technical_specifications", {})
        
        matching_fields = 0
        total_fields = len(set(pattern_specs.keys()) | set(ai_specs.keys()))
        
        for field in pattern_specs:
            if field in ai_specs:
                matching_fields += 1
        
        if total_fields > 0:
            return matching_fields / total_fields
        return 0.0
    
    def _apply_content_type_adjustments(self, base_confidence: float, 
                                      ai_analysis: Dict[str, Any], 
                                      extraction_method: str) -> float:
        """Apply content-type specific confidence adjustments."""
        
        method_multipliers = {
            "pdfplumber": 1.0,
            "pypdf2": 0.9,
            "pymupdf": 0.95
        }
        
        adjusted_confidence = base_confidence * method_multipliers.get(
            extraction_method, 0.8
        )
        
        extraction_metadata = ai_analysis.get("extraction_metadata", {})
        content_type = extraction_metadata.get("content_type", "unknown")
        
        if content_type == "insulation_datasheet":
            adjusted_confidence *= 1.05
        elif content_type == "technical_spec":
            adjusted_confidence *= 1.02
        elif content_type == "unknown":
            adjusted_confidence *= 0.9
        
        return min(1.0, adjusted_confidence)

    async def _extract_content_from_pdf(
        self, pdf_path: Path
    ) -> Dict[str, Any]:
        """
        Extracts raw text and table data from a PDF using multiple strategies.
        Returns a dictionary with extracted content and methods used.
        """
        text_content, tables, text_method = (
            self.extractor.extract_pdf_content(pdf_path)
        )
        
        advanced_tables_result = (
            self.advanced_table_extractor.extract_tables_hybrid(pdf_path)
        )
        if advanced_tables_result and advanced_tables_result.tables:
            tables.extend(advanced_tables_result.tables)
            table_method = advanced_tables_result.extraction_method
            table_quality_score = advanced_tables_result.quality_score
            advanced_tables_used = True
        else:
            table_method = "basic"
            table_quality_score = self._assess_table_quality(tables)
            advanced_tables_used = False

        return {
            "text_content": text_content,
            "tables": tables,
            "text_method": text_method,
            "table_method": table_method,
            "table_quality_score": table_quality_score,
            "advanced_tables_used": advanced_tables_used,
        }

    async def _analyze_content_with_ai(
        self, text_content: str, tables: List[Dict], pdf_name: str
    ) -> Dict[str, Any]:
        """Analyzes the extracted content using the AI service."""
        if self.ai_analyzer:
            return await self.ai_analyzer.analyze_rockwool_pdf(
                text_content, tables, pdf_name
            )
        return {}

    def _consolidate_extraction_results(
        self,
        pdf_path: Path,
        start_time: datetime,
        content: Dict[str, Any],
        ai_analysis: Dict[str, Any],
    ) -> PDFExtractionResult:
        """Consolidates all extracted data into a final result object."""
        text_content = content["text_content"]
        tables = content["tables"]
        text_method = content["text_method"]
        table_method = content["table_method"]

        pattern_specs = self._extract_specs_from_tables(tables)
        processing_time = (datetime.now() - start_time).total_seconds()

        return PDFExtractionResult(
            product_name=clean_utf8(
                ai_analysis.get("product_identification", {}).get("name")
                or pdf_path.stem
            ),
            extracted_text=clean_utf8(text_content),
            technical_specs=ai_analysis.get(
                "technical_specifications", pattern_specs
            ),
            pricing_info=ai_analysis.get("pricing_information", {}),
            tables_data=tables,
            confidence_score=self._calculate_enhanced_confidence(
                text_content,
                tables,
                pattern_specs,
                ai_analysis,
                text_method
            ),
            extraction_method=(
                f"text:{text_method}|table:{table_method}|ai:"
                f"{self.ai_analyzer.model if self.ai_analyzer else 'none'}"
            ),
            source_filename=pdf_path.name,
            processing_time=processing_time,
            table_quality_score=content["table_quality_score"],
            advanced_tables_used=content["advanced_tables_used"],
        )

    def _ingest_result(self, result: PDFExtractionResult, file_hash: str):
        """Ingests the final processing result into the databases."""
        if not self.ingestion_service:
            return

        product_id = self.ingestion_service.ingest_to_postgresql(result)
        if product_id:
            self.ingestion_service.ingest_to_chromadb(result, product_id)
            self.ingestion_service.save_processed_hash(
                file_hash, product_id
            )
            self.processed_file_hashes.add(file_hash)

    async def process_pdf(self, pdf_path: Path) -> Optional[PDFExtractionResult]:
        """
        Processes a single PDF file through the entire pipeline.
        """
        start_time = datetime.now()
        self.processing_stats["total_processed"] += 1

        file_hash = self._calculate_file_hash(pdf_path)
        if self.ingestion_service and file_hash in self.processed_file_hashes:
            logger.info(f"⏭️ Skipping duplicate file: {pdf_path.name}")
            self.processing_stats["skipped_duplicates"] += 1
            return None

        try:
            content = await self._extract_content_from_pdf(pdf_path)
            ai_analysis = await self._analyze_content_with_ai(
                content["text_content"], content["tables"], pdf_path.name
            )
            
            result = self._consolidate_extraction_results(
                pdf_path, start_time, content, ai_analysis
            )

            self._ingest_result(result, file_hash)

            self.processing_stats["successful"] += 1
            logger.info(
                f"✅ Successfully processed {pdf_path.name} "
                f"in {result.processing_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(
                f"❌ Failed to process {pdf_path.name}: {e}", exc_info=True
            )
            self.processing_stats["failed"] += 1
            return None

    async def process_directory(
        self, pdf_directory: Path, output_file: Optional[Path] = None, 
        test_pdfs: Optional[List[str]] = None
    ) -> List[PDFExtractionResult]:
        """Process PDFs in a directory with parallel processing."""
        
        if not pdf_directory.is_dir():
            raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
        
        if test_pdfs:
            pdf_files = [pdf_directory / test_pdf for test_pdf in test_pdfs if (pdf_directory / test_pdf).exists()]
            logger.info(f"🧪 Testing with {len(pdf_files)} selected PDFs.")
        else:
            pdf_files = list(pdf_directory.glob("*.pdf"))
            logger.info(f"📁 Found {len(pdf_files)} PDF files in {pdf_directory}.")

        # --- PÁRHUZAMOSÍTÁS ("DUPLA KAKAÓ") ---
        MAX_CONCURRENT_TASKS = 8
        logger.info(f"🚀 Engaging parallel processing with {MAX_CONCURRENT_TASKS} workers.")
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

        async def process_with_semaphore(pdf_path: Path, index: int, total: int) -> Optional[PDFExtractionResult]:
            """Helper to process a single PDF with semaphore control."""
            async with semaphore:
                logger.info(f"📄 ({index}/{total}) -> Indul a feldgozás: {pdf_path.name}")
                try:
                    return await self.process_pdf(pdf_path)
                except Exception as e:
                    logger.error(f"❌ Critical error in process_pdf for {pdf_path.name}: {e}", exc_info=True)
                    return None
        
        tasks = [process_with_semaphore(pdf_path, i + 1, len(pdf_files)) for i, pdf_path in enumerate(pdf_files)]
        
        # Futtatjuk a feladatokat párhuzamosan
        results_with_none = await asyncio.gather(*tasks)
        
        # Kiszűrjük a sikeres (nem None) eredményeket
        results = [res for res in results_with_none if res is not None]
        
        if output_file and results:
            self._save_results(results, output_file)
        
        self._print_final_stats(results)
        
        return results
    
    def _save_results(
        self, results: List[PDFExtractionResult], output_file: Path
    ):
        """Save processing results to JSON"""
        
        output_data = {
            "processing_timestamp": datetime.now().isoformat(),
            "total_pdfs_processed": len(results),
            "results": [asdict(result) for result in results],
            "statistics": self.processing_stats,
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {output_file}")

    def _print_final_stats(self, results: List[PDFExtractionResult]):
        """Print processing statistics."""
        
        print("\n" + "=" * 80)
        print("🏁 REAL PDF PROCESSING COMPLETE")
        print("=" * 80)
        
        stats = self.processing_stats
        print("📊 Processing Statistics:")
        print(f"   📄 Total files checked: {stats['total_processed']}")
        print(f"   ✅ New files processed: {stats['successful']}")
        print(f"   ⏭️  Skipped duplicates: {stats['skipped_duplicates']}")
        print(f"   ❌ Failed extractions: {stats['failed']}")
        print(
            f"   ⏱️  Total processing time: "
            f"{stats['total_extraction_time']:.2f}s"
        )
        
        if results:
            avg_confidence = (
                sum(r.confidence_score for r in results) / len(results)
            )
            avg_specs = (
                sum(len(r.technical_specs) for r in results)
            )
            if results:
                avg_specs /= len(results)
            
            print("\n🎯 Quality Metrics:")
            print(f"   📈 Average confidence: {avg_confidence:.2f}")
            print(f"   🔧 Average specs per product: {avg_specs:.1f}")
            
            methods = {}
            for result in results:
                methods[result.extraction_method] = (
                    methods.get(result.extraction_method, 0) + 1
                )
            
            print(f"\n🔧 Extraction Methods:")
            for method, count in methods.items():
                print(f"   {method}: {count} PDFs")
        
        print(f"\n✅ REAL AI-POWERED PDF PROCESSING COMPLETE")
        print("   - Actual PDF text extraction (PyPDF2, pdfplumber, PyMuPDF)")
        print("   - Real Claude 3.5 Haiku AI analysis")
        print("   - Structured technical data extraction")
        print("   - Pricing information extraction")
        print("   - NO SIMULATIONS - 100% real processing")

async def main():
    """Main execution function"""
    
    print("🚀 LAMBDA.HU REAL PDF PROCESSOR")
    print("=" * 80)
    print("NO SIMULATIONS - Real AI-powered PDF content extraction")
    print("✅ PyPDF2 + pdfplumber + PyMuPDF")
    print("✅ Claude 3.5 Haiku AI analysis")
    print("✅ Structured technical data extraction")
    print()
    
    db_session: Optional[Session] = None
    processor = None
    
    try:
        db_session = SessionLocal()

        processor = RealPDFProcessor(db_session)
        
        # JAVÍTÁS: Abszolút, feloldott útvonal használata a garantált működéshez
        script_dir = Path(__file__).resolve().parent
        pdf_directory = script_dir.parent / "downloads" / "rockwool_datasheets"
        output_file = script_dir.parent.parent.parent / "real_pdf_extraction_results.json"
        
        results = await processor.process_directory(
            pdf_directory, output_file, test_pdfs=None
        )
        
        print(f"\n🎉 SUCCESS: {len(results)} new PDFs processed.")
        
    except Exception as e:
        logger.error(f"❌ Top-level processing failed: {e}")
        raise
    finally:
        try:
            if processor:
                if hasattr(processor, 'ingestion_service') and processor.ingestion_service:
                    try:
                        # Assuming a close method might be needed in the future
                        # processor.ingestion_service.close_chromadb()
                        pass
                    except:
                        pass
                
                if hasattr(processor, 'db_session') and processor.db_session:
                    try:
                        processor.db_session.close()
                    except:
                        pass
            
            if db_session and db_session.is_active:
                try:
                    db_session.close()
                except:
                    pass
            
            import gc
            gc.collect()
            
            import time
            time.sleep(0.1)
            
        except Exception as cleanup_error:
            logger.debug(f"Cleanup warning (non-critical): {cleanup_error}")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main()) 
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        try:
            import gc
            gc.collect()
        except:
            pass

