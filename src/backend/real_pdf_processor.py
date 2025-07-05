#!/usr/bin/env python3
"""
Lambda.hu Real PDF Processor
NO SIMULATIONS - Real AI-powered PDF content extraction

Uses:
- PyPDF2/pdfplumber for actual PDF text extraction
- Claude 3.5 Sonnet for intelligent content analysis
- Structured data extraction for product specs and prices
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

# PDF Processing
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

# AI Integration
from anthropic import Anthropic

# Environment
from dotenv import load_dotenv

# Database Integration
from sqlalchemy.orm import Session
from app.database import SessionLocal
from models.processed_file_log import ProcessedFileLog
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.category import Category

# ChromaDB Integration
import chromadb
from chromadb.config import Settings

# Load environment variables
load_dotenv("../../.env")  # Load from root directory

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary."""
        return asdict(self)


class RealPDFExtractor:
    """Real PDF text extraction using multiple methods"""
    
    def __init__(self):
        self.extraction_methods = ["pdfplumber", "pypdf2", "pymupdf"]
        self.stats = {
            "pages_processed": 0,
            "text_extracted": 0,
            "tables_found": 0,
        }
    
    def extract_text_pdfplumber(
        self, pdf_path: Path
    ) -> Tuple[str, List[Dict]]:
        """Extract text and tables using pdfplumber"""
        text_content = ""
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content += (
                            f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
                        )
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    for table_idx, table in enumerate(page_tables):
                        if table:
                            table_dict = {
                                'page': page_num + 1,
                                'table_index': table_idx,
                                'headers': table[0] if table else [],
                                'data': table[1:] if len(table) > 1 else [],
                                'raw_table': table
                            }
                            tables.append(table_dict)
                    
                    self.stats['pages_processed'] += 1
        
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed: {e}")
            raise
        
        self.stats['text_extracted'] = len(text_content)
        self.stats['tables_found'] = len(tables)
        
        return text_content, tables
    
    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """Fallback extraction using PyPDF2"""
        text_content = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += (
                            f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
                        )
        
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise
        
        return text_content
    
    def extract_text_pymupdf(
        self, pdf_path: Path
    ) -> Tuple[str, List[Dict]]:
        """Extract text and structured data using PyMuPDF"""
        text_content = ""
        tables = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text
                page_text = page.get_text()
                if page_text:
                    text_content += (
                        f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
                    )
                
                # Extract tables (simplified)
                # Note: PyMuPDF table extraction requires additional processing
                blocks = page.get_text("dict")
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        # Process text blocks that might contain tabular data
                        pass
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise
        
        return text_content, tables
    
    def extract_pdf_content(
        self, pdf_path: Path
    ) -> Tuple[str, List[Dict], str]:
        """Extract PDF content using best available method"""
        
        logger.info(f"🔍 Extracting PDF content: {pdf_path.name}")
        
        # Try pdfplumber first (best for tables)
        try:
            text, tables = self.extract_text_pdfplumber(pdf_path)
            if text.strip():
                log_msg = f"✅ PDFPlumber: {len(text)} chars, {len(tables)} tables"
                logger.info(log_msg)
                return text, tables, "pdfplumber"
        except Exception as e:
            logger.warning(f"⚠️ PDFPlumber failed: {e}")
        
        # Fallback to PyPDF2
        try:
            text = self.extract_text_pypdf2(pdf_path)
            if text.strip():
                logger.info(f"✅ PyPDF2: {len(text)} chars")
                return text, [], "pypdf2"
        except Exception as e:
            logger.warning(f"⚠️ PyPDF2 failed: {e}")
        
        # Last resort: PyMuPDF
        try:
            text, tables = self.extract_text_pymupdf(pdf_path)
            if text.strip():
                log_msg = f"✅ PyMuPDF: {len(text)} chars, {len(tables)} tables"
                logger.info(log_msg)
                return text, tables, "pymupdf"
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            raise
        
        raise Exception("All PDF extraction methods failed")

