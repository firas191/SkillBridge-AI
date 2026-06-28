# SkillBridge AI — common developer commands.
# Usage: make <target>

.PHONY: help install backend frontend test lint dev-backend dev-frontend

help:
	@echo "Targets:"
	@echo "  install        Install backend + frontend dependencies"
	@echo "  dev-backend    Run FastAPI with autoreload on :8000"
	@echo "  dev-frontend   Run Vite dev server on :5173"
	@echo "  test           Run backend test suite"
	@echo "  compose-up     Start the Docker stack (NVIDIA NIM)"
	@echo "  compose-local  Start the Docker stack with local Ollama"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest

compose-up:
	docker compose up --build

compose-local:
	docker compose --profile local up --build
