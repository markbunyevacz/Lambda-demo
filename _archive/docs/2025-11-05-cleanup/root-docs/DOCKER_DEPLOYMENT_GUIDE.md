# Lambda.hu Docker Deployment Guide

## 🎯 Architecture Overview

Lambda.hu uses a **Docker-first architecture** with proper environment separation:

```
┌─── Development ───┐    ┌─── Production ───┐
│  Hot Reload       │    │  Optimized       │
│  Volume Mounts    │    │  Multi-worker    │  
│  Debug Enabled    │    │  Nginx Proxy     │
│  Flower UI        │    │  SSL/Security    │
└───────────────────┘    └──────────────────┘
```

## 🐳 Complete Docker Stack

- **PostgreSQL 15** - Main database
- **Redis 6.2** - Cache & Celery broker  
- **ChromaDB** - Vector database for RAG
- **FastAPI Backend** - Python API server
- **Next.js Frontend** - React/TypeScript UI
- **Celery Worker** - Async task processing
- **Flower** - Celery monitoring (dev only)
- **Nginx** - Reverse proxy (prod only)

## 🚀 Quick Start

### Prerequisites
```bash
# Start Docker Desktop on Windows
# Ensure Docker is running:
docker --version
docker-compose --version
```

### Development Environment
```bash
# Start all services in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f backend frontend

# Access services:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000  
# Flower: http://localhost:5555
# PostgreSQL: localhost:5432
# ChromaDB: http://localhost:8001
```

### Production Environment  
```bash
# Build and start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Access services:
# Frontend: http://localhost (via nginx)
# Backend: http://localhost/api (via nginx)
```

## 🔧 Environment-Specific Features

### Development Mode
- ✅ **Hot Reload**: Code changes reflect immediately
- ✅ **Volume Mounts**: Local file system mounted  
- ✅ **Debug Enabled**: Detailed error messages
- ✅ **Flower UI**: Celery task monitoring
- ✅ **Direct Port Access**: All services exposed

### Production Mode
- ✅ **Multi-Worker**: uvicorn with 4 workers
- ✅ **Optimized Build**: No dev dependencies
- ✅ **Nginx Proxy**: Reverse proxy with SSL
- ✅ **Security**: Debug disabled, minimal exposure
- ✅ **Auto-Restart**: Services auto-restart on failure

## 📋 Service Management

### View Status
```bash
docker-compose ps
```

### Restart Specific Service
```bash
docker-compose restart backend
docker-compose restart frontend
```

### View Logs
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs -f celery_worker
```

### Database Operations
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U lambda_user -d lambda_db

# Connect to Redis
docker-compose exec cache redis-cli
```

## 🔍 Troubleshooting

### Docker Desktop Not Running
```bash
# Error: "cannot find file specified"
# Solution: Start Docker Desktop application
```

### Port Already in Use
```bash
# Error: "port is already allocated"
# Solution: Stop conflicting services
docker-compose down
# Or change ports in docker-compose.yml
```

### Database Connection Issues
```bash
# Check database health
docker-compose exec db pg_isready -U lambda_user -d lambda_db

# Recreate database volume
docker-compose down -v
docker-compose up -d
```

## 🎯 Why Docker?

### ✅ **Environment Consistency**
- Same environment across dev/staging/prod
- No "works on my machine" issues
- Reproducible builds

### ✅ **Service Orchestration** 
- All services start in correct order
- Network isolation and service discovery
- Health checks and auto-restart

### ✅ **Scalability**
- Easy horizontal scaling
- Load balancing with nginx
- Resource limits and monitoring

### ✅ **Security**
- Network isolation
- Secret management
- Minimal attack surface

## 🚫 What NOT to Do

❌ **Manual Host Execution**: `python -m uvicorn app.main:app --reload`
❌ **Mixed Environments**: Some services in Docker, others on host
❌ **Production in Dev Mode**: Using --reload in production
❌ **No Environment Separation**: Same config for dev and prod

## ✅ What TO Do

✅ **Docker-First**: All services in containers
✅ **Environment-Specific Config**: Separate dev/prod overrides  
✅ **Proper Networking**: Services communicate via Docker networks
✅ **Health Checks**: Monitor service health
✅ **Volume Management**: Persistent data in Docker volumes

---

**Remember**: The whole point of containerization is consistency and isolation. Running manually on the host defeats this purpose! 