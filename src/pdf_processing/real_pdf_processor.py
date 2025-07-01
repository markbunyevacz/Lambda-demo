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
import re

# PDF Processing
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

# AI Integration
import anthropic
from anthropic import Anthropic

# Data Processing
import pandas as pd
import numpy as np

# Environment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

class RealPDFExtractor:
    """Real PDF text extraction using multiple methods"""
    
    def __init__(self):
        self.extraction_methods = ['pdfplumber', 'pypdf2', 'pymupdf']
        self.stats = {'pages_processed': 0, 'text_extracted': 0, 'tables_found': 0}
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
        """Extract text and tables using pdfplumber"""
        text_content = ""
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
                    
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
                        text_content += f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
        
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise
        
        return text_content
    
    def extract_text_pymupdf(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
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
                    text_content += f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
                
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
    
    def extract_pdf_content(self, pdf_path: Path) -> Tuple[str, List[Dict], str]:
        """Extract PDF content using best available method"""
        
        logger.info(f"🔍 Extracting PDF content: {pdf_path.name}")
        
        # Try pdfplumber first (best for tables)
        try:
            text, tables = self.extract_text_pdfplumber(pdf_path)
            if text.strip():
                logger.info(f"✅ PDFPlumber: {len(text)} chars, {len(tables)} tables")
                return text, tables, "pdfplumber"
        except Exception as e:
            logger.warning(f"PDFPlumber failed: {e}")
        
        # Fallback to PyPDF2
        try:
            text = self.extract_text_pypdf2(pdf_path)
            if text.strip():
                logger.info(f"✅ PyPDF2: {len(text)} chars")
                return text, [], "pypdf2"
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
        
        # Last resort: PyMuPDF
        try:
            text, tables = self.extract_text_pymupdf(pdf_path)
            if text.strip():
                logger.info(f"✅ PyMuPDF: {len(text)} chars, {len(tables)} tables")
                return text, tables, "pymupdf"
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            raise
        
        raise Exception("All PDF extraction methods failed")

class ClaudeAIAnalyzer:
    """Real Claude AI analysis for PDF content - no simulations"""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("❌ ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        logger.info(f"✅ Claude AI initialized: {self.model}")
    
    def analyze_rockwool_pdf(self, text_content: str, tables_data: List[Dict], filename: str) -> Dict[str, Any]:
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
                system="You are an expert technical data analyst specializing in building materials and insulation products. Extract accurate technical specifications and pricing information from ROCKWOOL product documentation.",
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            # Parse Claude's response
            analysis_result = self._parse_claude_response(response.content[0].text)
            
            logger.info(f"✅ Claude analysis complete for {filename}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            raise
    
    def _prepare_analysis_context(self, text: str, tables: List[Dict], filename: str) -> Dict[str, Any]:
        """Prepare context for Claude analysis"""
        
        context = {
            "filename": filename,
            "text_length": len(text),
            "tables_count": len(tables),
            "extracted_text": text[:8000],  # Limit text for API
            "tables_summary": []
        }
        
        # Summarize tables
        for table in tables[:5]:  # Limit to first 5 tables
            table_summary = {
                "page": table.get("page", "unknown"),
                "headers": table.get("headers", []),
                "row_count": len(table.get("data", [])),
                "sample_data": table.get("data", [])[:3]  # First 3 rows
            }
            context["tables_summary"].append(table_summary)
        
        return context
    
    def _create_extraction_prompt(self, context: Dict[str, Any]) -> str:
        """Create structured prompt for Claude"""
        
        prompt = f"""
ROCKWOOL TECHNICAL DATASHEET ANALYSIS

Filename: {context['filename']}
Text Length: {context['text_length']} characters
Tables Found: {context['tables_count']}

EXTRACTED CONTENT:
{context['extracted_text']}

"""
        
        # Add tables if available
        if context['tables_summary']:
            prompt += "\n\nTABLES FOUND:\n"
            for i, table in enumerate(context['tables_summary'], 1):
                prompt += f"\nTable {i} (Page {table['page']}):\n"
                prompt += f"Headers: {table['headers']}\n"
                prompt += f"Sample data: {table['sample_data']}\n"
        
        prompt += """

EXTRACT THE FOLLOWING INFORMATION IN JSON FORMAT:

{
  "product_identification": {
    "name": "exact product name",
    "product_code": "product code if available",
    "category": "product category",
    "application": "intended use/application"
  },
  "technical_specifications": {
    "thermal_conductivity": {
      "value": numerical_value,
      "unit": "W/mK",
      "conditions": "measurement conditions"
    },
    "fire_classification": {
      "value": "classification (A1, A2, etc.)",
      "standard": "test standard used"
    },
    "density": {
      "value": numerical_value,
      "unit": "kg/m³"
    },
    "compressive_strength": {
      "value": numerical_value,
      "unit": "kPa or kN/m²"
    },
    "dimensions": {
      "length": "value with unit",
      "width": "value with unit", 
      "thickness_options": ["available thicknesses"]
    },
    "temperature_range": {
      "min": "minimum temperature",
      "max": "maximum temperature"
    }
  },
  "pricing_information": {
    "prices": [
      {
        "thickness": "thickness value",
        "area": "coverage area",
        "price": "price with currency",
        "unit": "pricing unit (m², package, etc.)"
      }
    ],
    "currency": "HUF or other",
    "price_date": "pricing date if available"
  },
  "additional_data": {
    "certifications": ["list of certifications"],
    "standards": ["applicable standards"],
    "packaging": "packaging information",
    "warranty": "warranty information"
  },
  "confidence_assessment": {
    "overall_confidence": 0.95,
    "data_completeness": 0.90,
    "notes": "any extraction notes or uncertainties"
  }
}

IMPORTANT REQUIREMENTS:
1. Extract ONLY factual information found in the document
2. Use exact values and units as written
3. If information is not found, use null or "not specified"
4. Provide confidence scores based on data clarity
5. Include original language terms where relevant (Hungarian)
6. Focus on technical accuracy over completeness

Return only valid JSON with the extracted data.
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
            required_keys = ['product_identification', 'technical_specifications', 'confidence_assessment']
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
                "confidence_assessment": {"overall_confidence": 0.0, "notes": f"JSON parsing failed: {e}"}
            }
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            raise

class RealPDFProcessor:
    """Main class for real PDF processing - NO SIMULATIONS"""
    
    def __init__(self):
        self.extractor = RealPDFExtractor()
        self.ai_analyzer = ClaudeAIAnalyzer()
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_extraction_time': 0.0
        }
    
    def process_pdf(self, pdf_path: Path) -> PDFExtractionResult:
        """Process a single PDF with real AI analysis"""
        
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Processing PDF: {pdf_path.name}")
            
            # Step 1: Extract text and tables
            text_content, tables, method = self.extractor.extract_pdf_content(pdf_path)
            
            if not text_content.strip():
                raise ValueError("No text content extracted from PDF")
            
            # Step 2: AI analysis with Claude
            ai_analysis = self.ai_analyzer.analyze_rockwool_pdf(text_content, tables, pdf_path.name)
            
            # Step 3: Create result
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = PDFExtractionResult(
                product_name=ai_analysis.get('product_identification', {}).get('name', pdf_path.stem),
                extracted_text=text_content,
                technical_specs=ai_analysis.get('technical_specifications', {}),
                pricing_info=ai_analysis.get('pricing_information', {}),
                tables_data=tables,
                confidence_score=ai_analysis.get('confidence_assessment', {}).get('overall_confidence', 0.0),
                extraction_method=method,
                source_filename=pdf_path.name,
                processing_time=processing_time
            )
            
            # Update stats
            self.processing_stats['successful'] += 1
            self.processing_stats['total_extraction_time'] += processing_time
            
            logger.info(f"✅ Success: {pdf_path.name} ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            self.processing_stats['failed'] += 1
            logger.error(f"❌ Failed: {pdf_path.name} - {e}")
            raise
        
        finally:
            self.processing_stats['total_processed'] += 1
    
    def process_directory(self, pdf_directory: Path, output_file: Optional[Path] = None) -> List[PDFExtractionResult]:
        """Process all PDFs in directory"""
        
        if not pdf_directory.exists():
            raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
        
        # Find PDF files
        pdf_files = list(pdf_directory.glob("*.pdf"))
        product_pdfs = [f for f in pdf_files if "duplicates" not in str(f)]
        
        logger.info(f"📁 Processing directory: {pdf_directory}")
        logger.info(f"📄 Found {len(product_pdfs)} PDF files")
        
        results = []
        
        for i, pdf_path in enumerate(product_pdfs, 1):
            try:
                logger.info(f"\\n📄 Processing ({i}/{len(product_pdfs)}): {pdf_path.name}")
                
                result = self.process_pdf(pdf_path)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Skipping {pdf_path.name}: {e}")
                continue
        
        # Save results if output file specified
        if output_file and results:
            self._save_results(results, output_file)
        
        self._print_final_stats(results)
        
        return results
    
    def _save_results(self, results: List[PDFExtractionResult], output_file: Path):
        """Save processing results to JSON"""
        
        output_data = {
            "processing_timestamp": datetime.now().isoformat(),
            "total_pdfs_processed": len(results),
            "results": [asdict(result) for result in results],
            "statistics": self.processing_stats
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {output_file}")
    
    def _print_final_stats(self, results: List[PDFExtractionResult]):
        """Print processing statistics"""
        
        print("\\n" + "=" * 80)
        print("🏁 REAL PDF PROCESSING COMPLETE")
        print("=" * 80)
        
        print(f"📊 Processing Statistics:")
        print(f"   📄 Total PDFs processed: {self.processing_stats['total_processed']}")
        print(f"   ✅ Successful extractions: {self.processing_stats['successful']}")
        print(f"   ❌ Failed extractions: {self.processing_stats['failed']}")
        print(f"   ⏱️  Total processing time: {self.processing_stats['total_extraction_time']:.2f}s")
        
        if results:
            avg_confidence = sum(r.confidence_score for r in results) / len(results)
            avg_specs = sum(len(r.technical_specs) for r in results) / len(results)
            
            print(f"\\n🎯 Quality Metrics:")
            print(f"   📈 Average confidence: {avg_confidence:.2f}")
            print(f"   🔧 Average specs per product: {avg_specs:.1f}")
            
            # Method breakdown
            methods = {}
            for result in results:
                methods[result.extraction_method] = methods.get(result.extraction_method, 0) + 1
            
            print(f"\\n🔧 Extraction Methods:")
            for method, count in methods.items():
                print(f"   {method}: {count} PDFs")
        
        print(f"\\n✅ REAL AI-POWERED PDF PROCESSING COMPLETE")
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
    
    try:
        # Initialize processor
        processor = RealPDFProcessor()
        
        # Set paths
        pdf_directory = Path("src/downloads/rockwool_datasheets")
        output_file = Path("real_pdf_extraction_results.json")
        
        # Process PDFs
        results = processor.process_directory(pdf_directory, output_file)
        
        print(f"\\n🎉 SUCCESS: {len(results)} PDFs processed with real AI analysis!")
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        raise

if __name__ == "__main__":
    main() 