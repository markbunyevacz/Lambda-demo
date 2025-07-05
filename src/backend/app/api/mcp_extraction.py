"""
FastAPI Endpoints for MCP Orchestrator
======================================

REST API endpoints for PDF extraction using the MCP orchestrated system.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import tempfile
import os
from pathlib import Path
import uuid
import asyncio

from ..mcp_orchestrator import MCPOrchestrator

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP Extraction"])

# Global orchestrator instance
orchestrator = MCPOrchestrator()

# In-memory task storage (in production, use Redis or database)
active_extractions: Dict[str, Dict[str, Any]] = {}


class ExtractionRequest(BaseModel):
    """Request model for PDF extraction"""
    pdf_path: str = Field(..., description="Path to the PDF file to extract")
    use_tiered_approach: bool = Field(
        True, 
        description="Whether to use cost-optimized tiered approach"
    )
    max_cost_tier: int = Field(
        3, 
        ge=1, 
        le=4, 
        description="Maximum cost tier to escalate to (1-4)"
    )
    timeout_seconds: int = Field(
        300, 
        ge=30, 
        le=600, 
        description="Timeout for extraction in seconds"
    )


class ExtractionResponse(BaseModel):
    """Response model for extraction results"""
    task_id: str
    success: bool
    confidence: float
    completeness_score: float
    consistency_score: float
    requires_human_review: bool
    strategies_used: List[str]
    processing_time: float
    extracted_data: Dict[str, Any]
    field_confidences: Dict[str, Dict[str, Any]]
    ai_notes: str


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    pdf_path: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    progress: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/extract", response_model=ExtractionResponse)
async def extract_pdf(request: ExtractionRequest):
    """
    Extract data from a PDF using the MCP orchestrated approach
    
    This endpoint runs the full extraction pipeline with multiple strategies
    and AI-powered validation to produce a high-confidence result.
    """
    
    # Validate PDF path
    if not Path(request.pdf_path).exists():
        raise HTTPException(
            status_code=404, 
            detail=f"PDF file not found: {request.pdf_path}"
        )
    
    try:
        # Run extraction
        golden_record = await orchestrator.extract_pdf(
            pdf_path=request.pdf_path,
            use_tiered_approach=request.use_tiered_approach,
            max_cost_tier=request.max_cost_tier,
            timeout_seconds=request.timeout_seconds
        )
        
        # Convert field confidences to serializable format
        field_confidences = {}
        for field_name, field_conf in golden_record.field_confidences.items():
            field_confidences[field_name] = {
                'confidence_score': field_conf.confidence_score,
                'confidence_level': field_conf.get_confidence_level().value,
                'supporting_strategies': field_conf.supporting_strategies,
                'conflicting_values': field_conf.conflicting_values,
                'notes': field_conf.notes
            }
        
        return ExtractionResponse(
            task_id=str(uuid.uuid4()),  # Generate a task ID for this request
            success=True,
            confidence=golden_record.overall_confidence,
            completeness_score=golden_record.completeness_score,
            consistency_score=golden_record.consistency_score,
            requires_human_review=golden_record.requires_human_review,
            strategies_used=golden_record.strategies_used,
            processing_time=golden_record.total_processing_time,
            extracted_data=golden_record.extracted_data,
            field_confidences=field_confidences,
            ai_notes=golden_record.ai_adjudication_notes
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/extract-async")
async def extract_pdf_async(
    request: ExtractionRequest, 
    background_tasks: BackgroundTasks
):
    """
    Start PDF extraction in the background and return task ID
    
    Use this for long-running extractions. Poll /status/{task_id} for progress.
    """
    
    task_id = str(uuid.uuid4())
    
    # Store task info
    active_extractions[task_id] = {
        'status': 'pending',
        'pdf_path': request.pdf_path,
        'created_at': asyncio.get_event_loop().time(),
        'progress': 'Initializing extraction...'
    }
    
    # Start background extraction
    background_tasks.add_task(
        _run_background_extraction,
        task_id,
        request
    )
    
    return {
        'task_id': task_id,
        'status': 'pending',
        'message': 'Extraction started in background'
    }


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_extraction_status(task_id: str):
    """Get the status of a background extraction task"""
    
    if task_id not in active_extractions:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found: {task_id}"
        )
    
    task_info = active_extractions[task_id]
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_info['status'],
        pdf_path=task_info.get('pdf_path'),
        created_at=task_info.get('created_at'),
        started_at=task_info.get('started_at'),
        progress=task_info.get('progress'),
        error_message=task_info.get('error_message')
    )


@router.get("/stats")
async def get_orchestrator_stats():
    """Get orchestrator performance statistics"""
    
    stats = orchestrator.get_orchestrator_stats()
    
    return {
        'orchestrator_stats': stats,
        'active_tasks': len(active_extractions),
        'pending_tasks': len([
            t for t in active_extractions.values() 
            if t['status'] == 'pending'
        ]),
        'running_tasks': len([
            t for t in active_extractions.values() 
            if t['status'] == 'running'
        ])
    }


@router.post("/upload-and-extract")
async def upload_and_extract(
    file: UploadFile = File(..., description="PDF file to extract"),
    use_tiered_approach: bool = True,
    max_cost_tier: int = 3,
    timeout_seconds: int = 300
):
    """
    Upload a PDF file and extract data in one request
    
    Useful for testing with new files that aren't already on the server.
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Create extraction request
        request = ExtractionRequest(
            pdf_path=temp_path,
            use_tiered_approach=use_tiered_approach,
            max_cost_tier=max_cost_tier,
            timeout_seconds=timeout_seconds
        )
        
        # Run extraction
        result = await extract_pdf(request)
        
        return result
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


@router.delete("/tasks/{task_id}")
async def cancel_extraction_task(task_id: str):
    """Cancel a running extraction task"""
    
    if task_id not in active_extractions:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found: {task_id}"
        )
    
    task_info = active_extractions[task_id]
    
    if task_info['status'] in ['completed', 'failed', 'cancelled']:
        return {
            'message': f"Task {task_id} is already {task_info['status']}"
        }
    
    # Mark as cancelled
    task_info['status'] = 'cancelled'
    task_info['progress'] = 'Cancelled by user'
    
    return {
        'message': f"Task {task_id} cancelled successfully"
    }


# Background task function
async def _run_background_extraction(task_id: str, request: ExtractionRequest):
    """Run extraction in background"""
    
    task_info = active_extractions[task_id]
    
    try:
        task_info['status'] = 'running'
        task_info['started_at'] = asyncio.get_event_loop().time()
        task_info['progress'] = 'Running extraction strategies...'
        
        # Run extraction
        golden_record = await orchestrator.extract_pdf(
            pdf_path=request.pdf_path,
            use_tiered_approach=request.use_tiered_approach,
            max_cost_tier=request.max_cost_tier,
            timeout_seconds=request.timeout_seconds
        )
        
        # Store results
        task_info['status'] = 'completed'
        task_info['progress'] = 'Extraction completed successfully'
        task_info['results'] = {
            'confidence': golden_record.overall_confidence,
            'strategies_used': golden_record.strategies_used,
            'requires_review': golden_record.requires_human_review,
            'field_count': len(golden_record.extracted_data)
        }
        
    except Exception as e:
        task_info['status'] = 'failed'
        task_info['error_message'] = str(e)
        task_info['progress'] = f'Failed: {str(e)}' 