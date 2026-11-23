import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import engine
from app.config import settings
from app.llm import LLMError, LLMNotConfigured
from app.schemas import AssistIn, CreateSessionIn, MicroTestIn, ModuleIn, PlanIn
from app.store import get, save

app = FastAPI(title="思拆", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(127\.0\.0\.1|localhost):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ok(session: dict) -> dict:
    save(session)
    return {"session": engine.public_session(session)}


def _load(session_id: str) -> dict:
    session = get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请刷新页面重新开始。")
    return session


@app.get("/api/health")
def health():
    return {
        "product": "思拆",
        "ok": True,
        "configured": settings.llm_configured,
        "llm": "deepseek",
        "model": settings.siche_deepseek_model,
    }


@app.post("/api/sessions")
def create_session(body: CreateSessionIn | None = None):
    payload = body or CreateSessionIn()
    session = engine.create_session(payload.task_type, payload.topic)
    return _ok(session)


@app.get("/api/sessions/{session_id}")
def read_session(session_id: str):
    return _ok(_load(session_id))


@app.post("/api/sessions/{session_id}/module")
def set_module(session_id: str, body: ModuleIn):
    session = _load(session_id)
    if body.module not in engine.MODULES:
        raise HTTPException(status_code=400, detail="未知模块")
    session["current_module"] = body.module
    return _ok(session)


@app.post("/api/sessions/{session_id}/assist")
async def assist(session_id: str, body: AssistIn):
    session = _load(session_id)
    try:
        await engine.assist(session, body.message, body.module)
    except LLMNotConfigured as exc:
        save(session)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        save(session)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _ok(session)


@app.post("/api/sessions/{session_id}/messages/{message_id}/copy-request")
def copy_request(session_id: str, message_id: str):
    session = _load(session_id)
    try:
        result = engine.request_copy(session, message_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    save(session)
    return result


@app.post("/api/sessions/{session_id}/messages/{message_id}/micro-test")
def micro_test(session_id: str, message_id: str, body: MicroTestIn):
    session = _load(session_id)
    try:
        result = engine.submit_micro_test(
            session, message_id, body.option, body.text, body.event_id or None
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    save(session)
    return {"session": engine.public_session(session), "result": result}


@app.post("/api/sessions/{session_id}/messages/{message_id}/micro-test/refuse")
def refuse_micro_test(session_id: str, message_id: str, event_id: str = ""):
    session = _load(session_id)
    try:
        result = engine.refuse_micro_test(session, message_id, event_id or None)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    save(session)
    return {"session": engine.public_session(session), "result": result}


@app.post("/api/sessions/{session_id}/plan")
def save_plan(session_id: str, body: PlanIn):
    session = _load(session_id)
    engine.update_plan(session, body.model_dump())
    return _ok(session)


@app.post("/api/sessions/{session_id}/plan/prefill")
async def prefill_plan(session_id: str):
    session = _load(session_id)
    result = await engine.prefill_plan(session)
    return {"session": engine.public_session(session), "prefill": result}


@app.get("/api/sessions/{session_id}/export")
def export_session(session_id: str):
    session = _load(session_id)
    return engine.export_session(session)


def resolve_web_dir() -> Path | None:
    candidates: list[Path] = []
    env_web = os.environ.get("SICHE_WEB_DIR", "").strip()
    if env_web:
        candidates.append(Path(env_web))
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates += [
            meipass / "web",
            Path(sys.executable).resolve().parent / "web",
        ]
    else:
        root = Path(__file__).resolve().parents[2]
        candidates += [root / "frontend" / "dist"]
    for path in candidates:
        if (path / "index.html").is_file():
            return path
    return None


_web_dir = resolve_web_dir()
if _web_dir is not None:
    app.mount("/", StaticFiles(directory=str(_web_dir), html=True), name="web")
