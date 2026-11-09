.PHONY: help install lint test test-all clean

PYTHON ?= python3
VENV ?= .venv

help:
	@echo "Commandes disponibles :"
	@echo "  make install     - Crée le venv et installe les dépendances (CPU optimisé)"
	@echo "  make lint        - Vérifie la conformité du code avec ruff"
	@echo "  make test        - Lance les tests unitaires rapides (sans modèles lourds)"
	@echo "  make test-all    - Lance tous les tests (unitaires, intégration, kitsune, e2e)"
	@echo "  make clean       - Nettoie les caches et fichiers temporaires"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r envs/main.txt
	$(VENV)/bin/pip install -e .

lint:
	$(VENV)/bin/ruff check src/ tests/

test:
	$(VENV)/bin/pytest tests/unit/ -v -m "not requires_models and not requires_kitsune and not e2e"

test-all:
	$(VENV)/bin/pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
