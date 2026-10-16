# Riser / mep-estimator local helpers (inspired by DentAway/dental-jobs observability Make).
# Prefer: make help

SHELL := /bin/bash
.DEFAULT_GOAL := help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
WEBAPP_DIR := $(ROOT)/apps/inventory_webapp
UI_DIR := $(WEBAPP_DIR)/ui
ROOT_ENV := $(ROOT)/.env

DATA_DIR ?= /Users/pico/workspace/data/getriser
RISER_UI_PORT ?= 8870
RISER_API_PORT ?= 8871
RISER_COMPOSE_PROJECT ?= riser-inventory
RISER_API_IMAGE ?= riser-inventory-api:local
RISER_UI_IMAGE ?= riser-inventory-ui:local
VITE_API_URL ?=

.PHONY: help ports check-ports \
	build build-webapp up up-webapp down down-webapp ps logs \
	dev-api dev-ui seed-hubby test test-webapp migrate

help:
	@echo "Riser / mep-estimator Make targets"
	@echo ""
	@echo "Webapp (GR-6 inventory review):"
	@echo "  make build / build-webapp   Docker images (API + UI)"
	@echo "  make up / up-webapp         Compose up -d --build"
	@echo "  make down / down-webapp     Compose down"
	@echo "  make ps | logs              Compose status / follow logs"
	@echo "  make dev-api                Host uvicorn :$(RISER_API_PORT)"
	@echo "  make dev-ui                 Host Vite :5173 (proxies /api)"
	@echo "  make seed-hubby             riser-inventory ingest HubbyPremierInnLondon"
	@echo "  make migrate                Ensure review columns on getriser.sqlite"
	@echo "  make test / test-webapp     Pytest gates"
	@echo ""
	@echo "Ports (override if busy — do not commit remaps):"
	@echo "  UI  http://127.0.0.1:$(RISER_UI_PORT)/"
	@echo "  API http://127.0.0.1:$(RISER_API_PORT)/docs"
	@echo "  DATA_DIR=$(DATA_DIR)"
	@echo "  Compose project: $(RISER_COMPOSE_PROJECT)"
	@echo ""
	@$(MAKE) -s ports

ports:
	@echo "Host port map"
	@echo "  $(RISER_UI_PORT)   inventory webapp UI (Docker nginx)"
	@echo "  $(RISER_API_PORT)   inventory webapp API (FastAPI)"
	@echo "  5173   Vite dev UI (make dev-ui)"
	@echo "  8866/8867  dental-jobs observability (avoid)"

check-ports:
	@echo "Checking listeners (empty = free)…"
	@for spec in \
		"$(RISER_UI_PORT):riser-ui" \
		"$(RISER_API_PORT):riser-api" \
		"5173:vite-dev"; do \
		port=$${spec%%:*}; name=$${spec#*:}; \
		hits=$$(lsof -nP -iTCP:$$port -sTCP:LISTEN 2>/dev/null | awk 'NR>1{print $$1" pid="$$2}' | sort -u | tr '\n' ', ' | sed 's/, $$//'); \
		if [ -z "$$hits" ]; then echo "  $$port ($$name): free"; \
		else echo "  $$port ($$name): in use — $$hits"; fi; \
	done

_compose = cd "$(WEBAPP_DIR)" && \
	DATA_DIR="$(DATA_DIR)" \
	RISER_UI_PORT="$(RISER_UI_PORT)" \
	RISER_API_PORT="$(RISER_API_PORT)" \
	RISER_COMPOSE_PROJECT="$(RISER_COMPOSE_PROJECT)" \
	RISER_API_IMAGE="$(RISER_API_IMAGE)" \
	RISER_UI_IMAGE="$(RISER_UI_IMAGE)" \
	VITE_API_URL="$(VITE_API_URL)" \
	docker compose -p "$(RISER_COMPOSE_PROJECT)"

build build-webapp:
	@$(MAKE) -s check-ports
	$(_compose) build

up up-webapp:
	@$(MAKE) -s check-ports
	@test -f "$(DATA_DIR)/getriser.sqlite" || (echo "Missing $(DATA_DIR)/getriser.sqlite — run make seed-hubby"; exit 1)
	$(_compose) up -d --build
	@echo "UI  http://127.0.0.1:$(RISER_UI_PORT)/"
	@echo "API http://127.0.0.1:$(RISER_API_PORT)/docs"

down down-webapp:
	$(_compose) down

ps:
	$(_compose) ps

logs:
	$(_compose) logs -f

dev-api:
	@test -f "$(DATA_DIR)/getriser.sqlite" || (echo "Missing DB — make seed-hubby"; exit 1)
	cd "$(WEBAPP_DIR)" && \
	  DATA_DIR="$(DATA_DIR)" RISER_DB_PATH="$(DATA_DIR)/getriser.sqlite" \
	  uv run --with fastapi --with 'uvicorn[standard]' --with pydantic --with httpx \
	  uvicorn app.main:app --reload --host 127.0.0.1 --port "$(RISER_API_PORT)"

dev-ui:
	cd "$(UI_DIR)" && npm run dev -- --host 127.0.0.1 --port 5173

seed-hubby:
	cd "$(ROOT)" && \
	  DATA_DIR="$(DATA_DIR)" uv run riser-inventory ingest --project HubbyPremierInnLondon

migrate:
	cd "$(WEBAPP_DIR)" && \
	  DATA_DIR="$(DATA_DIR)" uv run --with fastapi --with pydantic \
	  python -c "from app.db import migrate; migrate(); print('migrated', '$(DATA_DIR)/getriser.sqlite')"

test:
	cd "$(ROOT)" && uv run pytest -q
	@$(MAKE) test-webapp

test-webapp:
	cd "$(WEBAPP_DIR)" && \
	  DATA_DIR="$(DATA_DIR)" \
	  PYTHONPATH="$(ROOT)/src:$${PYTHONPATH}" \
	  uv run --with fastapi --with 'uvicorn[standard]' --with pydantic --with httpx --with pytest --with pymupdf \
	  pytest -q
