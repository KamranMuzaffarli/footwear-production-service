# FootwearProductionService

FootwearProductionService is an asynchronous FastAPI backend built on top of the existing PostgreSQL manufacturing data model maintained by FootwearProductionCore. It exposes the Core schema through a REST API and adds application-level workflows around Shoe Models, Model Classes, material compositions, cloning, and production-readiness validation.

The project is intentionally focused on backend application design: asynchronous database access, explicit responsibility boundaries, transactional business workflows, integration testing against PostgreSQL, Docker-based execution, and automated CI.

## Key Capabilities

- Shoe Last read API with filtering and detailed size data
- Shoe Model read, create, and partial update workflows
- Model Class read, create, update, and transactional clone
- Material catalog and material attribute reads
- Reference data for construction methods, material categories, and usage roles
- Production Composition create, update, soft-deactivate, and reactivate lifecycle
- Duplicate composition protection
- Aggregated Production Specification
- Production-readiness diagnostics with structured validation issues
- Centralized application errors for service-layer business workflows
- Asynchronous PostgreSQL access through SQLAlchemy and asyncpg
- PostgreSQL-backed unit and integration test strategy
- Docker Compose development environment
- GitHub Actions quality gate

## Core Business Workflows

### Production Composition

A Model Class can define the materials required for production through Production Composition records.

The lifecycle is:

```text
create
→ update
→ soft-deactivate
→ optionally reactivate the same record
```

A composition is uniquely identified by the combination of:

```text
Model Class
+ Material
+ Material Usage Role
```

Creating an already active combination produces a conflict instead of creating a duplicate row.

If the same combination exists but was previously soft-deactivated, the service reactivates and updates that existing record rather than creating another database row.

This preserves composition identity while retaining soft-deactivation semantics.

### Transactional Model Class Clone

A Model Class can be cloned together with its active Production Composition.

Conceptually:

```text
source Model Class
+ active composition rows
↓
new Model Class
+ copied composition rows
↓
single transaction
```

Only active composition rows are copied.

The Service layer owns the transaction boundary. If any part of the clone fails, the complete operation is rolled back:

```text
failure
→ rollback
→ no partially cloned Model Class
```

### Production Specification

The Production Specification endpoint builds an aggregated manufacturing view for a Model Class.

It combines:

```text
Shoe Model
+ Shoe Last
+ Model Class
+ Construction Method
+ active Production Composition
+ Materials
+ Material Categories
+ Material Attributes
+ Material Usage Roles
```

The service then evaluates production readiness and returns:

```text
is_production_ready
validation_issues
```

Readiness checks include inactive domain entities, missing active composition, missing consumption quantities or units, and invalid consumption quantities.

A valid existing Model Class that is not production-ready is not treated as an HTTP error. The endpoint returns HTTP `200` with:

```json
{
  "is_production_ready": false,
  "validation_issues": [
    {
      "code": "...",
      "message": "..."
    }
  ]
}
```

The response reflects the actual FootwearProductionCore schema. There is no separate fabricated `production_standard` field.

## Architecture

The main write/business workflow is:

```text
HTTP request
→ FastAPI Router
→ Pydantic Schema
→ Service
→ Repository
→ SQLAlchemy AsyncSession
→ PostgreSQL
```

For small read-only slices where a Service layer would add no business behavior, the project deliberately uses the shorter path:

```text
HTTP request
→ FastAPI Router
→ Pydantic Schema
→ Repository
→ SQLAlchemy AsyncSession
→ PostgreSQL
```

The architecture therefore follows responsibility rather than forcing every endpoint through an identical number of layers.

### Responsibility Boundaries

| Layer | Responsibility |
|---|---|
| Router | HTTP routing, dependencies, status codes, request/response integration |
| Pydantic Schema | Request and response shape, basic validation, mutation surface |
| Service | Business rules, validation across entities, transaction orchestration |
| Repository | Persistence queries and database mutations |
| SQLAlchemy AsyncSession | Asynchronous database session and unit-of-work mechanism |
| PostgreSQL | Final relational and integrity constraints |

Repositories perform persistence operations and may `flush()` changes inside the active session.

For business write workflows, the Service layer owns transaction completion:

```text
success → commit
failure → rollback
```

## Asynchronous Database Access

The backend uses:

- FastAPI
- SQLAlchemy 2.x `AsyncSession`
- asyncpg

for asynchronous I/O-bound interaction with PostgreSQL.

