"""
Integration tests for the PDF processing pipeline.

This module tests the complete flow from PDF content extraction
through to database storage and search functionality.
"""

import pytest
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from app.services.pdf_processor import PDFProcessor
from app.models import Product, Category, Manufacturer
from app.main import app
from app.config.settings import settings


@pytest.mark.integration
class TestPDFProcessingPipeline:
    """Integration tests for the complete PDF processing pipeline."""

    def test_pdf_processor_extracts_specifications(self, pdf_processor, sample_pdf_content):
        """Test that PDFProcessor correctly extracts technical specifications."""
        specs = pdf_processor.extract_specs_from_pdf_content(sample_pdf_content)
        
        # Verify key specifications are extracted
        assert "Hővezetési tényező" in specs
        assert specs["Hővezetési tényező"] == "0,036 W/mK"
        
        assert "Testsűrűség" in specs
        assert specs["Testsűrűség"] == "140 kg/m³"
        
        assert "Tűzvédelmi osztály" in specs
        assert specs["Tűzvédelmi osztály"] == "A1 (nem éghető)"
        
        assert "Nyomószilárdság" in specs
        assert "40" in specs["Nyomószilárdság"]

    def test_pdf_processor_formats_content(self, pdf_processor, sample_pdf_content):
        """Test that PDFProcessor correctly formats PDF content for display."""
        formatted = pdf_processor.format_pdf_content_simple(sample_pdf_content)
        
        # Verify HTML formatting is applied
        assert "<h3>" in formatted  # Headers are formatted
        assert "<div class='spec-line'>" in formatted  # Spec lines are formatted
        assert "<p>" in formatted  # Paragraphs are formatted
        
        # Verify content is preserved
        assert "ROCKWOOL FRONTROCK S" in formatted
        assert "Hővezetési tényező" in formatted

    def test_pdf_processor_handles_empty_content(self, pdf_processor):
        """Test PDFProcessor gracefully handles empty or invalid content."""
        # Test empty content
        result = pdf_processor.format_pdf_content_simple("")
        assert "Nincs elérhető tartalom" in result
        
        # Test None content
        result = pdf_processor.format_pdf_content_simple(None)
        assert "Nincs elérhető tartalom" in result
        
        # Test extraction with empty content
        specs = pdf_processor.extract_specs_from_pdf_content("")
        assert specs == {}

    def test_database_product_creation_with_pdf_data(
        self, 
        test_db_session: Session, 
        sample_product_data,
        sample_category_data,
        sample_manufacturer_data
    ):
        """Test creating a complete product with category and manufacturer."""
        # Create test category
        category = Category(**sample_category_data)
        test_db_session.add(category)
        test_db_session.commit()
        test_db_session.refresh(category)
        
        # Create test manufacturer
        manufacturer = Manufacturer(**sample_manufacturer_data)
        test_db_session.add(manufacturer)
        test_db_session.commit()
        test_db_session.refresh(manufacturer)
        
        # Create product with extracted PDF data
        product_data = sample_product_data.copy()
        product_data["category_id"] = category.id
        product_data["manufacturer_id"] = manufacturer.id
        
        product = Product(**product_data)
        test_db_session.add(product)
        test_db_session.commit()
        test_db_session.refresh(product)
        
        # Verify product was created correctly
        assert product.id is not None
        assert product.name == "ROCKWOOL FRONTROCK S"
        assert product.category_id == category.id
        assert product.manufacturer_id == manufacturer.id
        assert product.technical_specs is not None
        
        # Verify relationships work
        assert product.category.name == "Hőszigetelő anyagok"
        assert product.manufacturer.name == "ROCKWOOL"

    @patch('app.main.get_chroma_client')
    def test_search_endpoint_with_pdf_content(
        self, 
        mock_get_chroma_client,
        test_client,
        test_db_session: Session,
        sample_product_data,
        mock_chroma_client
    ):
        """Test the complete search flow with PDF-processed data."""
        # Setup mock ChromaDB client
        mock_get_chroma_client.return_value = mock_chroma_client
        
        # Create test product in database
        product = Product(**sample_product_data)
        test_db_session.add(product)
        test_db_session.commit()
        test_db_session.refresh(product)
        
        # Update mock to return our test product
        mock_chroma_client.get_collection.return_value.query.return_value = {
            'documents': [['ROCKWOOL FRONTROCK S termékadatlap']],
            'metadatas': [[{
                'product_id': str(product.id),
                'name': 'ROCKWOOL FRONTROCK S',
                'category': 'Hőszigetelő anyagok',
                'doc_type': 'Termék'
            }]],
            'distances': [[0.1]]
        }
        
        # Perform search request
        response = test_client.post(
            "/search/rag",
            json={"query": "kőzetgyapot hőszigetelés", "limit": 10}
        )
        
        # Verify search response
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "kőzetgyapot hőszigetelés"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1
        
        result = data["results"][0]
        assert result["name"] == "ROCKWOOL FRONTROCK S"
        assert result["metadata"]["product_id"] == str(product.id)
        assert result["similarity_score"] > 0

    def test_product_detail_view_with_pdf_processing(
        self,
        test_client,
        test_db_session: Session,
        sample_product_data,
        sample_pdf_content
    ):
        """Test product detail view generates HTML with processed PDF content."""
        # Create test product with full text content
        product_data = sample_product_data.copy()
        product_data["full_text_content"] = sample_pdf_content
        
        product = Product(**product_data)
        test_db_session.add(product)
        test_db_session.commit()
        test_db_session.refresh(product)
        
        # Request product detail view
        response = test_client.get(f"/products/{product.id}/view")
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        
        html_content = response.content.decode()
        
        # Verify product information is displayed
        assert "ROCKWOOL FRONTROCK S" in html_content
        assert "Hővezetési tényező" in html_content
        assert "0,036 W/mK" in html_content
        assert "A1 (nem éghető)" in html_content
        
        # Verify HTML structure
        assert "<html" in html_content
        assert "<h1>" in html_content
        assert "<h2>Műszaki adatok</h2>" in html_content

    @patch('app.main.get_chroma_client')
    def test_search_endpoint_error_handling(
        self,
        mock_get_chroma_client,
        test_client
    ):
        """Test search endpoint handles ChromaDB connection errors gracefully."""
        # Mock ChromaDB connection failure
        mock_get_chroma_client.side_effect = Exception("ChromaDB connection failed")
        
        # Perform search request
        response = test_client.post(
            "/search/rag",
            json={"query": "test query", "limit": 10}
        )
        
        # Verify error handling
        assert response.status_code == 503
        data = response.json()
        assert "Kereső szolgáltatás nem elérhető" in data["detail"]

    def test_api_endpoints_create_product_flow(
        self,
        test_client,
        test_db_session: Session,
        sample_category_data,
        sample_manufacturer_data
    ):
        """Test the complete flow of creating products via API endpoints."""
        # Create category via API
        category_response = test_client.post(
            "/categories",
            params=sample_category_data
        )
        assert category_response.status_code == 200
        category = category_response.json()
        
        # Create manufacturer (assuming endpoint exists)
        manufacturer = Manufacturer(**sample_manufacturer_data)
        test_db_session.add(manufacturer)
        test_db_session.commit()
        test_db_session.refresh(manufacturer)
        
        # Create product via API
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "category_id": category["id"],
            "manufacturer_id": manufacturer.id,
            "technical_specs": {
                "thermal_conductivity": {"value": "0.040", "unit": "W/mK"}
            }
        }
        
        product_response = test_client.post(
            "/products",
            params=product_data
        )
        assert product_response.status_code == 200
        product = product_response.json()
        
        # Verify product was created
        assert product["name"] == "Test Product"
        assert product["category_id"] == category["id"]
        assert product["manufacturer_id"] == manufacturer.id

    def test_configuration_integration(self):
        """Test that configuration system works correctly in tests."""
        # Verify settings are accessible
        assert settings.title is not None
        assert settings.database.url is not None
        assert settings.chroma.collection_name is not None
        
        # Verify AI configuration (user requirement: Haiku 3.5)
        assert "haiku" in settings.ai.model_name.lower()
        assert settings.ai.provider == "anthropic"
        assert settings.ai.temperature == 0.0


