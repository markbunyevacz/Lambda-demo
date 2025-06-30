# Adaptive PDF Extraction Architecture
## Dynamic Content Processing with Vector PostgreSQL Integration

## 🎯 Problem Statement

**PDF Content Challenges:**
- ✅ **Unpredictable data structures** - New specs, missing fields, format changes
- ✅ **Variable units of measure** - Metric/Imperial, different notations
- ✅ **Dynamic additional information** - New technical data, updated standards
- ✅ **Layout variations** - Different PDF templates, multi-language content
- ✅ **Critical data variations** - Vital specifications that appear/disappear

**Current Rigid Approach Limitations:**
- ❌ Fixed regex patterns break with format changes
- ❌ Predefined data structures can't accommodate new fields
- ❌ No semantic understanding of content context
- ❌ Manual pattern updates required for each variation

---

## 🧠 AI-Powered Adaptive Solution

### **Core Architecture: Hybrid AI + Vector Database**

```python
# Adaptive Processing Pipeline
PDF → AI Content Understanding → Dynamic Schema Generation → Vector Storage
  ↓           ↓                      ↓                        ↓
Text        Semantic              Flexible JSON           Semantic Search
Extract     Analysis              Schema                  + Structured Query
```

### **Phase 1: AI-Powered Content Understanding**

#### **LLM-Based Technical Specification Extraction**
```python
class AdaptivePDFExtractor:
    def __init__(self):
        self.llm_client = OpenAI()  # or Claude, etc.
        self.vector_db = VectorPostgreSQL()
        
    def extract_with_ai_understanding(self, pdf_text: str, filename: str):
        """Use LLM to understand and extract ANY technical data"""
        
        prompt = f"""
        Analyze this ROCKWOOL technical document and extract ALL available data.
        Be flexible - extract any technical specifications, even if not in standard format.
        
        Document: {filename}
        Content: {pdf_text[:4000]}...
        
        Extract as JSON with these principles:
        1. Identify ALL technical specifications (thermal, fire, density, etc.)
        2. Preserve original units and notation
        3. Capture ANY additional technical information
        4. Note confidence level for each extracted field
        5. Handle multiple languages/formats gracefully
        
        Return flexible JSON structure that adapts to content found.
        """
        
        return self.llm_client.complete(prompt)
```

#### **Dynamic Schema Generation**
```python
def generate_flexible_schema(self, extracted_data: dict) -> dict:
    """Generate schema that adapts to actual content found"""
    
    schema = {
        "extraction_metadata": {
            "pdf_filename": str,
            "extraction_date": str,
            "extraction_confidence": float,
            "content_language": str,
            "document_version": str
        },
        "technical_specifications": {
            # Dynamic fields based on actual content
            **self.categorize_technical_data(extracted_data),
            "additional_specs": {}  # Catch-all for new/unexpected data
        },
        "measurement_units": {
            # Preserve original units for each measurement
            **self.extract_units_mapping(extracted_data)
        },
        "contextual_information": {
            # Additional context that might be important
            "application_notes": str,
            "installation_requirements": str,
            "compatibility_info": str,
            "regulatory_compliance": []
        }
    }
    
    return schema
```

---

## 🗄️ Vector PostgreSQL Integration

### **Hybrid Storage Architecture**

#### **Table Structure: Flexible + Semantic**
```sql
-- Enhanced Product table with vector capabilities
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category_id INTEGER,
    manufacturer_id INTEGER,
    
    -- Flexible JSON for structured data
    technical_specs JSONB,           -- Dynamic technical specifications
    extraction_metadata JSONB,       -- Extraction context and confidence
    measurement_units JSONB,         -- Original units preservation
    
    -- Vector embeddings for semantic search
    content_embedding vector(1536),  -- Full content semantic embedding
    specs_embedding vector(768),     -- Technical specs only embedding
    
    -- Traditional fields maintained
    price DECIMAL(10,2),
    currency VARCHAR(3),
    source_url TEXT,
    
    -- Indexes for hybrid search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_products_technical_specs_gin 
ON products USING GIN (technical_specs);

CREATE INDEX idx_products_content_embedding 
ON products USING ivfflat (content_embedding vector_cosine_ops);

CREATE INDEX idx_products_specs_embedding 
ON products USING ivfflat (specs_embedding vector_cosine_ops);
```

