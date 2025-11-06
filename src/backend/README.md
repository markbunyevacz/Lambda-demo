# Lambda Backend

FastAPI backend service for the Lambda.hu building materials product data platform.

## Features

- RESTful API for product data management
- PDF processing and data extraction pipeline
- Web scraping coordination (Rockwool, Leier, Baumit)
- Semantic search with ChromaDB vector database
- AI-powered product recommendations and compatibility checking
- Celery workers for asynchronous task processing

## Development

```bash
# Install dependencies
poetry install

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

See the main repository README and `docs/` directory for comprehensive documentation.
