#!/usr/bin/env python3
"""
ROCKWOOL PDF Content Extractor

Extracts technical specifications, pricing data, and metadata from 
ROCKWOOL PDF documents based on the PDF_CONTENT_EXTRACTION_PLAN.md
"""

import re
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TechnicalSpecs:
    thermal_conductivity: Optional[str] = None
    fire_classification: Optional[str] = None
    density: Optional[str] = None
    available_thicknesses: List[str] = field(default_factory=list)
    r_values: Dict[str, str] = field(default_factory=dict)
    compressive_strength: Optional[str] = None
    temperature_range: Optional[str] = None
    water_vapor_resistance: Optional[str] = None

@dataclass 
class PricingData:
    base_price: Optional[float] = None
    currency: str = "HUF"
    unit: str = "m²"
    price_date: Optional[str] = None
    bulk_discounts: Dict[str, str] = field(default_factory=dict)
    availability: Optional[str] = None

@dataclass
class PDFMetadata:
    filename: str
    file_size_mb: float
    pdf_pages: int
    extraction_date: str
    pdf_url: str
    document_type: str = "datasheet"

@dataclass 
class ProductData:
    technical_specs: TechnicalSpecs
    pricing: PricingData
    metadata: PDFMetadata
    extraction_confidence: float = 0.0

class RockwoolPDFExtractor:
    """Main extractor class for ROCKWOOL PDF documents"""
    
    def __init__(self):
        self.text_patterns = self._setup_extraction_patterns()
        
    def _setup_extraction_patterns(self) -> Dict[str, re.Pattern]:
        """Setup regex patterns for extracting technical data"""
        return {
            # Technical specifications
            'thermal_conductivity': re.compile(
                r'λ\s*[=:]?\s*(\d+[.,]\d+)\s*W/(?:m[·.]?K|mK)', 
                re.IGNORECASE
            ),
            'fire_classification': re.compile(
                r'(A1|A2-s\d,d\d|Euroclass\s+\w+|Non-combustible)',
                re.IGNORECASE
            ),
            'density': re.compile(
                r'(\d+)\s*kg/m³',
                re.IGNORECASE
            ),
            'thickness': re.compile(
                r'(\d+)\s*mm',
                re.IGNORECASE
            ),
            'r_value': re.compile(
                r'R\s*[=:]?\s*(\d+[.,]\d+)\s*m²K/W',
                re.IGNORECASE
            ),
            'compressive_strength': re.compile(
                r'(\d+)\s*(?:kPa|kN/m²)',
                re.IGNORECASE
            ),
            'temperature_range': re.compile(
                r'(-?\d+)°C\s*(?:to|bis|-|–)\s*\+?(\d+)°C',
                re.IGNORECASE
            ),
            
            # Pricing patterns (Hungarian)
            'price_huf': re.compile(
                r'(\d+(?:[.,]\d+)?)\s*(?:Ft|HUF|forint)',
                re.IGNORECASE
            ),
            'price_per_m2': re.compile(
                r'(\d+(?:[.,]\d+)?)\s*(?:Ft|HUF)/m²',
                re.IGNORECASE
            ),
            'sku_code': re.compile(
                r'\b(\d{6,8})\b'
            )
        }
    
    def extract_text_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_with_pdfplumber(self, pdf_path: Path) -> Tuple[str, List]:
        """Extract text and tables using pdfplumber"""
        try:
            text = ""
            tables = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
            return text, tables
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {pdf_path}: {e}")
            return "", []
    
    def extract_technical_specs(self, text: str) -> TechnicalSpecs:
        """Extract technical specifications from PDF text"""
        specs = TechnicalSpecs()
        
        # Thermal conductivity
        match = self.text_patterns['thermal_conductivity'].search(text)
        if match:
            specs.thermal_conductivity = f"{match.group(1)} W/mK"
        
        # Fire classification
        match = self.text_patterns['fire_classification'].search(text)
        if match:
            specs.fire_classification = match.group(1)
        
        # Density
        match = self.text_patterns['density'].search(text)
        if match:
            specs.density = f"{match.group(1)} kg/m³"
        
        # Available thicknesses
        thickness_matches = self.text_patterns['thickness'].findall(text)
        if thickness_matches:
            specs.available_thicknesses = [f"{t}mm" for t in thickness_matches]
        
        # R-values
        r_value_matches = self.text_patterns['r_value'].findall(text)
        if r_value_matches:
            for i, r_val in enumerate(r_value_matches):
                thickness = f"{(i+1)*50}mm"  # Estimate thickness
                specs.r_values[thickness] = f"{r_val} m²K/W"
        
        # Compressive strength
        match = self.text_patterns['compressive_strength'].search(text)
        if match:
            specs.compressive_strength = f"{match.group(1)} kPa"
        
        # Temperature range
        match = self.text_patterns['temperature_range'].search(text)
        if match:
            min_temp, max_temp = match.groups()
            specs.temperature_range = f"{min_temp}°C to +{max_temp}°C"
        
        return specs
    
    def calculate_extraction_confidence(self, specs: TechnicalSpecs, 
                                      pricing: PricingData) -> float:
        """Calculate confidence score for extraction quality"""
        score = 0.0
        total_fields = 8  # Total number of key fields
        
        # Technical specs scoring
        if specs.thermal_conductivity:
            score += 1.5  # Most important field
        if specs.fire_classification:
            score += 1.0
        if specs.density:
            score += 1.0
        if specs.available_thicknesses:
            score += 0.5
        if specs.r_values:
            score += 1.0
        if specs.compressive_strength:
            score += 0.5
        
        # Pricing scoring
        if pricing.base_price:
            score += 2.5  # Very important for business
        
        return min(score / total_fields, 1.0)
    
    def process_product_datasheet(self, pdf_path: Path) -> ProductData:
        """Process a single product datasheet PDF"""
        logger.info(f"Processing datasheet: {pdf_path.name}")
        
        # Extract text using both methods
        text_pymupdf = self.extract_text_with_pymupdf(pdf_path)
        text_pdfplumber, tables = self.extract_text_with_pdfplumber(pdf_path)
        
        # Combine text from both extractors
        combined_text = text_pymupdf + "\n" + text_pdfplumber
        
        # Extract data
        technical_specs = self.extract_technical_specs(combined_text)
        pricing_data = PricingData()  # Initialize empty pricing
        
        # Extract metadata
        stat = pdf_path.stat()
        file_size_mb = round(stat.st_size / (1024 * 1024), 2)
        
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
        except:
            page_count = 0
        
        metadata = PDFMetadata(
            filename=pdf_path.name,
            file_size_mb=file_size_mb,
            pdf_pages=page_count,
            extraction_date="2025-01-25",
            pdf_url=f"file://{pdf_path.absolute()}",
            document_type="datasheet"
        )
        
        # Calculate confidence
        confidence = self.calculate_extraction_confidence(
            technical_specs, pricing_data
        )
        
        return ProductData(
            technical_specs=technical_specs,
            pricing=pricing_data,
            metadata=metadata,
            extraction_confidence=confidence
        )