The application creates an async SQLAlchemy engine from `DATABASE_URL` and provides reusable `AsyncSession` instances through FastAPI dependencies.

## Database Ownership

FootwearProductionService **does not own the PostgreSQL schema**.

The schema belongs to the separate **FootwearProductionCore** project, which remains the authoritative source for:

- DDL
- schema migrations
- data migrations
- seed data

FootwearProductionService maps the existing Core schema through SQLAlchemy ORM models.

The backend currently maps 11 Core tables and intentionally does not duplicate Core SQL files in this repository.

For the same reason, v1 does not introduce Alembic as a second schema-management authority. Database evolution remains the responsibility of FootwearProductionCore.

### Core Compatibility

The CI environment currently validates this backend against the following immutable FootwearProductionCore revision:

```text
3f326652b9290af92292e6a0e9d25c6245afe5d3
```

Changing the Core schema therefore does not silently change the database version used by backend CI.

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| Database | PostgreSQL 18.3 |
| ORM | SQLAlchemy 2.x async |
| PostgreSQL driver | asyncpg |
| Validation/configuration | Pydantic, pydantic-settings |
| Testing | pytest, pytest-asyncio, HTTPX |
| Code quality | Ruff |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |
| Logging | Python standard `logging` |

## API Overview

The application exposes **21 business endpoints** under `/api/v1` and **22 endpoints total** including `/health`.

### Shoe Last

```text
GET /api/v1/shoe-lasts
GET /api/v1/shoe-lasts/{shoe_last_id}
```

Supports filtering by last type, gender category, and size system.

### Shoe Model

```text
GET   /api/v1/models
POST  /api/v1/models
GET   /api/v1/models/{shoe_model_id}
PATCH /api/v1/models/{shoe_model_id}

GET  /api/v1/models/{shoe_model_id}/classes
POST /api/v1/models/{shoe_model_id}/classes
```

### Model Class

```text
GET   /api/v1/model-classes/{shoe_model_class_id}
PATCH /api/v1/model-classes/{shoe_model_class_id}

POST /api/v1/model-classes/{shoe_model_class_id}/clone
GET  /api/v1/model-classes/{shoe_model_class_id}/specification
```

### Production Composition

```text
GET    /api/v1/model-classes/{shoe_model_class_id}/materials
POST   /api/v1/model-classes/{shoe_model_class_id}/materials
PATCH  /api/v1/model-classes/{shoe_model_class_id}/materials/{composition_id}
DELETE /api/v1/model-classes/{shoe_model_class_id}/materials/{composition_id}
```

`DELETE` performs soft-deactivation rather than physical deletion.

### Materials

```text
GET /api/v1/materials
GET /api/v1/materials/{material_id}
```

Material listing supports pagination, category filtering, active-state filtering, and text search.

### Reference Data

```text
GET /api/v1/construction-methods
GET /api/v1/material-categories
GET /api/v1/material-usage-roles
```

### System

```text
GET /health
```

Interactive API documentation is available at:

```text
/docs
/openapi.json
```

## Error Semantics

The application distinguishes transport/request validation from domain errors.

| Status | Meaning |
|---|---|
| `400` | Business rule violation |
| `404` | Requested entity does not exist |
| `409` | Conflict with existing state or uniqueness rules |
| `422` | FastAPI/Pydantic request validation failure |
| `503` | PostgreSQL unavailable during `/health` |

Service-layer application errors use the centralized response format:

```json
{
  "error": {
    "code": "conflict",
    "message": "..."
  }
}
```

Available application error codes include:

```text
business_rule_violation
entity_not_found
conflict
```

Some simple repository-backed read endpoints use FastAPI's standard `HTTPException` 404 response instead of the service-layer application error envelope.

Production readiness is different from an application error. An existing Model Class may return:

```text
HTTP 200
is_production_ready = false
validation_issues = [...]
```

## Testing

The current test suite contains:

```text
42 unit tests
36 integration tests
78 total
```

### Unit Tests

Unit tests focus primarily on Service behavior using controlled or mocked persistence/session collaborators.

They verify business rules such as:

- missing or inactive related entities
- duplicate Shoe Model and Model Class codes
- transaction commit behavior
- rollback after integrity errors
- composition duplicate handling
- composition reactivation
- soft-deactivation
- Model Class cloning
- Production Specification readiness rules
- collection of multiple validation issues

### Integration Tests

Integration tests exercise the real application stack:

