from typing import List, Optional
import logging

from .models import ExtractionResult, GoldenRecord, ExtractionTask
from .chroma_client import ChromaClient
from ..database import SessionLocal
from ..models import Product

logger = logging.getLogger(__name__)


class AIValidator:
    """
    Validates, merges, and saves extraction results to create a final Golden Record.
    """
    def __init__(self, chroma_client: ChromaClient):
        self.chroma_client = chroma_client
        if not self.chroma_client:
            raise ValueError("ChromaClient is required for AIValidator.")

    def is_text_sufficient(self, results: List[ExtractionResult]) -> bool:
        """Checks if any extraction result has a significant amount of text."""
        if not results:
            return False
        max_len = max(
            (len(r.extracted_data.get("raw_text", ""))
             for r in results if r.success),
            default=0
        )
        return max_len > 500  # Require at least 500 chars for AI analysis

    def select_best_input(
        self, results: List[ExtractionResult], modality: str = "raw_text"
    ) -> Optional[str]:
        """Selects the best data for a given modality from results."""
        if not results:
            return None
        
        best_result = max(
            (r for r in results if
             r.success and r.extracted_data.get(modality)),
            key=lambda r: len(r.extracted_data.get(modality, "")),
            default=None
        )
        return best_result.extracted_data.get(modality) if best_result else None

    async def validate_and_merge(
        self, all_results: List[ExtractionResult], task: ExtractionTask
    ) -> GoldenRecord:
        """
        Merges results from different strategies into a single Golden Record.
        It prioritizes data from the AI-powered NativePDFStrategy.
        """
        if not any(r.success for r in all_results):
            return GoldenRecord(
                task=task,
                requires_human_review=True,
                ai_adjudication_notes="No successful extractions."
            )

        # Prioritize AI result
        ai_result_data = None
        for r in all_results:
            if r.strategy_type == "NATIVE_PDF" and r.success:
                ai_result_data = r.extracted_data
                break
        
        # Fallback to best available data if AI failed
        if not ai_result_data:
            ai_result_data = {}

        # Build the final data dictionary
        tech_specs = (
            ai_result_data.get("technical_specifications") or
            self.select_best_input(all_results, "technical_specifications") or
            {}
        )
        final_data = {
            "product_name": (
                ai_result_data.get("product_name") or
                self.select_best_input(all_results, "product_name") or
                "Unknown Product"
            ),
            "description": (
                ai_result_data.get("description") or
                self.select_best_input(all_results, "description")
            ),
            "technical_specifications": tech_specs,
            "raw_text": self.select_best_input(all_results, "raw_text"),
            "pdf_url": task.pdf_path
        }

        # Simplified confidence score
        confidence = 0.85 if ai_result_data.get("product_name") else 0.6

        return GoldenRecord(
            task=task,
            extracted_data=final_data,
            overall_confidence=confidence,
            requires_human_review=(confidence < 0.7)
        )

    async def save_golden_record(self, golden_record: GoldenRecord):
        """Saves the final Golden Record to PostgreSQL and ChromaDB."""
        if not golden_record or not golden_record.task:
            logger.error("Cannot save an invalid or task-less Golden Record.")
            return

        db = SessionLocal()
        try:
            # --- Save to PostgreSQL ---
            product_name = golden_record.get_modality(
                "product_name", "Unknown Product"
            )
            
            new_product = Product(
                name=product_name,
                manufacturer_id=1,  # Assuming ROCKWOOL
                category_id=1,      # Assuming default category
                description=golden_record.get_modality("description"),
                datasheet_url=golden_record.get_modality("pdf_url"),
                technical_specifications=golden_record.get_modality("technical_specifications"),
                raw_text=golden_record.get_modality("raw_text"),
            )
            db.add(new_product)
            db.commit()
            db.refresh(new_product)
            logger.info(
                "Saved to PostgreSQL: '%s' (ID: %s)",
                product_name, new_product.id
            )

            # --- Save to ChromaDB ---
            document_content = self._create_searchable_document(golden_record)
            if document_content:
                chroma_id = f"prod_{new_product.id}"
                self.chroma_client.add_to_collection(
                    collection_name="rockwool_products",
                    documents=[document_content],
                    metadatas=[{
                        "product_id": new_product.id,
                        "product_name": new_product.name,
                        "manufacturer": "ROCKWOOL",
                        "source_pdf": golden_record.task.task_id
                    }],
                    ids=[chroma_id]
                )
        except Exception as e:
            logger.error(
                "Failed to save Golden Record for task %s. Error: %s",
                golden_record.task.task_id, e
            )
            db.rollback()
        finally:
            db.close()

    def _create_searchable_document(self, golden_record: GoldenRecord) -> str:
        """Creates a single string document for embedding."""
        parts = []
        data = golden_record.extracted_data
        
        name = data.get("product_name")
        description = data.get("description")
        specs = data.get("technical_specifications")
        
        if name and name != "Unknown Product":
            parts.append(f"Termék neve: {name}")
        if description:
            parts.append(f"Leírás: {description}")
        
        if specs and isinstance(specs, dict):
            spec_str = ", ".join(
                [f"{k}: {v}" for k, v in specs.items() if v]
            )
            if spec_str:
                parts.append(f"Műszaki adatok: {spec_str}")
        
        # Add a snippet of raw text for more context
        raw_text = data.get("raw_text")
        if raw_text:
            parts.append(f"Kivonat a dokumentumból: {raw_text[:1000]}")

        return "\n\n".join(parts)