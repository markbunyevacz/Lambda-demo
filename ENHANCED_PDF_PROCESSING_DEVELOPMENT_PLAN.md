# Enhanced PDF Processing Development Plan - Lambda.hu

## 📋 Current State vs Requirements Gap Analysis

### ✅ **What's Already Implemented**
- Basic PDF text extraction with PyMuPDF
- Pattern-based technical specification extraction
- Database integration with PostgreSQL
- Vector search with ChromaDB
- Duplicate prevention system
- UTF-8 encoding support

### 🚧 **What Needs Development** (Your Requirements)

---

## 🛠️ 1. Enhanced PDF Parser

### 📚 **Multi-Tool Approach Implementation**

#### **Current State**
```python
# From fix_pdf_metadata_extraction.py - Single tool approach
def extract_pdf_content(self, pdf_path: Path) -> str:
    try:
        doc = fitz.open(pdf_path)  # Only PyMuPDF
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return ""
```

#### **Required Enhancement**
```python
# New multi-tool extraction pipeline
class EnhancedPDFParser:
    def __init__(self):
        self.extractors = {
            'pymupdf': PyMuPDFExtractor(),
            'pdfplumber': PDFPlumberExtractor(), 
            'pypdf2': PyPDF2Extractor(),
            'ocr': TesseractOCRExtractor()
        }
    
    def extract_with_fallback(self, pdf_path: Path) -> ExtractionResult:
        """Try multiple extraction methods with quality scoring"""
        results = {}
        
        # Primary: PyMuPDF for text
        results['pymupdf'] = self.extractors['pymupdf'].extract(pdf_path)
        
        # Secondary: pdfplumber for tables
        results['pdfplumber'] = self.extractors['pdfplumber'].extract_tables(pdf_path)
        
        # Fallback: OCR for image-based PDFs
        if results['pymupdf'].quality_score < 0.7:
            results['ocr'] = self.extractors['ocr'].extract(pdf_path)
        
        # Combine best results
        return self.merge_extraction_results(results)
```

#### **Layout Detection Enhancement**
```python
class LayoutPreservingExtractor:
    def extract_with_structure(self, pdf_path: Path) -> StructuredDocument:
        """Preserve document structure and sections"""
        doc = fitz.open(pdf_path)
        structured_content = {
            'headers': [],
            'sections': {},
            'tables': [],
            'images': [],
            'layout_blocks': []
        }
        
        for page_num, page in enumerate(doc):
            # Extract layout blocks with positioning
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    # Detect headers by font size/style
                    if self.is_header(block):
                        structured_content['headers'].append({
                            'text': self.extract_text_from_block(block),
                            'page': page_num,
                            'bbox': block['bbox'],
                            'level': self.detect_header_level(block)
                        })
                    
                    # Group content by sections
                    section = self.identify_section(block)
                    if section not in structured_content['sections']:
                        structured_content['sections'][section] = []
                    structured_content['sections'][section].append(block)
        
        return StructuredDocument(structured_content)
```

### 🖼️ **OCR Fallback System**
```python
class TesseractOCRExtractor:
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6 -l hun+eng'
    
    def extract(self, pdf_path: Path) -> OCRResult:
        """OCR extraction for image-based or low-quality PDFs"""
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        extracted_text = ""
        confidence_scores = []
        
        for page_num, image in enumerate(images):
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(image)
            
            # Extract text with confidence
            data = pytesseract.image_to_data(
                processed_image, 
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            page_text, page_confidence = self.process_ocr_data(data)
            extracted_text += page_text
            confidence_scores.append(page_confidence)
        
        return OCRResult(
            text=extracted_text,
            confidence=sum(confidence_scores) / len(confidence_scores),
            method='tesseract_ocr'
        )
    
    def preprocess_image(self, image):
        """Enhance image for better OCR accuracy"""
        # Convert to grayscale
        # Increase contrast
        # Remove noise
        # Deskew if needed
        pass
```

---

