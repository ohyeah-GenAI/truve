from __future__ import annotations

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

from backend.feature_engineering import FEATURE_KEYS, extract_motion_features
from backend.puzzle.generator import PuzzleGenerator
from backend.puzzle.validator import PuzzleValidator


class SubmitPayload(BaseModel):
    session_id: str
    puzzle_type: str
    answer: Dict[str, Any]
    events: List[Dict[str, Any]]


ALLOWED_TYPES = {"slider", "clickseq", "pathtrace_v2"}

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
HUMAN_VS_BOT_MODEL_PATH = MODEL_DIR / "human_vs_bot_model.joblib"

if not HUMAN_VS_BOT_MODEL_PATH.exists():
    raise RuntimeError(f"human_vs_bot_model.joblib not found at {HUMAN_VS_BOT_MODEL_PATH}")

_human_vs_bot_model = joblib.load(HUMAN_VS_BOT_MODEL_PATH)

FRONTEND_DIR = (BASE_DIR.parent / "frontend").resolve()

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


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the main frontend page.

    정적 HTML을 그대로 내려만 주고, 디스크에 별도 로그는 남기지 않는다.
    """
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="index.html not found in frontend directory")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/puzzle/generate")
async def generate_puzzle(type: str = Query(..., alias="type")) -> Dict[str, Any]:
    if type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported puzzle type: {type}")

    puzzle = _generator.generate(type)
    session_id = str(uuid.uuid4())

    _SESSIONS[session_id] = {
        "puzzle_type": type,
        "answer": puzzle["answer"],
    }

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


@app.post("/api/puzzle/submit")
async def submit_puzzle(payload: SubmitPayload) -> Dict[str, Any]:
    session = _SESSIONS.pop(payload.session_id, None)
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
    pred = int(_human_vs_bot_model.predict(df)[0])
    is_bot = bool(pred)

    bot_risk_score = round(proba * 100.0, 1)

    if puzzle_correct and not is_bot:
        result = "success"
    elif is_bot:
        result = "bot"
    else:
        result = "fail"

    response_features = row.copy()

    return {
        "result": result,
        "is_bot": is_bot,
        "bot_risk_score": bot_risk_score,
        "puzzle_correct": puzzle_correct,
        "features": response_features,
    }


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8002, reload=True)