```text
HTTPX
→ FastAPI
→ Service
→ Repository
→ SQLAlchemy
→ dedicated PostgreSQL test database
```

Important integration scenarios include:

- Shoe Last, Shoe Model, Material, and Reference Data reads
- Shoe Model create/read/update lifecycle
- Model Class create/read/update lifecycle
- Production Composition full lifecycle
- immutable composition identity fields
- composition soft-deactivation
- Model Class clone
- rollback of partial clone database work
- Production Specification ready state
- Production Specification not-ready state
- aggregation of multiple readiness issues

### Integration-Test Isolation

Integration tests use a dedicated PostgreSQL test database.

The database session is bound to an outer test transaction and uses:

```text
join_transaction_mode="create_savepoint"
```

This allows application Services to execute real:

```python
await session.commit()
```

while the test infrastructure still rolls back database changes after each test.

`TEST_DATABASE_URL` must point to a database different from `DATABASE_URL`. The test infrastructure fails fast rather than allowing integration tests to run against the normal application database.

## Docker

The Docker Compose environment contains two services:

```text
api
db
```

Networking is:

```text
host → localhost:${API_PORT} → api:8000
api  → db:5432
```

The default host PostgreSQL mapping is:

```text
localhost:5433 → db:5432
```

This avoids conflict with a PostgreSQL server that may already be running locally on port `5432`.

Docker characteristics:

- `python:3.12-slim` backend image
- Uvicorn bound to `0.0.0.0:8000`
- non-root `appuser`
- PostgreSQL `18.3`
- `pg_isready` database healthcheck
- named PostgreSQL data volume
- no `.env` copied into the backend image
- no Core SQL copied into the backend repository or image

## Continuous Integration

GitHub Actions runs the `CI` workflow on:

```text
push
pull_request
```

The quality job uses an Ubuntu runner and performs:

```text
PostgreSQL 18.3 service
→ backend checkout
→ Python 3.12
→ project installation
→ FootwearProductionCore checkout at pinned commit
→ dedicated test database creation
→ Core schema/data initialization
→ database sanity check
→ Ruff lint check
→ Ruff format check
→ full pytest suite
```

The Core revision used by CI is:

```text
3f326652b9290af92292e6a0e9d25c6245afe5d3
```

The CI PostgreSQL database is ephemeral and does not depend on a developer's local `.env`, local PostgreSQL installation, or workstation state.

## Prerequisites

### Direct Python Workflow

- Git
- Python 3.12+
- PostgreSQL
- FootwearProductionCore

### Docker Workflow

- Git
- Docker with Docker Compose
- FootwearProductionCore

A separate host PostgreSQL installation is not required for the Docker workflow.

## Environment Variables

`.env.example` documents the supported local configuration.

### Application

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy application database URL |
| `TEST_DATABASE_URL` | Dedicated integration-test database URL |
| `LOG_LEVEL` | Python application log level |

Example placeholders:

```dotenv
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name
TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name_test
LOG_LEVEL=INFO
```

### Docker Compose

| Variable | Purpose | Default/example |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL container user | `postgres` |
| `POSTGRES_PASSWORD` | Local container password | replace locally |
| `POSTGRES_DB` | PostgreSQL container database | `footwear_production_core` |
| `POSTGRES_HOST_PORT` | PostgreSQL port exposed to host | `5433` |
| `API_PORT` | API port exposed to host | `8000` |

Do not commit real credentials. The repository tracks `.env.example`; local `.env` is excluded from Git.

## Local Python Setup

Clone both repositories:

```bash
git clone https://github.com/KamranMuzaffarli/footwear-production-core.git
git clone https://github.com/KamranMuzaffarli/footwear-production-service.git
```

For the backend compatibility boundary documented above, check out the tested Core revision:

```bash
cd footwear-production-core
git checkout 3f326652b9290af92292e6a0e9d25c6245afe5d3
cd ..
```

Create and initialize a PostgreSQL database using **FootwearProductionCore** as the schema authority.

Apply the Core database lifecycle in its documented order:

```text
DDL
→ schema migration
→ data migration
→ seed data
```

Then enter the backend repository:

