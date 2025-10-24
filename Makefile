# Makefile for Memorizer

.PHONY: help install run build docker-build docker-run clean test

help:
	@echo "Memorizer - Available commands:"
	@echo ""
	@echo "  make install      - Install dependencies in virtual environment"
	@echo "  make run          - Run locally (API + Streamlit)"
	@echo "  make build        - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-stop  - Stop Docker container"
	@echo "  make clean        - Clean temporary files"
	@echo "  make models       - Download LLM models"
	@echo ""

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

run:
	./run-local.sh

build:
	docker build -t memorizer:latest .

docker-run:
	docker run -d \
		-p 8000:8000 \
		-p 8501:8501 \
		-v memorizer-data:/app/data \
		-v memorizer-models:/app/models \
		--name memorizer \
		memorizer:latest
	@echo ""
	@echo "Memorizer is starting..."
	@echo "  UI:  http://localhost:8501"
	@echo "  API: http://localhost:8000"
	@echo ""
	@echo "Check status: docker logs -f memorizer"

docker-stop:
	docker stop memorizer || true
	docker rm memorizer || true

clean:
	rm -rf __pycache__
	rm -rf **/__pycache__
	rm -rf .pytest_cache
	rm -rf *.pyc
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

models:
	./download-models.sh

compose-up:
	docker-compose up -d
	@echo ""
	@echo "Memorizer is starting..."
	@echo "  UI:  http://localhost:8501"
	@echo "  API: http://localhost:8000"
	@echo ""
	@echo "Check logs: docker-compose logs -f"

compose-down:
	docker-compose down

compose-logs:
	docker-compose logs -f
