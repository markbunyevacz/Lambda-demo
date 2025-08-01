# Configuration Guide

This document explains how to configure the Lambda.hu AI system for different environments.

## 🔧 Configuration System

The application uses a centralized configuration system built with Pydantic Settings that:
- Validates configuration values at startup
- Supports environment variables and `.env` files
- Provides type safety and auto-completion
- Centralizes all settings in one place

## 📝 Environment File Setup

1. **Copy the example file**:
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file** with your specific values:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Set required values** (see sections below)

## 🗂️ Configuration Sections

### Application Settings
Basic application metadata and runtime configuration:

```bash
APP_TITLE="Lambda.hu Építőanyag AI Rendszer"
APP_DESCRIPTION="AI-alapú építőanyag keresési és ajánlási rendszer"
APP_VERSION="1.0.0"
APP_DEBUG=false
APP_ENVIRONMENT=production
```

### Database Configuration
PostgreSQL is recommended for production:

```bash
# Production (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/lambda_db
DATABASE_ECHO_SQL=false

# Development (SQLite)
DATABASE_URL=sqlite:///./lambda.db
```

### Redis Cache
Used for Celery task queue and general caching:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
```

### ChromaDB Vector Database
Stores document embeddings for similarity search:

```bash
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_FALLBACK_HOST=chroma  # Docker service name
CHROMA_FALLBACK_PORT=8000
CHROMA_COLLECTION_NAME=rockwool_products
```

### AI Model Configuration
**Important**: User requires Haiku 3.5 for PDF extraction:

```bash
AI_MODEL_NAME=claude-3-haiku-20240307
AI_PROVIDER=anthropic
AI_TEMPERATURE=0.0
AI_MAX_TOKENS=8192
```

### CORS Settings
Configure which origins can access your API:

```bash
# Development
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Production
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Security Settings
**Critical**: Change the secret key in production:

```bash
SECURITY_SECRET_KEY=your-super-secret-key-change-this-in-production
SECURITY_ALGORITHM=HS256
SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🐳 Docker Environment

When using Docker Compose, some values are automatically configured:

```yaml
# docker-compose.yml
environment:
  - DATABASE_URL=postgresql://admin:admin@db:5432/lambda_db
  - REDIS_HOST=cache
  - CHROMA_HOST=chroma
```

## 🔍 Configuration Access in Code

The configuration is available throughout the application:

```python
from app.config.settings import settings

# Access configuration values
database_url = settings.database.url
ai_model = settings.ai.model_name
cors_origins = settings.cors.allowed_origins

# Check environment
if settings.is_production:
    # Production-specific logic
    pass
```

## 📋 Environment-Specific Examples

### Development Environment
```bash
APP_DEBUG=true
APP_ENVIRONMENT=development
DATABASE_URL=sqlite:///./dev.db
REDIS_HOST=localhost
CHROMA_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
```

### Production Environment
```bash
APP_DEBUG=false
APP_ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@prod-db:5432/lambda_db
REDIS_HOST=prod-redis
CHROMA_HOST=prod-chroma
CORS_ALLOWED_ORIGINS=https://lambda.hu,https://www.lambda.hu
LOG_LEVEL=INFO
SECURITY_SECRET_KEY=your-production-secret-key
```

### Testing Environment
```bash
APP_ENVIRONMENT=testing
DATABASE_URL=sqlite:///./test.db
REDIS_HOST=localhost
CHROMA_HOST=localhost
CORS_ALLOWED_ORIGINS=*
LOG_LEVEL=WARNING
```

## ⚠️ Security Considerations

1. **Never commit `.env` files** to version control
2. **Change default passwords** and secret keys
3. **Use strong, unique secret keys** in production
4. **Restrict CORS origins** to only your domains
5. **Use HTTPS in production** for all external connections
6. **Rotate secrets regularly**

## 🔄 Configuration Validation

The application validates configuration at startup and will fail fast if:
- Required values are missing
- Values are of the wrong type
- Connections to external services fail

## 🚨 Troubleshooting

### Common Issues

1. **"Settings validation error"**
   - Check all required environment variables are set
   - Verify data types (numbers, booleans, URLs)

2. **"Database connection failed"**
   - Verify DATABASE_URL format and credentials
   - Ensure database server is running

3. **"ChromaDB connection failed"**
   - Check CHROMA_HOST and CHROMA_PORT values
   - Verify ChromaDB service is accessible

4. **"CORS errors in browser"**
   - Add your frontend URL to CORS_ALLOWED_ORIGINS
   - Ensure proper protocol (http/https) is specified

### Debug Configuration

To see current configuration values (without secrets):

```python
from app.config.settings import settings
print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database.url}")
print(f"Debug mode: {settings.debug}")
```

## 📚 Additional Resources

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)