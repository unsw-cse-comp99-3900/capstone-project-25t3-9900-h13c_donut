# FastAPI WebSocket Server Makefile

.PHONY: help install dev build up down logs clean test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

build: ## Build Docker image
	docker build -t fastapi-websocket .

up: ## Start services with Docker Compose
	docker-compose up -d

down: ## Stop services
	docker-compose down

logs: ## View logs
	docker-compose logs -f

clean: ## Clean up temporary files and Docker resources
	docker-compose down -v
	docker system prune -f
	rm -rf temp_audio/*
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

test: ## Run tests (placeholder)
	@echo "Tests not implemented yet"

setup-env: ## Create .env file from example
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

check-deps: ## Check if all dependencies are installed
	python -c "import fastapi, uvicorn, websockets, sqlalchemy, alembic, httpx, jose, passlib; print('All dependencies installed')"

create-temp-dir: ## Create temporary audio directory
	mkdir -p temp_audio

init: install create-temp-dir setup-env ## Initialize project for development
	@echo "Project initialized. Please edit .env file and run 'make dev'"


