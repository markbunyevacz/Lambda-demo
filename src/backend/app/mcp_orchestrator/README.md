# MCP Orchestrator - Advanced PDF Extraction System

## Overview

The MCP (Multi-Strategy, AI-Powered, Cost-Optimized) Orchestrator is a sophisticated PDF extraction system that uses multiple parallel strategies and AI-powered validation to achieve rock-solid data extraction from technical documents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Orchestrator                        │
├─────────────────────────────────────────────────────────────┤
│  Tiered Cost Optimization | AI Validation | Golden Records │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼───┐          ┌────▼───┐          ┌────▼───┐
   │ Tier 1 │          │ Tier 2 │          │ Tier 3 │
   │ Basic  │          │Validate│          │  OCR   │
   └────────┘          └────────┘          └────────┘
        │                    │                    │
   ┌────▼───┐          ┌────▼───┐          ┌────▼───┐
   │PDFPlumb│          │Cross-  │          │Tesser- │
   │PyMuPDF │          │Valid.  │          │act OCR │
   └────────┘          └────────┘          └────────┘
```

## Key Features

### 🎯 **Tiered Cost Optimization**
- **Tier 1**: Fast, cheap extraction (pdfplumber, PyMuPDF)
- **Tier 2**: Cross-validation and consensus building
- **Tier 3**: OCR escalation for difficult PDFs
- **Tier 4**: Full AI analysis (Claude native PDF)

### 🤖 **AI-Powered Validation**
- Cross-strategy consensus detection
- Intelligent conflict resolution
- Confidence scoring for each field
- Automatic quality assessment

### 📊 **Golden Record Generation**
- Merged results from multiple strategies
- Field-level confidence scores
- Completeness and consistency metrics
- Human review flags for low-confidence data

### ⚡ **Performance Optimization**
- Parallel strategy execution
- Timeout management
- Graceful fallbacks
- Resource usage tracking

## Quick Start

### Basic Usage

```python
import asyncio
from mcp_orchestrator import MCPOrchestrator

async def extract_pdf():
    orchestrator = MCPOrchestrator()
    
    golden_record = await orchestrator.extract_pdf(
        pdf_path="path/to/document.pdf",
        use_tiered_approach=True,
        max_cost_tier=3,
        timeout_seconds=120
    )
    
    print(f"Confidence: {golden_record.overall_confidence:.2f}")
    print(f"Extracted data: {golden_record.extracted_data}")

asyncio.run(extract_pdf())
```

### Demo Script

Run the included demo to see the system in action:

```bash
cd src/backend/app
python demo_mcp_orchestrator.py
```

## API Reference

### MCPOrchestrator

Main orchestrator class that coordinates the extraction process.

#### Methods

##### `extract_pdf(pdf_path, use_tiered_approach=True, max_cost_tier=4, timeout_seconds=300)`

Extract data from a PDF using the orchestrated approach.

**Parameters:**
- `pdf_path` (str): Path to the PDF file
- `use_tiered_approach` (bool): Whether to use cost-optimized tiering
- `max_cost_tier` (int): Maximum tier to escalate to (1-4)
- `timeout_seconds` (int): Overall timeout for extraction

**Returns:** `GoldenRecord` with extracted and validated data

##### `get_orchestrator_stats()`

Get performance statistics for the orchestrator.

**Returns:** Dictionary with success rates, processing times, and tier usage

### GoldenRecord

The final, merged, and validated extraction result.

#### Properties

- `extracted_data` (Dict): The merged extracted data
- `field_confidences` (Dict): Confidence information for each field
- `overall_confidence` (float): Overall confidence score (0.0-1.0)
- `completeness_score` (float): How complete the data is (0.0-1.0)
- `consistency_score` (float): How consistent across strategies (0.0-1.0)
- `requires_human_review` (bool): Whether human review is needed
- `strategies_used` (List[str]): List of strategies that were used
- `ai_adjudication_notes` (str): AI-generated notes about the process

#### Methods

##### `get_high_confidence_fields()`

Returns only fields with high confidence (>= 0.8).

##### `get_flagged_fields()`

Returns fields that need human review (low confidence or conflicts).

##### `get_confidence_level()`

Returns the overall confidence as an enum (VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW).

## Extraction Strategies

### PDFPlumberStrategy

Uses the `pdfplumber` library for text and table extraction. Best for datasheets with structured content.

- **Cost Tier**: 1 (Basic)
- **Strengths**: Excellent table extraction, understands layout
- **Timeout**: 30 seconds

### PyMuPDFStrategy

Uses PyMuPDF (fitz) for robust text extraction. Fast and reliable fallback.

- **Cost Tier**: 1 (Basic)
- **Strengths**: Fast, handles various PDF formats
- **Timeout**: 30 seconds

### OCRStrategy

Uses Tesseract OCR for image-based or low-quality PDFs.

- **Cost Tier**: 2 (Enhanced)
- **Strengths**: Works on scanned documents, image-based PDFs
- **Timeout**: 120 seconds
- **Requirements**: `tesseract-ocr` system package

### NativePDFStrategy

Uses Claude AI's native PDF analysis capabilities.

- **Cost Tier**: 4 (Premium)
- **Strengths**: Advanced AI understanding, complex document analysis
- **Timeout**: 60 seconds
- **Requirements**: Claude AI API access

## Configuration

### Strategy Configuration

Each strategy can be configured with:

```python
from mcp_orchestrator.models import ExtractionStrategy, StrategyType

