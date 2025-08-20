#!/bin/bash

# ============================================================================
# Docker Utility Script for Lambda.hu
# ============================================================================
# Usage: ./docker-utils.sh [command] [options]
#
# Commands:
#   dev       - Start development environment
#   prod      - Start production environment
#   build     - Build all images
#   stop      - Stop all containers
#   clean     - Clean up containers, volumes, and images
#   logs      - Show logs for a service
#   backup    - Backup databases
#   restore   - Restore databases
#   health    - Check health status of all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="lambda"
COMPOSE_DEV="docker-compose.dev.yml"
COMPOSE_PROD="docker-compose.prod.yml"

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "ℹ $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Start development environment
start_dev() {
    print_info "Starting development environment..."
    
    # Check if .env.dev exists
    if [ ! -f .env.dev ]; then
        print_warning ".env.dev not found. Creating from template..."
        cp .env.dev.example .env.dev
        print_info "Please edit .env.dev with your configuration"
        exit 1
    fi
    
    # Start services
    docker-compose -f $COMPOSE_DEV up -d
    
    print_success "Development environment started"
    print_info "Services:"
    print_info "  - Frontend: http://localhost:3000"
    print_info "  - Backend API: http://localhost:8000"
    print_info "  - API Docs: http://localhost:8000/docs"
    print_info "  - pgAdmin: http://localhost:5050"
    print_info "  - Flower (Celery): http://localhost:5555"
    print_info "  - Mailhog: http://localhost:8025"
}

# Start production environment
start_prod() {
    print_info "Starting production environment..."
    
    # Check if .env.prod exists
    if [ ! -f .env.prod ]; then
        print_error ".env.prod not found. Please create it from .env.prod.example"
        exit 1
    fi
    
    # Build images first
    print_info "Building production images..."
    docker-compose -f $COMPOSE_PROD build
    
    # Start services
    docker-compose -f $COMPOSE_PROD up -d
    
    print_success "Production environment started"
}

# Build all images
build_images() {
    print_info "Building all images..."
    
    # Build development images
    print_info "Building development images..."
    docker-compose -f $COMPOSE_DEV build
    
    # Build production images
    print_info "Building production images..."
    docker-compose -f $COMPOSE_PROD build
    
    print_success "All images built successfully"
}

# Stop all containers
stop_all() {
    print_info "Stopping all containers..."
    
    # Stop dev containers
    if [ -f $COMPOSE_DEV ]; then
        docker-compose -f $COMPOSE_DEV down
    fi
    
    # Stop prod containers
    if [ -f $COMPOSE_PROD ]; then
        docker-compose -f $COMPOSE_PROD down
    fi
    
    print_success "All containers stopped"
}

# Clean up everything
clean_all() {
    print_warning "This will remove all containers, volumes, and images for this project"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        exit 0
    fi
    
    print_info "Cleaning up..."
    
    # Stop and remove containers
    docker-compose -f $COMPOSE_DEV down -v --remove-orphans
    docker-compose -f $COMPOSE_PROD down -v --remove-orphans
    
    # Remove images
    docker images | grep $PROJECT_NAME | awk '{print $3}' | xargs -r docker rmi -f
    
    # Prune system
    docker system prune -f
    
    print_success "Cleanup complete"
}

# Show logs for a service
show_logs() {
    SERVICE=$2
    
    if [ -z "$SERVICE" ]; then
        print_error "Please specify a service name"
        print_info "Available services: db, cache, chroma, backend, celery_worker, frontend"
        exit 1
    fi
    
    # Determine which compose file to use
    if docker ps | grep -q "${PROJECT_NAME}-.*-dev"; then
        COMPOSE_FILE=$COMPOSE_DEV
    else
        COMPOSE_FILE=$COMPOSE_PROD
    fi
    
    docker-compose -f $COMPOSE_FILE logs -f $SERVICE
}

# Backup databases
backup_databases() {
    print_info "Backing up databases..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # Backup PostgreSQL
    print_info "Backing up PostgreSQL..."
    docker exec lambda-db pg_dump -U admin lambda_db > "$BACKUP_DIR/postgres.sql"
    
    # Backup Redis
    print_info "Backing up Redis..."
    docker exec lambda-cache redis-cli SAVE
    docker cp lambda-cache:/data/dump.rdb "$BACKUP_DIR/redis.rdb"
    
    # Backup ChromaDB
    print_info "Backing up ChromaDB..."
    docker run --rm -v lambda_chroma_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/chroma.tar.gz -C /data .
    
    print_success "Backup completed: $BACKUP_DIR"
}