## 🔤 2. Text Processing Pipeline

### 🇭🇺 **Hungarian Character Handling**

#### **Current Implementation**
```python
# From production_pdf_integration.py - Basic encoding fixes
def fix_encoding(self, text: str) -> str:
    replacements = {
        'xE9': 'é', 'x151': 'ő', 'xF3': 'ó', 'xE1': 'á',
        'xF6': 'ö', 'xFC': 'ü', 'xED': 'í', 'xFA': 'ú', 'x171': 'ű'
    }
    # Limited character set handling
```

#### **Required Enhancement**
```python
class HungarianTextProcessor:
    def __init__(self):
        self.encoding_map = self._build_comprehensive_encoding_map()
        self.normalization_rules = self._build_normalization_rules()
    
    def _build_comprehensive_encoding_map(self) -> Dict[str, str]:
        """Comprehensive Hungarian character encoding map"""
        return {
            # URL encoding
            '%C3%A1': 'á', '%C3%A9': 'é', '%C3%AD': 'í', '%C3%B3': 'ó', '%C3%BA': 'ú',
            '%C5%91': 'ő', '%C5%B1': 'ű', '%C3%B6': 'ö', '%C3%BC': 'ü',
            '%C3%81': 'Á', '%C3%89': 'É', '%C3%8D': 'Í', '%C3%93': 'Ó', '%C3%9A': 'Ú',
            '%C5%90': 'Ő', '%C5%B0': 'Ű', '%C3%96': 'Ö', '%C3%9C': 'Ü',
            
            # Hex encoding
            'xE1': 'á', 'xE9': 'é', 'xED': 'í', 'xF3': 'ó', 'xFA': 'ú',
            'x151': 'ő', 'x171': 'ű', 'xF6': 'ö', 'xFC': 'ü',
            
            # OCR common mistakes
            'a´': 'á', 'e´': 'é', 'i´': 'í', 'o´': 'ó', 'u´': 'ú',
            'o¨': 'ö', 'u¨': 'ü',
            
            # Legacy encoding issues
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú'
        }
    
    def process_text(self, text: str) -> ProcessedText:
        """Comprehensive Hungarian text processing"""
        # 1. Fix encoding issues
        clean_text = self.fix_encoding_issues(text)
        
        # 2. Normalize whitespace and special characters
        normalized_text = self.normalize_text(clean_text)
        
        # 3. Detect and fix OCR errors
        corrected_text = self.fix_ocr_errors(normalized_text)
        
        # 4. Validate Hungarian language consistency
        validation_result = self.validate_hungarian_text(corrected_text)
        
        return ProcessedText(
            text=corrected_text,
            confidence=validation_result.confidence,
            corrections_made=validation_result.corrections,
            encoding_issues_fixed=validation_result.encoding_fixes
        )
```

### 📑 **Section Detection System**

#### **Required Implementation**
```python
class DocumentSectionDetector:
    def __init__(self):
        self.section_patterns = {
            'technical_specs': [
                r'(?i)(műszaki\s+adatok|technical\s+data|specifications)',
                r'(?i)(tulajdonságok|properties)',
                r'(?i)(teljesítmény|performance)'
            ],
            'usage': [
                r'(?i)(felhasználás|alkalmazás|usage|application)',
                r'(?i)(területek|areas|uses)'
            ],
            'packaging': [
                r'(?i)(csomagolás|packaging|packing)',
                r'(?i)(kiszerelés|sizes|dimensions)'
            ],
            'installation': [
                r'(?i)(beépítés|installation|mounting)',
                r'(?i)(szerelés|assembly)'
            ],
            'standards': [
                r'(?i)(szabványok|standards|norms)',
                r'(?i)(EN\s+\d+|ISO\s+\d+|MSZ\s+\d+)'
            ]
        }
    
    def detect_sections(self, structured_doc: StructuredDocument) -> SectionMap:
        """Identify document sections using headers and content patterns"""
        sections = {}
        current_section = None
        
        for element in structured_doc.elements:
            if element.type == 'header':
                # Detect section type from header text
                section_type = self.classify_header(element.text)
                if section_type:
                    current_section = section_type
                    sections[current_section] = {
                        'header': element,
                        'content': [],
                        'confidence': element.confidence
                    }
            
            elif current_section and element.type in ['paragraph', 'table', 'list']:
                sections[current_section]['content'].append(element)
        
        # Post-process to handle missing headers
        sections = self.handle_implicit_sections(sections, structured_doc)
        
        return SectionMap(sections)
    
    def classify_header(self, header_text: str) -> Optional[str]:
        """Classify header text to section type"""
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, header_text):
                    return section_type
        return None
```

