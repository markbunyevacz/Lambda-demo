
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import fitz  # PyMuPDF
import pdfplumber
import PyPDF2

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

logger = logging.getLogger(__name__)


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
    
    def _deep_learning_validation(self, result: Dict) -> Dict:
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