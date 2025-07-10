#!/usr/bin/env python3
"""
AI Configuration System
-----------------------
Centralizes all AI-related configuration including model settings,
prompt templates, and API parameters. This enables easy modification
of AI behavior without code changes.

Configuration Sources (in priority order):
1. Environment variables
2. Configuration files
3. Default values
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AIModelConfig:
    """Configuration for AI model settings."""
    
    # Model identification
    model_name: str = "claude-3-5-haiku-20241022"
    provider: str = "anthropic"
    
    # API parameters
    temperature: float = 0.0
    max_tokens: int = 8192
    min_tokens: int = 2048
    token_decrement: int = 1024
    
    # Retry and timeout settings
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Content limits
    max_text_length: int = 8000
    max_tables_summary: int = 3


@dataclass
class PromptTemplates:
    """Configuration for AI prompt templates."""
    
    # Main extraction prompt template
    extraction_prompt: str = field(default_factory=lambda: """
## CONTEXT
You are an expert AI assistant specializing in the Hungarian construction
industry. Your task is to analyze the content of a technical datasheet for a
ROCKWOOL product and extract key information into a structured JSON format.

- **Source Filename**: {filename}
- **Extracted Text Snippet**:
  ```
  {text_content}
  ```
- **Extracted Tables Summary**:
  ```
  {tables_summary}
  ```

## INSTRUCTIONS
1.  **Analyze the text and tables provided.**
2.  **Identify key technical specifications.** Use this mapping:
    - 'hővezetési tényező' or 'λ' -> 'thermal_conductivity' (W/mK)
    - 'testsűrűség' or 'ρ' -> 'density' (kg/m³)
    - 'tűzvédelmi osztály' -> 'fire_classification' (e.g., A1)
    - 'nyomószilárdság' -> 'compressive_strength' (kPa)
3.  **Extract the product name.**
4.  **Format the output** as a single, valid JSON object. Do not include
    any text or explanations outside of the JSON block.