config = ExtractionStrategy(
    strategy_type=StrategyType.PDFPLUMBER,
    enabled=True,
    timeout_seconds=60,
    retry_attempts=2,
    cost_tier=1
)
```

### Environment Variables

Set these environment variables for optimal performance:

```bash
# For OCR strategy
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# For AI strategy
ANTHROPIC_API_KEY=your_claude_api_key

# For logging
LOG_LEVEL=INFO
```

## FastAPI Integration

The system includes FastAPI endpoints for REST API access:

### Endpoints

#### `POST /api/v1/mcp/extract`

Extract data from a PDF file.

**Request:**
```json
{
    "pdf_path": "/path/to/file.pdf",
    "use_tiered_approach": true,
    "max_cost_tier": 3,
    "timeout_seconds": 300
}
```

**Response:**
```json
{
    "task_id": "uuid",
    "success": true,
    "confidence": 0.92,
    "completeness_score": 0.88,
    "consistency_score": 0.95,
    "requires_human_review": false,
    "strategies_used": ["pdfplumber", "pymupdf"],
    "processing_time": 4.2,
    "extracted_data": {...},
    "field_confidences": {...},
    "ai_notes": "Consensus from 2/2 strategies"
}
```

#### `POST /api/v1/mcp/extract-async`

Start PDF extraction in the background.

#### `GET /api/v1/mcp/status/{task_id}`

Get the status of a background extraction task.

#### `POST /api/v1/mcp/upload-and-extract`

Upload a PDF file and extract data in one request.

#### `GET /api/v1/mcp/stats`

Get orchestrator performance statistics.

## Installation

### Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### System Dependencies

For OCR functionality, install Tesseract:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-hun tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Performance Guidelines

### Cost Optimization

- Use `max_cost_tier=2` for routine processing
- Reserve `max_cost_tier=4` for critical documents
- Monitor tier usage with `get_orchestrator_stats()`

### Timeout Guidelines

- Basic PDFs: 60 seconds
- Complex technical documents: 120 seconds
- Large multi-page documents: 300 seconds

### Confidence Thresholds

- **>= 0.95**: Very high confidence, no review needed
- **>= 0.80**: High confidence, spot check recommended
- **>= 0.60**: Medium confidence, review important fields
- **< 0.60**: Low confidence, full human review required

## Troubleshooting

### Common Issues

#### "No text extracted via OCR"
- Check Tesseract installation
- Verify language pack installation
- Try increasing timeout for OCR strategy

#### "Strategy timeout"
- Increase timeout_seconds parameter
- Check PDF file size and complexity
- Monitor system resources

#### "Import errors"
- Verify all dependencies are installed
- Check Python path configuration
- Ensure PDF processing libraries are available

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check orchestrator statistics:

```python
stats = orchestrator.get_orchestrator_stats()
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Tier usage: {stats['tier_usage']}")
```

## Contributing

### Adding New Strategies

1. Create a new strategy class inheriting from `BaseExtractionStrategy`
2. Implement the `extract(pdf_path)` method
3. Add the strategy to the orchestrator's strategy registry
4. Update the tier configuration

### Testing

Run the test suite:

```bash
python -m pytest tests/
```

Run the demo script:

```bash
python demo_mcp_orchestrator.py
```

## License

This project is part of the Lambda.hu building materials AI system. 