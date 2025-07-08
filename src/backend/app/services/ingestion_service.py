import logging
import os
from datetime import datetime
from typing import Optional, Set, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
# JAVÍTÁS: Hiányzó import a PDFExtractionResult típushoz
from processing.real_pdf_processor import PDFExtractionResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect

from app.database import SessionLocal
from app.models.product import Product, product_category_association
from app.models.manufacturer import Manufacturer
from app.models.category import Category
from app.models.processed_file_log import ProcessedFileLog
from app.utils import clean_utf8

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Handles all database interactions for PDF processing results."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.chroma_collection = None
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage."""
        try:
            os.environ['ANONYMIZED_TELEMETRY'] = 'False'
            os.environ['CHROMA_TELEMETRY'] = 'False'
            os.environ['CHROMA_SERVER_NOFILE'] = '1'
            
            for var in ['CHROMA_SERVER_AUTHN_CREDENTIALS_FILE', 'CHROMA_SERVER_AUTHN_PROVIDER', 
                       'CHROMA_SERVER_HOST', 'CHROMA_SERVER_HTTP_PORT']:
                if var in os.environ:
                    del os.environ[var]
            
            import logging
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
            
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="pdf_products",
                metadata={"description": "PDF product data for RAG pipeline"}
            )
            logger.info("✅ ChromaDB initialized successfully in DataIngestionService")
        except Exception as e:
            logger.info(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.chroma_collection = None

    def load_processed_hashes(self) -> Set[str]:
        """Loads all file hashes from the database into a set."""
        logger.info("Loading existing file hashes from the database...")
        processed_file_hashes = set()
        if not self.db_session:
            return processed_file_hashes

        try:
            self.db_session.rollback()
            all_logs = self.db_session.query(ProcessedFileLog).all()
            for log in all_logs:
                try:
                    file_hash = log.file_hash
                    if isinstance(file_hash, bytes):
                        for encoding in ['utf-8', 'latin1', 'cp1252', 'ascii']:
                            try:
                                file_hash = file_hash.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            file_hash = file_hash.decode('utf-8', errors='replace')
                    elif isinstance(file_hash, str):
                        file_hash = file_hash.encode('utf-8', errors='replace').decode('utf-8')
                    
                    if file_hash and len(file_hash) == 64 and all(c in '0123456789abcdef' for c in file_hash.lower()):
                        processed_file_hashes.add(file_hash)
                except Exception as e:
                    logger.debug(f"Skipping corrupted hash entry: {e}")
                    continue
            logger.info(f"✅ Loaded {len(processed_file_hashes)} file hashes from database")
        except Exception as e:
            logger.error(f"Database hash loading failed: {e}")
            logger.info("Starting with empty hash set...")
        return processed_file_hashes

    def save_processed_hash(self, file_hash: str, content_hash: str, source_filename: str):
        """Saves a processed file hash to the database."""
        if self.db_session:
            try:
                existing_log = self.db_session.query(ProcessedFileLog).filter_by(file_hash=file_hash).first()
                if not existing_log:
                    log_entry = ProcessedFileLog(
                        file_hash=file_hash,
                        content_hash=content_hash,
                        source_filename=source_filename
                    )
                    self.db_session.add(log_entry)
                    self.db_session.commit()
                    logger.debug(f"✅ Hash saved to database: {file_hash[:8]}...")
            except Exception as e:
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                logger.error(f"Hash save issue: {error_msg}")
                self.db_session.rollback()

    def ingest_to_postgresql(self, result: 'PDFExtractionResult') -> Optional[int]:
        """Ingests extraction result to PostgreSQL as a Product."""
        if not self.db_session:
            return None
        
        try:
            manufacturer_name = result.extraction_metadata.get("manufacturer", "ROCKWOOL")
            manufacturer = self.db_session.query(Manufacturer).filter_by(name=manufacturer_name).first()
            if not manufacturer:
                manufacturer = Manufacturer(name=manufacturer_name, description=f"{manufacturer_name} products")
                self.db_session.add(manufacturer)
                self.db_session.flush()

            category_name = self._determine_category(result.technical_specs)
            category = self.db_session.query(Category).filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                self.db_session.add(category)
                self.db_session.flush()

            def make_utf8_safe(text: str) -> str:
                if not text: return ""
                return text.encode('utf-8', 'replace').decode('utf-8')

            # JAVÍTÁS: A forrásfájl nevét a technical_specs JSON-be tesszük
            specs = result.technical_specs or {}
            specs['source_pdf'] = make_utf8_safe(result.source_filename)

            product = Product(
                name=make_utf8_safe(result.product_name),
                description=make_utf8_safe(result.extraction_metadata.get("description", "")),
                manufacturer_id=manufacturer.id,
                category_id=category.id,
                technical_specs=specs,
                price=self._extract_price_from_result(result),
                sku=self._generate_sku(result.product_name)
            )
            self.db_session.add(product)
            self.db_session.commit()
            logger.info(f"✅ Ingested to PostgreSQL: {result.product_name} (ID: {product.id})")
            return product.id
        except Exception as e:
            logger.error(f"❌ PostgreSQL ingestion failed for {result.product_name}: {e}")
            self.db_session.rollback()
            return None

    def ingest_to_chromadb(self, result: 'PDFExtractionResult', product_id: Optional[int]):
        """Ingests extraction result into ChromaDB for vector search."""
        if not self.chroma_collection or not product_id:
            return

        try:
            documents, metadatas, ids = self._create_chunked_documents(result, product_id)
            if not documents:
                logger.warning("No documents to ingest to ChromaDB.")
                return

            self.chroma_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Ingested {len(documents)} chunks to ChromaDB for product ID {product_id}")
        except Exception as e:
            logger.error(f"❌ ChromaDB ingestion failed for product ID {product_id}: {e}")

    def _create_chunked_documents(self, result: 'PDFExtractionResult', product_id: int) -> Tuple[List[str], List[Dict], List[str]]:
        """Creates chunked documents for ChromaDB ingestion."""
        
        # This function is highly dependent on the PDFExtractionResult dataclass
        # It's kept here for now but could be moved to a utility module.
        
        base_metadata = {
            "product_id": product_id,
            "product_name": result.product_name,
            "manufacturer": result.extraction_metadata.get("manufacturer", "Unknown"),
            "source_pdf": result.source_filename,
            "confidence": result.confidence_score
        }

        # Create chunks
        chunks = []
        
        # Chunk 1: General Info
        general_info = f"Termék: {result.product_name}. Gyártó: {base_metadata['manufacturer']}."
        chunks.append({"text": general_info, "type": "general"})

        # Chunk 2: Technical Specifications
        if result.technical_specs:
            spec_text = "Műszaki adatok: " + ", ".join([f"{k}: {v}" for k, v in result.technical_specs.items()])
            chunks.append({"text": spec_text, "type": "specs"})

        # Chunk 3: Extracted Text (split if too long)
        max_chunk_size = 1000
        text_chunks = [result.extracted_text[i:i + max_chunk_size] for i in range(0, len(result.extracted_text), max_chunk_size)]
        for i, chunk in enumerate(text_chunks):
            chunks.append({"text": f"Kivonatolt szöveg (rész {i+1}): {chunk}", "type": "text_chunk"})

        # Prepare for ChromaDB
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [{**base_metadata, "chunk_type": chunk["type"]} for chunk in chunks]
        ids = [f"prod_{product_id}_chunk_{i}" for i in range(len(chunks))]

        return documents, metadatas, ids

    def _determine_category(self, specs: Dict[str, Any]) -> str:
        if 'hővezetési' in str(specs).lower() or 'szigetelés' in str(specs).lower():
            return "Hőszigetelés"
        return "Általános"

    def _generate_sku(self, product_name: str) -> str:
        # JAVÍTÁS: Egyedi hash hozzáadása az SKU-hoz a duplikáció elkerülése érdekében
        import hashlib
        name_part = "".join(filter(str.isalnum, product_name)).upper()[:8]
        # Adjunk hozzá egy rövid hashot a név alapján, hogy egyedi legyen
        name_hash = hashlib.sha1(product_name.encode()).hexdigest()[:4]
        return f"PDF-{name_part}-{name_hash}"

    def _extract_price_from_result(self, result: 'PDFExtractionResult') -> Optional[float]:
        price_info = result.pricing_info
        if price_info and isinstance(price_info.get('price'), (int, float)):
            return float(price_info['price'])
        return None 