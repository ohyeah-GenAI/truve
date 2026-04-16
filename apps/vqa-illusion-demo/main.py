"""VQA Illusion Demo — FastAPI server (port 8001).

Endpoints
---------
GET  /internal/ai/health              → {"status": "ok"}
GET  /api/puzzle/generate             → generate 3x3 board, store in Redis, return session_id + popup_url
GET  /api/session/{session_id}        → return board + question + choices from Redis
POST /api/session/{session_id}/answer → verify answer, store result, return {"passed": bool}
POST /judge                           → called by ModuleController, return {"passed": bool, "is_human": bool}
POST /api/ai/vqa/verify               → lookup vqa:result:{userId}:{showScheduleId}, return {"passed": bool}
GET  /                                → serve static/index.html (popup)
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path setup — allow importing db.py from src/vqa_illusion/
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(_BASE_DIR / "src"))

from dotenv import load_dotenv
load_dotenv(_BASE_DIR / ".env")

from redis_client import close_redis, get_redis, init_redis  # noqa: E402
from vqa_illusion.db import get_db  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VQA_ILLUSION_BASE_URL: str = os.environ.get("VQA_ILLUSION_BASE_URL", "http://localhost:8001")

SESSION_TTL = 120   # seconds
DEDUP_TTL = 60      # seconds
RATELIMIT_TTL = 60  # seconds
RESULT_TTL = 600    # seconds
RATELIMIT_MAX = 10  # max refreshes per userId per minute

# ---------------------------------------------------------------------------
# Direction constants
# id, label, dx, dy
# ---------------------------------------------------------------------------
DIRECTIONS = [
    (0, "위쪽",                    0, +1),
    (1, "아래쪽",                   0, -1),
    (2, "왼쪽",                   -1,  0),
    (3, "오른쪽",                  +1,  0),
    (4, "오른쪽 위 대각선 방향",   +1, +1),
    (5, "왼쪽 아래 대각선 방향",  -1, -1),
    (6, "왼쪽 위 대각선 방향",    -1, +1),
    (7, "오른쪽 아래 대각선 방향", +1, -1),
]


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="VQA Illusion Service", version="1.0.0", lifespan=lifespan)

# Static files (popup HTML)
_static_dir = _BASE_DIR / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coord_to_index(x: int, y: int) -> int:
    """(1,1)=bottom-left coordinate system → 0-based array index."""
    return (x - 1) + (y - 1) * 3


def _board_hash(problems: list[dict]) -> str:
    ids = "-".join(str(p.get("problem_id", "")) for p in problems)
    return hashlib.md5(ids.encode()).hexdigest()[:8]


def _fetch_problems(db, policies: list[str] | None = None) -> list[dict]:
    """Fetch ≥9 problems linked to approved images.

    Returns a list of exactly 9 problem dicts (random sample), each with:
        problem_id, question, choices (jsonb list), correct_answer, image_url, illusion_image_id

    Args:
        policies: distractor_policy 값 목록 (예: ["variant_b", "variant_c"]).
                  None이면 모든 policy 허용.
    """
    # Collect illusion_image_ids that have been QC-approved
    approved_rows = db.select("approved_images")
    approved_ids = {r["illusion_image_id"] for r in approved_rows if r.get("illusion_image_id")}

    rows = db.select("problems", {"is_active": True})

    def _policy_ok(r: dict) -> bool:
        return policies is None or r.get("distractor_policy") in policies

    # Keep only problems whose image is in approved_images AND has a valid storage URL
    valid = [
        r for r in rows
        if r.get("illusion_image_id") in approved_ids
        and r.get("image_url")
        and "seed" in r["image_url"]
        and _policy_ok(r)
    ]

    if len(valid) < 9:
        # Fallback: any active problem with a new-format URL (policy 필터 유지)
        valid = [
            r for r in rows
            if r.get("image_url")
            and "seed" in r["image_url"]
            and _policy_ok(r)
        ]
    # Group by illusion_image_id — one problem per unique image on the board
    groups: dict = defaultdict(list)
    for r in valid:
        groups[r["illusion_image_id"]].append(r)

    if len(groups) < 9:
        raise HTTPException(status_code=500, detail="고유 이미지가 9개 미만입니다")

    sampled_keys = random.sample(list(groups.keys()), 9)
    return [random.choice(groups[k]) for k in sampled_keys]


def _generate_board_question(problems: list[dict], board_hash: str) -> dict:
    """유효한 (시작점, 방향, 거리) 조합 전체를 구한 뒤 랜덤 샘플링."""
    # 범위 내 조합만 사전 계산
    valid = [
        (sx, sy, dir_id, dir_text, dx, dy, dist)
        for sx in range(1, 4)
        for sy in range(1, 4)
        for (dir_id, dir_text, dx, dy) in DIRECTIONS
        for dist in (1, 2)
        if 1 <= sx + dx * dist <= 3 and 1 <= sy + dy * dist <= 3
    ]
    sx, sy, dir_id, dir_text, dx, dy, dist = random.choice(valid)

    target_index = _coord_to_index(sx + dx * dist, sy + dy * dist)
    target_prob = problems[target_index]

    raw_q = target_prob.get("question", "")
    suffix = raw_q[2:] if len(raw_q) > 2 else raw_q
    question = f"({sx},{sy})에서 {dir_text}으로 {dist}칸 이동한 위치의 {suffix}"

    raw_choices = target_prob.get("choices", [])
    if isinstance(raw_choices, str):
        try:
            choices = json.loads(raw_choices)
        except Exception:
            choices = [raw_choices]
    else:
        choices = list(raw_choices)

    correct_index = int(target_prob.get("correct_answer", 0))
    target_img_id = target_prob.get("illusion_image_id", "")
    problem_token = f"B{board_hash}:P{sx}{sy}:D{dir_id}:Dist{dist}:I{target_img_id}"

    board = [
        {"img_url": p.get("image_url", ""), "label": p.get("question", "")}
        for p in problems
    ]

    return {
        "board": board,
        "question": question,
        "choices": choices,
        "correct_index": correct_index,
        "problem_token": problem_token,
        "start_x": sx,
        "start_y": sy,
        "dir_id": dir_id,
        "dist": dist,
        "target_index": target_index,
    }


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AnswerRequest(BaseModel):
    answer_index: int
    userId: str | None = None
    showScheduleId: int | None = None


class JudgeRequest(BaseModel):
    session_id: str
    puzzle_type: str | None = None
    answer: dict | None = None
    events: list | None = None


class VerifyRequest(BaseModel):
    showScheduleId: int
    userId: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Serve the popup HTML."""
    html_path = _static_dir / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/internal/ai/health")
