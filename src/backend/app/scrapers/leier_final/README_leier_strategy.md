# LEIER Scraper Strategy & Implementation

This document outlines the comprehensive scraping strategy for LEIER Hungary based on their website structure and priorities.

## 🎯 **Target Analysis**

### Primary Entry Point
- **Main URL:** `https://www.leier.hu/hu/letoltheto-dokumentumok`
- **Website Structure:** Well-organized with clear navigation patterns
- **Access Level:** No significant restrictions identified

### Priority Matrix

#### High Priority 🔴
- **Downloadable Documents Section** (`/letoltheto-dokumentumok`)
  - Technical datasheets
  - Installation guides
  - Product specifications
  - CAD files and technical drawings

#### Medium Priority 🟡
- **Product Calculators and Pricing**
  - Cost estimation tools
  - Calculator data extraction
  - Pricing information (where available)

#### Low Priority 🟢
- **Prefab House Designs**
  - Specialized market segment
  - Limited general applicability

## 🏗️ **Architecture Overview**

The LEIER scraper follows the proven BrightData MCP architecture established in the ROCKWOOL implementation:

```
LEIER Scraper Architecture
├── leier_documents_scraper.py    # Main document scraper (High Priority)
├── leier_calculator_scraper.py   # Calculator/pricing scraper (Medium Priority)
├── leier_categories_scraper.py   # Category navigation handler
└── README_leier_strategy.md      # This strategy document
```

## 📊 **Product Categories Analysis**

LEIER offers 24+ product categories including:

### Construction Materials
- Concrete products
- Masonry elements  
- Roofing materials
- Insulation systems

### Building Systems
- Prefabricated elements
- Complete building solutions
- Specialized construction products

### Tools & Accessories
- Installation accessories
- Calculation tools
- Technical support materials

## 🔧 **Technical Implementation**

### 1. **Document Scraper** (High Priority)
```python
# Primary targets:
TARGET_URLS = {
    'main_documents': 'https://www.leier.hu/hu/letoltheto-dokumentumok',
    'technical_docs': 'https://www.leier.hu/hu/muszaki-dokumentumok',
    'product_catalogs': 'https://www.leier.hu/hu/termek-katalogusok'
}

# Expected document types:
DOCUMENT_TYPES = [
    'PDF',  # Technical datasheets, catalogs
    'CAD',  # Technical drawings  
    'XLS',  # Calculation sheets
    'DOC'   # Installation guides
]
```

### 2. **Calculator Scraper** (Medium Priority)
```python
# Calculator endpoints:
CALCULATOR_URLS = {
    'cost_estimation': 'https://www.leier.hu/hu/kalkulatorok',
    'material_calculator': 'https://www.leier.hu/hu/anyagmennyseg-szamolo',
    'pricing_tools': 'https://www.leier.hu/hu/arkalkulatorok'
}
```

### 3. **Navigation Strategy**
```python
# Category navigation pattern:
CATEGORY_PATTERN = {
    'base_path': '/hu/termekek/',
    'subcategory_selector': '.product-category-item',
    'document_selector': '.document-download-link',
    'pagination_selector': '.pagination-next'
}
```

## 🚀 **Scraping Methodology**

### Phase 1: Document Discovery (High Priority)
1. **Entry Point Analysis**
   - Parse main documents page structure
   - Identify all category links
   - Map document types and locations

2. **Category Traversal**
   - Navigate through 24+ categories systematically
   - Extract all document download links
   - Maintain category-to-document mapping

3. **Document Download**
   - Concurrent PDF/CAD file downloads
   - Smart duplicate detection
   - Organized file storage by category

### Phase 2: Calculator Integration (Medium Priority)
1. **Calculator Detection**
   - Identify interactive calculator tools
   - Extract calculation parameters
   - Capture pricing formulas

2. **Data Extraction**
   - Scrape cost estimation tools
   - Extract material calculators
   - Capture pricing matrices

### Phase 3: Quality Assurance
1. **Validation**
   - Verify document integrity
   - Validate download completeness
   - Cross-reference categories

2. **Optimization**
   - Performance tuning
   - Error handling enhancement
   - Duplicate prevention

## 📁 **Storage Organization**

```
downloads/leier_materials/
├── technical_datasheets/
│   ├── concrete_products/
│   ├── masonry_elements/
│   ├── roofing_materials/
│   └── insulation_systems/
├── installation_guides/
├── cad_files/
├── calculators/
│   ├── cost_estimation/
│   └── material_calculators/
└── pricing_data/
    ├── current_pricelists/
    └── calculator_parameters/
```

## 🔧 **Configuration**

### Environment Variables
```bash
# LEIER specific configuration
LEIER_BASE_URL=https://www.leier.hu
LEIER_DOCUMENTS_PATH=/hu/letoltheto-dokumentumok
LEIER_CALCULATORS_PATH=/hu/kalkulatorok

# BrightData MCP configuration (inherited)
BRIGHTDATA_API_TOKEN=your_token_here
ANTHROPIC_API_KEY=your_key_here
```

### Scraper Parameters
```python
SCRAPER_CONFIG = {
    'max_concurrent_downloads': 5,
    'retry_attempts': 3,
    'timeout_seconds': 60,
    'respect_robots_txt': True,
    'rate_limit_delay': 1.0  # seconds between requests
}
```

## 📈 **Success Metrics**

### Document Collection Goals
- **Target:** 500+ technical documents
- **Categories:** Complete coverage of 24+ product categories
- **File Types:** PDF, CAD, XLS, DOC comprehensive collection

### Quality Indicators
- **Completion Rate:** >95% successful downloads
- **Categorization:** 100% proper organization
- **Duplicate Management:** <5% duplicate rate

## 🔄 **Integration with Existing Infrastructure**

### Database Integration
- Leverage existing PostgreSQL schema
- Extend Product model for LEIER specifics
- Maintain ChromaDB vector embeddings

### AI Agent Integration
- BrightData MCP compatibility
- Claude AI content analysis
- RAG search capabilities

### API Endpoints
- RESTful LEIER product endpoints
- Search and filter capabilities
- Document download proxying

## 🔍 **Next Steps**

1. **Immediate Implementation**
   - Deploy `leier_documents_scraper.py`
   - Test document discovery and downloads
   - Validate category navigation

2. **Medium-term Goals**
   - Implement calculator scrapers
   - Integrate pricing data
   - Enhance search capabilities

3. **Long-term Vision**
   - Multi-manufacturer support
   - Unified product comparison
   - Advanced analytics and reporting

## 🛡️ **Risk Mitigation**

### Technical Risks
- **Mitigation:** Robust error handling and fallback mechanisms
- **Monitoring:** Comprehensive logging and alerts
- **Recovery:** Automatic retry logic with exponential backoff

### Legal/Ethical Considerations
- **Compliance:** Respect robots.txt and rate limits
- **Attribution:** Proper source attribution
- **Usage:** Educational and research purposes

---

*This strategy document provides the foundation for comprehensive LEIER product data collection, ensuring systematic coverage of all document types and categories while maintaining high quality standards.* 