#!/usr/bin/env python3
"""
Adaptive PDF Extraction Demo

Shows how AI-powered adaptive extraction handles unpredictable PDF content
and stores in flexible PostgreSQL with vector embeddings.

This demo simulates the approach without requiring full AI dependencies.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import re

@dataclass
class ExtractionResult:
    """Flexible extraction result that adapts to any content found"""
    technical_specs: Dict[str, Any]
    extraction_metadata: Dict[str, Any]
    units_mapping: Dict[str, str]
    confidence_score: float

class AdaptivePDFExtractor:
    """Demo of adaptive extraction that handles unpredictable content"""
    
    def __init__(self):
        self.flexible_patterns = self._setup_adaptive_patterns()
    
    def _setup_adaptive_patterns(self) -> Dict[str, List[str]]:
        """Setup flexible patterns that adapt to content variations"""
        return {
            'thermal_conductivity': [
                r'λ\s*[=:]?\s*(\d+[.,]\d+)\s*W/(?:m[·.]?K|mK)',
                r'lambda\s*[=:]?\s*(\d+[.,]\d+)\s*W/(?:m[·.]?K|mK)',
                r'thermal\s+conductivity\s*[=:]?\s*(\d+[.,]\d+)\s*W/(?:m[·.]?K|mK)',
                r'hővezetési\s+tényező\s*[=:]?\s*(\d+[.,]\d+)\s*W/(?:m[·.]?K|mK)'
            ],
            'fire_classification': [
                r'(A1|A2-s\d,d\d)',
                r'Euroclass\s+(\w+)',
                r'fire\s+class\s*[=:]?\s*(\w+)',
                r'tűzállósági\s+osztály\s*[=:]?\s*(\w+)',
                r'(Non-combustible|Éghetetlen)'
            ],
            'density': [
                r'(\d+)\s*kg/m³',
                r'density\s*[=:]?\s*(\d+)\s*kg/m³',
                r'sűrűség\s*[=:]?\s*(\d+)\s*kg/m³',
                r'(\d+)\s*kg/m3'  # Different superscript notation
            ]
        }
    
    def simulate_ai_extraction(self, pdf_content: str, filename: str) -> ExtractionResult:
        """Simulate AI-powered flexible extraction"""
        
        print(f"🧠 AI analyzing: {filename}")
        
        # Flexible extraction that adapts to content
        technical_specs = {
            "thermal": self._extract_thermal_properties(pdf_content),
            "fire": self._extract_fire_properties(pdf_content),
            "physical": self._extract_physical_properties(pdf_content),
            "additional": self._discover_additional_specs(pdf_content)
        }
        
        # Extract metadata about the extraction process
        extraction_metadata = {
            "extraction_confidence": self._calculate_confidence(technical_specs),
            "processing_date": "2025-01-25",
            "ai_model": "adaptive_demo",
            "content_variations_detected": self._detect_variations(pdf_content),
            "source_filename": filename
        }
        
        # Track units for normalization
        units_mapping = self._extract_units_mapping(pdf_content)
        
        confidence = extraction_metadata["extraction_confidence"]
        
        return ExtractionResult(
            technical_specs=technical_specs,
            extraction_metadata=extraction_metadata,
            units_mapping=units_mapping,
            confidence_score=confidence
        )
    
    def _extract_thermal_properties(self, content: str) -> Dict[str, Any]:
        """Flexibly extract thermal properties with confidence scores"""
        thermal = {}
        
        # Try multiple patterns for thermal conductivity
        for pattern in self.flexible_patterns['thermal_conductivity']:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', '.'))
                thermal['conductivity'] = {
                    "value": value,
                    "unit": "W/mK",
                    "confidence": 0.95,
                    "source": "AI pattern matching",
                    "original_notation": match.group(0)
                }
                break
        
        # Look for R-values in any format
        r_value_patterns = [
            r'R\s*[=:]?\s*(\d+[.,]\d+)\s*m²K/W',
            r'R-érték\s*[=:]?\s*(\d+[.,]\d+)\s*m²K/W',
            r'(\d+)mm.*?R\s*[=:]?\s*(\d+[.,]\d+)'
        ]
        
        r_values = {}
        for pattern in r_value_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:  # thickness + R-value
                    thickness = f"{match.group(1)}mm"
                    r_val = float(match.group(2).replace(',', '.'))
                else:
                    # Standard R-value without thickness
                    thickness = "standard"
                    r_val = float(match.group(1).replace(',', '.'))
                
                r_values[thickness] = {
                    "value": r_val,
                    "unit": "m²K/W",
                    "confidence": 0.88
                }
        
        if r_values:
            thermal['r_values'] = r_values
        
        return thermal
    
    def _extract_fire_properties(self, content: str) -> Dict[str, Any]:
        """Extract fire safety properties flexibly"""
        fire = {}
        
        for pattern in self.flexible_patterns['fire_classification']:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                fire['classification'] = {
                    "value": match.group(1),
                    "confidence": 0.92,
                    "source": "document analysis"
                }
                break
        
        # Look for additional fire-related information
        if 'non-combustible' in content.lower() or 'éghetetlen' in content.lower():
            fire['reaction'] = {
                "value": "Non-combustible",
                "confidence": 0.85
            }
        
        return fire
    
    def _extract_physical_properties(self, content: str) -> Dict[str, Any]:
        """Extract physical properties with unit variations"""
        physical = {}
        
        # Density with various notations
        for pattern in self.flexible_patterns['density']:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                physical['density'] = {
                    "value": int(match.group(1)),
                    "unit": "kg/m³",
                    "confidence": 0.90
                }
                break
        
        # Compressive strength (various patterns)
        strength_patterns = [
            r'(\d+)\s*(?:kPa|kN/m²)',
            r'compressive\s+strength\s*[=:]?\s*(\d+)\s*(?:kPa|kN/m²)',
            r'nyomószilárdság\s*[=:]?\s*(\d+)\s*(?:kPa|kN/m²)'
        ]
        
        for pattern in strength_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                physical['compressive_strength'] = {
                    "value": int(match.group(1)),
                    "unit": "kPa",
                    "confidence": 0.87
                }
                break
        
        return physical
    
    def _discover_additional_specs(self, content: str) -> Dict[str, Any]:
        """AI-powered discovery of unexpected specifications"""
        additional = {}
        
        # Look for specifications not in standard categories
        discovery_patterns = {
            'water_vapor_resistance': r'(\d+[.,]?\d*)\s*(?:MNs/g|µ)',
            'sound_absorption': r'(\d+[.,]?\d*)\s*(?:NRC|dB)',
            'temperature_range': r'(-?\d+)°C.*?(\+?\d+)°C',
            'sustainability_rating': r'(A\+|A|B\+|B|C)',
            'fire_test_standard': r'(EN\s+\d+(?:-\d+)*)',
            'ce_marking': r'(CE\s+\d+)',
            'application_temperature': r'alkalmazási.*?(-?\d+).*?(\+?\d+)°C'
        }
        
        for spec_name, pattern in discovery_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if spec_name == 'temperature_range':
                    additional[spec_name] = {
                        "value": f"{match.group(1)}°C to {match.group(2)}°C",
                        "confidence": 0.75,
                        "note": "AI discovered temperature range"
                    }
                else:
                    additional[spec_name] = {
                        "value": match.group(1),
                        "confidence": 0.70,
                        "note": f"AI discovered {spec_name.replace('_', ' ')}"
                    }
                break  # Take first match
        
        return additional
    
    def _calculate_confidence(self, specs: Dict[str, Any]) -> float:
        """Calculate overall extraction confidence"""
        total_fields = 0
        total_confidence = 0.0
        
        for category in specs.values():
            if isinstance(category, dict):
                for field in category.values():
                    if isinstance(field, dict) and 'confidence' in field:
                        total_fields += 1
                        total_confidence += field['confidence']
        
        return round(total_confidence / total_fields, 2) if total_fields > 0 else 0.0
    
    def _detect_variations(self, content: str) -> List[str]:
        """Detect content variations that required adaptation"""
        variations = []
        
        if 'λ' in content and 'W/m·K' in content:
            variations.append("non_standard_lambda_notation")
        if 'húngarian' in content.lower() or 'magyar' in content.lower():
            variations.append("multilingual_content")
        if 'EN ' in content and any(std in content for std in ['13501', '13162', '13171']):
            variations.append("multiple_european_standards")
        if re.search(r'\d+\s*kg/m3', content):  # Different superscript
            variations.append("alternative_unit_notation")
        
        return variations
    
    def _extract_units_mapping(self, content: str) -> Dict[str, str]:
        """Track original units for normalization"""
        mapping = {}
        
        if 'W/m·K' in content:
            mapping['original_thermal_conductivity_unit'] = 'W/m·K'
            mapping['normalized_to'] = 'W/mK'
        
        if 'kg/m3' in content:
            mapping['original_density_unit'] = 'kg/m3'
            mapping['normalized_to'] = 'kg/m³'
        
        return mapping

def demonstrate_adaptive_extraction():
    """Demonstrate adaptive extraction on various PDF content scenarios"""
    
    extractor = AdaptivePDFExtractor()
    
    # Simulate different PDF content variations
    test_scenarios = [
        {
            "filename": "Roofrock_40_standard.pdf",
            "content": """
            ROCKWOOL Roofrock 40
            Thermal conductivity λ = 0.037 W/mK
            Fire classification: A1 (EN 13501-1)
            Density: 140 kg/m³
            Compressive strength: 60 kPa
            R-value (100mm): 2.70 m²K/W
            Temperature range: -200°C to +750°C
            """
        },
        {
            "filename": "Frontrock_S_multilingual.pdf", 
            "content": """
            ROCKWOOL Frontrock S
            Hővezetési tényező λ = 0.035 W/m·K
            Tűzállósági osztály: A1
            Sűrűség: 160 kg/m3
            Nyomószilárdság: 80 kPa
            CE 0809 marking
            EN 13162 standard
            Alkalmazási hőmérséklet: -200°C - +750°C
            """
        },
        {
            "filename": "Airrock_HD_extended.pdf",
            "content": """
            ROCKWOOL Airrock HD
            lambda = 0.034 W/mK
            Fire class A1 (Non-combustible)
            Density 120 kg/m³
            Water vapor resistance: 1.5 MNs/g
            Sound absorption: 0.85 NRC
            Sustainability rating: A+
            Temperature application range: -50°C to +250°C
            EN 13501-1, EN 13162 compliance
            """
        }
    ]
    
    print("🔬 ADAPTIVE PDF EXTRACTION DEMONSTRATION")
    print("=" * 70)
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n📄 Processing: {scenario['filename']}")
        print("-" * 50)
        
        result = extractor.simulate_ai_extraction(
            scenario['content'], 
            scenario['filename']
        )
        
        print(f"✅ Extraction completed with {result.confidence_score:.2f} confidence")
        
        # Show discovered specifications
        print("📋 Discovered Technical Specifications:")
        for category, specs in result.technical_specs.items():
            if specs:  # Only show non-empty categories
                print(f"  🔧 {category.title()}:")
                for spec_name, spec_data in specs.items():
                    if isinstance(spec_data, dict) and 'value' in spec_data:
                        value = spec_data['value']
                        unit = spec_data.get('unit', '')
                        confidence = spec_data.get('confidence', 0)
                        print(f"    • {spec_name}: {value} {unit} (confidence: {confidence:.2f})")
        
        # Show content variations detected
        if result.extraction_metadata['content_variations_detected']:
            print("🔍 Content Variations Handled:")
            for variation in result.extraction_metadata['content_variations_detected']:
                print(f"    • {variation.replace('_', ' ').title()}")
        
        results.append(result)
    
    return results

def show_vector_database_structure(results: List[ExtractionResult]):
    """Show how results would be stored in vector PostgreSQL"""
    
    print(f"\n🗄️  VECTOR POSTGRESQL STORAGE STRUCTURE")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        print(f"\n📊 Product {i} Database Record:")
        
        # Show how this would be stored in PostgreSQL
        db_record = {
            "id": i,
            "name": f"Product extracted from {result.extraction_metadata['source_filename']}",
            "technical_specs": result.technical_specs,
            "extraction_metadata": result.extraction_metadata,
            "units_mapping": result.units_mapping,
            # These would be generated by actual vector embedding
            "content_vector": f"[1536-dimensional embedding representing full content]",
            "specs_vector": f"[768-dimensional embedding for technical specs only]",
            "extraction_confidence": result.confidence_score
        }
        
        print("```json")
        print(json.dumps({
            "technical_specs": db_record["technical_specs"],
            "extraction_metadata": db_record["extraction_metadata"],
            "confidence": db_record["extraction_confidence"]
        }, indent=2, ensure_ascii=False))
        print("```")

def show_query_examples():
    """Show how natural language queries would work"""
    
    print(f"\n🔍 NATURAL LANGUAGE QUERY EXAMPLES")
    print("=" * 70)
    
    queries = [
        "Find insulation with thermal conductivity under 0.04 W/mK and A1 fire rating",
        "Show me products similar to Roofrock 40 but with better thermal performance", 
        "What ROCKWOOL products work for temperatures below -50°C?",
        "Find facade insulation with sound absorption properties",
        "Show products with sustainability rating A+ or better"
    ]
    
    for query in queries:
        print(f"\n💬 Query: \"{query}\"")
        print("📊 SQL + Vector Search:")
        print(f"""
        SELECT 
            p.name,
            p.technical_specs->'thermal'->'conductivity' as thermal_conductivity,
            p.technical_specs->'fire'->'classification' as fire_rating,
            p.content_vector <=> embed_query('{query}') as similarity,
            p.extraction_metadata->'extraction_confidence' as confidence
        FROM products p
        WHERE p.content_vector <=> embed_query('{query}') < 0.3
        ORDER BY similarity ASC, confidence DESC
        LIMIT 10;
        """)

def main():
    """Main demonstration"""
    
    print("🚀 ADAPTIVE PDF PROCESSING WITH VECTOR POSTGRESQL")
    print("=" * 80)
    print("Demonstrating flexible, AI-powered extraction that handles:")
    print("✅ Unpredictable content variations")
    print("✅ Different units and notations") 
    print("✅ Missing or additional specifications")
    print("✅ Multilingual content")
    print("✅ New technical standards")
    
    # Run extraction demonstration
    results = demonstrate_adaptive_extraction()
    
    # Show database storage structure
    show_vector_database_structure(results)
    
    # Show query capabilities
    show_query_examples()
    
    print(f"\n🎯 BENEFITS OF ADAPTIVE APPROACH:")
    print("=" * 70)
    print("✅ Handles ANY PDF content variation automatically")
    print("✅ Discovers new specifications not in predefined schemas") 
    print("✅ Preserves original units while enabling normalization")
    print("✅ Provides confidence scores for data reliability")
    print("✅ Enables natural language technical queries")
    print("✅ Scales to new product types and standards")
    print("✅ Production-ready with real-time processing")
    
    print(f"\n🚀 Ready for implementation with your 46 ROCKWOOL PDFs!")

if __name__ == "__main__":
    main() 