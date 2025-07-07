#!/usr/bin/env python3
"""
Lambda.hu Real PDF Processor
NO SIMULATIONS - Real AI-powered PDF content extraction

Uses:
- PyPDF2/pdfplumber for actual PDF text extraction
- Claude 3.5 Haiku for intelligent content analysis
- Structured data extraction for product specs and prices
"""

import os
import json
import hashlib
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime


import fitz  # PyMuPDF
import pdfplumber
import PyPDF2
from anthropic import Anthropic
from sqlalchemy.orm import Session

# Advanced table extraction imports (optional)
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    
try:
    import tabula
    TABULA_AVAILABLE = True  
except ImportError:
    TABULA_AVAILABLE = False

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

# Load environment variables
load_dotenv()  # Current directory first
load_dotenv("../../.env")  # Fallback to root directory

# ✅ ENHANCED: Configure logging to ERROR level to hide all WARNING messages
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ✅ Set our own logger to INFO level for our messages
logger.setLevel(logging.INFO)

# ✅ CRITICAL: Silence all external library loggers that cause WARNING messages
external_loggers = [
    'tabula', 'jpype', 'jpype1', 'camelot', 'chromadb', 
    'pdfplumber', 'PyPDF2', 'fitz', 'urllib3', 'requests'
]
for lib_logger in external_loggers:
    logging.getLogger(lib_logger).setLevel(logging.CRITICAL)

