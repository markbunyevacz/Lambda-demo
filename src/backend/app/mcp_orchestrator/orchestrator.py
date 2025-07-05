import asyncio
import logging
from typing import List, Any
from pathlib import Path

from .models import (
    ExtractionTask, ExtractionResult, GoldenRecord, TaskStatus, StrategyType
)
from .strategies import (
    PDFPlumberStrategy, PyMuPDFStrategy, NativePDFStrategy
)
from .validator import AIValidator
from .chroma_client import ChromaClient
from ..database import SessionLocal
from ..models import Product


logger = logging.getLogger(__name__)


class MCPOrchestrator:
    def __init__(self):
        self.chroma_client = ChromaClient()
        self.validator = AIValidator(chroma_client=self.chroma_client)
        self.strategies = {
            StrategyType.PDFPLUMBER: PDFPlumberStrategy(),
            StrategyType.PYMUPDF: PyMuPDFStrategy(),
            StrategyType.NATIVE_PDF: NativePDFStrategy(),
        }

    async def process_task(self, task: ExtractionTask) -> GoldenRecord:
        task.status = TaskStatus.RUNNING
        logger.info(
            f"Starting extraction task {task.task_id} for {task.pdf_path}"
        )
        
        # --- Step 1: Run basic text extraction strategies ---
        base_results = await self._run_strategies_parallel(
            task,
            [
                (
                    StrategyType.PDFPLUMBER,
                    self.strategies[StrategyType.PDFPLUMBER]
                ),
                (
                    StrategyType.PYMUPDF,
                    self.strategies[StrategyType.PYMUPDF]
                )
            ]
        )

        # --- Step 2: Select the best text and run AI analysis ---
        all_results = list(base_results)
        best_raw_text = self.validator.select_best_input(
            all_results, modality="raw_text"
        )
        
        if best_raw_text:
            task.input_data = {"raw_text": best_raw_text}
            ai_result = await self._run_strategy_safe(
                task,
                StrategyType.NATIVE_PDF,
                self.strategies[StrategyType.NATIVE_PDF]
            )
            if ai_result.success:
                all_results.append(ai_result)
        
        # --- Step 3: Finalize and save the Golden Record ---
        golden_record = await self.validator.validate_and_merge(
            all_results, task
        )
        
        if not golden_record.requires_human_review:
            # Delegate saving to the validator
            await self.validator.save_golden_record(golden_record)
        
        task.status = TaskStatus.COMPLETED
        logger.info(
            f"Completed task {task.task_id} with "
            f"confidence {golden_record.overall_confidence:.2f}"
        )
        return golden_record

    async def _run_strategies_parallel(
        self, task: ExtractionTask, strategies: List
    ) -> List[ExtractionResult]:
        results = await asyncio.gather(
            *[self._run_strategy_safe(task, st, s) for st, s in strategies]
        )
        return [r for r in results if r]

    async def _run_strategy_safe(
        self, task: ExtractionTask, st: StrategyType, s: Any
    ) -> ExtractionResult:
        try:
            return await s.extract(Path(task.pdf_path), task)
        except Exception as e:
            logger.error(f"Strategy {st.value} failed: {e}")
            return ExtractionResult(
                strategy_type=st, success=False, error_message=str(e)
            )

    def wipe_and_reset_databases(self):
        db = SessionLocal()
        try:
            db.query(Product).delete()
            # Keep Manufacturer and Category for now, or add logic to re-create
            # db.query(Category).delete()
            # db.query(Manufacturer).delete()
            db.commit()
            print("PostgreSQL product table cleared.")
            
            # Use the ChromaClient
            self.chroma_client.delete_collection(name="rockwool_products")
        except Exception as e:
            print(f"Error wiping databases: {e}")
            db.rollback()
        finally:
            db.close()
            
    def get_chroma_collection(self):
        return self.chroma_client.get_or_create_collection(
            "rockwool_products"
        ) 