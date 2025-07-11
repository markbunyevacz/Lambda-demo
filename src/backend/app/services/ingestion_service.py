import logging
import os
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.processing_models import PDFExtractionResult
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.category import Category
# from app.models.processed_file_log import ProcessedFileLog
from app.processing.file_handler import FileHandler


logger = logging.getLogger(__name__)


class DataIngestionService:
    """Handles all database interactions for PDF processing results."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.file_handler = FileHandler(db_session)
        self.chroma_collection = None
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage."""
        try:
            os.environ['ANONYMIZED_TELEMETRY'] = 'False'
            os.environ['CHROMA_TELEMETRY'] = 'False'
            os.environ['CHROMA_SERVER_NOFILE'] = '1'
            
            chroma_vars_to_remove = [
                'CHROMA_SERVER_AUTHN_CREDENTIALS_FILE',
                'CHROMA_SERVER_AUTHN_PROVIDER',
                'CHROMA_SERVER_HOST',
                'CHROMA_SERVER_HTTP_PORT'
            ]
            for var in chroma_vars_to_remove:
                if var in os.environ:
                    del os.environ[var]
            
            chroma_logger = logging.getLogger('chromadb')
            chroma_logger.setLevel(logging.CRITICAL)
            
            import chromadb
            from chromadb.config import Settings
            
            self.chroma_client = chromadb.PersistentClient(
                path="./chromadb_data",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    chroma_server_nofile=True
                )
            )
            
            self.chroma_collection = (
                self.chroma_client.get_or_create_collection(
                    name="pdf_products",
                    metadata={
                        "description": "PDF product data for RAG pipeline"
                    }
                )
            )
            logger.info(
                "✅ ChromaDB initialized successfully"
            )
        except Exception as e:
            logger.info(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.chroma_collection = None

    def ingest_data(
        self, result: 'PDFExtractionResult', pdf_path_str: str
    ):
        """
        Main ingestion method that handles deduplication and database writes.
        """
        file_hash = self.file_handler.calculate_file_hash(Path(pdf_path_str))

        if self.file_handler.is_duplicate(file_hash):
            logger.info(
                "⏭️ Skipping duplicate file based on hash: %s",
                result.source_filename
            )
            return

        product_id = self.ingest_to_postgresql(result)
        if product_id:
            self.ingest_to_chromadb(result, product_id)
            self.file_handler.add_hash_to_log(file_hash)

    def ingest_to_postgresql(
        self, result: 'PDFExtractionResult'
    ) -> Optional[int]:
        """Ingests extraction result to PostgreSQL as a Product."""
        if not self.db_session:
            return None
        
        try:
            manufacturer_name = result.extraction_metadata.get(
                "manufacturer", "ROCKWOOL"
            )
            manufacturer = (
                self.db_session.query(Manufacturer)
                .filter_by(name=manufacturer_name).first()
            )
            if not manufacturer:
                manufacturer = Manufacturer(
                    name=manufacturer_name,
                    description=f"{manufacturer_name} products"
                )
                self.db_session.add(manufacturer)
                self.db_session.flush()

            category_name = self._determine_category(result.technical_specs)
            category = (
                self.db_session.query(Category)
                .filter_by(name=category_name).first()
            )
            if not category:
                category = Category(name=category_name)
                self.db_session.add(category)
                self.db_session.flush()

            def make_utf8_safe(text: str) -> str:
                if not text:
                    return ""
                return text.encode('utf-8', 'replace').decode('utf-8')

            specs = result.technical_specs or {}
            specs['source_pdf'] = make_utf8_safe(result.source_filename)

            description_text = (
                f"A {result.product_name} egy {manufacturer_name} által "
                f"gyártott {category_name.lower()} termék. A forrás: "
                f"'{result.source_filename}'."
            )

            product = Product(
                name=make_utf8_safe(result.product_name),
                description=description_text,
                full_text_content=make_utf8_safe(result.extracted_text),
                manufacturer_id=manufacturer.id,
                category_id=category.id,
                technical_specs=specs,
                price=self._extract_price_from_result(result),
                sku=self._generate_sku(result.product_name)
            )
            self.db_session.add(product)
            self.db_session.commit()
            logger.info(
                "✅ Ingested to PostgreSQL: %s (ID: %d)",
                result.product_name,
                product.id
            )
            return product.id
        except Exception as e:
            logger.error(
                "❌ PostgreSQL ingestion failed for %s: %s",
                result.product_name, e
            )
            self.db_session.rollback()
            return None

    def ingest_to_chromadb(
        self, result: 'PDFExtractionResult', product_id: Optional[int]
    ):
        """Ingests extraction result into ChromaDB for vector search."""
        if not self.chroma_collection or not product_id:
            return

        try:
            documents, metadatas, ids = self._create_chunked_documents(
                result, product_id
            )
            if not documents:
                logger.warning("No documents to ingest to ChromaDB.")
                return

            self.chroma_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(
                "✅ Ingested %d chunks to ChromaDB for product ID %d",
                len(documents),
                product_id
            )
        except Exception as e:
            logger.error(
                "❌ ChromaDB ingestion failed for product ID %d: %s",
                product_id, e
            )

    def _create_chunked_documents(
        self, result: 'PDFExtractionResult', product_id: int
    ) -> Tuple[List[str], List[Dict], List[str]]:
        """Creates chunked documents for ChromaDB ingestion."""
        base_metadata = {
            "product_id": product_id,
            "product_name": result.product_name,
            "manufacturer": result.extraction_metadata.get(
                "manufacturer", "Unknown"
            ),
            "source_pdf": result.source_filename,
            "confidence": result.confidence_score
        }

        chunks = []
        general_info = (
            f"Termék: {result.product_name}. "
            f"Gyártó: {base_metadata['manufacturer']}."
        )
        chunks.append({"text": general_info, "type": "general"})

        if result.technical_specs:
            spec_text = "Műszaki adatok: " + ", ".join(
                [f"{k}: {v}" for k, v in result.technical_specs.items()]
            )
            chunks.append({"text": spec_text, "type": "specs"})

        max_chunk_size = 1000
        text_chunks = [
            result.extracted_text[i:i + max_chunk_size]
            for i in range(0, len(result.extracted_text), max_chunk_size)
        ]
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": f"Kivonatolt szöveg (rész {i+1}): {chunk}",
                "type": "text_chunk"
            })

        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {**base_metadata, "chunk_type": chunk["type"]} for chunk in chunks
        ]
        ids = [f"prod_{product_id}_chunk_{i}" for i in range(len(chunks))]

        return documents, metadatas, ids

    def _determine_category(self, specs: Dict[str, Any]) -> str:
        if 'hővezetési' in str(specs).lower() or 'szigetelés' in str(specs).lower():
            return "Hőszigetelés"
        return "Általános"

    def _generate_sku(self, product_name: str) -> str:
        import hashlib
        name_part = "".join(filter(str.isalnum, product_name)).upper()[:8]
        name_hash = hashlib.sha1(product_name.encode()).hexdigest()[:4]
        return f"PDF-{name_part}-{name_hash}"

    def _extract_price_from_result(
        self, result: 'PDFExtractionResult'
    ) -> Optional[float]:
        price_info = result.pricing_info
        if price_info and isinstance(price_info.get('price'), (int, float)):
            return float(price_info['price'])
        return None 