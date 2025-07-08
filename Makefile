# English Learning Platform - Makefile

.PHONY: help build up down logs restart clean dev prod setup pull health

# Default target
help:
	@echo "English Learning Platform - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment with hot reload"
	@echo "  make dev-logs     - View development logs"
	@echo "  make dev-down     - Stop development environment"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-logs    - View production logs"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "General:"
	@echo "  make build        - Build all images"
	@echo "  make pull         - Pull latest base images"
	@echo "  make setup        - Setup Ollama models"
	@echo "  make health       - Check service health"
	@echo "  make clean        - Clean up containers, volumes, and images"
	@echo "  make restart      - Restart all services"
	@echo ""

# Development commands
dev:
	@echo "🚀 Starting development environment..."
	@chmod +x deploy.sh
	@./deploy.sh --dev --setup-models

dev-logs:
	@docker-compose -f docker-compose.dev.yml logs -f

dev-down:
	@echo "🛑 Stopping development environment..."
	@docker-compose -f docker-compose.dev.yml down

# Production commands
prod:
	@echo "🚀 Starting production environment..."
	@chmod +x deploy.sh
	@./deploy.sh --setup-models

prod-logs:
	@docker-compose -f docker-compose.yml logs -f

prod-down:
	@echo "🛑 Stopping production environment..."
	@docker-compose -f docker-compose.yml down

# Build commands
build:
	@echo "🏗️  Building all images..."
	@docker-compose -f docker-compose.yml build
	@docker-compose -f docker-compose.dev.yml build

build-no-cache:
	@echo "🏗️  Building all images (no cache)..."
	@docker-compose -f docker-compose.yml build --no-cache
	@docker-compose -f docker-compose.dev.yml build --no-cache

# Utility commands
pull:
	@echo "📥 Pulling latest base images..."
	@docker-compose -f docker-compose.yml pull
	@docker-compose -f docker-compose.dev.yml pull

setup:
	@echo "🤖 Setting up Ollama models..."
	@chmod +x setup-ollama.sh
	@docker-compose exec ollama bash -c "cd / && curl -sSL https://raw.githubusercontent.com/yourusername/english-learning-platform/main/setup-ollama.sh | bash"

health:
	@echo "🏥 Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "Backend health:"
	@curl -s http://localhost:8000/ || echo "Backend not responding"
	@echo ""
	@echo "Ollama health:"
	@curl -s http://localhost:11434/api/tags || echo "Ollama not responding"

logs:
	@docker-compose logs -f

restart:
	@echo "🔄 Restarting all services..."
	@docker-compose restart

# Cleanup commands
clean:
	@echo "🧹 Cleaning up..."
	@docker-compose -f docker-compose.yml down -v --remove-orphans
	@docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	@docker system prune -f
	@docker volume prune -f

clean-all:
	@echo "🧹 Deep cleaning (WARNING: This will remove all unused Docker resources)..."
	@docker-compose -f docker-compose.yml down -v --remove-orphans
	@docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	@docker system prune -a -f
	@docker volume prune -f

# Database commands
db-backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	@docker-compose exec mongodb mongodump --uri="mongodb://admin:password123@localhost:27017/EnglishLearning?authSource=admin" --out=/tmp/backup
	@docker cp english-learning-mongodb:/tmp/backup ./backups/backup-$(shell date +%Y%m%d-%H%M%S)
	@echo "✅ Backup created in ./backups/"

db-restore:
	@echo "📥 Restoring database..."
	@read -p "Enter backup directory name: " backup && \
	docker cp ./backups/$$backup english-learning-mongodb:/tmp/restore && \
	docker-compose exec mongodb mongorestore --uri="mongodb://admin:password123@localhost:27017/EnglishLearning?authSource=admin" /tmp/restore/EnglishLearning

# Shell access
shell-backend:
	@docker-compose exec backend /bin/bash

shell-frontend:
	@docker-compose exec frontend /bin/sh

shell-mongodb:
	@docker-compose exec mongodb mongosh "mongodb://admin:password123@localhost:27017/EnglishLearning?authSource=admin"

shell-ollama:
	@docker-compose exec ollama /bin/bash

# Install and run
install: build dev

# Quick start for first time users
quick-start:
	@echo "🚀 Quick start for English Learning Platform"
	@echo "============================================"
	@echo ""
	@echo "This will:"
	@echo "1. Build all Docker images"
	@echo "2. Start the development environment"
	@echo "3. Download required AI models"
	@echo ""
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@make build
	@make dev
