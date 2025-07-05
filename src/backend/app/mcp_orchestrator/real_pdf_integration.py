"""
Real PDF Processor - MCP Orchestrator Integration
================================================

This module aligns the existing real_pdf_processor.py with the MCP Orchestrator system.
It preserves all proven functionality while adding orchestration capabilities.

Key Integration Points:
- Wraps existing RealPDFExtractor and ClaudeAIAnalyzer
- Maps PDFExtractionResult to MCP ExtractionResult format
- Provides backward compatibility with existing workflows
- Enables orchestrated, multi-strategy extraction
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time

# Import existing real_pdf_processor components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from real_pdf_processor import (
    RealPDFExtractor, 
    ClaudeAIAnalyzer, 
    RealPDFProcessor,
    PDFExtractionResult
)

# Import MCP Orchestrator models
from .models import (
    ExtractionTask,
    ExtractionResult,
    GoldenRecord,
    FieldConfidence,
    StrategyType,
    TaskStatus,
    ConfidenceLevel
)

from .strategies import BaseExtractionStrategy

logger = logging.getLogger(__name__)


class RealPDFMCPStrategy(BaseExtractionStrategy):
    """
    A wrapper to integrate the existing RealPDFProcessor as a strategy 
    within the MCP Orchestrator framework.
    """
    def __init__(self, db_session=None):
        """Initializes the strategy by creating instances of the existing extractor and analyzer."""
        print("Initializing RealPDFMCPStrategy with existing components...")
        self.extractor = RealPDFExtractor()
        self.ai_analyzer = ClaudeAIAnalyzer()
        print("✅ RealPDFMCPStrategy Initialized.")

    async def extract(self, pdf_path: Path, task: ExtractionTask) -> ExtractionResult:
        """

        Executes the extraction using the old `real_pdf_processor` logic and
        maps the output to the new `ExtractionResult` format.
        """
        try:
            print(f"Executing legacy extraction for: {pdf_path.name}")
            # 1. Use existing, proven PDF extraction logic
            text, tables, method = self.extractor.extract_pdf_content(pdf_path)

            if not text:
                print(f"⚠️ No text content extracted from {pdf_path.name}. Returning failure.")
                return ExtractionResult(strategy_type=StrategyType.LEGACY_REAL_PDF, success=False, error_message="No text content extracted.")

            # 2. Use existing Claude AI analysis
            print(f"Executing Claude AI analysis for: {pdf_path.name}")
            ai_analysis = self.ai_analyzer.analyze_rockwool_pdf(text, tables, pdf_path.name)
            
            # 3. Map the old result format to the new MCP ExtractionResult format
            print(f"Mapping result to MCP format for: {pdf_path.name}")
            mcp_result = self._map_to_mcp_format(text, tables, ai_analysis, method)
            
            print(f"✅ Successfully processed {pdf_path.name} with RealPDFMCPStrategy.")
            return mcp_result

        except Exception as e:
            print(f"❌ Error during RealPDFMCPStrategy execution for {pdf_path.name}: {e}")
            return ExtractionResult(
                strategy_type=StrategyType.LEGACY_REAL_PDF,
                success=False,
                error_message=str(e),
            )

    def _map_to_mcp_format(self, text: str, tables: List[Any], ai_analysis: Dict[str, Any], method: str) -> ExtractionResult:
        """Helper to convert the legacy dictionary format to the structured ExtractionResult model."""
        
        confidence = ai_analysis.get("confidence_assessment", {}).get("overall_confidence", 0.0)
        
        return ExtractionResult(
            strategy_type=StrategyType.LEGACY_REAL_PDF,
            success=True,
            extracted_data={
                "product_identification": ai_analysis.get("product_identification"),
                "technical_specifications": ai_analysis.get("technical_specifications"),
                "application_areas": ai_analysis.get("application_areas"),
                "pricing_information": ai_analysis.get("pricing_information"),
                "raw_text": text,
                "tables_data": tables,
            },
            confidence_score=float(confidence),
            method_used=method
        )


class MCPCompatibleProcessor:
    """
    Enhanced processor that can work in both legacy and orchestration modes
    
    This class provides backward compatibility while enabling orchestration:
    - Legacy mode: Works exactly like existing RealPDFProcessor
    - Orchestration mode: Participates in multi-strategy extraction
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        
        # Initialize both legacy and orchestration components
        if db_session:
            self.legacy_processor = RealPDFProcessor(db_session)
        else:
            self.legacy_processor = None
            
        self.mcp_strategy = RealPDFMCPStrategy(db_session)
        
        logger.info("✅ MCPCompatibleProcessor initialized")
    
    async def process_pdf_legacy(self, pdf_path: Path) -> Optional[PDFExtractionResult]:
        """
        Legacy processing mode - exactly like existing real_pdf_processor.py
        
        Use this for backward compatibility with existing workflows.
        """
        if not self.legacy_processor:
            raise ValueError("Database session required for legacy processing")
        
        return self.legacy_processor.process_pdf(pdf_path)
    
    async def process_pdf_orchestrated(
        self, 
        pdf_path: Path, 
        task: ExtractionTask
    ) -> ExtractionResult:
        """
        Orchestration mode - compatible with MCP system
        
        Use this for multi-strategy orchestration and enhanced confidence.
        """
        return await self.mcp_strategy.extract(pdf_path, task)
    
    async def process_directory_hybrid(
        self,
        pdf_directory: Path,
        use_orchestration: bool = True,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Hybrid processing mode - can switch between legacy and orchestration
        
        Returns unified results from either processing mode.
        """
        results = {
            "processed_files": [],
            "extraction_results": [],
            "legacy_results": [],
            "processing_mode": "orchestration" if use_orchestration else "legacy",
            "total_files": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
        
        pdf_files = list(pdf_directory.glob("*.pdf"))
        results["total_files"] = len(pdf_files)
        
        for pdf_file in pdf_files:
            try:
                if use_orchestration:
                    task = ExtractionTask(pdf_path=str(pdf_file))
                    extraction_result = await self.process_pdf_orchestrated(pdf_file, task)
                    results["extraction_results"].append(extraction_result)
                    if extraction_result.success:
                        results["successful_extractions"] += 1
                    else:
                        results["failed_extractions"] += 1
                else:
                    legacy_result = await self.process_pdf_legacy(pdf_file)
                    if legacy_result:
                        results["legacy_results"].append(legacy_result)
                        results["successful_extractions"] += 1
                    else:
                        results["failed_extractions"] += 1
                
                results["processed_files"].append(str(pdf_file))
                
            except Exception as e:
                logger.error(f"❌ Failed to process {pdf_file}: {e}")
                results["failed_extractions"] += 1
        
        # Save results if requested
        if output_file:
            self._save_hybrid_results(results, output_file)
        
        return results
    
    def _save_hybrid_results(self, results: Dict[str, Any], output_file: Path):
        """Save hybrid processing results to file"""
        import json
        
        # Convert non-serializable objects to dictionaries
        serializable_results = {
            "processed_files": results["processed_files"],
            "processing_mode": results["processing_mode"],
            "total_files": results["total_files"],
            "successful_extractions": results["successful_extractions"],
            "failed_extractions": results["failed_extractions"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Add extraction results based on mode
        if results["processing_mode"] == "orchestration":
            serializable_results["extraction_results"] = [
                {
                    "strategy_type": result.strategy_type.value,
                    "success": result.success,
                    "confidence_score": result.confidence_score,
                    "execution_time": result.execution_time_seconds,
                    "extracted_data": result.extracted_data
                }
                for result in results["extraction_results"]
            ]
        else:
            serializable_results["legacy_results"] = [
                result.to_dict() for result in results["legacy_results"]
            ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Hybrid results saved to: {output_file}")


# Integration utilities for backward compatibility
def migrate_legacy_result_to_mcp(
    legacy_result: PDFExtractionResult
) -> ExtractionResult:
    """
    Convert legacy PDFExtractionResult to MCP ExtractionResult format
    
    This enables gradual migration from legacy to orchestration system.
    """
    
    extracted_data = {
        "product_identification": {
            "name": legacy_result.product_name,
            "category": "Building Materials",  # Default
        },
        "technical_specifications": legacy_result.technical_specs,
        "pricing_information": legacy_result.pricing_info,
        "tables_data": legacy_result.tables_data,
        "legacy_data": {
            "extracted_text": legacy_result.extracted_text,
            "source_filename": legacy_result.source_filename,
            "processing_time": legacy_result.processing_time
        }
    }
    
    return ExtractionResult(
        strategy_type=StrategyType.PDFPLUMBER,  # Legacy used pdfplumber primarily
        success=True,
        execution_time_seconds=legacy_result.processing_time,
        extracted_data=extracted_data,
        confidence_score=legacy_result.confidence_score,
        method_used=legacy_result.extraction_method,
        text_length=len(legacy_result.extracted_text),
        tables_found=len(legacy_result.tables_data)
    )


def create_golden_record_from_legacy(
    legacy_result: PDFExtractionResult
) -> GoldenRecord:
    """
    Create a GoldenRecord from a single legacy result
    
    This enables legacy results to participate in orchestration workflows.
    """
    
    extracted_data = {
        "product_identification": {
            "name": legacy_result.product_name,
        },
        "technical_specifications": legacy_result.technical_specs,
        "pricing_information": legacy_result.pricing_info,
    }
    
    # Create field confidences based on legacy confidence
    field_confidences = {}
    base_confidence = legacy_result.confidence_score
    
    for field_name, value in extracted_data.items():
        if isinstance(value, dict) and value:
            for sub_field, sub_value in value.items():
                if sub_value:
                    field_confidences[f"{field_name}.{sub_field}"] = FieldConfidence(
                        field_name=f"{field_name}.{sub_field}",
                        value=sub_value,
                        confidence_score=base_confidence,
                        supporting_strategies=["legacy_real_pdf_processor"]
                    )
    
    return GoldenRecord(
        extracted_data=extracted_data,
        field_confidences=field_confidences,
        overall_confidence=legacy_result.confidence_score,
        strategies_used=["legacy_real_pdf_processor"],
        total_processing_time=legacy_result.processing_time,
        completeness_score=0.8 if legacy_result.technical_specs else 0.5,
        consistency_score=1.0,  # Single source, so perfectly consistent
        requires_human_review=legacy_result.confidence_score < 0.7
    )


# Factory functions for easy integration
def create_real_pdf_strategy(db_session=None) -> RealPDFMCPStrategy:
    """Factory function to create RealPDF strategy for MCP orchestration"""
    return RealPDFMCPStrategy(db_session)


def create_compatible_processor(db_session=None) -> MCPCompatibleProcessor:
    """Factory function to create compatible processor for legacy/orchestration"""
    return MCPCompatibleProcessor(db_session)


if __name__ == "__main__":
    """
    Example usage showing integration between legacy and orchestration systems
    """
    import asyncio
    from pathlib import Path
    
    async def demo_integration():
        # Initialize compatible processor
        processor = create_compatible_processor()
        
        # Demo PDF path
        demo_pdf = Path("src/downloads/rockwool_datasheets/sample.pdf")
        
        if demo_pdf.exists():
            print("🔄 Testing orchestration mode...")
            task = ExtractionTask(pdf_path=str(demo_pdf))
            result = await processor.process_pdf_orchestrated(demo_pdf, task)
            print(f"✅ Orchestration result: {result.success}, confidence: {result.confidence_score}")
        else:
            print("ℹ️ Demo PDF not found, skipping test")
    
    # Run demo
    asyncio.run(demo_integration()) 