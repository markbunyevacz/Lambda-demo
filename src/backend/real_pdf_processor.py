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

# Advanced Table Extraction
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logging.warning("CAMELOT not available. Install with: pip install camelot-py[cv]")

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False
    logging.warning("TABULA not available. Install with: pip install tabula-py")

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


@dataclass
class TableExtractionResult:
    """Advanced table extraction result with quality metrics"""
    tables: List[Dict[str, Any]]
    extraction_method: str
    quality_score: float
    confidence: float
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
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
        self.model = "claude-3-5-haiku-20241022"
        
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
        """Create a dynamic, adaptive prompt for Claude based on actual PDF content."""
        
        # Analyze the PDF content structure first
        content_analysis = self._analyze_pdf_structure(context)
        
        # Build adaptive prompt based on what we actually found
        prompt = f"""
🔍 DINAMIKUS TARTALOM ELEMZÉS - '{context['filename']}'

📊 AUTOMATIKUS STRUKTÚRA FELISMERÉS:
{content_analysis['structure_summary']}

🎯 ADAPTÍV KINYERÉSI STRATÉGIA:
{content_analysis['extraction_strategy']}

📋 TALÁLT TARTALOM TÍPUSOK:
{content_analysis['content_types']}

DOKUMENTUM TARTALOM:
{context['extracted_text']}
"""
        
        # Add tables only if they exist and are meaningful
        if context["tables_summary"] and content_analysis['has_meaningful_tables']:
            prompt += f"\n\n🔍 TÁBLÁZAT ADATOK ({len(context['tables_summary'])} db):\n"
            for i, table in enumerate(context["tables_summary"], 1):
                prompt += f"\nTáblázat {i}:\n"
                prompt += f"Fejlécek: {table['headers']}\n"
                prompt += f"Adatok: {table['sample_data']}\n"
        
        # Dynamic field mapping based on content
        field_mapping = self._generate_dynamic_field_mapping(content_analysis)
        prompt += f"\n\n🗺️ DINAMIKUS MEZŐ LEKÉPEZÉS:\n{field_mapping}\n"
        
        # Adaptive extraction instructions
        prompt += f"""
🤖 ADAPTÍV KINYERÉSI UTASÍTÁSOK:

1. TARTALOM ALAPÚ MEGKÖZELÍTÉS:
   - Elemezd a tényleges tartalmat, ne keress előre definiált mezőket
   - Azonosítsd a műszaki adatokat bárhol is legyenek
   - Használd a kontextust az adatok értelmezéséhez

2. DINAMIKUS STRUKTÚRA KEZELÉS:
   - Ha táblázat van → prioritás a táblázat adatoknak
   - Ha csak szöveg van → regex és pattern matching
   - Ha vegyes tartalom → kombináld a módszereket

3. ADAPTÍV KIMENETI SÉMA:
   - Csak azokat a mezőket add vissza, amik ténylegesen megtalálhatók
   - Null értékek helyett hagyd ki a hiányzó mezőket
   - Confidence score legyen reális a talált adatok alapján

4. MINŐSÉGI VALIDÁCIÓ:
   - Ellenőrizd az értékek konzisztenciáját
   - Mértékegységek és szabványok pontossága
   - Logikus értéktartományok (pl. λ: 0.02-0.1 W/mK)

📤 KIMENETI JSON FORMÁTUM (DINAMIKUS):
{{
  "product_identification": {{
    // Csak a ténylegesen talált adatok
    {content_analysis['likely_fields']['product_identification']}
  }},
  "technical_specifications": {{
    // Csak a PDF-ben szereplő műszaki adatok
    {content_analysis['likely_fields']['technical_specifications']}
  }},
  "extraction_metadata": {{
    "content_type": "{content_analysis['content_type']}",
    "extraction_method": "{content_analysis['best_extraction_method']}",
    "data_completeness": "0.0-1.0 között",
    "confidence_score": "0.0-1.0 között",
    "found_fields": ["lista", "a", "talált", "mezőkről"],
    "missing_fields": ["lista", "a", "hiányzó", "mezőkről"]
  }}
}}

⚡ KRITIKUS: Ne használj sablont! Elemezd a tényleges tartalmat és csak azt add vissza, amit ténylegesen megtalálsz!
"""
        
        return prompt
    
    def _analyze_pdf_structure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the actual PDF structure to determine extraction strategy."""
        
        text = context['extracted_text'].lower()
        tables = context['tables_summary']
        
        analysis = {
            'content_type': 'unknown',
            'has_meaningful_tables': False,
            'extraction_strategy': 'text_based',
            'structure_summary': '',
            'likely_fields': {
                'product_identification': {},
                'technical_specifications': {}
            },
            'best_extraction_method': 'pattern_matching'
        }
        
        # Detect content type
        if 'rockwool' in text or 'hőszigetelés' in text:
            analysis['content_type'] = 'insulation_datasheet'
        elif 'árlista' in text or 'ár' in text:
            analysis['content_type'] = 'price_list'
        elif 'műszaki' in text or 'technical' in text:
            analysis['content_type'] = 'technical_spec'
        
        # Analyze tables
        if tables:
            meaningful_tables = 0
            for table in tables:
                if len(table.get('headers', [])) > 1 and len(table.get('sample_data', [])) > 0:
                    meaningful_tables += 1
            
            if meaningful_tables > 0:
                analysis['has_meaningful_tables'] = True
                analysis['extraction_strategy'] = 'table_based'
                analysis['best_extraction_method'] = 'table_parsing'
        
        # Detect likely fields based on content
        if 'λ' in text or 'hővezetési' in text:
            analysis['likely_fields']['technical_specifications']['thermal_conductivity'] = 'expected'
        if 'tűzvédelmi' in text or 'fire' in text:
            analysis['likely_fields']['technical_specifications']['fire_classification'] = 'expected'
        if 'testsűrűség' in text or 'density' in text:
            analysis['likely_fields']['technical_specifications']['density'] = 'expected'
        
        # Generate structure summary
        analysis['structure_summary'] = f"""