#### **Dynamic JSONB Schema Examples**
```json
{
  "technical_specs": {
    "thermal_properties": {
      "conductivity": {
        "value": "0.037",
        "unit": "W/mK", 
        "confidence": 0.95,
        "source_location": "page 2, table 1"
      },
      "r_values": {
        "50mm": {"value": "1.35", "unit": "m²K/W", "confidence": 0.90},
        "100mm": {"value": "2.70", "unit": "m²K/W", "confidence": 0.90}
      }
    },
    "fire_properties": {
      "classification": {
        "value": "A1",
        "standard": "EN 13501-1",
        "confidence": 0.98
      },
      "reaction_to_fire": {
        "value": "Non-combustible",
        "confidence": 0.85
      }
    },
    "physical_properties": {
      "density": {
        "value": "140",
        "unit": "kg/m³",
        "confidence": 0.92
      },
      "compressive_strength": {
        "value": "60",
        "unit": "kPa",
        "confidence": 0.88
      }
    },
    // Dynamic section for unexpected/new specifications
    "additional_specifications": {
      "water_vapor_resistance": {
        "value": "1.5",
        "unit": "MNs/g",
        "confidence": 0.75,
        "note": "Found in extended specifications section"
      },
      "acoustic_properties": {
        "sound_absorption": {
          "value": "0.85",
          "unit": "NRC",
          "frequency": "500-2000 Hz",
          "confidence": 0.70
        }
      }
    }
  },
  "measurement_units": {
    "thermal_conductivity": "W/mK",
    "density": "kg/m³", 
    "thickness": "mm",
    "r_value": "m²K/W",
    "compressive_strength": "kPa"
  },
  "contextual_information": {
    "application_areas": ["Flat roofs", "Industrial buildings"],
    "temperature_range": "-200°C to +750°C",
    "installation_notes": "Requires vapor barrier in humid conditions",
    "certifications": ["CE marking", "KEYMARK", "EPD"]
  }
}
```

---

## 🔧 Implementation Architecture

### **Adaptive Processing Pipeline**

#### **Stage 1: Multi-Modal Content Extraction**
```python
class FlexibleContentExtractor:
    def extract_all_content(self, pdf_path: Path) -> ContentBundle:
        """Extract everything - text, tables, images, metadata"""
        
        return ContentBundle(
            raw_text=self.extract_raw_text(pdf_path),
            structured_tables=self.extract_tables(pdf_path),
            images_with_text=self.extract_image_text(pdf_path),
            document_metadata=self.extract_pdf_metadata(pdf_path),
            page_layouts=self.analyze_page_structure(pdf_path)
        )
```

#### **Stage 2: AI-Powered Semantic Analysis**
```python
class SemanticContentAnalyzer:
    def analyze_technical_content(self, content: ContentBundle) -> TechnicalAnalysis:
        """Use AI to understand technical content semantically"""
        
        # Multi-pass analysis for different aspects
        analyses = {
            'thermal_properties': self.analyze_thermal_data(content),
            'fire_safety': self.analyze_fire_safety_data(content),
            'physical_properties': self.analyze_physical_properties(content),
            'dimensional_data': self.analyze_dimensional_data(content),
            'application_context': self.analyze_application_context(content),
            'additional_specs': self.discover_additional_specifications(content)
        }
        
        return self.synthesize_analysis(analyses)
    
    def discover_additional_specifications(self, content: ContentBundle) -> dict:
        """AI-powered discovery of unexpected/new technical data"""
        
        prompt = f"""
        Analyze this technical document for ANY specifications not covered by standard categories.
        Look for:
        - New technical properties
        - Environmental data
        - Acoustic properties  
        - Chemical resistance
        - Sustainability metrics
        - Any other measurable characteristics
        
        Content: {content.raw_text}
        Tables: {content.structured_tables}
        
        Return JSON with discovered specifications, values, units, and confidence.
        """
        
        return self.llm_client.extract_structured_data(prompt)
```

