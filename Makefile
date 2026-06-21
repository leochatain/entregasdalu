# entregasdalu — one-word dev targets. Backend lives in backend/ and uses uv;
# frontend in frontend/ (npm); prod deploy is docker-compose (see DEPLOY.md).

BACKEND := backend
FRONTEND := frontend
# Run uv from inside backend/ so pytest/pyright pick up backend/pyproject.toml config.
RUN := cd $(BACKEND) && uv run

# Local dev defaults (no Google, no secrets). Override via a repo-root .env.
DEV_ENV := DEBUG=True DEV_LOGIN_ENABLED=True ALLOWED_EMAILS=leochatain@gmail.com \
	DEV_LOGIN_EMAIL=leochatain@gmail.com

.PHONY: help install migrate makemigrations dev run test lint format typecheck check openapi \
	fe-install fe-dev fe-build fe-gen deploy down logs ps

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Sync backend deps + venv from uv.lock
	cd $(BACKEND) && uv sync

migrate:  ## Apply DB migrations
	$(RUN) python manage.py migrate

makemigrations:  ## Generate new migrations for the diary app
	$(RUN) python manage.py makemigrations diary

dev run:  ## Run the dev server (DEBUG + dev-login) on :8000
	cd $(BACKEND) && $(DEV_ENV) uv run python manage.py runserver 0.0.0.0:8000

test:  ## Run the test suite
	$(RUN) pytest

lint:  ## Ruff lint
	$(RUN) ruff check .

format:  ## Ruff format
	$(RUN) ruff format .

typecheck:  ## Pyright
	$(RUN) pyright

check: lint typecheck test  ## Lint + typecheck + tests

openapi:  ## Print the OpenAPI schema (FE codegen source)
	cd $(BACKEND) && DJANGO_SETTINGS_MODULE=config.settings uv run python -c \
		"import django; django.setup(); from diary.api import api; import json; \
		print(json.dumps(api.get_openapi_schema(), indent=2))"

# --- Frontend (npm) -------------------------------------------------------
fe-install:  ## Install frontend deps (npm ci)
	cd $(FRONTEND) && npm ci

fe-dev:  ## Run the Vite dev server (proxies /api to :8000)
	cd $(FRONTEND) && npm run dev

fe-build:  ## Production build of the SPA (vite build)
	cd $(FRONTEND) && npm run build

fe-gen:  ## Regenerate src/api/generated.ts from a running backend (:8000)
	cd $(FRONTEND) && npm run gen:api

# --- Production (docker-compose; see DEPLOY.md) ---------------------------
deploy:  ## Build images and (re)start the stack detached
	docker compose up -d --build

down:  ## Stop the stack
	docker compose down

logs:  ## Follow logs from both services
	docker compose logs -f

ps:  ## Show service status
	docker compose ps
