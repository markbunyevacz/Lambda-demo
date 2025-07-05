"""
PDF Extraction Strategies
========================

This module implements various PDF extraction strategies that can be run
in parallel and compared for optimal results.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

# PDF extraction libraries
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF

# Project imports
from .models import (
    ExtractionResult,
    StrategyType,
    ExtractionStrategy
)


class BaseExtractionStrategy(ABC):
    """Base class for all extraction strategies"""
    
    def __init__(self, config: ExtractionStrategy):
        self.config = config
        self.strategy_type = config.strategy_type
    
    @abstractmethod
    async def extract(self, pdf_path: str) -> ExtractionResult:
        """Extract data from PDF and return structured result"""
        pass
    
    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality"""
        if not extracted_data:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Check for basic product information
        fields_to_check = [
            'product_name', 'manufacturer', 'description',
            'technical_specs', 'dimensions', 'thermal_properties'
        ]
        
        for field in fields_to_check:
            max_score += 1.0
            if field in extracted_data and extracted_data[field]:
                if isinstance(extracted_data[field], str):
                    # Text fields - check length and quality
                    text = extracted_data[field].strip()
                    if len(text) > 10:  # Reasonable length
                        score += 1.0
                    elif len(text) > 3:
                        score += 0.5
                elif isinstance(extracted_data[field], dict):
                    # Structured data - check if non-empty
                    if extracted_data[field]:
                        score += 1.0
                elif isinstance(extracted_data[field], list):
                    # Lists - check if non-empty
                    if extracted_data[field]:
                        score += 1.0
        
        return min(score / max_score, 1.0) if max_score > 0 else 0.0
    
    def _extract_technical_specs(self, text: str) -> Dict[str, Any]:
        """Extract technical specifications from text"""
        specs = {}
        
        # Common patterns for technical specifications
        import re
        
        # Thermal conductivity patterns
        thermal_patterns = [
            r'(?:hővezetési tényező|thermal conductivity)[:\s]*(\d+[.,]\d+)\s*(?:w/mk|w/m·k)',
            r'λ[:\s]*(\d+[.,]\d+)\s*(?:w/mk|w/m·k)',
        ]
        
        for pattern in thermal_patterns:
            match = re.search(pattern, text.lower())
            if match:
                value = match.group(1).replace(',', '.')
                try:
                    specs['thermal_conductivity'] = {
                        'value': float(value),
                        'unit': 'W/mK'
                    }
                    break
                except ValueError:
                    pass
        
        # Density patterns
        density_patterns = [
            r'(?:sűrűség|density)[:\s]*(\d+)\s*(?:kg/m³|kg/m3)',
            r'ρ[:\s]*(\d+)\s*(?:kg/m³|kg/m3)',
        ]
        
        for pattern in density_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    specs['density'] = {
                        'value': int(match.group(1)),
                        'unit': 'kg/m³'
                    }
                    break
                except ValueError:
                    pass
        
        # Fire resistance patterns
        fire_patterns = [
            r'(?:tűzálló|fire resistance|fire class)[:\s]*([a-z0-9\-]+)',
            r'(?:euroclass)[:\s]*([a-z0-9\-]+)',
        ]
        
        for pattern in fire_patterns:
            match = re.search(pattern, text.lower())
            if match:
                specs['fire_resistance'] = match.group(1).upper()
                break
        
        return specs


