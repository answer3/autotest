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

# Workflow Overview

The system follows a strict, versioned test lifecycle designed for reproducibility, determinism, and auditability.

---

### 1. Create Test Case and first Revision with request

```text
POST /test-cases
```

A **Test Case** represents a logical test scenario
(e.g., "User can log in and access dashboard").

Each Test Case may have multiple **Revisions**.

Key rules:

- Revisions are **immutable**
- Existing revisions are never modified
- Any change creates a **new revision**

A revision contains:

- Natural language test description
- Placeholder variables instead of real values

All dynamic data must use placeholders:

```text
 <login> <password> <email> <any_variable>
```

#### Example of **nl_text** value:
`
User logs in using <login> and <password> and should see the dashboard.
`

No real credentials or environment-specific values are allowed in revisions.
This makes revisions environment-agnostic and reusable.

You can create new revision with request

```text
POST /test-cases/{test_case_id}/revisions
```

### 2. LLM Plan Proposal Generation

When a revision is ready, the LLM Worker:
1) Consumes a queue task
2) Reads the revision's natural language description
3) Generates a structured DSL plan (JSON format).

**DSL Example:**

```json
{
  "steps": [
    "await page.goto('/login')",
    "await page.fill('#username', '<login>')",
    "await page.fill('#password', '<password>')",
    "await page.click('#submit-login')",
    "etc..."
  ],
  "assertions": [
    "await expect(page).toHaveURL('/secure')",
    "await expect(page.locator('#flash')).toBeVisible()",
    "etc...."
  ]
}
```

The DSL is:

- Strictly structured
- Deterministic
- Limited to allowed Playwright commands

**Important!**
To run test proposal must be marked as **is_ready_for_test = true**
You can do this with request to the endpoint

```text
PATCH /plan-proposals/{plan_proposal_id}/ready
```

### 3. Create Test Run

A Test Run is created explicitly via API.
The request must include:
- Placeholder values mapping
```json

{
  "<login>": "user@example.com",
  "<password>": "secret"
}
```
- Base Url (with protocol and without trailing slash)
```text
http(s)://subdomain.domain.com
```

### 4. Plan Rendering and Execution

The Runner Worker performs:
1) Loads the Plan Proposal
2) Substitutes placeholders with provided values
3) Converts DSL into executable Playwright Python steps
4) Executes via playwright.async_api
5) Captures:
- Final URL
- Executed steps
- Executed assertions
- Video artifact
- Screenshot artifact(in case of "failed")

### 5. Result Persistence

After execution:
1) Status is updated to: "passed" or "failed"
2) Execution metadata is stored in the database
3) Artifact object keys are persisted
4) Optional upload to object storage (S3 / MinIO) is performed

### Design Principles

- Immutable revisions
- Environment-agnostic DSL
- Explicit placeholder injection
- Deterministic execution
- Separation of generation and execution
- Full traceability of artifacts and runs

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
