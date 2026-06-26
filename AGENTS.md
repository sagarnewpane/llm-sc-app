# AGENTS.md — FastAPI Server Development Agent

## Overview

You are an expert FastAPI backend development agent. Your job is to help build, extend, debug, and maintain a FastAPI server. Follow all instructions in this file precisely and consistently across every session.

---

## Environment Setup

### Python & Package Manager: `uv`

**Always use `uv` for all Python environment and package management.** Do not use `pip`, `pip3`, `virtualenv`, or `conda` directly.

#### 1. Install `uv` (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # or restart the shell
```

Verify: `uv --version`

#### 2. Create a virtual environment

```bash
uv venv .venv
```

#### 3. Activate the virtual environment

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Always confirm the venv is active before running any commands. The shell prompt should show `(.venv)`.

#### 4. Install packages

```bash
uv pip install fastapi uvicorn[standard]
uv pip install <package-name>          # add new dependencies
uv pip install -r requirements.txt    # from existing file
```

#### 5. Save dependencies

```bash
uv pip freeze > requirements.txt
```

Or, if using `pyproject.toml`, add dependencies there and run:

```bash
uv pip sync pyproject.toml
```

**Never install packages globally.** Always install inside `.venv`.

---

## Project Structure

Use this standard layout unless the user specifies otherwise:

```
project/
├── .venv/                  # uv-managed virtual environment (never commit)
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app entry point
│   ├── config.py           # Settings via pydantic-settings
│   ├── dependencies.py     # Shared dependency functions
│   ├── routers/            # One file per feature/domain
│   │   └── users.py
│   ├── models/             # SQLAlchemy or other ORM models
│   │   └── user.py
│   ├── schemas/            # Pydantic request/response schemas
│   │   └── user.py
│   ├── services/           # Business logic layer
│   │   └── user_service.py
│   └── db/                 # Database setup and session management
│       └── session.py
├── tests/
│   └── test_main.py
├── requirements.txt
├── .env
└── .gitignore
```

---

## Running the Server

```bash
uvicorn app.main:app --reload           # development
uvicorn app.main:app --host 0.0.0.0 --port 8000  # production-like
```

For production, prefer:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## FastAPI Tips & Best Practices

### App Initialization

```python
# app/main.py
from fastapi import FastAPI
from app.routers import users

app = FastAPI(
    title="My API",
    version="1.0.0",
    description="API description here",
)

app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### Routers

Always split routes into separate router files — never put all routes in `main.py`.

```python
# app/routers/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/{user_id}")
def get_user(user_id: int):
    ...
```

### Pydantic Schemas

Use Pydantic v2 (ships with FastAPI 0.100+). Define separate schemas for input and output:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}  # replaces orm_mode in v2
```

### Configuration with `pydantic-settings`

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()
```

Install: `uv pip install pydantic-settings`

### Dependency Injection

Use `Depends()` for shared logic like DB sessions, auth, and pagination:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    ...
```

### Async Endpoints

Prefer `async def` for I/O-bound routes (DB, HTTP calls). Use `def` for CPU-bound or sync-only libraries:

```python
@router.get("/")
async def list_items():
    result = await some_async_db_call()
    return result
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str):
    ...  # runs after response is sent

@router.post("/register")
def register(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com")
    return {"message": "Registered"}
```

### Error Handling

Use `HTTPException` for expected errors, and custom exception handlers for global ones:

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="User not found")
```

```python
# Global handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

### Response Models

Always declare `response_model` to control what gets serialized and avoid leaking internal fields:

```python
@router.get("/{id}", response_model=UserResponse)
def get_user(id: int):
    ...
```

### Status Codes

Be explicit with status codes:

```python
from fastapi import status

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(...):
    ...
```

### Path & Query Parameters

```python
@router.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = None, skip: int = 0, limit: int = 10):
    ...
```

### Request Body

```python
@router.post("/users/")
def create_user(user: UserCreate):
    ...
```

### Lifespan Events (Startup / Shutdown)

Use the `lifespan` context manager (preferred over deprecated `on_event`):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    yield
    # shutdown
    await close_db()

app = FastAPI(lifespan=lifespan)
```

### CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Versioning

Prefix routers with version numbers:

```python
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
```

---

## Database (SQLAlchemy + Alembic)

Install: `uv pip install sqlalchemy alembic asyncpg psycopg2-binary`

### Session setup (sync)

```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

### Alembic migrations

```bash
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## Authentication

Install: `uv pip install python-jose[cryptography] passlib[bcrypt]`

Use OAuth2 with JWT tokens. Keep auth logic in `app/services/auth_service.py` and expose it via `Depends()`.

---

## Testing

Install: `uv pip install pytest pytest-asyncio httpx`

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
```

Run tests:

```bash
pytest tests/ -v
```

---

## Common Gotchas to Avoid

- **Never** put business logic directly in route functions — use a service layer.
- **Never** import `settings` at module level in tests — patch them via dependency override.
- **Never** use mutable default arguments in Pydantic models or function signatures.
- Pydantic v2 uses `model_dump()` not `.dict()`, and `model_validate()` not `.from_orm()`.
- `async def` routes run in the event loop; calling sync blocking code inside them will block. Use `run_in_executor` or a thread pool for blocking sync calls.
- SQLAlchemy sessions are **not** thread-safe or async-safe by default — use one session per request via `Depends`.
- Always close DB sessions — use `yield` in dependency functions so cleanup runs even on exceptions.
- Do not store secrets in code — use `.env` files loaded via `pydantic-settings`.
- Add `.venv/`, `.env`, and `__pycache__/` to `.gitignore`.

---

## `.gitignore` Essentials

```
.venv/
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/
dist/
```

---

## Useful `uv` Commands Reference

| Task | Command |
|---|---|
| Create venv | `uv venv .venv` |
| Activate venv | `source .venv/bin/activate` |
| Install package | `uv pip install <pkg>` |
| Install from file | `uv pip install -r requirements.txt` |
| Freeze deps | `uv pip freeze > requirements.txt` |
| List installed | `uv pip list` |
| Uninstall | `uv pip uninstall <pkg>` |
| Upgrade package | `uv pip install --upgrade <pkg>` |

---

## Agent Behavior Rules

1. **Always check** if `.venv` exists before installing anything. If not, create it with `uv venv .venv` first.
2. **Always activate** the venv before running any `uv pip` or `python`/`uvicorn` commands.
3. **Always use `uv pip`** — never bare `pip`.
4. When adding a new dependency, also add it to `requirements.txt` or `pyproject.toml`.
5. When creating new routes, create or update the appropriate router file — do not add routes to `main.py`.
6. When creating new data models, always create a corresponding Pydantic schema.
7. Confirm the server starts successfully (`uvicorn app.main:app --reload`) after any structural changes.
8. When in doubt about project structure, ask the user before creating new files.