### 📊 **Advanced Table Extraction**

#### **Current Limitation**
The existing code lacks comprehensive table extraction capabilities.

#### **Required Implementation**
```python
class AdvancedTableExtractor:
    def __init__(self):
        self.table_detectors = [
            PDFPlumberTableDetector(),
            CamelotTableDetector(),
            TabulaTableDetector(),
            LayoutBasedTableDetector()
        ]
    
    def extract_all_tables(self, pdf_path: Path) -> List[ExtractedTable]:
        """Extract tables using multiple methods and merge results"""
        all_tables = []
        
        for detector in self.table_detectors:
            try:
                tables = detector.extract(pdf_path)
                for table in tables:
                    # Quality assessment
                    quality_score = self.assess_table_quality(table)
                    if quality_score > 0.7:
                        all_tables.append(ExtractedTable(
                            data=table.data,
                            page=table.page,
                            bbox=table.bbox,
                            quality_score=quality_score,
                            extraction_method=detector.name
                        ))
            except Exception as e:
                logger.warning(f"Table extraction failed with {detector.name}: {e}")
        
        # Deduplicate and merge overlapping tables
        return self.merge_overlapping_tables(all_tables)
    
    def assess_table_quality(self, table: RawTable) -> float:
        """Assess extracted table quality"""
        quality_factors = {
            'completeness': self.check_completeness(table),
            'structure': self.check_structure(table),
            'data_consistency': self.check_data_consistency(table),
            'header_detection': self.check_headers(table)
        }
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def format_table_for_extraction(self, table: ExtractedTable) -> FormattedTable:
        """Format table for technical specification extraction"""
        # Detect table type (specs, dimensions, etc.)
        table_type = self.detect_table_type(table)
        
        if table_type == 'technical_specifications':
            return self.format_specs_table(table)
        elif table_type == 'dimensions':
            return self.format_dimensions_table(table)
        elif table_type == 'r_values':
            return self.format_r_values_table(table)
        
        return FormattedTable(table.data, table_type)
```

---

## ✅ 3. Quality Control System

### 🔍 **Completeness Validation**

#### **Required Implementation**
```python
class ExtractionQualityController:
    def __init__(self):
        self.required_sections = {
            'rockwool_datasheet': {
                'mandatory': ['technical_specs', 'thermal_properties'],
                'expected': ['usage', 'packaging', 'standards'],
                'optional': ['installation', 'certifications']
            }
        }
        
        self.required_specifications = {
            'thermal_conductivity': {'mandatory': True, 'format': r'\d+\.\d+\s*W/mK'},
            'fire_classification': {'mandatory': True, 'format': r'A[12](-s\d,d\d)?'},
            'density': {'mandatory': True, 'format': r'\d+\s*kg/m³'},
            'available_thicknesses': {'mandatory': False, 'format': r'\d+mm'}
        }
    
    def validate_extraction_completeness(self, extraction_result: ExtractionResult) -> ValidationReport:
        """Comprehensive completeness validation"""
        report = ValidationReport()
        
        # 1. Section completeness
        section_validation = self.validate_sections(extraction_result.sections)
        report.add_section_validation(section_validation)
        
        # 2. Technical specifications completeness
        specs_validation = self.validate_specifications(extraction_result.technical_specs)
        report.add_specs_validation(specs_validation)
        
        # 3. Data quality assessment
        quality_assessment = self.assess_data_quality(extraction_result)
        report.add_quality_assessment(quality_assessment)
        
        # 4. Generate overall score
        report.overall_score = self.calculate_overall_score(report)
        
        return report
    
    def validate_sections(self, sections: SectionMap) -> SectionValidation:
        """Validate presence of required sections"""
        doc_type = self.detect_document_type(sections)
        required = self.required_sections.get(doc_type, {})
        
        validation = SectionValidation()
        
        # Check mandatory sections
        for section in required.get('mandatory', []):
            if section not in sections:
                validation.add_missing_mandatory(section)
            else:
                validation.add_found_mandatory(section)
        
        # Check expected sections
        for section in required.get('expected', []):
            if section not in sections:
                validation.add_missing_expected(section)
            else:
                validation.add_found_expected(section)
        
        return validation
```

