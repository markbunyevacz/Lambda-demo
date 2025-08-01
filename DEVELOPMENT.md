# Development Guide

This document outlines the development tools and practices for the Lambda.hu project.

## 🛠️ Development Tools

We use modern development tools to ensure code quality, consistency, and maintainability:

### Backend (Python)
- **Poetry**: Dependency management and packaging
- **Black**: Code formatting
- **Ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **MyPy**: Static type checking
- **Pytest**: Testing framework
- **Bandit**: Security linting

### Frontend (TypeScript/React)
- **Prettier**: Code formatting
- **ESLint**: JavaScript/TypeScript linting
- **Jest**: Testing framework
- **TypeScript**: Static type checking

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lambda-hu
   ```

2. **Install pre-commit hooks** (recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Start development environment**
   ```bash
   docker-compose up --build
   ```

## 🧹 Code Quality Tools

### Pre-commit Hooks

We use pre-commit hooks to automatically check code quality before commits. These hooks:
- Format code with Black (Python) and Prettier (TypeScript)
- Lint code with Ruff (Python) and ESLint (TypeScript)
- Check for common issues (trailing whitespace, large files, etc.)
- Run security scans with Bandit

To run pre-commit hooks manually:
```bash
pre-commit run --all-files
```

### Backend Tools

#### Running linters and formatters manually:

```bash
cd src/backend

# Format code with Black
poetry run black .

# Sort imports with isort (built into Ruff)
poetry run ruff check --select I --fix .

# Lint with Ruff
poetry run ruff check .

# Fix automatically fixable issues
poetry run ruff check --fix .

# Type checking with MyPy
poetry run mypy .

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Security scan
poetry run bandit -r app/
```

### Frontend Tools

#### Running linters and formatters manually:

```bash
cd frontend

# Format code with Prettier
yarn format

# Check formatting
yarn format:check

# Lint with ESLint
yarn lint

# Fix automatically fixable linting issues
yarn lint:fix

# Type checking
yarn type-check

# Run tests
yarn test

# Run tests with coverage
yarn test:coverage
```

## 🏗️ Docker Development

### Services
- **Backend**: FastAPI application (port 8000)
- **Frontend**: Next.js application (port 3000)
- **Database**: PostgreSQL (port 5432)
- **Cache**: Redis (port 6379)
- **Vector DB**: ChromaDB (port 8001)

### Common Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild services
docker-compose up --build

# View logs
docker-compose logs -f [service-name]

# Run commands in containers
docker-compose exec backend poetry run python -m app.main
docker-compose exec frontend yarn build

# Stop all services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## 🧪 Testing

### Backend Testing

```bash
cd src/backend

# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_api.py

# Run tests matching pattern
poetry run pytest -k "test_user"

# Generate coverage report
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Frontend Testing

```bash
cd frontend

# Run all tests
yarn test

# Run in watch mode
yarn test:watch

# Run with coverage
yarn test:coverage

# Update snapshots
yarn test -- --updateSnapshot
```

## 🔧 Configuration

### Backend Configuration
- **Poetry**: `src/backend/pyproject.toml`
- **Ruff**: `src/backend/ruff.toml`
- **Environment**: `.env` file

### Frontend Configuration
- **Package**: `frontend/package.json`
- **Prettier**: `frontend/.prettierrc`
- **Jest**: `frontend/jest.config.js`
- **TypeScript**: `frontend/tsconfig.json`
- **ESLint**: `frontend/.eslintrc.json`

### Global Configuration
- **Pre-commit**: `.pre-commit-config.yaml`
- **GitHub Actions**: `.github/workflows/ci.yml`
- **Git**: `.gitignore`

## 🚨 Common Issues & Solutions

### Pre-commit Hooks Failing
If pre-commit hooks fail:
1. Fix the issues manually
2. Stage the changes: `git add .`
3. Try committing again

### Docker Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check service logs
docker-compose logs [service-name]
```

### Poetry Issues
```bash
# Clear Poetry cache
poetry cache clear --all pypi

# Reinstall dependencies
poetry install --no-cache

# Update lock file
poetry lock --no-update
```

## 📈 CI/CD Pipeline

Our GitHub Actions workflow automatically:
1. **Lints and formats** all code
2. **Runs tests** for backend and frontend
3. **Builds Docker images**
4. **Performs security scans**
5. **Runs integration tests**

The pipeline runs on:
- Every push to `main` and `develop` branches
- Every pull request

## 📝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Ensure all tests pass: `poetry run pytest` and `yarn test`
4. Commit your changes (pre-commit hooks will run automatically)
5. Push and create a pull request

## 🔍 IDE Setup

### VS Code
Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Ruff
- TypeScript Importer
- Prettier - Code formatter
- ESLint
- Jest

### PyCharm
- Enable Poetry as the interpreter
- Install Ruff plugin
- Configure Black as external formatter

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pre-commit Documentation](https://pre-commit.com/)