@pytest.mark.integration
@pytest.mark.slow
class TestFullPipelineIntegration:
    """End-to-end integration tests simulating real usage scenarios."""

    def test_complete_pdf_to_search_pipeline(
        self,
        test_client,
        test_db_session: Session,
        pdf_processor,
        sample_pdf_content,
        mock_chroma_client
    ):
        """Test the complete pipeline from PDF processing to search results."""
        with patch('app.main.get_chroma_client', return_value=mock_chroma_client):
            # Step 1: Process PDF content
            specs = pdf_processor.extract_specs_from_pdf_content(sample_pdf_content)
            formatted_content = pdf_processor.format_pdf_content_simple(sample_pdf_content)
            
            # Step 2: Create product with processed data
            product = Product(
                name="ROCKWOOL FRONTROCK S",
                description="Homlokzati hőszigetelő lemez",
                technical_specs={
                    "thermal_conductivity": {"value": specs.get("Hővezetési tényező", "")},
                    "fire_classification": {"value": specs.get("Tűzvédelmi osztály", "")}
                },
                full_text_content=sample_pdf_content
            )
            test_db_session.add(product)
            test_db_session.commit()
            test_db_session.refresh(product)
            
            # Step 3: Configure mock to return our product
            mock_chroma_client.get_collection.return_value.query.return_value = {
                'documents': [[sample_pdf_content]],
                'metadatas': [[{
                    'product_id': str(product.id),
                    'name': product.name,
                    'category': 'Hőszigetelő anyagok',
                    'doc_type': 'Termék'
                }]],
                'distances': [[0.05]]
            }
            
            # Step 4: Perform search
            search_response = test_client.post(
                "/search/rag",
                json={"query": "homlokzati hőszigetelés", "limit": 5}
            )
            
            # Step 5: Verify search results
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert search_data["total_results"] == 1
            
            result = search_data["results"][0]
            assert result["name"] == "ROCKWOOL FRONTROCK S"
            assert result["similarity_score"] > 0.9
            
            # Step 6: Get product detail view
            detail_response = test_client.get(f"/products/{product.id}/view")
            assert detail_response.status_code == 200
            
            html_content = detail_response.content.decode()
            assert "0,036 W/mK" in html_content  # Extracted spec
            assert "A1 (nem éghető)" in html_content  # Extracted spec
            
            # Verify pipeline preserved all data correctly
            assert product.technical_specs["thermal_conductivity"]["value"] == "0,036 W/mK"
            assert "A1" in product.technical_specs["fire_classification"]["value"]