### 🔄 **Cross-Reference Verification**

```python
class CrossReferenceValidator:
    def __init__(self):
        self.reference_database = self.load_reference_data()
        self.tolerance_ranges = {
            'thermal_conductivity': 0.005,  # ±0.005 W/mK
            'density': 10,  # ±10 kg/m³
            'compressive_strength': 5  # ±5 kPa
        }
    
    def verify_against_references(self, product_data: ProductData) -> VerificationReport:
        """Cross-reference extracted data against known values"""
        report = VerificationReport()
        
        # Find reference product
        reference = self.find_reference_product(product_data.name)
        
        if reference:
            # Compare technical specifications
            for spec_name, extracted_value in product_data.technical_specs.items():
                if spec_name in reference.specs:
                    comparison = self.compare_values(
                        extracted_value, 
                        reference.specs[spec_name],
                        self.tolerance_ranges.get(spec_name)
                    )
                    report.add_comparison(spec_name, comparison)
        
        # Flag significant discrepancies
        discrepancies = report.get_discrepancies(threshold=0.8)
        if discrepancies:
            report.flag_for_review("Significant discrepancies found", discrepancies)
        
        return report
    
    def load_reference_data(self) -> ReferenceDatabase:
        """Load reference product data for verification"""
        # Load from existing database, manufacturer specs, etc.
        pass
```

### 👥 **Human Review Loop**

```python
class HumanReviewManager:
    def __init__(self):
        self.review_queue = ReviewQueue()
        self.review_criteria = self.load_review_criteria()
    
    def queue_for_review(self, extraction_result: ExtractionResult, reason: str):
        """Queue extraction for human review"""
        review_item = ReviewItem(
            extraction_result=extraction_result,
            reason=reason,
            priority=self.calculate_priority(extraction_result, reason),
            created_at=datetime.now()
        )
        
        self.review_queue.add(review_item)
        self.notify_reviewers(review_item)
    
    def should_require_review(self, validation_report: ValidationReport) -> bool:
        """Determine if extraction requires human review"""
        criteria = [
            validation_report.overall_score < 0.8,
            validation_report.has_missing_mandatory_sections(),
            validation_report.has_significant_discrepancies(),
            validation_report.extraction_confidence < 0.85
        ]
        
        return any(criteria)
    
    def generate_review_package(self, review_item: ReviewItem) -> ReviewPackage:
        """Generate comprehensive review package for human reviewer"""
        return ReviewPackage(
            original_pdf=review_item.source_pdf,
            extracted_data=review_item.extraction_result,
            validation_report=review_item.validation_report,
            highlighted_issues=review_item.issues,
            suggested_corrections=self.generate_suggestions(review_item),
            review_form=self.generate_review_form(review_item)
        )
```

---

## 📋 4. Structured Output Format

### 📄 **JSON Schema Definition**

