#!/usr/bin/env python3
"""
AI Configuration Admin API
--------------------------
Provides API endpoints for managing AI configuration through the admin interface.
Includes real-time configuration updates, validation, cost tracking, and monitoring.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.config.ai_config import get_ai_config, reload_ai_config, AIModelConfig, PromptTemplates
from app.services.ai_service import AnalysisService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/admin/ai-config", tags=["AI Configuration Admin"])

# Cost tracking (simplified - in production, use proper database)
ai_usage_stats = {
    "total_requests": 0,
    "total_tokens": 0,
    "total_cost_usd": 0.0,
    "requests_today": 0,
    "tokens_today": 0,
    "cost_today_usd": 0.0,
    "last_reset": datetime.now().date(),
    "recent_requests": []  # Last 100 requests
}

# Claude pricing (as of 2024)
AI_PROVIDER_PRICING = {
    # Anthropic Claude models
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "input_tokens_per_million": 0.25,
        "output_tokens_per_million": 1.25
    },
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic", 
        "input_tokens_per_million": 3.00,
        "output_tokens_per_million": 15.00
    },
    "claude-3-opus-20240229": {
        "provider": "anthropic",
        "input_tokens_per_million": 15.00,
        "output_tokens_per_million": 75.00
    },
    
    # OpenAI GPT models
    "gpt-4o": {
        "provider": "openai",
        "input_tokens_per_million": 5.00,
        "output_tokens_per_million": 15.00
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "input_tokens_per_million": 0.15,
        "output_tokens_per_million": 0.60
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "input_tokens_per_million": 10.00,
        "output_tokens_per_million": 30.00
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "input_tokens_per_million": 0.50,
        "output_tokens_per_million": 1.50
    },
    
    # Google AI models
    "gemini-1.5-pro": {
        "provider": "google",
        "input_tokens_per_million": 3.50,
        "output_tokens_per_million": 10.50
    },
    "gemini-1.5-flash": {
        "provider": "google",
        "input_tokens_per_million": 0.075,
        "output_tokens_per_million": 0.30
    },
    "gemini-pro": {
        "provider": "google",
        "input_tokens_per_million": 0.50,
        "output_tokens_per_million": 1.50
    },
    
    # Default pricing for unknown models
    "custom": {
        "provider": "custom",
        "input_tokens_per_million": 1.00,
        "output_tokens_per_million": 3.00
    }
}


class AIModelConfigRequest(BaseModel):
    """Request model for updating AI model configuration."""
    
    model_name: str = Field(..., description="AI model name (free text)")
    provider: str = Field(..., description="AI provider (anthropic, openai, google, custom)")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    max_tokens: int = Field(..., ge=1024, le=32768, description="Maximum tokens")
    min_tokens: int = Field(..., ge=512, le=16384, description="Minimum tokens")
    token_decrement: int = Field(..., ge=256, le=4096, description="Token decrement")
    max_retries: int = Field(..., ge=1, le=10, description="Maximum retries")
    timeout_seconds: int = Field(..., ge=5, le=300, description="Timeout seconds")
    max_text_length: int = Field(..., ge=1000, le=50000, description="Max text length")
    max_tables_summary: int = Field(..., ge=1, le=20, description="Max tables summary")
    
    # Custom pricing for unknown models
    custom_input_price: Optional[float] = Field(None, ge=0.0, description="Custom input price per million tokens")
    custom_output_price: Optional[float] = Field(None, ge=0.0, description="Custom output price per million tokens")
    
    @validator('min_tokens')
    def validate_min_tokens(cls, v, values):
        if 'max_tokens' in values and v >= values['max_tokens']:
            raise ValueError('min_tokens must be less than max_tokens')
        return v


class PromptTemplateRequest(BaseModel):
    """Request model for updating prompt templates."""
    
    template_name: str = Field(..., description="Template name")
    template_content: str = Field(..., min_length=10, description="Template content")


class AIUsageRequest(BaseModel):
    """Request model for logging AI usage."""
    
    request_type: str = Field(..., description="Type of AI request")
    input_tokens: int = Field(..., ge=0, description="Input tokens used")
    output_tokens: int = Field(..., ge=0, description="Output tokens used")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
    success: bool = Field(..., description="Whether request was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class AIConfigResponse(BaseModel):
    """Response model for AI configuration."""
    
    model_config: Dict[str, Any]
    prompt_templates: Dict[str, str]
    usage_stats: Dict[str, Any]
    validation_errors: List[str] = []
    last_updated: str


class AIUsageStatsResponse(BaseModel):
    """Response model for AI usage statistics."""
    
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    requests_today: int
    tokens_today: int
    cost_today_usd: float
    average_tokens_per_request: float
    average_cost_per_request: float
    recent_requests: List[Dict[str, Any]]


@router.get("/status", response_model=AIConfigResponse)
async def get_ai_config_status():
    """Get current AI configuration and usage statistics."""
    try:
        config_manager = get_ai_config()
        model_config = config_manager.get_model_config()
        prompt_templates = config_manager.get_prompt_templates()
        
        # Reset daily stats if needed
        _reset_daily_stats_if_needed()
        
        return AIConfigResponse(
            model_config={
                "model_name": model_config.model_name,
                "provider": model_config.provider,
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_tokens,
                "min_tokens": model_config.min_tokens,
                "token_decrement": model_config.token_decrement,
                "max_retries": model_config.max_retries,
                "timeout_seconds": model_config.timeout_seconds,
                "max_text_length": model_config.max_text_length,
                "max_tables_summary": model_config.max_tables_summary,
            },
            prompt_templates={
                "extraction_prompt": prompt_templates.extraction_prompt[:200] + "...",  # Truncated
                "table_summary_template": prompt_templates.table_summary_template,
                "no_tables_message": prompt_templates.no_tables_message,
                "error_fallback_template": prompt_templates.error_fallback_template,
            },
            usage_stats=ai_usage_stats.copy(),
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get AI config status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.post("/model-config")
async def update_model_config(
    config_request: AIModelConfigRequest,
    background_tasks: BackgroundTasks
):
    """Update AI model configuration with validation."""
    try:
        config_manager = get_ai_config()
        
        # Validate model name
        if config_request.model_name not in AI_PROVIDER_PRICING:
            available_models = list(AI_PROVIDER_PRICING.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid model name. Available models: {available_models}"
            )
        
        # Update configuration
        config_manager.update_model_config(
            model_name=config_request.model_name,
            provider=config_request.provider,
            temperature=config_request.temperature,
            max_tokens=config_request.max_tokens,
            min_tokens=config_request.min_tokens,
            token_decrement=config_request.token_decrement,
            max_retries=config_request.max_retries,
            timeout_seconds=config_request.timeout_seconds,
            max_text_length=config_request.max_text_length,
            max_tables_summary=config_request.max_tables_summary,
        )
        
        # Save configuration to file
        background_tasks.add_task(_save_config_to_file, config_manager)
        
        logger.info(f"AI model configuration updated: {config_request.model_name}")
        
        return {
            "success": True,
            "message": "AI model configuration updated successfully",
            "updated_config": config_request.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model config: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@router.post("/prompt-template")
async def update_prompt_template(
    template_request: PromptTemplateRequest,
    background_tasks: BackgroundTasks
):
    """Update a specific prompt template."""
    try:
        config_manager = get_ai_config()
        prompt_templates = config_manager.get_prompt_templates()
        
        # Validate template name
        valid_templates = ["extraction_prompt", "table_summary_template", 
                          "no_tables_message", "error_fallback_template"]
        if template_request.template_name not in valid_templates:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template name. Valid templates: {valid_templates}"
            )
        
        # Update template
        config_manager.update_prompt_template(
            template_request.template_name,
            template_request.template_content
        )
        
        # Save configuration to file
        background_tasks.add_task(_save_config_to_file, config_manager)
        
        logger.info(f"Prompt template updated: {template_request.template_name}")
        
        return {
            "success": True,
            "message": f"Prompt template '{template_request.template_name}' updated successfully",
            "template_name": template_request.template_name,
            "template_length": len(template_request.template_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt template: {e}")
        raise HTTPException(status_code=500, detail=f"Template update failed: {str(e)}")


@router.get("/prompt-template/{template_name}")
async def get_prompt_template(template_name: str):
    """Get full content of a specific prompt template."""
    try:
        config_manager = get_ai_config()
        prompt_templates = config_manager.get_prompt_templates()
        
        if not hasattr(prompt_templates, template_name):
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        template_content = getattr(prompt_templates, template_name)
        
        return {
            "template_name": template_name,
            "template_content": template_content,
            "template_length": len(template_content),
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve template: {str(e)}")


@router.post("/usage/log")
async def log_ai_usage(usage_request: AIUsageRequest):
    """Log AI usage for cost tracking and monitoring."""
    try:
        # Reset daily stats if needed
        _reset_daily_stats_if_needed()
        
        # Calculate cost
        config_manager = get_ai_config()
        model_config = config_manager.get_model_config()
        model_name = model_config.model_name
        
        # Get pricing information
        pricing = None
        if model_name in AI_PROVIDER_PRICING:
            pricing = AI_PROVIDER_PRICING[model_name]
        else:
            # Use custom pricing if available, otherwise default
            custom_input = getattr(model_config, 'custom_input_price', None)
            custom_output = getattr(model_config, 'custom_output_price', None)
            
            if custom_input is not None and custom_output is not None:
                pricing = {
                    "provider": "custom",
                    "input_tokens_per_million": custom_input,
                    "output_tokens_per_million": custom_output
                }
            else:
                # Use default custom pricing
                pricing = AI_PROVIDER_PRICING["custom"]
        
        # Calculate costs
        input_cost = (usage_request.input_tokens / 1_000_000) * pricing["input_tokens_per_million"]
        output_cost = (usage_request.output_tokens / 1_000_000) * pricing["output_tokens_per_million"]
        total_cost = input_cost + output_cost
        
        # Update statistics
        ai_usage_stats["total_requests"] += 1
        ai_usage_stats["total_tokens"] += usage_request.input_tokens + usage_request.output_tokens
        ai_usage_stats["total_cost_usd"] += total_cost
        ai_usage_stats["requests_today"] += 1
        ai_usage_stats["tokens_today"] += usage_request.input_tokens + usage_request.output_tokens
        ai_usage_stats["cost_today_usd"] += total_cost
        
        # Add to recent requests (keep last 100)
        request_log = {
            "timestamp": datetime.now().isoformat(),
            "request_type": usage_request.request_type,
            "input_tokens": usage_request.input_tokens,
            "output_tokens": usage_request.output_tokens,
            "total_tokens": usage_request.input_tokens + usage_request.output_tokens,
            "cost_usd": round(total_cost, 4),
            "processing_time_ms": usage_request.processing_time_ms,
            "success": usage_request.success,
            "error_message": usage_request.error_message,
            "model_name": model_name
        }
        
        ai_usage_stats["recent_requests"].append(request_log)
        if len(ai_usage_stats["recent_requests"]) > 100:
            ai_usage_stats["recent_requests"] = ai_usage_stats["recent_requests"][-100:]
        
        return {
            "success": True,
            "logged_cost_usd": round(total_cost, 4),
            "total_cost_today_usd": round(ai_usage_stats["cost_today_usd"], 4)
        }
        
    except Exception as e:
        logger.error(f"Failed to log AI usage: {e}")
        raise HTTPException(status_code=500, detail=f"Usage logging failed: {str(e)}")


@router.get("/usage/stats", response_model=AIUsageStatsResponse)
async def get_usage_stats():
    """Get detailed AI usage statistics and cost analysis."""
    try:
        # Reset daily stats if needed
        _reset_daily_stats_if_needed()
        
        # Calculate averages
        total_requests = ai_usage_stats["total_requests"]
        avg_tokens = ai_usage_stats["total_tokens"] / max(total_requests, 1)
        avg_cost = ai_usage_stats["total_cost_usd"] / max(total_requests, 1)
        
        return AIUsageStatsResponse(
            total_requests=ai_usage_stats["total_requests"],
            total_tokens=ai_usage_stats["total_tokens"],
            total_cost_usd=round(ai_usage_stats["total_cost_usd"], 4),
            requests_today=ai_usage_stats["requests_today"],
            tokens_today=ai_usage_stats["tokens_today"],
            cost_today_usd=round(ai_usage_stats["cost_today_usd"], 4),
            average_tokens_per_request=round(avg_tokens, 1),
            average_cost_per_request=round(avg_cost, 4),
            recent_requests=ai_usage_stats["recent_requests"][-20:]  # Last 20 requests
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage stats: {str(e)}")


@router.post("/test-configuration")
async def test_ai_configuration():
    """Test current AI configuration with a sample request."""
    try:
        # Create a test analysis service
        service = AnalysisService()
        
        # Test with sample data
        test_text = "ROCKWOOL Frontrock MAX E termékadatlap. Hővezetési tényező: 0.035 W/mK"
        test_tables = [{"headers": ["Tulajdonság", "Érték"], "data": [["λ", "0.035 W/mK"]]}]
        test_filename = "test_configuration.pdf"
        
        start_time = time.time()
        
        # Perform test analysis
        result = await service.analyze_pdf_content(test_text, test_tables, test_filename)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log the test usage
        await log_ai_usage(AIUsageRequest(
            request_type="configuration_test",
            input_tokens=100,  # Estimated
            output_tokens=50,  # Estimated
            processing_time_ms=processing_time,
            success=True
        ))
        
        return {
            "success": True,
            "message": "AI configuration test completed successfully",
            "test_result": {
                "processing_time_ms": processing_time,
                "extracted_product_name": result.get("product_identification", {}).get("product_name", "N/A"),
                "confidence_score": result.get("extraction_metadata", {}).get("confidence_score", 0.0),
                "has_technical_specs": bool(result.get("technical_specifications", {}))
            },
            "current_config": service.get_current_config()
        }
        
    except Exception as e:
        logger.error(f"AI configuration test failed: {e}")
        
        # Log the failed test
        try:
            await log_ai_usage(AIUsageRequest(
                request_type="configuration_test",
                input_tokens=100,
                output_tokens=0,
                processing_time_ms=0,
                success=False,
                error_message=str(e)
            ))
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Configuration test failed: {str(e)}")


@router.get("/providers", summary="Get available AI providers and models")
async def get_ai_providers():
    """Get list of available AI providers and their models."""
    try:
        providers = {}
        
        for model_name, details in AI_PROVIDER_PRICING.items():
            provider = details["provider"]
            if provider not in providers:
                providers[provider] = {
                    "name": provider,
                    "display_name": {
                        "anthropic": "Anthropic Claude",
                        "openai": "OpenAI GPT",
                        "google": "Google AI",
                        "custom": "Custom Model"
                    }.get(provider, provider.title()),
                    "models": []
                }
            
            providers[provider]["models"].append({
                "model_name": model_name,
                "input_price": details["input_tokens_per_million"],
                "output_price": details["output_tokens_per_million"]
            })
        
        return {
            "providers": list(providers.values()),
            "total_models": len(AI_PROVIDER_PRICING),
            "supported_providers": list(providers.keys())
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI providers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")


@router.post("/reload")
async def reload_ai_configuration():
    """Reload AI configuration from files and environment variables."""
    try:
        reload_ai_config()
        
        logger.info("AI configuration reloaded from external sources")
        
        return {
            "success": True,
            "message": "AI configuration reloaded successfully",
            "reloaded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload AI configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration reload failed: {str(e)}")


def _reset_daily_stats_if_needed():
    """Reset daily statistics if it's a new day."""
    current_date = datetime.now().date()
    if ai_usage_stats["last_reset"] != current_date:
        ai_usage_stats["requests_today"] = 0
        ai_usage_stats["tokens_today"] = 0
        ai_usage_stats["cost_today_usd"] = 0.0
        ai_usage_stats["last_reset"] = current_date


def _save_config_to_file(config_manager):
    """Background task to save configuration to file."""
    try:
        config_manager.save_to_file()
        logger.info("AI configuration saved to file")
    except Exception as e:
        logger.error(f"Failed to save AI configuration to file: {e}")


# Include router in main application
def include_router(app):
    """Include this router in the main FastAPI application."""
    app.include_router(router) 