class PDFPlumberStrategy(BaseExtractionStrategy):
    """Strategy using pdfplumber for text and table extraction"""
    
    def __init__(self, config: Optional[ExtractionStrategy] = None):
        if config is None:
            config = ExtractionStrategy(
                strategy_type=StrategyType.PDFPLUMBER,
                cost_tier=1,
                timeout_seconds=30
            )
        super().__init__(config)
    
    async def extract(self, pdf_path: str) -> ExtractionResult:
        """Extract data using pdfplumber"""
        start_time = time.time()
        
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            extracted_data = {}
            pages_processed = 0
            tables_found = 0
            total_text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                pages_processed = len(pdf.pages)
                
                # Extract text from all pages
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        total_text += page_text + "\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        tables_found += len(tables)
                        extracted_data[f'page_{page.page_number}_tables'] = tables
                
                # Extract basic product information
                lines = total_text.split('\n')
                if lines:
                    # First non-empty line often contains product name
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 5:
                            extracted_data['product_name'] = line
                            break
                
                # Extract technical specifications
                extracted_data['technical_specs'] = self._extract_technical_specs(
                    total_text
                )
                
                # Store full text
                extracted_data['full_text'] = total_text.strip()
                extracted_data['page_count'] = pages_processed
            
            execution_time = time.time() - start_time
            confidence = self._calculate_confidence(extracted_data)
            
            return ExtractionResult(
                strategy_type=StrategyType.PDFPLUMBER,
                success=True,
                execution_time_seconds=execution_time,
                extracted_data=extracted_data,
                confidence_score=confidence,
                method_used="pdfplumber",
                pages_processed=pages_processed,
                tables_found=tables_found,
                text_length=len(total_text),
                data_completeness=min(len(extracted_data) / 6.0, 1.0),
                structure_quality=0.8 if tables_found > 0 else 0.6
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExtractionResult(
                strategy_type=StrategyType.PDFPLUMBER,
                success=False,
                execution_time_seconds=execution_time,
                error_message=f"PDFPlumber extraction failed: {str(e)}",
                confidence_score=0.0
            )


class PyMuPDFStrategy(BaseExtractionStrategy):
    """Strategy using PyMuPDF (fitz) for robust text extraction"""
    
    def __init__(self, config: Optional[ExtractionStrategy] = None):
        if config is None:
            config = ExtractionStrategy(
                strategy_type=StrategyType.PYMUPDF,
                cost_tier=1,
                timeout_seconds=30
            )
        super().__init__(config)
    
    async def extract(self, pdf_path: str) -> ExtractionResult:
        """Extract data using PyMuPDF"""
        start_time = time.time()
        
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            extracted_data = {}
            pages_processed = 0
            total_text = ""
            
            doc = fitz.open(pdf_path)
            pages_processed = len(doc)
            
            # Extract text from all pages
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text:
                    total_text += page_text + "\n"
            
            doc.close()
            
            # Extract basic product information
            lines = total_text.split('\n')
            if lines:
                # First non-empty line often contains product name
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 5:
                        extracted_data['product_name'] = line
                        break
            
            # Extract technical specifications
            extracted_data['technical_specs'] = self._extract_technical_specs(
                total_text
            )
            
            # Store full text
            extracted_data['full_text'] = total_text.strip()
            extracted_data['page_count'] = pages_processed
            
            execution_time = time.time() - start_time
            confidence = self._calculate_confidence(extracted_data)
            
            return ExtractionResult(
                strategy_type=StrategyType.PYMUPDF,
                success=True,
                execution_time_seconds=execution_time,
                extracted_data=extracted_data,
                confidence_score=confidence,
                method_used="pymupdf",
                pages_processed=pages_processed,
                tables_found=0,  # PyMuPDF doesn't extract tables directly
                text_length=len(total_text),
                data_completeness=min(len(extracted_data) / 6.0, 1.0),
                structure_quality=0.6  # Lower because no table extraction
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExtractionResult(
                strategy_type=StrategyType.PYMUPDF,
                success=False,
                execution_time_seconds=execution_time,
                error_message=f"PyMuPDF extraction failed: {str(e)}",
                confidence_score=0.0
            )



class NativePDFStrategy(BaseExtractionStrategy):
    """Strategy using Claude AI's native PDF analysis capabilities"""
    
    def __init__(self, config: Optional[ExtractionStrategy] = None):
        if config is None:
            config = ExtractionStrategy(
                strategy_type=StrategyType.NATIVE_PDF,
                cost_tier=4,  # Most expensive due to AI calls
                timeout_seconds=60
            )
        super().__init__(config)
    
    async def extract(self, pdf_path: str) -> ExtractionResult:
        """Extract data using Claude AI's native PDF analysis"""
        start_time = time.time()
        
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Note: This would require implementing Claude AI PDF analysis
            # For now, we'll return a placeholder indicating this needs integration
            
            extracted_data = {
                'note': 'Native PDF strategy requires Claude AI integration',
                'pdf_path': pdf_path,
                'strategy': 'native_pdf_ai'
            }
            
            execution_time = time.time() - start_time
            
            return ExtractionResult(
                strategy_type=StrategyType.NATIVE_PDF,
                success=False,  # Not implemented yet
                execution_time_seconds=execution_time,
                extracted_data=extracted_data,
                confidence_score=0.0,
                error_message="Native PDF strategy not yet implemented",
                method_used="claude_ai_native"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExtractionResult(
                strategy_type=StrategyType.NATIVE_PDF,
                success=False,
                execution_time_seconds=execution_time,
                error_message=f"Native PDF extraction failed: {str(e)}",
                confidence_score=0.0
            ) 