## DESIRED JSON OUTPUT STRUCTURE
```json
{{
  "product_identification": {{
    "product_name": "[Extracted Product Name]"
  }},
  "technical_specifications": {{
    "thermal_conductivity": {{"value": "[Number]", "unit": "W/mK"}},
    "density": {{"value": "[Number]", "unit": "kg/m³"}},
    "fire_classification": {{"value": "[String]"}}
  }},
  "extraction_metadata": {{
      "confidence_score": [A number between 0.0 and 1.0]
  }}
}}
```
""")
    
    # Table summary template
    table_summary_template: str = "Table {index}: Headers={headers}, Rows={row_count}"
    
    # No tables message
    no_tables_message: str = "No tables were extracted from the document."
    
    # Error fallback template
    error_fallback_template: str = """
{{
  "product_identification": {{}},
  "technical_specifications": {{}},
  "extraction_metadata": {{
    "confidence_score": 0.0,
    "error": "{error_message}"
  }}
}}
"""


class AIConfigManager:
    """
    Manages AI configuration with support for environment variables,
    configuration files, and runtime updates.
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize AI configuration manager.
        
        Args:
            config_file: Optional path to JSON configuration file
        """
        self.config_file = config_file or Path(__file__).parent / "ai_config.json"
        self.model_config = AIModelConfig()
        self.prompt_templates = PromptTemplates()
        
        # Load configuration in priority order
        self._load_from_file()
        self._load_from_environment()
        
    def _load_from_file(self):
        """Load configuration from JSON file if it exists."""
        if not self.config_file.exists():
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Update model configuration
            if 'model' in config_data:
                model_data = config_data['model']
                for key, value in model_data.items():
                    if hasattr(self.model_config, key):
                        setattr(self.model_config, key, value)
                        
            # Update prompt templates
            if 'prompts' in config_data:
                prompt_data = config_data['prompts']
                for key, value in prompt_data.items():
                    if hasattr(self.prompt_templates, key):
                        setattr(self.prompt_templates, key, value)
                        
        except Exception as e:
            # Log warning but don't fail - use defaults
            import logging
            logging.warning(f"Failed to load AI config from {self.config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables (highest priority)."""
        
        # Model configuration from environment
        env_mappings = {
            'AI_MODEL_NAME': 'model_name',
            'AI_PROVIDER': 'provider',
            'AI_TEMPERATURE': ('temperature', float),
            'AI_MAX_TOKENS': ('max_tokens', int),
            'AI_MIN_TOKENS': ('min_tokens', int),
            'AI_TOKEN_DECREMENT': ('token_decrement', int),
            'AI_MAX_RETRIES': ('max_retries', int),
            'AI_TIMEOUT_SECONDS': ('timeout_seconds', int),
            'AI_MAX_TEXT_LENGTH': ('max_text_length', int),
            'AI_MAX_TABLES_SUMMARY': ('max_tables_summary', int),
        }
        
        for env_var, attr_info in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                if isinstance(attr_info, tuple):
                    attr_name, type_converter = attr_info
                    try:
                        converted_value = type_converter(env_value)
                        setattr(self.model_config, attr_name, converted_value)
                    except ValueError:
                        pass  # Keep default if conversion fails
                else:
                    setattr(self.model_config, attr_info, env_value)
        
        # Prompt templates from environment
        prompt_env_mappings = {
            'AI_EXTRACTION_PROMPT': 'extraction_prompt',
            'AI_TABLE_SUMMARY_TEMPLATE': 'table_summary_template',
            'AI_NO_TABLES_MESSAGE': 'no_tables_message',
            'AI_ERROR_FALLBACK_TEMPLATE': 'error_fallback_template',
        }
        
        for env_var, attr_name in prompt_env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                setattr(self.prompt_templates, attr_name, env_value)
    
    def get_model_config(self) -> AIModelConfig:
        """Get current model configuration."""
        return self.model_config
    
    def get_prompt_templates(self) -> PromptTemplates:
        """Get current prompt templates."""
        return self.prompt_templates
    
    def update_model_config(self, **kwargs):
        """Update model configuration at runtime."""
        for key, value in kwargs.items():
            if hasattr(self.model_config, key):
                setattr(self.model_config, key, value)
    
    def update_prompt_template(self, template_name: str, template_content: str):
        """Update a specific prompt template at runtime."""
        if hasattr(self.prompt_templates, template_name):
            setattr(self.prompt_templates, template_name, template_content)
    
    def save_to_file(self, file_path: Optional[Path] = None):
        """Save current configuration to JSON file."""
        target_file = file_path or self.config_file
        
        config_data = {
            'model': {
                'model_name': self.model_config.model_name,
                'provider': self.model_config.provider,
                'temperature': self.model_config.temperature,
                'max_tokens': self.model_config.max_tokens,
                'min_tokens': self.model_config.min_tokens,
                'token_decrement': self.model_config.token_decrement,
                'max_retries': self.model_config.max_retries,
                'timeout_seconds': self.model_config.timeout_seconds,
                'max_text_length': self.model_config.max_text_length,
                'max_tables_summary': self.model_config.max_tables_summary,
            },
            'prompts': {
                'extraction_prompt': self.prompt_templates.extraction_prompt,
                'table_summary_template': self.prompt_templates.table_summary_template,
                'no_tables_message': self.prompt_templates.no_tables_message,
                'error_fallback_template': self.prompt_templates.error_fallback_template,
            }
        }
        
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get_extraction_prompt(self, filename: str, text_content: str, 
                            tables_summary: str) -> str:
        """
        Generate the extraction prompt using the template and provided data.
        
        Args:
            filename: Source PDF filename
            text_content: Extracted text content
            tables_summary: Summary of extracted tables
            
        Returns:
            Formatted prompt string ready for AI
        """
        return self.prompt_templates.extraction_prompt.format(
            filename=filename,
            text_content=text_content[:self.model_config.max_text_length],
            tables_summary=tables_summary
        )
    
    def get_table_summary(self, tables_data: list) -> str:
        """
        Generate table summary using the configured template.
        
        Args:
            tables_data: List of table dictionaries
            
        Returns:
            Formatted table summary string
        """
        if not tables_data:
            return self.prompt_templates.no_tables_message
        
        summary_parts = []
        max_tables = self.model_config.max_tables_summary
        
        for i, table in enumerate(tables_data[:max_tables]):
            headers = table.get("headers", [])
            row_count = len(table.get("data", []))
            
            summary = self.prompt_templates.table_summary_template.format(
                index=i+1,
                headers=headers,
                row_count=row_count
            )
            summary_parts.append(summary)
            
        return "\n".join(summary_parts)
    
    def get_error_fallback(self, error_message: str) -> dict:
        """
        Generate error fallback structure using the template.
        
        Args:
            error_message: Error description
            
        Returns:
            Parsed error structure dictionary
        """
        try:
            error_json = self.prompt_templates.error_fallback_template.format(
                error_message=error_message
            )
            return json.loads(error_json)
        except json.JSONDecodeError:
            # Ultimate fallback
            return {
                "product_identification": {},
                "technical_specifications": {},
                "extraction_metadata": {
                    "confidence_score": 0.0,
                    "error": error_message,
                }
            }


# Global configuration instance
_ai_config_manager = None


def get_ai_config() -> AIConfigManager:
    """Get the global AI configuration manager instance."""
    global _ai_config_manager
    if _ai_config_manager is None:
        _ai_config_manager = AIConfigManager()
    return _ai_config_manager


def reload_ai_config(config_file: Optional[Path] = None):
    """Reload AI configuration from file and environment."""
    global _ai_config_manager
    _ai_config_manager = AIConfigManager(config_file)
    return _ai_config_manager 