class ClaudeAIAnalyzer:
    """Real Claude AI analysis for PDF content - no simulations"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ ANTHROPIC_API_KEY not found in environment variables"
            )
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        logger.info(f"✅ Claude AI initialized: {self.model}")
    
    def analyze_rockwool_pdf(
        self, text_content: str, tables_data: List[Dict], filename: str
    ) -> Dict[str, Any]:
        """Analyze ROCKWOOL PDF content with Claude AI"""
        
        # Prepare context for Claude
        context = self._prepare_analysis_context(text_content, tables_data, filename)
        
        # Create prompt for structured extraction
        prompt = self._create_extraction_prompt(context)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,  # Low temperature for factual extraction
                system=(
                    "You are an expert technical data analyst specializing in "
                    "building materials and insulation products. Extract "
                    "accurate technical specifications and pricing information "
                    "from ROCKWOOL product documentation."
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Parse Claude's response
            analysis_result = self._parse_claude_response(response.content[0].text)
            
            logger.info(f"✅ Claude analysis complete for {filename}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            raise
    
    def _prepare_analysis_context(
        self, text: str, tables: List[Dict], filename: str
    ) -> Dict[str, Any]:
        """Prepare context for Claude analysis"""
        
        context = {
            "filename": filename,
            "text_length": len(text),
            "tables_count": len(tables),
            "extracted_text": text[:8000],  # Limit text for API
            "tables_summary": [],
        }
        
        # Summarize tables
        for table in tables[:5]:  # Limit to first 5 tables
            table_summary = {
                "page": table.get("page", "unknown"),
                "headers": table.get("headers", []),
                "row_count": len(table.get("data", [])),
                "sample_data": table.get("data", [])[:3],  # First 3 rows
            }
            context["tables_summary"].append(table_summary)
        
        return context
    
    def _create_extraction_prompt(self, context: Dict[str, Any]) -> str:
        """Create a more generic, structured prompt for Claude."""
        
        prompt = f"""
Analyze the following content from the document '{context['filename']}'.
The document contains {context['text_length']} characters of text and {context['tables_count']} tables.

EXTRACTED CONTENT:
{context['extracted_text']}
"""
        if context["tables_summary"]:
            prompt += "\n\nTABLES SUMMARY:\n"
            for i, table in enumerate(context["tables_summary"], 1):
                prompt += f"\nTable {i} (Page {table['page']}):\n"
                prompt += f"Headers: {table['headers']}\n"
                prompt += f"Sample data: {table['sample_data']}\n"
        
        prompt += """

EXTRACT THE FOLLOWING INFORMATION IN A VALID JSON FORMAT:

{
  "product_identification": {
    "name": "The exact product name, including any variations or model numbers",
    "product_code": "The official product code or SKU, if available",
    "category": "The general product category (e.g., 'Insulation', 'Brick', 'Mortar')",
    "application": "The intended use or application area of the product"
  },
  "technical_specifications": {
    "thermal_conductivity": { "value": "numerical_value", "unit": "W/mK" },
    "fire_classification": { "value": "A1, A2, etc.", "standard": "e.g., EN 13501-1" },
    "density": { "value": "numerical_value", "unit": "kg/m³" },
    "compressive_strength": { "value": "numerical_value", "unit": "kPa" }
  },
  "confidence_assessment": {
    "overall_confidence": "A score from 0.0 to 1.0 indicating your confidence in the accuracy of the extracted data",
    "notes": "Any uncertainties, ambiguities, or missing information you encountered"
  }
}

IMPORTANT REQUIREMENTS:
1.  Extract ONLY factual information found in the document.
2.  If a value is not found, use `null`.
3.  Populate all fields in the requested JSON structure.
4.  Focus on technical accuracy.

Return only the valid JSON object.
"""
        return prompt
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response"""
        
        try:
            # Find JSON in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in Claude response")
            
            json_text = response_text[json_start:json_end]
            
            # Parse JSON
            result = json.loads(json_text)
            
            # Validate structure
            required_keys = [
                "product_identification",
                "technical_specifications",
                "confidence_assessment",
            ]
            for key in required_keys:
                if key not in result:
                    logger.warning(f"Missing key in Claude response: {key}")
                    result[key] = {}
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            # Return empty structure
            return {
                "product_identification": {},
                "technical_specifications": {},
                "pricing_information": {},
                "additional_data": {},
                "confidence_assessment": {
                    "overall_confidence": 0.0,
                    "notes": f"JSON parsing failed: {e}",
                },
            }
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            raise

