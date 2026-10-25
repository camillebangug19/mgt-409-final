"""FastAPI entrypoint. Serves the API, and the built frontend in production."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import chat, db
from .api_models import ChatRequest, ChatResponse, SessionResponse
from .config import MODEL_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="ReadyHome", version="0.2.0", lifespan=lifespan)

# The Vite dev server runs on another port during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Liveness check for Render (REQUIREMENTS.md 11)."""
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/api/session", response_model=SessionResponse)
def start_session() -> SessionResponse:
    """Start an anonymous session. No account, no name, no address."""
    session_id = str(uuid.uuid4())
    with db.session_db() as conn:
        db.create_session(conn, session_id)
        db.log_event(conn, session_id, "survey_started")
    return SessionResponse(session_id=session_id)


@app.post("/api/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    """One survey turn."""
    with db.session_db() as conn:
        if not db.get_session(conn, request.session_id):
            raise HTTPException(status_code=404, detail="Unknown session")
        return await chat.run_turn(conn, request.session_id, request.message)