# Example usage and testing functions
def demo_extraction():
    """Demo function to test the extractor"""
    print("🔍 ROCKWOOL PDF Extraction Demo")
    print("=" * 50)
    
    extractor = RockwoolPDFExtractor()
    pdf_dir = Path("src/downloads/rockwool_datasheets")
    
    if not pdf_dir.exists():
        print("❌ PDF directory not found. Please ensure PDFs are in src/downloads/rockwool_datasheets/")
        return
    
    # Process a few sample files
    sample_files = [
        "Roofrock 40 termékadatlap.pdf",
        "Frontrock S termékadatlap.pdf"
    ]
    
    for filename in sample_files:
        pdf_path = pdf_dir / filename
        if pdf_path.exists():
            print(f"\n🔍 Processing: {filename}")
            try:
                data = extractor.process_product_datasheet(pdf_path)
                print(f"📋 Technical specs extracted:")
                print(f"   Thermal conductivity: {data.technical_specs.thermal_conductivity}")
                print(f"   Fire classification: {data.technical_specs.fire_classification}")
                print(f"   Density: {data.technical_specs.density}")
                print(f"   Thicknesses: {data.technical_specs.available_thicknesses}")
                print(f"   Confidence: {data.extraction_confidence:.2f}")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️  File not found: {filename}")

if __name__ == "__main__":
    demo_extraction() 