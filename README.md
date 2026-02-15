# Autotest Backend
### LLM-powered test plan generation + Playwright execution engine

---

## Overview

Autotest Backend is a service for dynamically generating and executing browser automation tests.

The system consists of:

- **FastAPI API** — manages test cases, revisions, plan proposals, and test runs
- **LLM Worker** — generates structured test execution plans
- **Runner Worker** — executes plans using Playwright
- **Artifacts Service** — stores execution artifacts (video + screenshot)
- **SQLAlchemy 2.x + Alembic** — database layer
- **Redis Queue** — async task dispatch between API and workers

This architecture enables automated end-to-end test generation, execution, and artifact storage.

---

# Architecture

## API (FastAPI)

Handles:
- Test cases
- Test case revisions
- Plan proposals
- Test runs
- Filtering, pagination, sorting

## LLM Worker

- Consumes plan generation tasks from Redis
- Generates structured execution plan
- Stores `result_payload` in `plan_proposals`

## Runner Worker

- Consumes `run_id`
- Renders plan with placeholders
- Executes steps via Playwright
- Uploads artifacts
- Updates run status (`passed` / `failed`)

## Artifacts

- Stored locally (`ARTIFACTS_ROOT_DIR_PATH`)
- Optional object storage (MinIO / S3 compatible)

---

# Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Redis
- Playwright
- Pydantic v2
- Poetry
- Ruff + MyPy
- Pytest

---

# Local Development (Poetry)

## 1) Install dependencies

```bash
poetry install
```

## 2) Environment variables
#### Create .env in project root:

```bash
cp .env.example .env
```
#### Change variables

## 3) Run database migrations

```bash
poetry run alembic upgrade head
```

## 4) Start API

```bash
poetry run uvicorn app.main:app --reload
```
#### Swagger URL
```bash
http://localhost:8000/docs
```

## 5) Start workers
```bash
poetry run python -m app.workers.llm_worker
poetry run python -m app.workers.run_test_worker
```

---

# Docker setup
### Edit docker-compose.dev.yml
```bash
docker compose -f docker-compose.dev.yml up -d
```

---

# Testing

```bash
poetry run pytest tests/
```

# Code Quality

## Ruff
```bash
poetry run ruff check . --fix
poetry run ruff format .
```

## MyPy
```bash
poetry run mypy .
```

## Pre-commit
```bash
pre-commit install
pre-commit run --all-files
```

# Licence

### Private / Internal project