```bash
cd footwear-production-service
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it using the command appropriate for your shell.

Upgrade pip and install the project with test and development extras:

```bash
python -m pip install --upgrade pip
python -m pip install ".[test,dev]"
```

Create a local `.env` from `.env.example` and set `DATABASE_URL` to the initialized Core database.

For example:

```dotenv
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/footwear_production_core
TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/footwear_production_test
LOG_LEVEL=INFO
```

Run the application:

```bash
uvicorn app.main:app --reload
```

Verify:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## Docker Setup

Clone FootwearProductionCore and FootwearProductionService into neighboring directories.

Inside the backend repository, create `.env` from `.env.example` and provide a local Docker PostgreSQL password.

Start PostgreSQL first:

```bash
docker compose up -d db
```

The database container is published on host port `5433` by default.

The PostgreSQL schema and seed data must still be initialized from the **original FootwearProductionCore files**. Docker Compose provides the database infrastructure; it does not become a second schema authority.

The verified initialization order is:

```text
database/ddl/01_reference_tables.sql
→ database/schema_migrations/001_update_shoe_models_classification_fields.sql
→ database/data_migrations/001_add_padding_material_category.sql
→ database/dml/01_seed_data.sql
```

Example using PowerShell from the backend repository when the Core repository is a neighboring directory:

```powershell
$core = "..\footwear-production-core"
$psql = 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

Get-Content -Raw -Encoding UTF8 "$core\database\ddl\01_reference_tables.sql" |
    docker compose exec -T db sh -c $psql

Get-Content -Raw -Encoding UTF8 "$core\database\schema_migrations\001_update_shoe_models_classification_fields.sql" |
    docker compose exec -T db sh -c $psql

Get-Content -Raw -Encoding UTF8 "$core\database\data_migrations\001_add_padding_material_category.sql" |
    docker compose exec -T db sh -c $psql

Get-Content -Raw -Encoding UTF8 "$core\database\dml\01_seed_data.sql" |
    docker compose exec -T db sh -c $psql
```

Do not run the Core demo-query script as part of initialization.

After the database is initialized, start the API:

```bash
docker compose up -d api
```

Check service state:

```bash
docker compose ps
```

Then verify:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

Useful operational commands include:

```bash
docker compose logs api
docker compose logs db
docker compose restart api
docker compose down
```

`docker compose down` preserves the named PostgreSQL volume.

To remove the Docker database data as well:

```bash
docker compose down -v
```

## Running Tests

Tests require a dedicated PostgreSQL database initialized from FootwearProductionCore.

Set:

```dotenv
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/application_database
TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/test_database
```

The two URLs must not identify the same database.

Initialize the test database with the same Core lifecycle:

```text
DDL
→ schema migration
→ data migration
→ seed data
```

Then run:

```bash
pytest -v
```

Current baseline:

```text
78 passed
```

## Code Quality

Run lint checks:

```bash
ruff check app tests
```

Verify formatting without modifying files:

```bash
ruff format --check app tests
```

CI executes both commands before the test suite.

## Repository Structure

```text
app/
├── api/                  # FastAPI routes, dependencies, exception handlers
├── core/                 # Configuration, logging, application exceptions
├── db/                   # SQLAlchemy base and async session setup
├── models/               # ORM mapping of FootwearProductionCore
├── repositories/         # Persistence queries and mutations
├── schemas/              # Pydantic request/response models
└── services/             # Business rules and transaction orchestration

tests/
├── unit/
└── integration/

.github/
└── workflows/
    └── tests.yml

Dockerfile
docker-compose.yml
pyproject.toml
README.md
```

## Design Decisions

### FootwearProductionCore remains authoritative

The backend maps an existing manufacturing database instead of owning a parallel schema definition. Core DDL, migrations, and seed data remain outside this repository.

### Async database access

FastAPI, SQLAlchemy `AsyncSession`, and asyncpg are used for PostgreSQL I/O.

### Services own business transactions

Repositories mutate and flush data; Services decide when a business operation is committed or rolled back.

### Composition records are soft-deactivated

Deleting a Production Composition disables it rather than physically removing it. Re-adding the same Model Class + Material + Usage Role combination reactivates the existing row.

### Model Class clone is atomic

Class creation and active composition copying form one transaction. Partial clones are rolled back.

### Production readiness is computed state

Production readiness is calculated from the current manufacturing graph and returned together with validation issues rather than persisted as a fabricated standalone standard.

## Scope

Version 1 intentionally focuses on the backend domain and its database integration.

The following technologies are not part of the current scope:

- authentication / JWT
- Redis
- Celery
- microservices
- Kubernetes
- cloud deployment

They were outside the project's domain and Definition of Done rather than being added solely to increase the technology count.