.PHONY: help build up down clean dev test lint format health logs

# Default target
help:
	@echo "Available commands:"
	@echo "  help      - Show this help message"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start production services"
	@echo "  dev       - Start development services"
	@echo "  down      - Stop all services"
	@echo "  clean     - Remove containers, images, and volumes"
	@echo "  test      - Run tests"
	@echo "  lint      - Run code linting"
	@echo "  format    - Format code"
	@echo "  health    - Check service health"
	@echo "  logs      - Show service logs"
	@echo "  install   - Install local dependencies"
	@echo "  shell     - Access backend shell"

# Build Docker images
build:
	@echo "🐳 Building Docker images..."
	docker compose build --parallel
	docker compose -f docker-compose.dev.yml build --parallel

# Start production services
up:
	@echo "🚀 Starting production services..."
	docker compose up -d
	@echo "✅ Services started!"
	@echo "🌐 OpenWebUI: http://localhost:3000"
	@echo "⚡ Backend: http://localhost:8000"

# Start development services
dev:
	@echo "🛠️ Starting development services..."
	docker compose -f docker-compose.dev.yml up -d
	@echo "✅ Development services started!"
	@echo "🌐 OpenWebUI: http://localhost:3000"
	@echo "⚡ Backend: http://localhost:8000"

# Stop all services
down:
	@echo "🛑 Stopping all services..."
	docker compose down
	docker compose -f docker-compose.dev.yml down

# Clean up containers, images, and volumes
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run linting
lint:
	@echo "🔍 Running linters..."
	docker compose exec backend poetry run black --check backend/
	docker compose exec backend poetry run isort --check-only backend/
	docker compose exec backend poetry run mypy backend/

# Format code
format:
	@echo "✨ Formatting code..."
	docker compose exec backend poetry run black backend/
	docker compose exec backend poetry run isort backend/

# Check service health
health:
	@echo "❤️ Checking service health..."
	@echo "FastAPI Backend:"
	@curl -f http://localhost:8000/health || echo "❌ Backend not responding"
	@echo ""
	@echo "OpenWebUI:"
	@curl -f http://localhost:3000 || echo "❌ OpenWebUI not responding"
	@echo ""
	@echo "Docker containers:"
	@docker compose ps

# Show logs
logs:
	docker compose logs -f

# Install local dependencies
install:
	@echo "📦 Installing local dependencies..."
	pip install poetry
	poetry install

# Access backend shell
shell:
	docker compose exec backend bash

# Quick development setup
setup: install
	@echo "🚀 Setting up development environment..."
	@echo "Creating directories..."
	mkdir -p pdf logs
	@echo "✅ Setup complete!"
	@echo "Run 'make dev' to start development services"