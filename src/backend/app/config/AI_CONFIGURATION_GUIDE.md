# AI Configuration System Guide

## 📋 Overview

The AI Configuration System provides flexible, externalized configuration for all AI-related settings, replacing hardcoded values with configurable parameters. This enables easy customization of AI behavior without code changes.

## 🔧 Configuration Sources

Configuration is loaded in the following priority order:

1. **Environment Variables** (Highest Priority)
2. **Configuration Files** (ai_config.json)
3. **Default Values** (Lowest Priority)

## 🌍 Environment Variables

### Model Configuration

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `AI_MODEL_NAME` | string | `claude-3-5-haiku-20241022` | Claude model to use |
| `AI_PROVIDER` | string | `anthropic` | AI provider (future: openai, etc.) |
| `AI_TEMPERATURE` | float | `0.0` | Temperature for AI responses (0.0-1.0) |
| `AI_MAX_TOKENS` | int | `8192` | Maximum tokens for AI responses |
| `AI_MIN_TOKENS` | int | `2048` | Minimum tokens before retry |
| `AI_TOKEN_DECREMENT` | int | `1024` | Token reduction per retry |
| `AI_MAX_RETRIES` | int | `3` | Maximum API call retries |
| `AI_TIMEOUT_SECONDS` | int | `30` | API call timeout |
| `AI_MAX_TEXT_LENGTH` | int | `8000` | Maximum text content length |
| `AI_MAX_TABLES_SUMMARY` | int | `3` | Maximum tables to summarize |

### Prompt Templates

| Environment Variable | Description |
|---------------------|-------------|
| `AI_EXTRACTION_PROMPT` | Main extraction prompt template |
| `AI_TABLE_SUMMARY_TEMPLATE` | Template for table summaries |
| `AI_NO_TABLES_MESSAGE` | Message when no tables found |
| `AI_ERROR_FALLBACK_TEMPLATE` | Error response template |

## 📄 Configuration File Format

Create `ai_config.json` in the config directory:

```json
{
  "model": {
    "model_name": "claude-3-5-haiku-20241022",
    "provider": "anthropic",
    "temperature": 0.0,
    "max_tokens": 8192,
    "min_tokens": 2048,
    "token_decrement": 1024,
    "max_retries": 3,
    "timeout_seconds": 30,
    "max_text_length": 8000,
    "max_tables_summary": 3
  },
  "prompts": {
    "extraction_prompt": "Your custom prompt template...",
    "table_summary_template": "Table {index}: Headers={headers}, Rows={row_count}",
    "no_tables_message": "No tables were extracted from the document.",
    "error_fallback_template": "{\n  \"error\": \"{error_message}\"\n}"
  }
}
```

## 🚀 Usage Examples

### Basic Configuration

```bash
# Set environment variables
export AI_MODEL_NAME="claude-3-5-sonnet-20241022"
export AI_TEMPERATURE="0.1"
export AI_MAX_TOKENS="4096"

# Run your application
python your_script.py
```

### Runtime Configuration Updates

```python
from app.services.ai_service import AnalysisService

# Initialize service
service = AnalysisService()

# Update configuration at runtime
service.update_model_config(
    temperature=0.2,
    max_tokens=6144
)

# Reload configuration from files
service.reload_configuration()

# Get current configuration
config = service.get_current_config()
print(f"Current model: {config['model_name']}")
```

### Custom Prompt Templates

```python
from app.config.ai_config import get_ai_config

# Get configuration manager
config = get_ai_config()

# Update prompt template
new_prompt = """
Custom extraction prompt for {filename}:
{text_content}

Extract data in JSON format.
"""

config.update_prompt_template('extraction_prompt', new_prompt)

# Save to file for persistence
config.save_to_file()
```

## 🎯 Configuration Scenarios

### Development Environment

```bash
# More verbose, higher temperature for experimentation
export AI_TEMPERATURE="0.3"
export AI_MAX_TOKENS="8192"
export AI_MAX_TEXT_LENGTH="10000"
```

### Production Environment

