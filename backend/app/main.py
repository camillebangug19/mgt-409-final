"""FastAPI entrypoint. Serves the API, and the built frontend in production."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .config import MODEL_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="ReadyHome", version="0.1.0", lifespan=lifespan)


@app.get("/api/health")
def health() -> dict:
    """Liveness check for Render (REQUIREMENTS.md 11)."""
    return {"status": "ok", "model": MODEL_NAME}
