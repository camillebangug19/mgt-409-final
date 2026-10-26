"""FastAPI entrypoint. Serves the API, and the built frontend in production."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import chat, db, events, limits, plan, survey
from .api_models import ChatRequest, ChatResponse, CompleteStepRequest, SessionResponse
from .config import FRONTEND_DIST, MODEL_NAME


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


@app.get("/api/usage")
def usage(session_id: str) -> dict:
    """Tokens and estimated cost for this session (REQUIREMENTS.md 8)."""
    with db.session_db() as conn:
        return plan.usage_summary(conn, session_id)


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
        events.log(conn, session_id, events.SURVEY_STARTED)
    return SessionResponse(session_id=session_id)


@app.get("/api/session/{session_id}")
def session_status(session_id: str) -> dict:
    """What we remember about a returning visitor.

    There are no accounts: the browser keeps an anonymous id in localStorage
    and this reports how far that id got, so someone can pick up where they
    left off (REQUIREMENTS.md 6.4).
    """
    with db.session_db() as conn:
        row = db.get_session(conn, session_id)
        if not row:
            return {"found": False}
        answers = chat.load_answers(conn, session_id)
        state = survey.survey_state(answers)
        profile = survey.build_profile(answers)
        return {
            "found": True,
            "survey_done": bool(row["survey_done"]),
            "progress": state["progress"],
            "answered": len(state["filled"]),
            "remaining": len(state["missing"]),
            "first_score": row["first_score"],
            "latest_score": row["latest_score"],
            "completed_steps": len(db.completed_steps(conn, session_id)),
            "people": len(profile.people),
            "pets": sum(p.count for p in profile.pets),
            "state": profile.state,
            "started_at": row["created_at"],
        }


@app.post("/api/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    """One survey turn."""
    with db.session_db() as conn:
        if not db.get_session(conn, request.session_id):
            raise HTTPException(status_code=404, detail="Unknown session")
        try:
            return await chat.run_turn(conn, request.session_id, request.message)
        except chat.BudgetExceeded as exc:
            raise HTTPException(status_code=429, detail=str(exc))


@app.get("/api/plan")
async def get_plan(session_id: str) -> dict:
    """The score reveal and the three next steps."""
    with db.session_db() as conn:
        if not db.get_session(conn, session_id):
            raise HTTPException(status_code=404, detail="Unknown session")
        if limits.budget_exceeded(conn):
            raise HTTPException(status_code=429, detail=limits.BUDGET_MESSAGE)
        result = await plan.build_plan(conn, session_id)
        db.record_score(conn, session_id, result["score"])
        events.log(conn, session_id, events.SCORE_SHOWN, {"score": result["score"]})
        return result


@app.post("/api/steps/{step_id}/complete")
async def complete_step(step_id: str, request: CompleteStepRequest) -> dict:
    """Tick off a step's self-check, re-score, and hand back the next steps."""
    with db.session_db() as conn:
        if not db.get_session(conn, request.session_id):
            raise HTTPException(status_code=404, detail="Unknown session")
        try:
            outcome = plan.complete_step(conn, request.session_id, step_id, request.checked)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown step {step_id}")
        refreshed = await plan.build_plan(conn, request.session_id)
        return {**refreshed, "completion": outcome}


# --- the built frontend ---------------------------------------------------
# FastAPI serves the React bundle, so the whole app runs on one port and one
# URL in production (REQUIREMENTS.md 11). Mounted last so /api/* wins.

if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str) -> FileResponse:
        """Serve the SPA, falling back to index.html for client-side routes."""
        candidate = (FRONTEND_DIST / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
