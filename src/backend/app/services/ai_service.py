
import os
import json
import logging
import re
from typing import Dict, List, Any

from anthropic import Anthropic

# REFACTORING: Import the new AI configuration system
from app.config.ai_config import get_ai_config

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Handles all interactions with the Claude AI model for content analysis.
    
    REFACTORING NOTE: This service now uses the centralized AI configuration
    system instead of hardcoded values. All AI parameters, model names, and
    prompt templates are now externally configurable.
    
    This service is responsible for prompt engineering, making API calls,
    and parsing the structured data from the AI's response.
    """
    
    def __init__(self):
        """
        Initialize the Analysis Service with externalized configuration.
        
        CONFIGURATION SOURCES (in priority order):
        1. Environment variables (highest priority)
        2. Configuration files (ai_config.json)
        3. Default values (lowest priority)
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ ANTHROPIC_API_KEY not found in environment variables"
            )
        
        self.client = Anthropic(api_key=api_key)
        
        # DECOUPLING: Load all AI configuration from external sources
        self.config = get_ai_config()
        self.model_config = self.config.get_model_config()
        self.prompt_templates = self.config.get_prompt_templates()

        logger.info(f"✅ Analysis Service initialized with model: {self.model_config.model_name}")
        logger.info(f"📊 Configuration: temp={self.model_config.temperature}, "
                   f"max_tokens={self.model_config.max_tokens}")

    async def analyze_pdf_content(
        self, 
        text_content: str, 
        tables_data: List[Dict], 
        filename: str
    ) -> Dict[str, Any]:
        """
        Analyze PDF content and return structured data.

        This method is used by the admin interface for testing configurations.
        
        Args:
            text_content: Raw text extracted from PDF
            tables_data: List of table dictionaries
            filename: Name of the source PDF file
            
        Returns:
            Dict containing structured analysis results
        """
        try:
            # Use the existing analyze_rockwool_pdf method
            result = await self.analyze_rockwool_pdf(text_content, tables_data, filename)
            return result

        except Exception as e:
            logger.error(f"PDF content analysis failed: {e}")
            return {
                "product_identification": {"product_name": "Analysis Failed"},
                "extraction_metadata": {"confidence_score": 0.0},
                "error": str(e)
            }

    def _create_extraction_prompt(
        self, text_content: str, tables_data: List[Dict], filename: str
    ) -> str:
        """
        Creates a sophisticated prompt using externalized templates.
        
        REFACTORING: Previously this method contained hardcoded prompt text.
        Now it uses the configuration system to generate prompts from
        templates, making them easily customizable.
        """
        # EXTERNALIZED: Table summary generation using configuration
        tables_summary = self.config.get_table_summary(tables_data)
        
        # EXTERNALIZED: Prompt generation using template system
        return self.config.get_extraction_prompt(
            filename=filename,
            text_content=text_content,
            tables_summary=tables_summary
        )

    async def _make_api_call(self, prompt: str) -> str:
        """
        Executes the API call to Claude with configurable retry logic.
        
        REFACTORING: Token limits, retry logic, and API parameters are now
        externally configurable instead of hardcoded constants.
        """
        # EXTERNALIZED: All parameters come from configuration
        max_tokens = self.model_config.max_tokens
        min_tokens = self.model_config.min_tokens
        decrement = self.model_config.token_decrement
        last_error = None

        while max_tokens >= min_tokens:
            try:
                response = self.client.messages.create(
                    model=self.model_config.model_name,  # EXTERNALIZED: Model name
                    max_tokens=max_tokens,
                    temperature=self.model_config.temperature,  # EXTERNALIZED: Temperature
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            except Exception as e:
                last_error = e
                if "max_tokens" in str(e):
                    logger.warning(
                        f"Token limit error with max_tokens={max_tokens}. "
                        f"Retrying with reduced tokens..."
                    )
                    max_tokens -= decrement
                    continue
                logger.error(f"Unhandled Claude API error: {e}")
                raise
        
        logger.error("Failed to get a response from Claude after reducing tokens.")
        raise last_error or RuntimeError("Unknown API call failure.")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parses the JSON response from the AI, cleaning it if necessary.
        
        REFACTORING: Error handling now uses externalized fallback templates
        instead of hardcoded error structures.
        """
        try:
            # Find the JSON block in the response text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            logger.error("No JSON object found in AI response.")
            return self._get_fallback_error_structure("No JSON found")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from AI response: {e}")
            return self._get_fallback_error_structure(f"JSON decode error: {e}")

    def _get_fallback_error_structure(self, error_message: str) -> Dict[str, Any]:
        """
        Returns a standardized error structure when analysis fails.
        
        REFACTORING: Error structure now comes from externalized template
        instead of hardcoded dictionary.
        """
        # EXTERNALIZED: Error fallback structure from configuration
        return self.config.get_error_fallback(error_message)
    
    def reload_configuration(self):
        """
        Reload AI configuration at runtime without restarting the service.
        
        NEW FEATURE: Enables dynamic reconfiguration of AI parameters
        and prompt templates during operation.
        """
        self.config = get_ai_config()
        self.model_config = self.config.get_model_config()
        self.prompt_templates = self.config.get_prompt_templates()
        
        logger.info(f"🔄 AI configuration reloaded: model={self.model_config.model_name}")
    
    def update_model_config(self, **kwargs):
        """
        Update AI model configuration at runtime.
        
        NEW FEATURE: Allows fine-tuning of AI parameters during operation
        for testing and optimization purposes.
        
        Args:
            **kwargs: Model configuration parameters to update
        """
        self.config.update_model_config(**kwargs)
        self.model_config = self.config.get_model_config()
        
        logger.info(f"🔧 AI model config updated: {kwargs}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current AI configuration for admin interface.
        
        Returns:
            Dict containing current AI configuration settings
        """
        config_manager = get_ai_config()
        model_config = config_manager.get_model_config()
        
        return {
            "model_name": model_config.model_name,
            "provider": model_config.provider,
            "temperature": model_config.temperature,
            "max_tokens": model_config.max_tokens,
            "timeout_seconds": model_config.timeout_seconds,
            "max_retries": model_config.max_retries
        } 