```bash
# Optimized for consistency and performance
export AI_TEMPERATURE="0.0"
export AI_MAX_TOKENS="4096"
export AI_MAX_TEXT_LENGTH="6000"
export AI_TIMEOUT_SECONDS="15"
```

### Testing Environment

```bash
# Fast, minimal configuration for testing
export AI_MODEL_NAME="claude-3-5-haiku-20241022"
export AI_MAX_TOKENS="2048"
export AI_MIN_TOKENS="1024"
export AI_TIMEOUT_SECONDS="10"
```

## 🔍 Monitoring and Debugging

### Check Current Configuration

```python
from app.services.ai_service import AnalysisService

service = AnalysisService()
config = service.get_current_config()

print("Current AI Configuration:")
for key, value in config.items():
    print(f"  {key}: {value}")
```

### Configuration Validation

The system automatically validates configuration values:

- **Temperature**: Must be between 0.0 and 1.0
- **Tokens**: min_tokens must be ≤ max_tokens
- **Timeouts**: Must be positive integers
- **Text length**: Must be positive

Invalid values are logged as warnings and defaults are used.

## 🛠️ Advanced Features

### Dynamic Model Switching

```python
# Switch to different model for specific tasks
service.update_model_config(
    model_name="claude-3-5-sonnet-20241022",
    temperature=0.1
)

# Process with new model
result = await service.analyze_pdf_content(text, tables, filename)

# Switch back
service.update_model_config(
    model_name="claude-3-5-haiku-20241022",
    temperature=0.0
)
```

### Prompt Template Customization

```python
# Custom prompt for specific document types
leier_prompt = """
Analyze this LEIER construction product datasheet:
{text_content}

Focus on:
- Building block specifications
- Thermal properties
- Structural characteristics

Output JSON format: {...}
"""

config.update_prompt_template('extraction_prompt', leier_prompt)
```

### Configuration Backup and Restore

```python
from pathlib import Path

# Save current configuration
config.save_to_file(Path("backup_config.json"))

# Restore from backup
from app.config.ai_config import reload_ai_config
reload_ai_config(Path("backup_config.json"))
```

## ⚠️ Best Practices

### 1. Environment-Specific Configuration

- Use environment variables for deployment-specific settings
- Use configuration files for stable, shared settings
- Document all custom configurations

### 2. Testing Configuration Changes

- Test configuration changes in development first
- Monitor AI response quality after changes
- Keep backup configurations for rollback

### 3. Security Considerations

- Never commit API keys to configuration files
- Use environment variables for sensitive data
- Restrict access to configuration files in production

### 4. Performance Optimization

- Lower temperature (0.0-0.1) for consistent extraction
- Adjust max_tokens based on document complexity
- Monitor API call patterns and adjust retry settings

## 🔧 Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   ```bash
   # Check file permissions
   ls -la ai_config.json
   
   # Verify JSON syntax
   python -m json.tool ai_config.json
   ```

2. **Environment Variables Not Applied**
   ```bash
   # Verify environment variables
   env | grep AI_
   
   # Check variable names (case sensitive)
   echo $AI_MODEL_NAME
   ```

3. **Invalid Configuration Values**
   ```python
   # Check logs for validation warnings
   import logging
   logging.basicConfig(level=logging.WARNING)
   
   # Validate current config
   service = AnalysisService()
   config = service.get_current_config()
   ```

### Debug Mode

```bash
# Enable detailed logging
export LOG_LEVEL="DEBUG"

# Run with configuration debugging
python -c "
from app.config.ai_config import get_ai_config
config = get_ai_config()
print('Model Config:', config.get_model_config())
print('Prompt Templates:', config.get_prompt_templates())
"
```

## 📚 Related Documentation

- **Service Architecture**: `src/backend/processing/REFACTORING_DOCUMENTATION.md`
- **AI Service API**: `src/backend/app/services/ai_service.py`
- **Configuration Examples**: `src/backend/app/config/ai_config.example.json`

---

*Last Updated: 2025-01-28*
*Version: 1.0.0*
*Configuration System: Production Ready* 