async def health():
    return {"status": "ok"}


@app.get("/api/puzzle/generate")
async def generate_puzzle(
    userId: str | None = None,
    distractor_policy: str = "variant_b,variant_c",
):
    """Generate a 3x3 VQA puzzle, store session in Redis, return popup_url.

    Args:
        distractor_policy: 쉼표로 구분된 policy 목록 (기본: variant_b,variant_c).
                           예) ?distractor_policy=variant_a
                               ?distractor_policy=variant_b,variant_c
    """
    redis = get_redis()

    # Optional rate-limit guard
    if userId:
        rl_key = f"vqa:ratelimit:{userId}"
        count = await redis.incr(rl_key)
        if count == 1:
            await redis.expire(rl_key, RATELIMIT_TTL)
        if count > RATELIMIT_MAX:
            raise HTTPException(status_code=429, detail="새로고침 횟수를 초과했습니다")

    policies = [p.strip() for p in distractor_policy.split(",") if p.strip()]

    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="DB가 구성되지 않았습니다")

    problems = _fetch_problems(db, policies or None)
    board_hash = _board_hash(problems)

    # do-while with dedup check, outer retry up to 5
    data: dict[str, Any] | None = None
    for _outer in range(5):
        try:
            data = _generate_board_question(problems, board_hash)
        except RuntimeError:
            continue  # fallback: 예상치 못한 실패 시 outer 루프에서 재시도

        token = data["problem_token"]
        dup_key = f"vqa:dup_filter:{token}"
        # SETNX: returns 1 if set (new), 0 if already exists
        set_ok = await redis.set(dup_key, "1", nx=True, ex=DEDUP_TTL)
        if set_ok:
            break
        # duplicate — regenerate
        data = None
    else:
        raise HTTPException(status_code=500, detail="중복 없는 문제 생성 실패")

    session_id = str(uuid.uuid4())
    session_data = {
        "board": data["board"],
        "question": data["question"],
        "choices": data["choices"],
        "correct_index": data["correct_index"],
        "userId": userId,
        "showScheduleId": None,
    }
    session_key = f"vqa:session:{session_id}"
    await redis.set(session_key, json.dumps(session_data, ensure_ascii=False), ex=SESSION_TTL)

    popup_url = f"{VQA_ILLUSION_BASE_URL}/?session_id={session_id}"
    if userId:
        popup_url += f"&userId={userId}"

    return {
        "session_id": session_id,
        "puzzle_type": "vqa-illusion",
        "puzzle_config": {
            "popup_url": popup_url,
        },
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Return board + question + choices for the popup."""
    redis = get_redis()
    raw = await redis.get(f"vqa:session:{session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 만료되었습니다")

    data = json.loads(raw)

    # Build board with position metadata
    board_with_pos = []
    for idx, cell in enumerate(data["board"]):
        x = (idx % 3) + 1
        y = (idx // 3) + 1
        board_with_pos.append({
            "img_url": cell.get("img_url", ""),
            "position": {"x": x, "y": y},
        })

    # TTL remaining → expires_at (approximate)
    import time
    ttl = await redis.ttl(f"vqa:session:{session_id}")
    expires_at = int(time.time()) + ttl if ttl > 0 else 0

    return {
        "board": board_with_pos,
        "question": data["question"],
        "choices": data["choices"],
        "expires_at": expires_at,
    }


@app.post("/api/session/{session_id}/answer")
async def submit_answer(session_id: str, body: AnswerRequest):
    """Verify the user's answer and store the result in Redis."""
    redis = get_redis()
    session_key = f"vqa:session:{session_id}"
    raw = await redis.get(session_key)
    if not raw:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 만료되었습니다")

    data = json.loads(raw)
    passed = body.answer_index == data["correct_index"]

    # Persist result if we have userId + showScheduleId
    if body.userId and body.showScheduleId is not None:
        result_key = f"vqa:result:{body.userId}:{body.showScheduleId}"
        await redis.set(result_key, "1" if passed else "0", ex=RESULT_TTL)

        # Update session with userId / showScheduleId for /judge lookups
        data["userId"] = body.userId
        data["showScheduleId"] = body.showScheduleId
        # Preserve remaining TTL
        ttl = await redis.ttl(session_key)
        remaining = ttl if ttl > 0 else SESSION_TTL
        await redis.set(session_key, json.dumps(data, ensure_ascii=False), ex=remaining)

    return {"passed": passed}


@app.post("/judge")
async def judge(body: JudgeRequest):
    """Called by ModuleController. Resolves result from Redis session."""
    redis = get_redis()
    raw = await redis.get(f"vqa:session:{body.session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 만료되었습니다")

    data = json.loads(raw)

    # Try to look up pre-stored result key (set by /answer endpoint)
    user_id = data.get("userId")
    show_schedule_id = data.get("showScheduleId")
    passed = False

    blocked = bool(body.answer.get("blocked")) if isinstance(body.answer, dict) else False

    if user_id and show_schedule_id is not None:
        result_key = f"vqa:result:{user_id}:{show_schedule_id}"
        stored = await redis.get(result_key)
        if stored is not None:
            passed = stored == "1"
    else:
        # Fallback: evaluate answer_index from request body if provided
        if body.answer and "answer_index" in body.answer:
            passed = body.answer["answer_index"] == data.get("correct_index")

    return {"passed": passed, "is_human": passed, "blocked": blocked}


@app.post("/api/ai/vqa/verify")
async def vqa_verify(body: VerifyRequest):
    """Called by backend at ticketing time. Looks up stored result."""
    redis = get_redis()
    result_key = f"vqa:result:{body.userId}:{body.showScheduleId}"
    stored = await redis.get(result_key)
    if stored is None:
        # No result on record → treat as not passed
        return {"passed": False}
    return {"passed": stored == "1"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