```python
class ProductDataSchema:
    """Standardized JSON schema for product data"""
    
    @staticmethod
    def get_schema() -> Dict:
        return {
            "type": "object",
            "required": ["product_info", "technical_specifications", "extraction_metadata"],
            "properties": {
                "product_info": {
                    "type": "object",
                    "required": ["name", "manufacturer", "category"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "manufacturer": {"type": "string"},
                        "category": {"type": "string"},
                        "product_code": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "technical_specifications": {
                    "type": "object",
                    "properties": {
                        "thermal_properties": {
                            "type": "object",
                            "properties": {
                                "conductivity": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "number", "minimum": 0},
                                        "unit": {"type": "string", "enum": ["W/mK"]},
                                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                        "test_standard": {"type": "string"}
                                    },
                                    "required": ["value", "unit"]
                                },
                                "r_values": {
                                    "type": "object",
                                    "patternProperties": {
                                        "^\\d+mm$": {
                                            "type": "object",
                                            "properties": {
                                                "value": {"type": "number", "minimum": 0},
                                                "unit": {"type": "string", "enum": ["m²K/W"]}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "fire_properties": {
                            "type": "object",
                            "properties": {
                                "classification": {
                                    "type": "string",
                                    "pattern": "^A[12](-s\\d,d\\d)?$"
                                },
                                "reaction_to_fire": {"type": "string"},
                                "test_standard": {"type": "string"}
                            }
                        },
                        "physical_properties": {
                            "type": "object",
                            "properties": {
                                "density": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "integer", "minimum": 0},
                                        "unit": {"type": "string", "enum": ["kg/m³"]}
                                    }
                                },
                                "compressive_strength": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "number", "minimum": 0},
                                        "unit": {"type": "string", "enum": ["kPa"]}
                                    }
                                },
                                "available_thicknesses": {
                                    "type": "array",
                                    "items": {"type": "string", "pattern": "^\\d+mm$"}
                                }
                            }
                        }
                    }
                },
                "extraction_metadata": {
                    "type": "object",
                    "required": ["source_file", "extraction_date", "overall_confidence"],
                    "properties": {
                        "source_file": {"type": "string"},
                        "extraction_date": {"type": "string", "format": "date-time"},
                        "extraction_method": {"type": "string"},
                        "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "processing_time_seconds": {"type": "number"},
                        "validation_status": {"type": "string", "enum": ["passed", "warning", "failed"]},
                        "requires_review": {"type": "boolean"}
                    }
                }
            }
        }
```

### 🔍 **Validation Rules Engine**

```python
class ValidationRulesEngine:
    def __init__(self):
        self.rules = self.load_validation_rules()
        self.schema = ProductDataSchema.get_schema()
    
    def validate_product_data(self, data: Dict) -> ValidationResult:
        """Comprehensive validation using schema and business rules"""
        result = ValidationResult()
        
        # 1. Schema validation
        schema_validation = self.validate_against_schema(data)
        result.add_schema_validation(schema_validation)
        
        # 2. Business rules validation
        business_validation = self.validate_business_rules(data)
        result.add_business_validation(business_validation)
        
        # 3. Cross-field validation
        cross_field_validation = self.validate_cross_fields(data)
        result.add_cross_field_validation(cross_field_validation)
        
        return result
    
    def load_validation_rules(self) -> List[ValidationRule]:
        """Load business validation rules"""
        return [
            ValidationRule(
                name="thermal_conductivity_range",
                description="Thermal conductivity must be within reasonable range",
                validator=lambda x: 0.020 <= x.get('thermal_properties', {}).get('conductivity', {}).get('value', 0) <= 0.060,
                error_message="Thermal conductivity outside expected range (0.020-0.060 W/mK)"
            ),
            ValidationRule(
                name="fire_classification_format",
                description="Fire classification must follow EN standard format",
                validator=lambda x: re.match(r'^A[12](-s\d,d\d)?$', x.get('fire_properties', {}).get('classification', '')),
                error_message="Invalid fire classification format"
            ),
            ValidationRule(
                name="density_thickness_correlation",
                description="Density should correlate with available thicknesses",
                validator=self.validate_density_thickness_correlation,
                error_message="Density and thickness values seem inconsistent"
            )
        ]
```