#### **Stage 3: Vector Embedding Generation**
```python
class VectorEmbeddingGenerator:
    def generate_hybrid_embeddings(self, extracted_data: dict) -> EmbeddingSet:
        """Generate multiple embeddings for different search patterns"""
        
        return EmbeddingSet(
            # Full content embedding for general semantic search
            full_content=self.embed_text(extracted_data['full_content']),
            
            # Technical specs only for precise technical queries
            technical_specs=self.embed_text(
                self.serialize_technical_specs(extracted_data['technical_specs'])
            ),
            
            # Application context for use-case matching
            application_context=self.embed_text(extracted_data['contextual_information']),
            
            # Problem-solution embeddings for recommendations
            problem_solution=self.embed_text(
                self.create_problem_solution_text(extracted_data)
            )
        )
```

#### **Stage 4: Adaptive Database Storage**
```python
class AdaptiveDatabaseStorage:
    def store_flexible_product_data(self, product_data: dict, embeddings: EmbeddingSet):
        """Store data with flexible schema adaptation"""
        
        # Normalize and validate technical specifications
        normalized_specs = self.normalize_technical_specs(
            product_data['technical_specs']
        )
        
        # Update database with flexible JSONB structure
        query = """
        INSERT INTO products (
            name, category_id, manufacturer_id,
            technical_specs, extraction_metadata, measurement_units,
            content_embedding, specs_embedding,
            price, currency, source_url
        ) VALUES (
            %(name)s, %(category_id)s, %(manufacturer_id)s,
            %(technical_specs)s, %(extraction_metadata)s, %(measurement_units)s,
            %(content_embedding)s, %(specs_embedding)s,
            %(price)s, %(currency)s, %(source_url)s
        )
        ON CONFLICT (name, manufacturer_id) 
        DO UPDATE SET
            technical_specs = EXCLUDED.technical_specs || products.technical_specs,
            extraction_metadata = EXCLUDED.extraction_metadata,
            content_embedding = EXCLUDED.content_embedding,
            updated_at = NOW()
        """
        
        return self.execute_with_vector_params(query, product_data, embeddings)
```

---

## 🔍 Advanced Query Capabilities

### **Hybrid Search: Structured + Semantic**

#### **Technical Specification Queries**
```python
class HybridProductSearch:
    def search_technical_specs(self, query: str, filters: dict = None):
        """Combine structured JSON queries with semantic search"""
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Hybrid SQL query
        sql = """
        SELECT 
            p.*,
            p.content_embedding <=> %(query_embedding)s as semantic_similarity,
            p.technical_specs,
            ts_rank(to_tsvector(p.technical_specs::text), plainto_tsquery(%(query)s)) as text_rank
        FROM products p
        WHERE 1=1
        """
        
        # Add structured filters
        if filters.get('thermal_conductivity_max'):
            sql += """
            AND (p.technical_specs->'thermal_properties'->'conductivity'->>'value')::float 
                <= %(thermal_conductivity_max)s
            """
        
        if filters.get('fire_classification'):
            sql += """
            AND p.technical_specs->'fire_properties'->'classification'->>'value' 
                = %(fire_classification)s
            """
        
        # Add semantic similarity
        sql += """
        ORDER BY 
            (semantic_similarity * 0.4 + text_rank * 0.6) DESC,
            p.technical_specs->'extraction_metadata'->>'extraction_confidence' DESC
        LIMIT 20
        """
        
        return self.execute_hybrid_query(sql, query, query_embedding, filters)
    
    def find_similar_products(self, product_id: int, similarity_threshold: float = 0.8):
        """Find products with similar technical characteristics"""
        
        sql = """
        WITH target_product AS (
            SELECT content_embedding, technical_specs 
            FROM products WHERE id = %(product_id)s
        )
        SELECT 
            p.*,
            p.content_embedding <=> t.content_embedding as similarity,
            p.technical_specs
        FROM products p, target_product t
        WHERE p.id != %(product_id)s
        AND p.content_embedding <=> t.content_embedding < %(threshold)s
        ORDER BY similarity ASC
        LIMIT 10
        """
        
        return self.execute_vector_query(sql, product_id, 1.0 - similarity_threshold)
```

