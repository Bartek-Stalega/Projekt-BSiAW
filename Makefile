.DEFAULT_GOAL := help
VENV := .venv
PY := $(VENV)/bin/python

.PHONY: help install run test lint up down logs seed

help: ## Lista dostepnych komend
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Tworzy .venv i instaluje zaleznosci
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt

run: ## Uruchamia aplikacje lokalnie na SQLite (bez Dockera)
	$(VENV)/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 43117

test: ## Uruchamia testy
	$(PY) -m pytest

lint: ## Sprawdza styl kodu
	$(VENV)/bin/ruff check app tests scripts

up: ## Uruchamia srodowisko w Dockerze
	docker compose up --build -d

down: ## Zatrzymuje srodowisko Docker
	docker compose down

logs: ## Podglad logow aplikacji
	docker compose logs -f app

seed: ## Dodaje dane demonstracyjne
	docker compose exec app python -m scripts.seed_demo_data

seed-force: ## Nadpisuje dane demonstracyjne
	docker compose exec app python -m scripts.seed_demo_data --force