- Tartalom típus: {analysis['content_type']}
- Táblázatok: {len(tables)} db ({'jelentős' if analysis['has_meaningful_tables'] else 'kevés adat'})
- Szöveg hossz: {context['text_length']} karakter
- Ajánlott módszer: {analysis['best_extraction_method']}
"""
        
        return analysis
    
    def _generate_dynamic_field_mapping(self, analysis: Dict[str, Any]) -> str:
        """Generate field mapping based on content analysis."""
        
        mapping = "DINAMIKUS MEZŐ FELISMERÉS:\n"
        
        # Hungarian technical terms that might appear
        hungarian_terms = {
            'hővezetési tényező': 'thermal_conductivity',
            'λd': 'thermal_conductivity', 
            'lambda': 'thermal_conductivity',
            'tűzvédelmi osztály': 'fire_classification',
            'testsűrűség': 'density',
            'ρ': 'density',
            'nyomószilárdság': 'compressive_strength',
            'páradiffúziós': 'vapor_resistance',
            'μ': 'vapor_resistance',
            'vízfelvétel': 'water_absorption',
            'ws': 'water_absorption',
            'wl': 'water_absorption'
        }
        
        for hu_term, en_key in hungarian_terms.items():
            mapping += f"- '{hu_term}' → {en_key}\n"
        
        mapping += "\n🎯 ADAPTÍV STRATÉGIA: Keress hasonló kifejezéseket és értelmezd a kontextus alapján!"
        
        return mapping
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's dynamic JSON response - adapts to actual content"""
        
        try:
            # Find JSON in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in Claude response")
            
            json_text = response_text[json_start:json_end]
            
            # Parse JSON
            result = json.loads(json_text)
            
            # Dynamic validation - only check for what we actually expect
            self._validate_dynamic_structure(result)
            
            # Enhance with extraction metadata
            result = self._enhance_with_metadata(result)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            # Return minimal structure with error info
            return {
                "product_identification": {},
                "technical_specifications": {},
                "extraction_metadata": {
                    "confidence_score": 0.0,
                    "extraction_method": "failed",
                    "error": f"JSON parsing failed: {e}",
                    "found_fields": [],
                    "missing_fields": ["all"]
                }
            }
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            raise
    
    def _validate_dynamic_structure(self, result: Dict[str, Any]) -> None:
        """Validate structure dynamically based on what was actually found"""
        
        # Ensure basic structure exists
        if "product_identification" not in result:
            result["product_identification"] = {}
        if "technical_specifications" not in result:
            result["technical_specifications"] = {}
        if "extraction_metadata" not in result:
            result["extraction_metadata"] = {}
        
        # Validate technical specifications format
        tech_specs = result.get("technical_specifications", {})
        for key, value in tech_specs.items():
            if isinstance(value, dict):
                # Ensure proper structure for technical values
                if "value" not in value:
                    logger.warning(f"Technical spec {key} missing 'value' field")
                if "unit" not in value:
                    logger.warning(f"Technical spec {key} missing 'unit' field")
    
    def _enhance_with_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance result with extraction metadata"""
        
        metadata = result.get("extraction_metadata", {})
        
        # Count found fields
        found_fields = []
        if result.get("product_identification"):
            found_fields.extend(result["product_identification"].keys())
        if result.get("technical_specifications"):
            found_fields.extend(result["technical_specifications"].keys())
        
        # Calculate data completeness
        expected_fields = [
            "product_identification.name",
            "technical_specifications.thermal_conductivity",
            "technical_specifications.fire_classification",
            "technical_specifications.density"
        ]
        
        completeness = len(found_fields) / len(expected_fields) if expected_fields else 0
        
        # Update metadata
        metadata.update({
            "found_fields": found_fields,
            "data_completeness": round(completeness, 2),
            "extraction_timestamp": datetime.now().isoformat()
        })
        
        result["extraction_metadata"] = metadata
        
        return result

class AdvancedTableExtractor:
    """
    🎯 ROCKWOOL PDF Optimális Táblázat Kinyerő
    
    Hibrid megközelítés:
    1. CAMELOT (elsődleges eszköz)
    2. Deep Learning validáció 
    3. Manuális végső ellenőrzés
    """
    
    def __init__(self):
        self.extraction_methods = []
        self.stats = {
            'camelot_success': 0,
            'tabula_success': 0,
            'fallback_used': 0,
            'total_extractions': 0
        }
        
        # Initialize available methods
        self._initialize_methods()
    
    def _initialize_methods(self):
        """Initialize available extraction methods"""
        
        if CAMELOT_AVAILABLE:
            self.extraction_methods.append(('camelot_lattice', self._camelot_lattice))
            self.extraction_methods.append(('camelot_stream', self._camelot_stream))
            logger.info("✅ CAMELOT initialized - optimal for technical PDFs")
        
        if TABULA_AVAILABLE:
            self.extraction_methods.append(('tabula', self._tabula_extract))
            logger.info("✅ TABULA initialized - Java-based table extraction")
        
        # Always available fallback
        self.extraction_methods.append(('pymupdf_advanced', self._pymupdf_advanced))
        self.extraction_methods.append(('pdfplumber_backup', self._pdfplumber_backup))
        
        logger.info(f"Table extraction methods available: {len(self.extraction_methods)}")
    
    def extract_tables_hybrid(self, pdf_path: Path) -> TableExtractionResult:
        """
        🚀 Hibrid táblázat kinyerés ROCKWOOL PDF-ekhez
        
        Sorrend:
        1. CAMELOT (elsődleges)
        2. Deep Learning validáció
        3. Manuális ellenőrzés
        """
        
        start_time = datetime.now()
        logger.info(f"🔍 Advanced table extraction: {pdf_path.name}")
        
        best_result = None
        best_score = 0
        extraction_attempts = []
        
        # Try each extraction method
        for method_name, method_func in self.extraction_methods:
            try:
                logger.info(f"📊 Trying {method_name}...")
                
                tables = method_func(pdf_path)
                quality_score = self._calculate_quality_score(tables)
                
                extraction_attempts.append({
                    'method': method_name,
                    'tables_count': len(tables),
                    'quality_score': quality_score,
                    'success': len(tables) > 0
                })
                
                if quality_score > best_score:
                    best_result = {
                        'tables': tables,
                        'method': method_name,
                        'quality_score': quality_score
                    }
                    best_score = quality_score
                    
                logger.info(f"✅ {method_name}: {len(tables)} tables, score: {quality_score:.2f}")
                
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {e}")
                extraction_attempts.append({
                    'method': method_name,
                    'error': str(e),
                    'success': False
                })
                continue
        
        # Deep Learning Validáció
        if best_result and best_result['quality_score'] > 0.5:
            validated_result = self._deep_learning_validation(best_result)
            if validated_result:
                best_result = validated_result
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create final result
        if best_result:
            result = TableExtractionResult(
                tables=best_result['tables'],
                extraction_method=best_result['method'],
                quality_score=best_result['quality_score'],
                confidence=self._calculate_confidence(best_result, extraction_attempts),
                processing_time=processing_time
            )
            
            self.stats['total_extractions'] += 1
            if 'camelot' in best_result['method']:
                self.stats['camelot_success'] += 1
            elif 'tabula' in best_result['method']:
                self.stats['tabula_success'] += 1
            else:
                self.stats['fallback_used'] += 1
            
            logger.info(f"🎯 Best result: {best_result['method']} (score: {best_result['quality_score']:.2f})")
            return result
        
        # Fallback to empty result
        logger.warning("⚠️ No tables extracted from PDF")
        return TableExtractionResult(
            tables=[],
            extraction_method='failed',
            quality_score=0.0,
            confidence=0.0,
            processing_time=processing_time
        )
    
    def _camelot_lattice(self, pdf_path: Path) -> List[Dict]:
        """CAMELOT Lattice method - best for technical tables with borders"""
        
        if not CAMELOT_AVAILABLE:
            raise ImportError("CAMELOT not available")
        
        tables = camelot.read_pdf(
            str(pdf_path),
            flavor='lattice',
            pages='all',
            line_scale=40,  # Adjust for table detection
            copy_text=['v', 'h'],  # Copy text along vertical/horizontal lines
            shift_text=['l', 't', 'r']  # Shift text left/top/right
        )
        
        extracted_tables = []
        for i, table in enumerate(tables):
            if table.df.empty:
                continue
                
            # Clean and process table data
            table_data = self._clean_table_data(table.df)
            
            extracted_tables.append({
                'data': table_data,
                'headers': table.df.columns.tolist(),
                'page': table.page,
                'accuracy': table.accuracy,
                'method': 'camelot_lattice',
                'table_index': i,
                'shape': table.df.shape,
                'parsing_report': table.parsing_report
            })
        
        return extracted_tables
    
    def _camelot_stream(self, pdf_path: Path) -> List[Dict]:
        """CAMELOT Stream method - for tables without borders"""
        
        if not CAMELOT_AVAILABLE:
            raise ImportError("CAMELOT not available")
        
        tables = camelot.read_pdf(
            str(pdf_path),
            flavor='stream',
            pages='all',
            row_tol=10,  # Row tolerance
            column_tol=0  # Column tolerance
        )
        
        extracted_tables = []
        for i, table in enumerate(tables):
            if table.df.empty:
                continue
                
            table_data = self._clean_table_data(table.df)
            
            extracted_tables.append({
                'data': table_data,
                'headers': table.df.columns.tolist(),
                'page': table.page,
                'accuracy': table.accuracy,
                'method': 'camelot_stream',
                'table_index': i,
                'shape': table.df.shape
            })
        
        return extracted_tables
    
    def _tabula_extract(self, pdf_path: Path) -> List[Dict]:
        """TABULA extraction - Java-based reliable fallback"""
        
        if not TABULA_AVAILABLE:
            raise ImportError("TABULA not available")
        
        # Multiple extraction strategies
        strategies = [
            {'multiple_tables': True, 'pandas_options': {'header': 0}},
            {'multiple_tables': True, 'stream': True},
            {'multiple_tables': True, 'lattice': True}
        ]
        
        best_tables = []
        best_count = 0
        
        for strategy in strategies:
            try:
                tables = tabula.read_pdf(
                    str(pdf_path),
                    pages='all',
                    **strategy
                )
                
                if len(tables) > best_count:
                    best_tables = tables
                    best_count = len(tables)
                    
            except Exception as e:
                logger.debug(f"TABULA strategy failed: {e}")
                continue
        
        extracted_tables = []
        for i, df in enumerate(best_tables):
            if df.empty:
                continue
                
            table_data = self._clean_table_data(df)
            
            extracted_tables.append({
                'data': table_data,
                'headers': df.columns.tolist(),
                'method': 'tabula',
                'table_index': i,
                'shape': df.shape
            })
        
        return extracted_tables
    
    def _pymupdf_advanced(self, pdf_path: Path) -> List[Dict]:
        """PyMuPDF advanced table detection"""
        
        doc = fitz.open(pdf_path)
        extracted_tables = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Try to find tables using PyMuPDF
            try:
                tables = page.find_tables()
                
                for table_idx, table in enumerate(tables):
                    table_data = table.extract()
                    
                    if not table_data or len(table_data) < 2:
                        continue
                    
                    extracted_tables.append({
                        'data': table_data,
                        'headers': table_data[0] if table_data else [],
                        'page': page_num + 1,
                        'method': 'pymupdf_advanced',
                        'table_index': table_idx,
                        'bbox': table.bbox
                    })
                    
            except AttributeError:
                # Fallback if find_tables is not available
                logger.debug("PyMuPDF find_tables not available, using basic extraction")
                
        doc.close()
        return extracted_tables
    
    def _pdfplumber_backup(self, pdf_path: Path) -> List[Dict]:
        """PDFPlumber backup method"""
        
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(page_tables):
                        if table and len(table) > 1:
                            tables.append({
                                'data': table,
                                'headers': table[0] if table else [],
                                'page': page_num + 1,
                                'method': 'pdfplumber_backup',
                                'table_index': table_idx
                            })
        except Exception as e:
            logger.error(f"PDFPlumber backup failed: {e}")
        
        return tables
    
    def _clean_table_data(self, df) -> List[List[str]]:
        """Clean and normalize table data"""
        
        # Fill NaN values
        df = df.fillna('')
        
        # Convert to strings and clean
        cleaned_data = []
        for _, row in df.iterrows():
            cleaned_row = []
            for cell in row:
                cell_str = str(cell).strip()
                # Remove extra whitespace
                cell_str = ' '.join(cell_str.split())
                cleaned_row.append(cell_str)
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
    
    def _calculate_quality_score(self, tables: List[Dict]) -> float:
        """Calculate table extraction quality score"""
        
        if not tables:
            return 0.0
        
        total_score = 0
        
        for table in tables:
            score = 0
            
            # Table size score
            data = table.get('data', [])
            rows = len(data)
            cols = len(data[0]) if data else 0
            size_score = min(rows * cols / 20, 1.0)  # Normalize by 20 cells
            
            # Method bonus
            method_bonus = {
                'camelot_lattice': 1.0,
                'camelot_stream': 0.9,
                'tabula': 0.8,
                'pymupdf_advanced': 0.7,
                'pdfplumber_backup': 0.6
            }.get(table.get('method', 'unknown'), 0.5)
            
            # Accuracy bonus (if available)
            accuracy_bonus = table.get('accuracy', 0.5)
            
            # Calculate final score
            score = (size_score * method_bonus * accuracy_bonus) * 100
            total_score += score
        
        return total_score / len(tables)
    
    def _calculate_confidence(self, best_result: Dict, attempts: List[Dict]) -> float:
        """Calculate confidence based on extraction attempts"""
        
        successful_attempts = [a for a in attempts if a.get('success', False)]
        
        if not successful_attempts:
            return 0.0
        
        # Base confidence from quality score
        quality_confidence = min(best_result['quality_score'] / 100, 1.0)
        
        # Multiple methods agreement bonus
        method_agreement = len(successful_attempts) / len(attempts)
        
        # Final confidence
        confidence = (quality_confidence * 0.7) + (method_agreement * 0.3)
        
        return round(confidence, 3)
    
    def _deep_learning_validation(self, result: Dict) -> Optional[Dict]:
        """
        🧠 Deep Learning validáció
        
        TODO: Implement AI-based table validation
        - OCR verification
        - Content pattern recognition
        - Anomaly detection
        """
        
        # Placeholder for future AI validation
        logger.info("🧠 Deep Learning validation (placeholder)")
        
        # Simple validation rules for now
        tables = result.get('tables', [])
        validated_tables = []
        
        for table in tables:
            # Basic validation
            data = table.get('data', [])
            if len(data) > 1 and len(data[0]) > 1:
                # Check for technical content patterns
                has_technical_content = self._check_technical_patterns(data)
                
                if has_technical_content:
                    table['validated'] = True
                    validated_tables.append(table)
        
        if validated_tables:
            result['tables'] = validated_tables
            result['quality_score'] *= 1.1  # Validation bonus
            return result
        
        return None
    
    def _check_technical_patterns(self, data: List[List[str]]) -> bool:
        """Check for ROCKWOOL technical content patterns"""
        
        technical_keywords = [
            'λ', 'lambda', 'w/m', 'kg/m³', 'pa', 'kpa', 'mm', 'cm', 'm²',
            'thermal', 'conductivity', 'density', 'thickness', 'fire',
            'hővezetési', 'tényező', 'testsűrűség', 'vastagság', 'tűz'
        ]
        
        text_content = ' '.join([' '.join(row) for row in data]).lower()
        
        matches = sum(1 for keyword in technical_keywords if keyword in text_content)
        
        return matches >= 3  # At least 3 technical terms
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        
        total = self.stats['total_extractions']
        
        return {
            'total_extractions': total,
            'camelot_success_rate': (self.stats['camelot_success'] / total * 100) if total > 0 else 0,
            'tabula_success_rate': (self.stats['tabula_success'] / total * 100) if total > 0 else 0,
            'fallback_usage_rate': (self.stats['fallback_used'] / total * 100) if total > 0 else 0,
            'available_methods': len(self.extraction_methods)
        }


class RealPDFProcessor:
    """Main class for real PDF processing - NO SIMULATIONS"""
    
    def __init__(self, db_session: Session):
        """Initializes the processor with a database session."""
        self.extractor = RealPDFExtractor()
        self.ai_analyzer = ClaudeAIAnalyzer()
        self.advanced_table_extractor = AdvancedTableExtractor()  # ✅ NEW
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
                price=self._extract_price_from_result(result),
                full_text_content=result.extracted_text  # ✅ JAVÍTÁS: teljes szöveg mentése
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
        """Calculate dynamic confidence score based on actual content quality."""
        
        confidence_factors = []
        
        # Factor 1: AI confidence (dynamic based on extraction metadata)
        extraction_metadata = ai_analysis.get("extraction_metadata", {})
        ai_confidence = extraction_metadata.get("confidence_score", 0.5)
        data_completeness = extraction_metadata.get("data_completeness", 0.0)
        
        if isinstance(ai_confidence, (int, float)):
            confidence_factors.append(("ai_confidence", float(ai_confidence), 0.35))
        
        # Factor 2: Data completeness from AI analysis
        if isinstance(data_completeness, (int, float)):
            confidence_factors.append(("data_completeness", float(data_completeness), 0.25))
        
        # Factor 3: Text extraction quality (dynamic thresholds)
        text_quality = self._assess_text_quality(text_content)
        confidence_factors.append(("text_quality", text_quality, 0.15))
        
        # Factor 4: Table extraction success (dynamic assessment)
        table_quality = self._assess_table_quality(tables)
        confidence_factors.append(("table_quality", table_quality, 0.15))
        
        # Factor 5: Cross-validation between AI and pattern extraction
        validation_score = self._cross_validate_extractions(pattern_specs, ai_analysis)
        confidence_factors.append(("validation_score", validation_score, 0.1))
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in confidence_factors)
        total_weight = sum(weight for _, _, weight in confidence_factors)
        
        final_confidence = total_score / total_weight if total_weight > 0 else 0.0
        
        # Apply dynamic adjustments based on content type
        final_confidence = self._apply_content_type_adjustments(
            final_confidence, ai_analysis, extraction_method
        )
        
        # Log confidence breakdown for debugging
        logger.debug(f"Dynamic confidence breakdown: {confidence_factors}")
        logger.debug(f"Final confidence: {final_confidence:.3f}")
        
        return round(final_confidence, 3)
    
    def _assess_text_quality(self, text_content: str) -> float:
        """Assess text quality based on content characteristics."""
        if not text_content:
            return 0.0
        
        # Check for meaningful content indicators
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
            
            # Check for meaningful headers
            headers = table.get('headers', [])
            if headers and len(headers) > 1:
                table_score += 0.4
            
            # Check for data rows
            data = table.get('data', [])
            if data and len(data) > 1:
                table_score += 0.4
            
            # Check for technical content
            table_text = str(table).lower()
            if any(term in table_text for term in ['λ', 'w/mk', 'kg/m³', 'kpa']):
                table_score += 0.2
            
            total_quality += table_score
        
        # Average quality across all tables
        return min(1.0, total_quality / len(tables))
    
    def _cross_validate_extractions(self, pattern_specs: Dict[str, Any], 
                                   ai_analysis: Dict[str, Any]) -> float:
        """Cross-validate pattern-based and AI extractions."""
        if not pattern_specs and not ai_analysis.get("technical_specifications"):
            return 0.0
        
        ai_specs = ai_analysis.get("technical_specifications", {})
        
        # Count matching fields
        matching_fields = 0
        total_fields = len(set(pattern_specs.keys()) | set(ai_specs.keys()))
        
        for field in pattern_specs:
            if field in ai_specs:
                matching_fields += 1
        
        # Calculate validation score
        if total_fields > 0:
            return matching_fields / total_fields
        return 0.0
    
    def _apply_content_type_adjustments(self, base_confidence: float, 
                                      ai_analysis: Dict[str, Any], 
                                      extraction_method: str) -> float:
        """Apply content-type specific confidence adjustments."""
        
        # Method reliability adjustments
        method_multipliers = {
            "pdfplumber": 1.0,   # Best for tables
            "pypdf2": 0.9,       # Reliable fallback  
            "pymupdf": 0.95      # Good alternative
        }
        
        adjusted_confidence = base_confidence * method_multipliers.get(extraction_method, 0.8)
        
        # Content type adjustments
        extraction_metadata = ai_analysis.get("extraction_metadata", {})
        content_type = extraction_metadata.get("content_type", "unknown")
        
        if content_type == "insulation_datasheet":
            adjusted_confidence *= 1.05  # Boost for expected content
        elif content_type == "technical_spec":
            adjusted_confidence *= 1.02  # Slight boost for technical content
        elif content_type == "unknown":
            adjusted_confidence *= 0.9   # Penalty for unknown content
        
        return min(1.0, adjusted_confidence)

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
        print("   - Real Claude 3.5 Haiku AI analysis")
        print("   - Structured technical specifications")
        print("   - Pricing information extraction")
        print("   - NO SIMULATIONS - 100% real processing")

def main():
    """Main execution function"""
    
    print("🚀 LAMBDA.HU REAL PDF PROCESSOR")
    print("=" * 80)
    print("NO SIMULATIONS - Real AI-powered PDF content extraction")
    print("✅ PyPDF2 + pdfplumber + PyMuPDF")
    print("✅ Claude 3.5 Haiku AI analysis")
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