#### **Natural Language Technical Queries**
```sql
-- Example: "Find insulation with thermal conductivity below 0.04 W/mK and fire rating A1"
SELECT 
    name,
    technical_specs->'thermal_properties'->'conductivity' as thermal_conductivity,
    technical_specs->'fire_properties'->'classification' as fire_rating,
    content_embedding <=> $1 as semantic_match
FROM products
WHERE 
    (technical_specs->'thermal_properties'->'conductivity'->>'value')::float < 0.04
    AND technical_specs->'fire_properties'->'classification'->>'value' = 'A1'
ORDER BY semantic_match ASC
LIMIT 10;
```

---

## 🚀 Real-Time Processing Capabilities

### **Live PDF Processing Pipeline**

#### **Continuous Adaptation System**
```python
class ContinuousAdaptationSystem:
    def process_new_pdf(self, pdf_path: Path) -> ProcessingResult:
        """Process new PDF with continuous learning"""
        
        # Extract content adaptively
        content = self.flexible_extractor.extract_all_content(pdf_path)
        
        # AI-powered analysis with schema evolution
        analysis = self.semantic_analyzer.analyze_with_schema_evolution(content)
        
        # Update schema if new patterns detected
        if analysis.new_specifications_found:
            self.schema_manager.evolve_schema(analysis.new_specifications)
            
        # Generate embeddings
        embeddings = self.embedding_generator.generate_hybrid_embeddings(analysis)
        
        # Store with confidence tracking
        result = self.adaptive_storage.store_with_confidence_tracking(
            analysis, embeddings
        )
        
        # Update extraction patterns for future processing
        self.pattern_learner.learn_from_extraction(content, analysis, result)
        
        return result
    
    def handle_extraction_uncertainty(self, uncertain_data: dict) -> dict:
        """Handle uncertain extractions with multiple approaches"""
        
        approaches = [
            self.llm_cross_validation(uncertain_data),
            self.pattern_matching_validation(uncertain_data), 
            self.table_structure_analysis(uncertain_data),
            self.context_based_inference(uncertain_data)
        ]
        
        return self.confidence_weighted_merge(approaches)
```

---

## 📊 Expected Performance & Benefits

### **Flexibility Gains**
| Capability | Rigid Regex Approach | AI-Adaptive Approach |
|------------|---------------------|---------------------|
| **New PDF Formats** | ❌ Manual pattern updates | ✅ Automatic adaptation |
| **Missing Data Fields** | ❌ Extraction failure | ✅ Graceful degradation |
| **New Technical Specs** | ❌ Undetected | ✅ AI discovery & learning |
| **Unit Variations** | ❌ Pattern mismatch | ✅ Semantic understanding |
| **Multi-language PDFs** | ❌ Language-specific patterns | ✅ Context-aware processing |
| **Content Evolution** | ❌ Requires redevelopment | ✅ Continuous learning |

### **Search & Query Benefits**
- **🔍 Natural Language Queries**: "Find roof insulation under 2000 HUF/m² with A1 fire rating"
- **📊 Semantic Similarity**: Discover products with similar technical profiles
- **🎯 Precision Filtering**: Combine exact technical criteria with semantic search
- **📈 Confidence Scoring**: Know how reliable each extracted specification is

### **Future-Proof Architecture**
- **📄 New Document Types**: Automatically adapt to certificates, test reports, guides
- **🔧 New Technical Standards**: AI discovers and learns new specification categories
- **🌍 International Expansion**: Handle different languages and regional standards
- **📱 API Integration**: Vector search API for advanced product recommendations

---

## 🎯 Implementation Priority

### **Phase 1: Core Adaptive System** (Week 1)
1. AI-powered content extraction with LLM
2. Flexible JSONB schema in PostgreSQL  
3. Basic vector embedding generation
4. Confidence-based data storage

### **Phase 2: Vector Integration** (Week 2)  
1. pgvector setup and optimization
2. Hybrid search implementation
3. Semantic similarity queries
4. Performance tuning

### **Phase 3: Continuous Learning** (Week 3)
1. Schema evolution detection
2. Pattern learning from extractions  
3. Confidence improvement algorithms
4. Real-time processing pipeline

**Ready to implement this adaptive, AI-powered solution?** This approach will handle any PDF content variations while building a semantically searchable technical database. 