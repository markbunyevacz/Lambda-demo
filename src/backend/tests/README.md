# Lambda.hu Backend Tests

This directory contains comprehensive tests for the Lambda.hu AI system backend.

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── run_tests.py             # Test runner script with various options
├── fixtures/                # Test data and sample files
│   └── sample_pdf_content.txt
├── unit/                    # Unit tests for individual components
│   └── test_pdf_processor.py
└── integration/             # Integration tests for complete workflows
    └── test_pdf_processing_pipeline.py
```

## 🧪 Test Categories

### Unit Tests
- **PDFProcessor Service**: Tests text extraction and formatting logic
- **Configuration System**: Tests settings validation and loading
- **Database Models**: Tests ORM relationships and validation
- **Utility Functions**: Tests helper functions in isolation

### Integration Tests
- **PDF Processing Pipeline**: End-to-end tests from PDF content to search results
- **API Endpoints**: Tests complete request/response cycles
- **Database Operations**: Tests with real database transactions
- **Search Functionality**: Tests ChromaDB integration with mocked services

## 🚀 Running Tests

### Using the Test Runner Script

```bash
cd src/backend

# Run all tests
python run_tests.py all

# Run only unit tests
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run tests with coverage report
python run_tests.py coverage

# Run fast tests (excluding slow integration tests)
python run_tests.py fast

# Run PDF processing tests specifically
python run_tests.py pdf

# Run code quality checks
python run_tests.py lint

# Auto-fix code quality issues
python run_tests.py fix
```

### Using Pytest Directly

```bash
cd src/backend

# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/unit/test_pdf_processor.py

# Run tests matching a pattern
poetry run pytest -k "pdf"

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run tests excluding slow ones
poetry run pytest -m "not slow"

# Run only integration tests
poetry run pytest -m integration

# Run only unit tests
poetry run pytest -m unit
```

## 🏷️ Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_ai` - Tests requiring AI services

## 🔧 Test Fixtures

### Database Fixtures
- `test_db_engine` - In-memory SQLite database for testing
- `test_db_session` - Database session for tests
- `test_client` - FastAPI test client with database override

### Mock Fixtures
- `mock_chroma_client` - Mocked ChromaDB client
- `mock_ai_response` - Mocked AI service responses

### Data Fixtures
- `sample_pdf_content` - Sample PDF text content
- `sample_product_data` - Sample product data for testing
- `sample_category_data` - Sample category data
- `sample_manufacturer_data` - Sample manufacturer data

## 📊 Coverage Reports

After running tests with coverage:

```bash
# View HTML coverage report
open htmlcov/index.html

# View terminal coverage summary
poetry run pytest --cov=app --cov-report=term-missing
```

### Coverage Targets
- **Overall**: > 80%
- **Core Services**: > 90%
- **API Endpoints**: > 85%
- **Critical Functions**: > 95%

## 🧩 Test Examples

### Testing PDF Processing
```python
def test_pdf_extraction(pdf_processor, sample_pdf_content):
    specs = pdf_processor.extract_specs_from_pdf_content(sample_pdf_content)
    assert "Hővezetési tényező" in specs
    assert "0,037 W/mK" in specs["Hővezetési tényező"]
```

### Testing API Endpoints
```python
def test_search_endpoint(test_client, mock_chroma_client):
    with patch('app.main.get_chroma_client', return_value=mock_chroma_client):
        response = test_client.post("/search/rag", json={"query": "test"})
        assert response.status_code == 200
```

### Testing Database Operations
```python
def test_product_creation(test_db_session, sample_product_data):
    product = Product(**sample_product_data)
    test_db_session.add(product)
    test_db_session.commit()
    assert product.id is not None
```

## 🐛 Debugging Tests

### Running Individual Tests
```bash
# Run single test method
poetry run pytest tests/unit/test_pdf_processor.py::TestPDFProcessor::test_extract_thermal_conductivity_variations -v

# Run with pdb debugger
poetry run pytest --pdb tests/unit/test_pdf_processor.py::TestPDFProcessor::test_extract_thermal_conductivity_variations
```

### Test Output and Logging
```bash
# Show print statements
poetry run pytest -s

# Show logging output
poetry run pytest --log-cli-level=DEBUG
```

## 🔄 Continuous Integration

Tests run automatically in GitHub Actions on:
- Every push to `main` and `develop` branches
- Every pull request
- Nightly builds

### CI Test Commands
```yaml
# In .github/workflows/ci.yml
- name: Run tests
  run: poetry run pytest tests/ -v --cov=app --cov-report=xml

- name: Run integration tests
  run: poetry run pytest tests/integration/ -v
```

## 📝 Writing New Tests

### Unit Test Guidelines
1. Test one function/method at a time
2. Use mocks for external dependencies
3. Test edge cases and error conditions
4. Keep tests fast and isolated

### Integration Test Guidelines
1. Test complete workflows end-to-end
2. Use real database transactions (with test data)
3. Mock external services (AI, ChromaDB)
4. Verify data flows correctly through the system

### Test Data Guidelines
1. Use realistic sample data
2. Keep test data minimal but representative
3. Store complex test data in fixtures/
4. Clean up test data after tests

## ⚠️ Common Issues

### Import Errors
```bash
# Ensure you're in the correct directory
cd src/backend

# Ensure Poetry environment is activated
poetry shell
```

### Database Errors
- Tests use in-memory SQLite by default
- Each test gets a fresh database session
- If tests fail due to database issues, check conftest.py

### Mock Issues
- ChromaDB client is mocked by default in integration tests
- AI services are mocked to avoid external API calls
- Check mock configuration in conftest.py

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)
- [Coverage.py](https://coverage.readthedocs.io/)