# Restore databases
restore_databases() {
    BACKUP_DIR=$2
    
    if [ -z "$BACKUP_DIR" ]; then
        print_error "Please specify backup directory"
        print_info "Available backups:"
        ls -la backups/
        exit 1
    fi
    
    if [ ! -d "backups/$BACKUP_DIR" ]; then
        print_error "Backup directory not found: backups/$BACKUP_DIR"
        exit 1
    fi
    
    print_warning "This will overwrite current data"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        exit 0
    fi
    
    print_info "Restoring databases from backups/$BACKUP_DIR..."
    
    # Restore PostgreSQL
    if [ -f "backups/$BACKUP_DIR/postgres.sql" ]; then
        print_info "Restoring PostgreSQL..."
        docker exec -i lambda-db psql -U admin lambda_db < "backups/$BACKUP_DIR/postgres.sql"
    fi
    
    # Restore Redis
    if [ -f "backups/$BACKUP_DIR/redis.rdb" ]; then
        print_info "Restoring Redis..."
        docker cp "backups/$BACKUP_DIR/redis.rdb" lambda-cache:/data/dump.rdb
        docker exec lambda-cache redis-cli SHUTDOWN SAVE
        docker-compose -f $COMPOSE_FILE restart cache
    fi
    
    # Restore ChromaDB
    if [ -f "backups/$BACKUP_DIR/chroma.tar.gz" ]; then
        print_info "Restoring ChromaDB..."
        docker run --rm -v lambda_chroma_data:/data -v $(pwd)/backups/$BACKUP_DIR:/backup alpine tar xzf /backup/chroma.tar.gz -C /data
    fi
    
    print_success "Restore completed"
}

# Check health status
check_health() {
    print_info "Checking health status of all services..."
    
    # Determine which compose file to use
    if docker ps | grep -q "${PROJECT_NAME}-.*-dev"; then
        COMPOSE_FILE=$COMPOSE_DEV
        ENV="Development"
    else
        COMPOSE_FILE=$COMPOSE_PROD
        ENV="Production"
    fi
    
    print_info "Environment: $ENV"
    echo
    
    # Check each service
    services=("db" "cache" "chroma" "backend" "frontend")
    
    for service in "${services[@]}"; do
        container_name="${PROJECT_NAME}-${service}"
        if [ "$ENV" = "Development" ]; then
            container_name="${container_name}-dev"
        fi
        
        if docker ps | grep -q $container_name; then
            # Get health status
            health=$(docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null || echo "no healthcheck")
            
            if [ "$health" = "healthy" ]; then
                print_success "$service: healthy"
            elif [ "$health" = "no healthcheck" ]; then
                if docker ps | grep -q $container_name; then
                    print_warning "$service: running (no healthcheck)"
                else
                    print_error "$service: not running"
                fi
            else
                print_error "$service: $health"
            fi
        else
            print_error "$service: not running"
        fi
    done
    
    echo
    print_info "Container resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep $PROJECT_NAME || true
}

# Main script
main() {
    check_docker
    
    case "$1" in
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        build)
            build_images
            ;;
        stop)
            stop_all
            ;;
        clean)
            clean_all
            ;;
        logs)
            show_logs $@
            ;;
        backup)
            backup_databases
            ;;
        restore)
            restore_databases $@
            ;;
        health)
            check_health
            ;;
        *)
            echo "Lambda.hu Docker Utility"
            echo ""
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  dev       - Start development environment"
            echo "  prod      - Start production environment"
            echo "  build     - Build all images"
            echo "  stop      - Stop all containers"
            echo "  clean     - Clean up containers, volumes, and images"
            echo "  logs      - Show logs for a service"
            echo "  backup    - Backup databases"
            echo "  restore   - Restore databases"
            echo "  health    - Check health status of all services"
            echo ""
            echo "Examples:"
            echo "  $0 dev                    # Start development environment"
            echo "  $0 logs backend           # Show backend logs"
            echo "  $0 restore 20240101_120000  # Restore from backup"
            ;;
    esac
}

main $@