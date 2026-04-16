from __future__ import annotations

import json
from datetime import datetime
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.backend.feature_engineering import FEATURE_KEYS, extract_motion_features
from src.backend.puzzle.generator import PuzzleGenerator
from src.backend.puzzle.validator import PuzzleValidator


class SubmitPayload(BaseModel):
    session_id: str
    puzzle_type: str
    answer: Dict[str, Any]
    events: List[Dict[str, Any]]
    save_json: bool = False


class JudgeRequest(BaseModel):
    session_id: str
    puzzle_type: str
    answer: Dict[str, Any]
    events: List[Dict[str, Any]]


class JudgeResponse(BaseModel):
    is_human: bool
    module: str
    passed: bool


class HealthResponse(BaseModel):
    status: str


class InternalAIHealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    supported_puzzle_types: List[str]


class GeneratePuzzleResponse(BaseModel):
    session_id: str
    puzzle_type: str
    puzzle_config: Dict[str, Any]


class SubmitResponse(BaseModel):
    result: str
    is_bot: bool
    bot_risk_score: float
    puzzle_correct: bool
    features: Dict[str, Any]


ALLOWED_TYPES = {"slider"}

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "src" / "backend" / "models"
HUMAN_VS_BOT_MODEL_PATH = MODEL_DIR / "human_vs_bot_model.joblib"

if not HUMAN_VS_BOT_MODEL_PATH.exists():
    raise RuntimeError(f"human_vs_bot_model.joblib not found at {HUMAN_VS_BOT_MODEL_PATH}")

_human_vs_bot_model = joblib.load(HUMAN_VS_BOT_MODEL_PATH)

FRONTEND_DIR = (BASE_DIR / "src" / "frontend").resolve()

app = FastAPI(title="Puzzle Bot Detection MSA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_generator = PuzzleGenerator()
_validator = PuzzleValidator()

_SESSIONS: Dict[str, Dict[str, Any]] = {}
BOT_THRESHOLD = 0.5
TEST_LOG_DIR = BASE_DIR / "src" / "backend" / "test_logs"
SESSION_TTL_SECONDS = 300


def _create_session(puzzle_type: str, answer: Dict[str, Any]) -> str:
    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "puzzle_type": puzzle_type,
        "answer": answer,
        "created_at": time.time(),
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return session_id


def _get_session(session_id: str) -> Dict[str, Any] | None:
    session = _SESSIONS.get(session_id)
    if not session:
        return None
    if session.get("expires_at", 0) < time.time():
        _SESSIONS.pop(session_id, None)
        return None
    return session


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the main frontend page."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="index.html not found in frontend directory")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return {"status": "ok"}


@app.get("/internal/ai/health", response_model=InternalAIHealthResponse)
async def internal_ai_health() -> InternalAIHealthResponse:
    return {
        "status": "ok",
        "model_loaded": _human_vs_bot_model is not None,
        "model_path": str(HUMAN_VS_BOT_MODEL_PATH),
        "supported_puzzle_types": sorted(ALLOWED_TYPES),
    }


@app.get("/api/puzzle/generate", response_model=GeneratePuzzleResponse)
async def generate_puzzle(type: str = Query(..., alias="type")) -> GeneratePuzzleResponse:
    if type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported puzzle type: {type}")

    puzzle = _generator.generate(type)
    session_id = _create_session(type, puzzle["answer"])

    return {
        "session_id": session_id,
        "puzzle_type": type,
        "puzzle_config": puzzle["config"],
    }


def _build_feature_row(puzzle_type: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    motion = extract_motion_features(events, start_time=None)

    event_len = len(events)
    mousedown_count = sum(1 for e in events if str(e.get("type", "")).lower() == "mousedown")
    click_count = sum(1 for e in events if str(e.get("type", "")).lower() == "click")

    row: Dict[str, Any] = {k: float(motion.get(k, 0.0)) for k in FEATURE_KEYS}
    row.update(
        {
            "event_len": float(event_len),
            "event_mousedown_count": float(mousedown_count),
            "event_click_count": float(click_count),
            "puzzle_type": puzzle_type,
        }
    )
    return row


def _persist_test_json(payload: SubmitPayload, response: Dict[str, Any]) -> None:
    TEST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_name = f"{now}__{payload.puzzle_type}__{payload.session_id[:8]}.json"
    out_path = TEST_LOG_DIR / file_name
    doc = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "session_id": payload.session_id,
        "puzzle_type": payload.puzzle_type,
        "answer": payload.answer,
        "events": payload.events,
        "response": response,
    }
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


@app.post("/api/puzzle/submit", response_model=SubmitResponse)
async def submit_puzzle(payload: SubmitPayload) -> SubmitResponse:
    session = _get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired session_id")

    if payload.puzzle_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported puzzle type: {payload.puzzle_type}")

    if session["puzzle_type"] != payload.puzzle_type:
        raise HTTPException(status_code=400, detail="Puzzle type mismatch for this session")

    correct_answer = session["answer"]
    puzzle_correct = bool(
        _validator.validate(
            puzzle_type=payload.puzzle_type,
            correct_answer=correct_answer,
            user_answer=payload.answer,
        )
    )

    # Feature extraction for the trained model
    row = _build_feature_row(payload.puzzle_type, payload.events)
    df = pd.DataFrame([row])

    proba = float(_human_vs_bot_model.predict_proba(df)[:, 1][0])
    is_bot = proba >= BOT_THRESHOLD

    bot_risk_score = round(proba * 100.0, 1)

    if puzzle_correct and not is_bot:
        result = "success"
    elif is_bot:
        result = "bot"
    else:
        result = "fail"

    response_features = row.copy()

    response = {
        "result": result,
        "is_bot": is_bot,
        "bot_risk_score": bot_risk_score,
        "puzzle_correct": puzzle_correct,
        "features": response_features,
    }

    if payload.save_json:
        try:
            _persist_test_json(payload, response)
        except OSError:
            # 저장 실패가 사용자 흐름을 막지 않도록 무시
            pass

    _SESSIONS.pop(payload.session_id, None)

    return response


@app.post("/judge", tags=["AI Verification"], response_model=JudgeResponse)
async def judge(payload: JudgeRequest) -> JudgeResponse:
    """내부 봇 판별 엔드포인트 — ModuleController에서 호출됨."""
    session = _get_session(payload.session_id)
    if not session:
        return JudgeResponse(is_human=False, module="mouse", passed=False)

    if payload.puzzle_type not in ALLOWED_TYPES:
        return JudgeResponse(is_human=False, module="mouse", passed=False)

    if session["puzzle_type"] != payload.puzzle_type:
        return JudgeResponse(is_human=False, module="mouse", passed=False)

    correct_answer = session["answer"]
    puzzle_correct = bool(
        _validator.validate(
            puzzle_type=payload.puzzle_type,
            correct_answer=correct_answer,
            user_answer=payload.answer,
        )
    )

    row = _build_feature_row(payload.puzzle_type, payload.events)
    df = pd.DataFrame([row])

    proba = float(_human_vs_bot_model.predict_proba(df)[:, 1][0])
    is_bot = proba >= BOT_THRESHOLD

    _SESSIONS.pop(payload.session_id, None)

    return JudgeResponse(
        is_human=not is_bot,
        module="mouse",
        passed=puzzle_correct and not is_bot,
    )


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)