# ✅ FIX: Suppress external library warnings
warnings.filterwarnings("ignore", message="Failed to import jpype dependencies.*")
warnings.filterwarnings("ignore", message="No module named 'jpype'")
warnings.filterwarnings("ignore", category=UserWarning, module="camelot.*")
warnings.filterwarnings("ignore", message="No tables found in table area.*")
# ✅ NEW: Suppress ChromaDB telemetry errors
warnings.filterwarnings("ignore", message="Failed to send telemetry event.*")
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
    ai_analysis_method: str = "claude-3.5-haiku"
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
        """Extract text and tables using pdfplumber (primary method)"""
        
        text_content = ""
        tables_data = []
        total_cells = 0
        
        pdf = None
        try:
            pdf = pdfplumber.open(pdf_path)
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Extract text from page
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    
                    # Extract tables from page
                    page_tables = page.extract_tables()
                    for table_idx, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            rows = len(table)
                            cols = len(table[0]) if table[0] else 0
                            cells = rows * cols
                            total_cells += cells
                            
                            tables_data.append({
                                "page": page_num + 1,
                                "table_index": table_idx,
                                "data": table,
                                "rows": rows,
                                "columns": cols,
                                "total_cells": cells,
                                "headers": table[0] if table else [],
                                "extraction_method": "pdfplumber"
                            })
                except Exception as page_error:
                    logger.warning(f"Error processing page {page_num + 1}: {page_error}")
                    continue
        
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed: {e}")
            raise
        finally:
            # ✅ CRITICAL: Explicit file handle cleanup for Windows
            if pdf:
                try:
                    pdf.close()
                except:
                    pass
        
        return text_content, tables_data
    
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
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = None
                try:
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
                            
                except Exception as page_error:
                    logger.warning(f"Error processing PyMuPDF page {page_num + 1}: {page_error}")
                    continue
                finally:
                    # Clean up page object
                    if page:
                        try:
                            del page
                        except:
                            pass
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise
        finally:
            # ✅ CRITICAL: Explicit document cleanup for Windows
            if doc:
                try:
                    doc.close()
                except:
                    pass
        
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
                # Calculate total dimensions for logging
                total_cells = sum(t.get('total_cells', 0) for t in tables)
                table_dimensions = [
                    f"{t.get('rows', 0)}×{t.get('columns', 0)}" 
                    for t in tables
                ]
                dimensions_str = (
                    ", ".join(table_dimensions) 
                    if table_dimensions 
                    else "no tables"
                )
                
                log_msg = (
                    f"✅ PDFPlumber: {len(text)} chars, {len(tables)} tables "
                    f"({total_cells} cells): {dimensions_str}"
                )
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
                cell_count = sum(
                    len(t.get('data', [])) * len(t.get('data', [[]])[0]) 
                    for t in tables
                )
                log_msg = (
                    f"✅ PyMuPDF: {len(text)} chars, {len(tables)} tables "
                    f"({cell_count} cells)"
                )
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
    
    async def claude_api_call(self, prompt: str) -> str:
        """Simple Claude API call for raw text extraction"""
        
        try:
            # Call Claude API directly with raw prompt
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,  # Low temperature for factual extraction
                system="You are an expert technical data analyst specializing "
                       "in building materials and insulation products. "
                       "Extract accurate technical specifications from PDFs.",
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Return raw response text
            response_text = response.content[0].text
            response_len = len(response_text)
            logger.info(f"✅ Claude API call complete, length: {response_len}")
            return response_text
            
        except Exception as e:
            logger.error(f"❌ Claude API call error: {e}")
            raise

    async def analyze_rockwool_pdf(
        self, text_content: str, tables_data: List[Dict], filename: str
    ) -> Dict[str, Any]:
        """Analyze ROCKWOOL PDF content with Claude AI"""
        
        # Prepare context for Claude
        context = self._prepare_analysis_context(text_content, tables_data, filename)
        
        # Create prompt for structured extraction
        prompt = self._create_extraction_prompt(context)
        
        try:
            # Call Claude API using the async method
            response_text = await self.claude_api_call(prompt)
            
            # Parse Claude's response
            analysis_result = self._parse_claude_response(response_text)
            
            logger.info(f"✅ Claude analysis complete for {filename}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            # Return a safe fallback structure
            return {
                "product_identification": {},
                "technical_specifications": {},
                "extraction_metadata": {
                    "confidence_score": 0.0,
                    "extraction_method": "failed",
                    "error": str(e),
                    "found_fields": [],
                    "missing_fields": ["all"]
                }
            }
    
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
{content_analysis['content_type']}

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

⚡ KRITIKUS: Ne használj sablont! Elemezd a tényleges tartalmat és csak azt 
add vissza, amit ténylegesen megtalálsz!
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
        tech_specs = analysis['likely_fields']['technical_specifications']
        if 'λ' in text or 'hővezetési' in text:
            tech_specs['thermal_conductivity'] = 'expected'
        if 'tűzvédelmi' in text or 'fire' in text:
            tech_specs['fire_classification'] = 'expected'
        if 'testsűrűség' in text or 'density' in text:
            tech_specs['density'] = 'expected'
        
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
        
        logger.debug(f"📝 Parsing Claude response (length: {len(response_text)})")
        
        # ✅ ENHANCED: More flexible JSON pattern matching for Claude responses
        json_patterns = [
            (r'\{(?:[^{}]*\{[^{}]*\}[^{}]*)*[^{}]*\}', "complete JSON object"),
            (r'```json\s*(\{.*?\})\s*```', "JSON code block"),
            (r'```\s*(\{.*?\})\s*```', "code block"),
            (r'\{[\s\S]*?\}(?=\s*$|\s*\n\s*[A-Z])', "JSON at end of response"),
            (r'(?:json|JSON)[\s:]*(\{[\s\S]*?\})', "labeled JSON block"),
        ]
        
        for pattern, description in json_patterns:
            import re
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean the JSON text
                    json_text = match.strip()
                    if json_text.startswith('json'):
                        json_text = json_text[4:].strip()
                    
                    result = json.loads(json_text)
                    logger.info(f"✅ JSON parsed successfully using {description}")
                    
                    # Dynamic validation - only check for what we actually expect
                    self._validate_dynamic_structure(result)
                    
                    # Enhance with extraction metadata
                    result = self._enhance_with_metadata(result)
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"❌ Failed to parse {description}: {e}")
                    continue
        
        # Fallback: look for simple JSON block boundaries
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                
                # Try to fix common JSON issues
                json_text = self._clean_json_text(json_text)
                
                result = json.loads(json_text)
                logger.info("✅ JSON parsed using fallback method")
                
                # Dynamic validation and enhancement
                self._validate_dynamic_structure(result)
                result = self._enhance_with_metadata(result)
                
                return result
            else:
                logger.warning("⚠️ No JSON boundaries found in response")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.debug(f"Problematic JSON text: {json_text[:200]}...")
        except Exception as e:
            logger.error(f"❌ Unexpected error during JSON parsing: {e}")
        
        # Final fallback: return error structure
        logger.warning("⚠️ Using fallback response structure")
        return {
            "product_identification": {},
            "technical_specifications": {},
            "extraction_metadata": {
                "confidence_score": 0.0,
                "extraction_method": "failed",
                "error": "No valid JSON found in Claude response",
                "found_fields": [],
                "missing_fields": ["all"],
                "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }
        }
    
    def _clean_json_text(self, json_text: str) -> str:
        """✅ ENHANCED: Clean JSON text to fix common Claude AI response issues"""
        
        import re
        
        # Remove any trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Replace single quotes with double quotes (common AI mistake)
        json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)
        json_text = re.sub(r":\s*'([^']*)'", r': "\1"', json_text)
        
        # Fix Hungarian characters and Unicode issues
        hungarian_fixes = {
            '\u00e9': 'é', '\u0151': 'ő', '\u00f3': 'ó', '\u00e1': 'á',
            '\u00f6': 'ö', '\u00fc': 'ü', '\u00ed': 'í', '\u00fa': 'ú', 
            '\u0171': 'ű', '\u0170': 'Ű', '\u0150': 'Ő'
        }
        for unicode_char, normal_char in hungarian_fixes.items():
            json_text = json_text.replace(unicode_char, normal_char)
        
        # Remove comments and explanatory text
        json_text = re.sub(r'//.*$', '', json_text, flags=re.MULTILINE)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        # Remove common Claude explanation prefixes
        json_text = re.sub(r'^[^{]*(?=\{)', '', json_text)
        json_text = re.sub(r'\}[^}]*$', '}', json_text)
        
        # Fix newlines and spacing
        json_text = re.sub(r'\n\s*\n', '\n', json_text)
        
        return json_text.strip()
    
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
        """Extract tables using CAMELOT lattice method"""
        
        tables = []
        
        try:
            # ✅ CAMELOT lattice extraction with explicit cleanup
            camelot_tables = camelot.read_pdf(
                str(pdf_path), 
                flavor='lattice',
                pages='all'
            )
            
            for i, table in enumerate(camelot_tables):
                try:
                    # Convert to our format
                    df = table.df
                    if not df.empty:
                        table_data = self._clean_table_data(df)
                        if table_data:
                            tables.append({
                                "page": table.page,
                                "data": table_data,
                                "extraction_method": "camelot_lattice",
                                "rows": len(table_data),
                                "columns": len(table_data[0]) if table_data else 0,
                                "parsing_report": {
                                    "accuracy": table.parsing_report.get('accuracy', 0),
                                    "whitespace": table.parsing_report.get('whitespace', 0),
                                    "order": table.parsing_report.get('order', 0)
                                }
                            })
                except Exception as table_error:
                    logger.warning(
                        "Error processing CAMELOT lattice table %s: %s",
                        i,
                        table_error
                    )
                    continue
                finally:
                    # ✅ CRITICAL: Cleanup table object
                    try:
                        del table
                    except Exception:  # Broad exception for cleanup
                        pass
            
        except Exception as e:
            logger.warning("CAMELOT lattice extraction failed: %s", e)
        finally:
            # ✅ CRITICAL: Force cleanup of any temporary files
            try:
                import gc
                gc.collect()
            except Exception:  # Broad exception for cleanup resilience
                pass
        
        return tables
    
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
            
        # Initialize ChromaDB (optional)
        self.chroma_collection = None
        try:
            self._init_chromadb()
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
            
        # Load processed file hashes for deduplication
        if db_session:
            self._load_hashes()
        else:
            self.processed_file_hashes = set()
            
        logger.info(f"🚀 RealPDFProcessor initialized (AI: {self.enable_ai_analysis})")

    def _load_hashes(self):
        """Loads all file hashes from the database into memory with UTF-8 safe handling."""
        logger.info("Loading existing file hashes from the database...")
        try:
            # CRITICAL: Clear any existing corrupted data first
            self.db_session.rollback()

            # Try to load hashes with UTF-8 safe handling
            all_logs = self.db_session.query(ProcessedFileLog).all()
            self.processed_file_hashes = set()
            
            for log in all_logs:
                try:
                    # ✅ ENHANCED: Ultra-safe UTF-8 handling
                    file_hash = log.file_hash
                    if isinstance(file_hash, bytes):
                        # Try multiple encodings for bytes
                        for encoding in ['utf-8', 'latin1', 'cp1252', 'ascii']:
                            try:
                                file_hash = file_hash.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all encodings fail, use safe replacement
                            file_hash = file_hash.decode('utf-8', errors='replace')
                    
                    elif isinstance(file_hash, str):
                        # Ensure string is clean UTF-8
                        file_hash = file_hash.encode('utf-8', errors='replace').decode('utf-8')
                    
                    # Only add valid hashes (SHA256 should be 64 hex chars)
                    if file_hash and len(file_hash) == 64 and all(c in '0123456789abcdef' for c in file_hash.lower()):
                        self.processed_file_hashes.add(file_hash)
                        
                except Exception as e:
                    logger.debug(f"Skipping corrupted hash entry: {e}")
                    continue
            
            logger.info(f"✅ Loaded {len(self.processed_file_hashes)} file hashes from database")
            
        except Exception as e:
            logger.info(f"Database hash loading failed: {e}")
            logger.info("Starting with empty hash set...")
            self.processed_file_hashes = set()

    def _save_hash(self, file_hash: str, db_id: Optional[int]):
        """Save the hash of a processed file to database to avoid reprocessing"""
        
        # Add to in-memory set for current session
        self.processed_file_hashes.add(file_hash)
        
        # Save to database if session is available
        if self.db_session and db_id:
            try:
                # Create or update ProcessedFileLog entry
                existing_log = self.db_session.query(ProcessedFileLog).filter_by(
                    file_hash=file_hash
                ).first()
                
                if not existing_log:
                    log_entry = ProcessedFileLog(
                        file_hash=file_hash,
                        product_id=db_id,
                        processed_at=datetime.now(),
                        processing_status="completed"
                    )
                    self.db_session.add(log_entry)
                    self.db_session.commit()
                    logger.debug(f"✅ Hash saved to database: {file_hash[:8]}...")
                else:
                    logger.debug(f"Hash already exists in database: {file_hash[:8]}...")
                    
            except Exception as e:
                # ✅ CRITICAL FIX: UTF-8 safe exception logging
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                logger.info(f"Hash save issue (continuing with in-memory): {error_msg}")
                self.db_session.rollback()

    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage."""
        try:
            # ✅ CRITICAL: Completely disable ChromaDB telemetry BEFORE import
            os.environ['ANONYMIZED_TELEMETRY'] = 'False'
            os.environ['CHROMA_TELEMETRY'] = 'False'
            os.environ['CHROMA_SERVER_NOFILE'] = '1'
            
            # Remove all problematic server settings
            for var in ['CHROMA_SERVER_AUTHN_CREDENTIALS_FILE', 'CHROMA_SERVER_AUTHN_PROVIDER', 
                       'CHROMA_SERVER_HOST', 'CHROMA_SERVER_HTTP_PORT']:
                if var in os.environ:
                    del os.environ[var]
            
            # ✅ ENHANCED: Suppress all ChromaDB logging before import
            import logging
            chroma_logger = logging.getLogger('chromadb')
            chroma_logger.setLevel(logging.CRITICAL)
            
            # Import with completely suppressed telemetry
            import chromadb
            from chromadb.config import Settings
            
            # Initialize ChromaDB client with all telemetry and logging disabled
            self.chroma_client = chromadb.PersistentClient(
                path="./chromadb_data",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    chroma_server_nofile=True
                )
            )
            
            # Get or create collection for PDF content
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="pdf_products",
                metadata={"description": "PDF product data for RAG pipeline"}
            )
            
            logger.info("✅ ChromaDB initialized successfully")
            
        except Exception as e:
            logger.info(f"ChromaDB initialization failed, proceeding without vector storage: {e}")
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
            
            # ✅ ENHANCED UTF-8 safe string processing with Hungarian character support
            def make_utf8_safe(text: str, max_length: int = None) -> str:
                """Convert text to UTF-8 safe format, preserving Hungarian characters - NO FORCED LIMITS"""
                if not text:
                    return ""
                
                try:
                    # Handle different input types
                    if isinstance(text, bytes):
                        # Try multiple encodings for bytes
                        for encoding in ['utf-8', 'latin1', 'cp1252', 'latin2']:
                            try:
                                text = text.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all fail, use replacement
                            text = text.decode('utf-8', errors='replace')
                    
                    # Ensure we have a string
                    text = str(text)
                    
                    # Fix common Hungarian encoding issues
                    hungarian_fixes = {
                        'xE9': 'é', 'x151': 'ő', 'xF3': 'ó', 'xE1': 'á',
                        'xF6': 'ö', 'xFC': 'ü', 'xED': 'í', 'xFA': 'ú', 
                        'x171': 'ű', 'x170': 'Ű', 'x150': 'Ő', 'xC9': 'É'
                    }
                    
                    for encoded, decoded in hungarian_fixes.items():
                        text = text.replace(encoded, decoded)
                    
                    # Normalize unicode but preserve accented characters
                    import unicodedata
                    safe_text = unicodedata.normalize('NFC', text)
                    
                    # Remove only truly problematic characters, keep Hungarian accents
                    safe_text = ''.join(
                        c for c in safe_text 
                        if c.isprintable() or c in 'áéíóöőúüűÁÉÍÓÖŐÚÜŰ'
                    )
                    
                    # Final UTF-8 validation
                    safe_text = safe_text.encode('utf-8', errors='replace').decode('utf-8')
                    
                    # ✅ FIXED: Only apply length limit if explicitly requested
                    if max_length and len(safe_text) > max_length:
                        safe_text = safe_text[:max_length-3] + "..."
                        
                    return safe_text.strip()
                    
                except Exception as e:
                    logger.warning(f"UTF-8 conversion error: {e}, using fallback")
                    # Emergency fallback - just return ASCII-safe version
                    fallback = ''.join(c for c in str(text) if ord(c) < 128)
                    if max_length:
                        fallback = fallback[:max_length]
                    return fallback or "unknown"
            
            # Create safe product data
            safe_name = make_utf8_safe(result.product_name, 255)
            safe_description = make_utf8_safe(f"Extracted from {result.source_filename}", 500)
            # ✅ CRITICAL FIX: Store FULL content without arbitrary limits!
            safe_text_content = make_utf8_safe(result.extracted_text)  # NO LENGTH LIMIT!
            
            # Log content size for monitoring
            content_size_kb = len(safe_text_content) / 1024
            logger.info(f"💾 Storing {content_size_kb:.1f}KB of content for {safe_name}")
            
            product = Product(
                name=safe_name,
                description=safe_description,
                manufacturer_id=manufacturer.id,
                category_id=category.id,
                technical_specs=result.technical_specs,
                sku=self._generate_sku(safe_name),
                price=self._extract_price_from_result(result),
                full_text_content=safe_text_content  # ✅ FULL CONTENT PRESERVED!
            )
            
            self.db_session.add(product)
            self.db_session.commit()
            
            logger.info(f"💾 Product saved to PostgreSQL: {safe_name} ({content_size_kb:.1f}KB)")
            return product.id
            
        except Exception as e:
            # ✅ CRITICAL FIX: UTF-8 safe exception logging
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            logger.info(f"PostgreSQL ingestion failed, continuing with processing: {error_msg}")
            self.db_session.rollback()
            return None

    def _ingest_to_chromadb(self, result: PDFExtractionResult, product_id: Optional[int]):
        """Ingest extraction result to ChromaDB with intelligent chunking for large documents."""
        if not self.chroma_collection:
            logger.warning("ChromaDB not available, skipping vector ingestion")
            return
            
        try:
            content_size_kb = len(result.extracted_text) / 1024
            
            # ✅ INTELLIGENT CHUNKING: Large documents split into overlapping chunks
            if len(result.extracted_text) > 25000:  # 25KB threshold
                logger.info(f"🔍 Large document ({content_size_kb:.1f}KB) - using chunking strategy")
                chunks = self._create_chunked_documents(result, product_id)
                
                # Add all chunks to ChromaDB
                documents = [chunk["text"] for chunk in chunks]
                metadatas = [chunk["metadata"] for chunk in chunks]
                ids = [chunk["id"] for chunk in chunks]
                
                self.chroma_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"🔍 Added {len(chunks)} chunks to ChromaDB for {result.source_filename}")
                
            else:
                # Small documents - single entry (original logic)
                doc_text = self._create_document_text(result)
                
                metadata = {
                    "product_name": result.product_name,
                    "source_filename": result.source_filename,
                    "extraction_method": result.extraction_method,
                    "confidence_score": result.confidence_score,
                    "processing_time": result.processing_time,
                    "product_id": product_id if product_id else -1,
                    "manufacturer": "ROCKWOOL",
                    "content_size_kb": content_size_kb,
                    "is_chunked": False
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
                
                logger.info(f"🔍 Document added to ChromaDB: {doc_id} ({content_size_kb:.1f}KB)")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB ingestion failed: {e}")

    def _create_chunked_documents(self, result: PDFExtractionResult) -> List[Dict]:
        """Split large documents into chunks with overlap for better retrieval"""
        
        full_text = result.extracted_text
        chunk_size = 25000  # 25K per chunk
        overlap = 2500      # 2.5K overlap between chunks
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(full_text):
            end = min(start + chunk_size, len(full_text))
            chunk_text = full_text[start:end]
            
            # Create metadata for each chunk
            chunk_metadata = {
                "product_name": result.product_name,
                "source_filename": result.source_filename,
                "chunk_id": chunk_id,
                "total_chunks": (len(full_text) // chunk_size) + 1,
                "chunk_start": start,
                "chunk_end": end,
                "confidence_score": result.confidence_score,
                "manufacturer": "ROCKWOOL"
            }
            
            # Add technical specs to first chunk only
            if chunk_id == 0:
                for key, value in result.technical_specs.items():
                    if isinstance(value, (str, int, float)):
                        chunk_metadata[f"spec_{key}"] = str(value)
            
            chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata,
                "id": f"pdf_{result.source_filename}_{chunk_id}"
            })
            
            chunk_id += 1
            start = end - overlap  # Overlap for continuity
            
            if start >= len(full_text):
                break
    
        return chunks

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
            text_parts.append(result.extracted_text[:29000])  # First 29000 chars
        
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

    async def process_pdf(self, pdf_path: Path) -> Optional[PDFExtractionResult]:
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
            
            # Step 1: CSAK SZÖVEG kinyerés (PDFplumber szöveghez)
            text_content, _, basic_method = self.extractor.extract_pdf_content(pdf_path)
            
            # Step 1.5: SPECIÁLIS TÁBLÁZAT KINYERÉS (PDFplumber helyett!)
            logger.info("🔧 Running specialized table extraction (NO PDFplumber fallback)...")
            advanced_table_result = self.advanced_table_extractor.extract_tables_hybrid(pdf_path)
            
            # ✅ MÓDOSÍTÁS: CSAK speciális táblázat kinyerőket használunk
            if advanced_table_result.tables:
                logger.info(f"✅ Using specialized tables: {advanced_table_result.extraction_method} (confidence: {advanced_table_result.confidence:.2f})")
                tables = advanced_table_result.tables
                extraction_method = f"specialized_{advanced_table_result.extraction_method}"
            else:
                logger.info("⚠️ No tables found by specialized extractors - proceeding with empty tables")
                tables = []  # ÜRES táblázatok, ne fallback PDFplumber-re!
                extraction_method = "no_tables_found"

            if not text_content.strip():
                raise ValueError("No text content could be extracted from PDF")
            
            # Step 2: Attempt pattern-based extraction from tables
            pattern_based_specs = self._extract_specs_from_tables(tables)

            # Step 3: AI analysis with Claude
            ai_analysis = await self.ai_analyzer.analyze_rockwool_pdf(
                text_content, tables, pdf_path.name
            )
            
            # Step 4: Combine and create result
            final_specs = pattern_based_specs.copy()
            final_specs.update(ai_analysis.get("technical_specifications", {}))

            processing_time = (datetime.now() - start_time).total_seconds()

            # === TASK 5: ENHANCED CONFIDENCE SCORING ===
            enhanced_confidence = self._calculate_enhanced_confidence(
                text_content, tables, pattern_based_specs, ai_analysis, extraction_method
            )
            
            # Create result with comprehensive tracking metadata
            result = PDFExtractionResult(
                product_name=ai_analysis.get("product_identification", {}).get("name", pdf_path.stem),
                extracted_text=text_content,
                technical_specs=final_specs,
                pricing_info=self._extract_price_from_result(
                    PDFExtractionResult(
                        product_name="temp", extracted_text=text_content, 
                        technical_specs={}, pricing_info={}, tables_data=tables,
                        confidence_score=0, extraction_method="temp", 
                        source_filename="temp", processing_time=0
                    )
                ) or {},
                tables_data=tables,
                confidence_score=enhanced_confidence,
                extraction_method=extraction_method,
                source_filename=pdf_path.name,
                processing_time=processing_time,
                
                # ✅ NEW: Comprehensive tracking metadata
                extraction_metadata={
                    "file_size_bytes": pdf_path.stat().st_size,
                    "file_modified": pdf_path.stat().st_mtime,
                    "text_length": len(text_content),
                    "tables_found": len(tables),
                    "ai_analysis_fields": list(ai_analysis.keys()),
                    "confidence_factors": {
                        "text_quality": self._assess_text_quality(text_content),
                        "table_quality": self._assess_table_quality(tables),
                        "ai_confidence": ai_analysis.get("extraction_metadata", {}).get("confidence_score", 0.0)
                    }
                },
                text_extraction_method="pdfplumber",  # Always pdfplumber for text
                table_extraction_method=extraction_method,
                table_quality_score=advanced_table_result.quality_score if advanced_table_result.tables else 0.0,
                advanced_tables_used=bool(advanced_table_result.tables and advanced_table_result.confidence > 0.5),
                extraction_attempts=[
                    {
                        "method": "basic_pdfplumber_text_only",
                        "tables_found": 0,  # Most már nem a PDFplumber-től nyerjük a táblázatokat!
                        "success": len(text_content) > 0
                    },
                    {
                        "method": "advanced_hybrid",
                        "extractor_used": advanced_table_result.extraction_method,
                        "tables_found": len(advanced_table_result.tables),
                        "quality_score": advanced_table_result.quality_score,
                        "confidence": advanced_table_result.confidence,
                        "success": advanced_table_result.confidence > 0.5
                    }
                ]
            )

            # === SAVE NEW HASH TO DATABASE ===
            try:
                # ✅ ENHANCED: Ultra-safe filename and hash handling
                def ultra_safe_string(text: str, max_length: int = 255) -> str:
                    """Convert any string to ultra-safe UTF-8 format while preserving Hungarian characters"""
                    if not text:
                        return ""
                    
                    try:
                        # Handle different input types
                        if isinstance(text, bytes):
                            # Try multiple encodings for bytes
                            for encoding in ['utf-8', 'latin1', 'cp1252', 'latin2']:
                                try:
                                    text = text.decode(encoding)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                # If all fail, use replacement
                                text = text.decode('utf-8', errors='replace')
                        
                        # Ensure we have a string
                        text = str(text)
                        
                        # Fix common Hungarian encoding issues
                        hungarian_fixes = {
                            'xE9': 'é', 'x151': 'ő', 'xF3': 'ó', 'xE1': 'á',
                            'xF6': 'ö', 'xFC': 'ü', 'xED': 'í', 'xFA': 'ú', 
                            'x171': 'ű', 'x170': 'Ű', 'x150': 'Ő', 'xC9': 'É'
                        }
                        
                        for encoded, decoded in hungarian_fixes.items():
                            text = text.replace(encoded, decoded)
                        
                        # Normalize unicode but preserve accented characters
                        import unicodedata
                        safe_text = unicodedata.normalize('NFC', text)
                        
                        # Remove only truly problematic characters, keep Hungarian accents and printable characters
                        safe_text = ''.join(
                            c for c in safe_text 
                            if c.isprintable() or c in 'áéíóöőúüűÁÉÍÓÖŐÚÜŰ'
                        )
                        
                        # Final UTF-8 validation
                        safe_text = safe_text.encode('utf-8', errors='replace').decode('utf-8')
                        
                        # Limit length if specified
                        if max_length and len(safe_text) > max_length:
                            safe_text = safe_text[:max_length-3] + "..."
                            
                        return safe_text.strip()
                        
                    except Exception as e:
                        logger.warning(f"UTF-8 conversion error: {e}, using fallback")
                        # Emergency fallback - just return simple string
                        fallback = ''.join(c for c in str(text) if c.isalnum() or c.isspace())[:max_length or 255]
                        return fallback or "unknown"
                
                safe_filename = ultra_safe_string(pdf_path.name, 255)
                safe_hash = str(file_hash)  # SHA256 hash is always ASCII safe
                
                new_log = ProcessedFileLog(
                    file_hash=safe_hash,
                    content_hash=safe_hash,
                    source_filename=safe_filename,
                )
                self.db_session.add(new_log)
                self.db_session.commit()
                self.processed_file_hashes.add(safe_hash)
                logger.info(f"💾 Hash for {safe_filename} saved to DB.")
            except Exception as e:
                # ✅ CRITICAL FIX: UTF-8 safe exception logging
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                logger.info(f"Hash save issue (continuing with in-memory): {error_msg}")
                self.db_session.rollback()
                # Use safe hash for in-memory storage
                safe_hash = str(file_hash)  # SHA256 is always safe
                self.processed_file_hashes.add(safe_hash)  # In-memory only for this run

            # If confidence is reasonable, proceed to full ingestion
            # ✅ FIXED: Lowered threshold from 0.25 to 0.15 for Hungarian PDFs
            if result.confidence_score >= 0.15:  # Confidence threshold
                product_id = self._ingest_to_postgresql(result)
                if product_id:
                    self._ingest_to_chromadb(result, product_id)
                    self.processing_stats["successful"] += 1
                else:
                    self.processing_stats["failed"] += 1
            else:
                # ✅ DEBUGGING: Stop at first low confidence instead of continuing
                logger.error(
                    f"🚨 STOPPING AT LOW CONFIDENCE ({result.confidence_score:.2f}) for "
                    f"{pdf_path.name}. Debug threshold: 0.15"
                )
                raise ValueError(f"Low confidence debug stop: {result.confidence_score:.2f} < 0.15")
            
            return result
            
        except Exception as e:
            self.processing_stats['failed'] += 1
            logger.error(f"❌ Failed: {pdf_path.name} - {e}")
            
            # ✅ DEBUGGING: Stop at first error instead of continuing
            if "utf-8" in str(e).lower() or "confidence" in str(e).lower():
                logger.error(f"🚨 STOPPING FOR DEBUG: {e}")
                raise  # Stop processing for debugging
            
            # CRITICAL: Rollback session to prevent transaction errors
            if self.db_session.is_active:
                self.db_session.rollback()
            raise
        
        finally:
            self.processing_stats["total_processed"] += 1
    
    async def process_directory(
        self, pdf_directory: Path, output_file: Optional[Path] = None, 
        test_pdfs: Optional[List[str]] = None
    ) -> List[PDFExtractionResult]:
        """Process PDFs in a directory. If test_pdfs provided, only process those."""
        
        if not pdf_directory.exists():
            raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
        
        if test_pdfs:
            # Process only specific test PDFs
            pdf_files = []
            for test_pdf in test_pdfs:
                pdf_path = pdf_directory / test_pdf
                if pdf_path.exists():
                    pdf_files.append(pdf_path)
                else:
                    logger.warning(f"Test PDF not found: {test_pdf}")
            logger.info(f"🧪 Testing with {len(pdf_files)} selected PDFs.")
        else:
            # Process all PDFs
            pdf_files = list(pdf_directory.glob("*.pdf"))
            logger.info(f"📁 Found {len(pdf_files)} PDF files in {pdf_directory}.")
        
        results = []
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                logger.info(
                    f"\n📄 ({i}/{len(pdf_files)}): Checking {pdf_path.name}"
                )
                result = await self.process_pdf(pdf_path)
                if result:  # Only append if not a duplicate
                    results.append(result)
                
            except Exception as e:
                logger.error(f"Skipping {pdf_path.name} due to error: {e}")
                # Ensure session is clean for next iteration
                if self.db_session.is_active:
                    self.db_session.rollback()
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
        # Get a database session
        db_session = SessionLocal()

        # Initialize processor with the session
        processor = RealPDFProcessor(db_session)
        
        # Set paths - TESTING: Only process 3 representative PDFs
        pdf_directory = Path("src/downloads/rockwool_datasheets")
        output_file = Path("real_pdf_extraction_results.json")
        
        # PRODUCTION: Process ALL PDFs in the directory (34 ROCKWOOL PDFs)
        # No test_pdfs parameter = process all PDFs
        results = await processor.process_directory(
            pdf_directory, output_file, test_pdfs=None
        )
        
        print(f"\n🎉 SUCCESS: {len(results)} new PDFs processed.")
        
    except Exception as e:
        logger.error(f"❌ Top-level processing failed: {e}")
        raise
    finally:
        # ✅ CRITICAL: Comprehensive cleanup for Windows PermissionError prevention
        try:
            if processor:
                # Close ChromaDB client if exists
                if hasattr(processor, 'chroma_client') and processor.chroma_client:
                    try:
                        processor.chroma_client = None
                    except:
                        pass
                
                # Close database session properly
                if hasattr(processor, 'db_session') and processor.db_session:
                    try:
                        processor.db_session.close()
                    except:
                        pass
            
            # Close main database session
            if db_session and db_session.is_active:
                try:
                    db_session.close()
                except:
                    pass
            
            # Force garbage collection to release all file handles
            import gc
            gc.collect()
            
            # Give Windows a moment to release file locks
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
        # ✅ FINAL CLEANUP: Ensure everything is released
        try:
            import gc
            gc.collect()
        except:
            pass