### 📤 **Multiple Output Formats**

```python
class OutputFormatManager:
    def __init__(self):
        self.formatters = {
            'json': JSONFormatter(),
            'csv': CSVFormatter(),
            'excel': ExcelFormatter(),
            'xml': XMLFormatter(),
            'yaml': YAMLFormatter()
        }
    
    def export_data(self, product_data: ProductData, formats: List[str]) -> ExportResult:
        """Export data in multiple formats"""
        export_result = ExportResult()
        
        for format_name in formats:
            if format_name in self.formatters:
                formatter = self.formatters[format_name]
                try:
                    output = formatter.format(product_data)
                    export_result.add_output(format_name, output)
                except Exception as e:
                    export_result.add_error(format_name, str(e))
        
        return export_result

class CSVFormatter:
    def format(self, product_data: ProductData) -> str:
        """Format product data as CSV"""
        # Flatten nested JSON structure for CSV
        flattened = self.flatten_product_data(product_data)
        
        # Create CSV with proper headers
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=flattened.keys())
        writer.writeheader()
        writer.writerow(flattened)
        
        return csv_buffer.getvalue()
    
    def flatten_product_data(self, data: ProductData) -> Dict[str, Any]:
        """Flatten nested structure for CSV export"""
        flattened = {}
        
        # Product info
        flattened.update({
            'product_name': data.product_info.name,
            'manufacturer': data.product_info.manufacturer,
            'category': data.product_info.category
        })
        
        # Technical specs (flatten with prefixes)
        if data.technical_specifications.thermal_properties:
            thermal = data.technical_specifications.thermal_properties
            if thermal.conductivity:
                flattened['thermal_conductivity_value'] = thermal.conductivity.value
                flattened['thermal_conductivity_unit'] = thermal.conductivity.unit
                flattened['thermal_conductivity_confidence'] = thermal.conductivity.confidence
        
        return flattened
```

---

## 🚀 Implementation Roadmap

### 📅 **Phase 1: Foundation (Weeks 1-2)**
1. ✅ **Enhanced PDF Parser**
   - Implement multi-tool extraction pipeline
   - Add OCR fallback system
   - Create layout detection system

2. ✅ **Hungarian Text Processing**
   - Comprehensive encoding map
   - OCR error correction
   - Text validation system

### 📅 **Phase 2: Extraction Enhancement (Weeks 3-4)**
1. ✅ **Section Detection**
   - Pattern-based section identification
   - Header classification system
   - Content organization

2. ✅ **Advanced Table Extraction**
   - Multiple table detection methods
   - Quality assessment system
   - Table formatting pipeline

### 📅 **Phase 3: Quality Control (Weeks 5-6)**
1. ✅ **Validation System**
   - Completeness checking
   - Cross-reference verification
   - Human review workflow

2. ✅ **Output Standards**
   - JSON schema implementation
   - Multi-format export system
   - Validation rules engine

### 📅 **Phase 4: Integration & Testing (Weeks 7-8)**
1. ✅ **System Integration**
   - Connect all components
   - End-to-end testing
   - Performance optimization

2. ✅ **Production Deployment**
   - Docker containerization
   - Monitoring and logging
   - Documentation completion

---

## 📊 Success Metrics

### 🎯 **Quality Targets**
- **Extraction Accuracy**: 95%+ for technical specifications
- **Section Detection**: 90%+ correct identification
- **Table Extraction**: 85%+ complete data capture
- **Hungarian Text**: 99%+ character accuracy
- **Human Review Rate**: <15% of documents

### ⚡ **Performance Targets**
- **Processing Speed**: <30 seconds per PDF
- **Memory Usage**: <2GB per document
- **Throughput**: 100+ PDFs per hour
- **Availability**: 99.9% uptime

This comprehensive development plan addresses all your requirements while building on the existing foundation. The modular approach ensures that each component can be developed and tested independently while maintaining integration with the current system.