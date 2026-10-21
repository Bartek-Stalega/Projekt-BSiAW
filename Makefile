.DEFAULT_GOAL := help
VENV := .venv
PY := $(VENV)/bin/python

.PHONY: help venv install run test lint security up down logs seed clean

help: ## Lista dostepnych komend
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Tworzy wirtualne srodowisko
	python3 -m venv $(VENV)

install: venv ## Instaluje zaleznosci deweloperskie
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt

run: ## Uruchamia aplikacje lokalnie na SQLite (bez Dockera)
	APP_DATABASE_URL=sqlite:///./data/secforum.db \
	$(VENV)/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 43117

test: ## Uruchamia testy
	$(PY) -m pytest

lint: ## Analiza statyczna stylu i bledow
	$(VENV)/bin/ruff check app tests scripts
	$(VENV)/bin/ruff format --check app tests scripts

security: ## Skany bezpieczenstwa (SAST + zaleznosci) - baza pod L6
	$(VENV)/bin/bandit -q -c pyproject.toml -r app scripts
	$(VENV)/bin/pip-audit -r requirements.txt

up: ## Uruchamia pelne srodowisko w Dockerze
	docker compose up --build -d

down: ## Zatrzymuje srodowisko Docker (z wolumenem bazy)
	docker compose down -v

logs: ## Podglad logow aplikacji
	docker compose logs -f app proxy

seed: ## Dodaje dane demonstracyjne w kontenerze
	docker compose exec app python -m scripts.seed_demo_data

clean: ## Czysci artefakty lokalne
	rm -rf $(VENV) .pytest_cache .ruff_cache data __pycache__
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