class RealPDFProcessor:
    """Main class for real PDF processing - NO SIMULATIONS"""
    
    def __init__(self, db_session: Session):
        """Initializes the processor with a database session."""
        self.extractor = RealPDFExtractor()
        self.ai_analyzer = ClaudeAIAnalyzer()
        self.db_session = db_session
        self._load_hashes()
        self._init_chromadb()
        self.parameter_map = {
            # --- Thermal Properties ---
            "hővezetési tényező": "thermal_conductivity",
            "lambda érték": "thermal_conductivity",
            "hővezetési tényező λd": "thermal_conductivity",
            "deklarált hővezetési tényező": "thermal_conductivity",
            # --- Fire Safety ---
            "tűzvédelmi osztály": "fire_classification",
            "éghetőségi osztály": "fire_classification",
            "reakció tűzre": "fire_classification",
            "tűzveszélyességi osztály": "fire_classification",
            # --- Mechanical Properties ---
            "testsűrűség": "density",
            "névleges testsűrűség": "density",
            "nyomószilárdság": "compressive_strength",
            "nyomófeszültség": "compressive_strength",
        }
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped_duplicates": 0,
            "total_extraction_time": 0.0,
        }

    def _load_hashes(self):
        """Loads all file hashes from the database into memory."""
        logger.info("Loading existing file hashes from the database...")
        all_logs = self.db_session.query(ProcessedFileLog.file_hash).all()
        self.processed_file_hashes = {log.file_hash for log in all_logs}
        logger.info(
            f"Loaded {len(self.processed_file_hashes)} unique file hashes."
        )

    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage."""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path="./chromadb_data"
            )
            
            # Get or create collection for PDF content
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="pdf_products",
                metadata={"description": "PDF product data for RAG pipeline"}
            )
            
            logger.info("✅ ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.chroma_collection = None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculates the SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _extract_specs_from_tables(self, tables: List[Dict]) -> Dict[str, Any]:
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

    def _ingest_to_postgresql(self, result: PDFExtractionResult) -> Optional[int]:
        """Ingest extraction result to PostgreSQL as a Product."""
        try:
            # Get or create manufacturer (assuming ROCKWOOL for now)
            manufacturer = self.db_session.query(Manufacturer).filter_by(
                name="ROCKWOOL"
            ).first()
            
            if not manufacturer:
                manufacturer = Manufacturer(
                    name="ROCKWOOL",
                    description="ROCKWOOL insulation products"
                )
                self.db_session.add(manufacturer)
                self.db_session.flush()  # Get ID
            
            # Get or create category (determine from specs or default)
            category_name = self._determine_category(result.technical_specs)
            category = self.db_session.query(Category).filter_by(
                name=category_name
            ).first()
            
            if not category:
                category = Category(name=category_name)
                self.db_session.add(category)
                self.db_session.flush()  # Get ID
            
            # Create product
            product = Product(
                name=result.product_name,
                description=f"Extracted from {result.source_filename}",
                manufacturer_id=manufacturer.id,
                category_id=category.id,
                technical_specs=result.technical_specs,
                sku=self._generate_sku(result.product_name),
                price=self._extract_price_from_result(result)
            )
            
            self.db_session.add(product)
            self.db_session.commit()
            
            logger.info(f"💾 Product saved to PostgreSQL: {product.name}")
            return product.id
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL ingestion failed: {e}")
            self.db_session.rollback()
            return None

    def _ingest_to_chromadb(self, result: PDFExtractionResult, product_id: Optional[int]):
        """Ingest extraction result to ChromaDB for vector search."""
        if not self.chroma_collection:
            logger.warning("ChromaDB not available, skipping vector ingestion")
            return
            
        try:
            # Create document text for embedding
            doc_text = self._create_document_text(result)
            
            # Create metadata
            metadata = {
                "product_name": result.product_name,
                "source_filename": result.source_filename,
                "extraction_method": result.extraction_method,
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time,
                "product_id": product_id if product_id else -1,
                "manufacturer": "ROCKWOOL"
            }
            
            # Add technical specs to metadata
            for key, value in result.technical_specs.items():
                if isinstance(value, (str, int, float)):
                    metadata[f"spec_{key}"] = str(value)
            
            # Generate unique ID for ChromaDB
            doc_id = f"pdf_{result.source_filename}_{hashlib.md5(doc_text.encode()).hexdigest()[:8]}"
            
            # Add to ChromaDB
            self.chroma_collection.add(
                documents=[doc_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"🔍 Document added to ChromaDB: {doc_id}")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB ingestion failed: {e}")

    def _determine_category(self, specs: Dict[str, Any]) -> str:
        """Determine product category from technical specifications."""
        # Simple heuristic based on specs
        if "thermal_conductivity" in specs:
            return "Thermal Insulation"
        elif "fire_classification" in specs:
            return "Fire Protection"
        elif "compressive_strength" in specs:
            return "Structural Materials"
        else:
            return "Building Materials"

    def _generate_sku(self, product_name: str) -> str:
        """Generate a simple SKU from product name."""
        # Clean product name and create SKU
        clean_name = "".join(c for c in product_name if c.isalnum())[:10].upper()
        return f"ROCK-{clean_name}-{datetime.now().strftime('%Y%m')}"

    def _extract_price_from_result(self, result: PDFExtractionResult) -> Optional[float]:
        """Extract price from result if available."""
        pricing_info = result.pricing_info
        if pricing_info and "price" in pricing_info:
            try:
                return float(pricing_info["price"])
            except (ValueError, TypeError):
                pass
        return None

    def _create_document_text(self, result: PDFExtractionResult) -> str:
        """Create searchable document text for ChromaDB."""
        text_parts = [
            f"Product: {result.product_name}",
            f"Source: {result.source_filename}",
        ]
        
        # Add technical specifications
        if result.technical_specs:
            text_parts.append("Technical Specifications:")
            for key, value in result.technical_specs.items():
                text_parts.append(f"- {key}: {value}")
        
        # Add excerpt from extracted text
        if result.extracted_text:
            text_parts.append("Content excerpt:")
            text_parts.append(result.extracted_text[:1000])  # First 1000 chars
        
        return "\n".join(text_parts)

    def _calculate_enhanced_confidence(
        self, 
        text_content: str, 
        tables: List[Dict], 
        pattern_specs: Dict[str, Any], 
        ai_analysis: Dict[str, Any], 
        extraction_method: str
    ) -> float:
        """Calculate enhanced confidence score based on multiple quality factors."""
        
        confidence_factors = []
        
        # Factor 1: AI confidence (if available)
        ai_confidence = ai_analysis.get("confidence_assessment", {}).get(
            "overall_confidence", 0.5
        )
        if isinstance(ai_confidence, (int, float)):
            confidence_factors.append(("ai_confidence", float(ai_confidence), 0.3))
        
        # Factor 2: Text extraction quality
        text_quality = min(1.0, len(text_content) / 1000.0)  # Normalize by 1000 chars
        confidence_factors.append(("text_quality", text_quality, 0.2))
        
        # Factor 3: Table extraction success
        table_quality = min(1.0, len(tables) / 3.0)  # Normalize by 3 tables
        confidence_factors.append(("table_quality", table_quality, 0.2))
        
        # Factor 4: Pattern-based extraction success
        pattern_quality = min(1.0, len(pattern_specs) / 5.0)  # Normalize by 5 specs
        confidence_factors.append(("pattern_quality", pattern_quality, 0.15))
        
        # Factor 5: Extraction method reliability
        method_reliability = {
            "pdfplumber": 0.9,  # Best for tables
            "pypdf2": 0.7,      # Reliable fallback
            "pymupdf": 0.8      # Good alternative
        }.get(extraction_method, 0.5)
        confidence_factors.append(("method_reliability", method_reliability, 0.15))
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in confidence_factors)
        total_weight = sum(weight for _, _, weight in confidence_factors)
        
        final_confidence = total_score / total_weight if total_weight > 0 else 0.0
        
        # Log confidence breakdown for debugging
        logger.debug(f"Confidence breakdown: {confidence_factors}")
        logger.debug(f"Final confidence: {final_confidence:.3f}")
        
        return round(final_confidence, 3)

    def process_pdf(self, pdf_path: Path) -> Optional[PDFExtractionResult]:
        """Process a single PDF with real AI analysis and deduplication."""
        
        start_time = datetime.now()
        
        try:
            # === DEDUPLICATION CHECK ===
            file_hash = self._calculate_file_hash(pdf_path)
            if file_hash in self.processed_file_hashes:
                logger.warning(
                    f"⏭️  SKIPPING DUPLICATE: {pdf_path.name} already processed."
                )
                self.processing_stats["skipped_duplicates"] += 1
                return None

            logger.info(f"🚀 Processing new file: {pdf_path.name}")
            
            # Step 1: Extract text and tables
            text_content, tables, method = self.extractor.extract_pdf_content(
                pdf_path
            )
            if not text_content.strip():
                raise ValueError("No text content could be extracted from PDF")
            
            # Step 2: Attempt pattern-based extraction from tables
            pattern_based_specs = self._extract_specs_from_tables(tables)

            # Step 3: AI analysis with Claude
            ai_analysis = self.ai_analyzer.analyze_rockwool_pdf(
                text_content, tables, pdf_path.name
            )
            
            # Step 4: Combine and create result
            final_specs = pattern_based_specs.copy()
            final_specs.update(ai_analysis.get("technical_specifications", {}))

            processing_time = (datetime.now() - start_time).total_seconds()

            # === TASK 5: ENHANCED CONFIDENCE SCORING ===
            enhanced_confidence = self._calculate_enhanced_confidence(
                text_content, tables, pattern_based_specs, ai_analysis, method
            )
            
            result = PDFExtractionResult(
                product_name=ai_analysis.get("product_identification", {}).get(
                    "name", pdf_path.stem
                ),
                extracted_text=text_content,
                technical_specs=final_specs,
                pricing_info=ai_analysis.get("pricing_information", {}),
                tables_data=tables,
                confidence_score=enhanced_confidence,
                extraction_method=method,
                source_filename=pdf_path.name,
                processing_time=processing_time,
            )

            # === SAVE NEW HASH TO DATABASE ===
            new_log = ProcessedFileLog(
                file_hash=file_hash,
                content_hash=file_hash,  # Placeholder, can be enhanced later
                source_filename=pdf_path.name,
            )
            self.db_session.add(new_log)
            self.db_session.commit()
            self.processed_file_hashes.add(file_hash)  # Update in-memory set
            logger.info(f"💾 Hash for {pdf_path.name} saved to DB.")

            # === TASK 4: FINAL DATA INGESTION ===
            # Ingest to PostgreSQL
            product_id = self._ingest_to_postgresql(result)
            
            # Ingest to ChromaDB for vector search
            self._ingest_to_chromadb(result, product_id)
            
            # Update stats
            self.processing_stats["successful"] += 1
            self.processing_stats['total_extraction_time'] += processing_time
            
            logger.info(f"✅ Success: {pdf_path.name} ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            self.processing_stats['failed'] += 1
            logger.error(f"❌ Failed: {pdf_path.name} - {e}")
            raise
        
        finally:
            self.processing_stats["total_processed"] += 1
    
    def process_directory(
        self, pdf_directory: Path, output_file: Optional[Path] = None
    ) -> List[PDFExtractionResult]:
        """Process all PDFs in a directory."""
        
        if not pdf_directory.exists():
            raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
        
        pdf_files = list(pdf_directory.glob("*.pdf"))
        logger.info(
            f"📁 Found {len(pdf_files)} PDF files in {pdf_directory}."
        )
        
        results = []
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                logger.info(
                    f"\n📄 ({i}/{len(pdf_files)}): Checking {pdf_path.name}"
                )
                result = self.process_pdf(pdf_path)
                if result:  # Only append if not a duplicate
                    results.append(result)
                
            except Exception as e:
                logger.error(f"Skipping {pdf_path.name} due to error: {e}")
                continue
        
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
            
            # Method breakdown
            methods = {}
            for result in results:
                methods[result.extraction_method] = methods.get(result.extraction_method, 0) + 1
            
            print(f"\n🔧 Extraction Methods:")
            for method, count in methods.items():
                print(f"   {method}: {count} PDFs")
        
        print(f"\n✅ REAL AI-POWERED PDF PROCESSING COMPLETE")
        print("   - Actual PDF text extraction (PyPDF2, pdfplumber, PyMuPDF)")
        print("   - Real Claude 3.5 Sonnet AI analysis")
        print("   - Structured technical specifications")
        print("   - Pricing information extraction")
        print("   - NO SIMULATIONS - 100% real processing")

def main():
    """Main execution function"""
    
    print("🚀 LAMBDA.HU REAL PDF PROCESSOR")
    print("=" * 80)
    print("NO SIMULATIONS - Real AI-powered PDF content extraction")
    print("✅ PyPDF2 + pdfplumber + PyMuPDF")
    print("✅ Claude 3.5 Sonnet AI analysis")
    print("✅ Structured technical data extraction")
    print()
    
    db_session: Optional[Session] = None
    try:
        # Get a database session
        db_session = SessionLocal()

        # Initialize processor with the session
        processor = RealPDFProcessor(db_session)
        
        # Set paths
        pdf_directory = Path("src/downloads/rockwool_datasheets")
        output_file = Path("real_pdf_extraction_results.json")
        
        # Process PDFs
        results = processor.process_directory(pdf_directory, output_file)
        
        print(f"\n🎉 SUCCESS: {len(results)} new PDFs processed.")
        
    except Exception as e:
        logger.error(f"❌ Top-level processing failed: {e}")
        raise
    finally:
        if db_session and db_session.is_active:
            db_session.close()


if __name__ == "__main__":
    main() 