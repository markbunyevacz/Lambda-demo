"""
Pytest configuration and shared fixtures for Lambda.hu tests.

This module provides common test fixtures and configuration
for both unit and integration tests.
"""

import pytest
import tempfile
import os
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock

# Import our application components
from app.main import app
from app.database import Base, get_db
from app.config.settings import AppSettings
from app.services.pdf_processor import PDFProcessor


@pytest.fixture
def test_settings() -> AppSettings:
    """Create test-specific settings."""
    return AppSettings(
        title="Test Lambda.hu API",
        description="Test API",
        version="0.1.0-test",
        debug=True,
        environment="testing",
        database={"url": "sqlite:///:memory:", "echo_sql": False},
        redis={"host": "localhost", "port": 6379, "db": 1},
        chroma={"host": "localhost", "port": 8001, "collection_name": "test_collection"},
        cors={"allowed_origins": ["*"]},
        ai={
            "model_name": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "temperature": 0.0,
        },
    )


@pytest.fixture
def test_db_engine(test_settings):
    """Create a test database engine."""
    engine = create_engine(
        test_settings.database.url,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(test_db_session):
    """Create a test client for FastAPI."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_chroma_client():
    """Create a mock ChromaDB client for testing."""
    mock_client = Mock()
    mock_collection = Mock()
    
    # Mock collection methods
    mock_collection.query.return_value = {
        'documents': [['Test document content']],
        'metadatas': [[{
            'product_id': '1',
            'name': 'Test Product',
            'category': 'Test Category',
            'doc_type': 'Termék'
        }]],
        'distances': [[0.1]]
    }
    mock_collection.count.return_value = 1
    
    mock_client.get_collection.return_value = mock_collection
    mock_client.heartbeat.return_value = True
    
    return mock_client


@pytest.fixture
def pdf_processor():
    """Create a PDFProcessor instance for testing."""
    return PDFProcessor()


@pytest.fixture
def sample_pdf_content():
    """Sample PDF text content for testing."""
    return '''
ROCKWOOL FRONTROCK S
Homlokzati hőszigetelő lemez

Műszaki adatok:
Hővezetési tényező (λD): 0,036 W/mK
Testsűrűség: 140 kg/m³
Tűzvédelmi osztály: A1 (nem éghető)
Nyomószilárdság 10%-os összenyomódásnál: ≥ 40 kPa
Olvadáspont: > 1000°C

Alkalmazási területek:
- Homlokzati hőszigetelő kompozit rendszerek (HISZ/ETICS)
- Kétféle falazat közötti hőszigetelés
- Vakolható homlokzati rendszerek

Előnyök:
- Nem éghető (A1 tűzvédelmi osztály)
- Víztaszító, páraáteresztő
- Hangelnyelő tulajdonság
- Stabil hőszigetelő képesség
'''


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "ROCKWOOL FRONTROCK S",
        "description": "Homlokzati hőszigetelő lemez nem éghető kőzetgyapotból",
        "category_id": 1,
        "manufacturer_id": 1,
        "technical_specs": {
            "thermal_conductivity": {"value": "0.036", "unit": "W/mK"},
            "density": {"value": "140", "unit": "kg/m³"},
            "fire_classification": {"value": "A1"},
            "compressive_strength": {"value": "40", "unit": "kPa"}
        }
    }


@pytest.fixture
def sample_category_data():
    """Sample category data for testing."""
    return {
        "name": "Hőszigetelő anyagok",
        "description": "Kőzetgyapot és egyéb hőszigetelő termékek",
        "parent_id": None
    }


@pytest.fixture
def sample_manufacturer_data():
    """Sample manufacturer data for testing."""
    return {
        "name": "ROCKWOOL",
        "description": "Vezető kőzetgyapot gyártó",
        "website": "https://www.rockwool.com/hu",
        "country": "Dánia"
    }


@pytest.fixture
def temp_file():
    """Create a temporary file for testing file operations."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_ai_response():
    """Mock AI response for PDF processing tests."""
    return {
        "product_identification": {
            "product_name": "ROCKWOOL FRONTROCK S"
        },
        "technical_specifications": {
            "thermal_conductivity": {"value": "0.036", "unit": "W/mK"},
            "density": {"value": "140", "unit": "kg/m³"},
            "fire_classification": {"value": "A1"}
        },
        "extraction_metadata": {
            "confidence_score": 0.95
        }
    }


# Test markers configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_ai: marks tests that require AI service"
    )


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Add any cleanup logic here if needed
    pass