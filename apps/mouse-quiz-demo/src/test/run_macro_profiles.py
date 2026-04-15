from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

# =========================
# TEST CONFIG (edit here)
# =========================
BASE_URL = "http://127.0.0.1:8002/api"

# 3 macro profiles and run counts.
RUN_COUNTS: Dict[str, int] = {
    "general_macro": 1,
    "human_like_macro": 1,
    "llm_macro": 1,
}

# Puzzle targets to test. Use one or more from: slider, clickseq, pathtrace_v2
PUZZLE_TYPES = ["slider", "clickseq", "pathtrace_v2"]

# If true, backend will persist submit payload/response json in backend/test_logs
SAVE_SERVER_JSON = True

# Local summary output
LOCAL_OUTPUT_PATH = "test/macro_test_results.json"
RANDOM_SEED = 42
REQUEST_TIMEOUT_SEC = 10


@dataclass
class RunResult:
    profile: str
    run_index: int
    puzzle_type: str
    session_id: str
    status_code: int
    is_bot: bool | None
    bot_risk_score: float | None
    result: str | None
    error: str | None
    request_duration_ms: int


def _default_answer(puzzle_type: str) -> Dict[str, Any]:
    if puzzle_type == "slider":
        return {"offset_x": 0}
    if puzzle_type == "clickseq":
        return {"sequence": []}
    return {"points": []}


def _build_events(profile: str, puzzle_type: str, base_ts: int, rng: random.Random) -> List[Dict[str, Any]]:
    # Synthetic mouse traces for stress-testing detector profiles.
    # They are intentionally simple and do not guarantee puzzle correctness.
    events: List[Dict[str, Any]] = []

    if puzzle_type == "slider":
        start_x, start_y = 40, 120
        end_x = 270
    elif puzzle_type == "clickseq":
        start_x, start_y = 80, 90
        end_x = 280
    else:  # pathtrace_v2
        start_x, start_y = 40, 160
        end_x = 320

    ts = base_ts

    def add_event(ev_type: str, x: float, y: float, dt: int) -> None:
        nonlocal ts
        ts += max(dt, 1)
        events.append(
            {
                "type": ev_type,
                "x": round(float(x), 2),
                "y": round(float(y), 2),
                "timestamp": int(ts),
                "button": 0,
            }
        )

    if profile == "general_macro":
        # Fast, straight, minimal pauses.
        add_event("mousemove", start_x, start_y, 3)
        add_event("mousedown", start_x, start_y, 2)
        steps = 12
        for i in range(1, steps + 1):
            x = start_x + (end_x - start_x) * (i / steps)
            add_event("mousemove", x, start_y, 4)
        add_event("mouseup", end_x, start_y, 2)
        add_event("click", end_x, start_y, 1)

    elif profile == "human_like_macro":
        # Slower, jitter, occasional pauses, mild overshoot.
        add_event("mousemove", start_x, start_y, 20)
        add_event("mousedown", start_x, start_y, 25)
        steps = 24
        for i in range(1, steps + 1):
            frac = i / steps
            x = start_x + (end_x - start_x) * frac + rng.uniform(-4, 4)
            y = start_y + rng.uniform(-6, 6)
            dt = rng.randint(12, 35)
            add_event("mousemove", x, y, dt)
            if i in (8, 16):
                add_event("mousemove", x, y, rng.randint(80, 140))
        add_event("mouseup", end_x + rng.uniform(-3, 3), start_y + rng.uniform(-3, 3), 18)
        add_event("click", end_x, start_y, 12)

    elif profile == "llm_macro":
        # Medium speed with curved pattern and variable tempo.
        add_event("mousemove", start_x, start_y, 8)
        add_event("mousedown", start_x, start_y, 8)
        steps = 18
        amp = 10.0 if puzzle_type != "clickseq" else 6.0
        for i in range(1, steps + 1):
            frac = i / steps
            x = start_x + (end_x - start_x) * frac
            y = start_y + amp * (0.5 - abs(0.5 - frac)) * (1 if i % 2 == 0 else -1)
            x += rng.uniform(-2.5, 2.5)
            y += rng.uniform(-2.5, 2.5)
            add_event("mousemove", x, y, rng.randint(7, 18))
            if i % 7 == 0:
                add_event("mousemove", x, y, rng.randint(35, 60))
        add_event("mouseup", end_x, start_y, 8)
        add_event("click", end_x, start_y, 4)

    else:
        raise ValueError(f"Unsupported profile: {profile}")

    return events


def _create_session(base_url: str, puzzle_type: str) -> Dict[str, Any]:
    url = f"{base_url}/puzzle/generate"
    res = requests.get(url, params={"type": puzzle_type}, timeout=REQUEST_TIMEOUT_SEC)
    res.raise_for_status()
    return res.json()


def _submit(
    base_url: str,
    session_id: str,
    puzzle_type: str,
    answer: Dict[str, Any],
    events: List[Dict[str, Any]],
    save_json: bool,
) -> requests.Response:
    url = f"{base_url}/puzzle/submit"
    payload = {
        "session_id": session_id,
        "puzzle_type": puzzle_type,
        "answer": answer,
        "events": events,
        "save_json": save_json,
    }
    return requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SEC)


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    out_path = Path(LOCAL_OUTPUT_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    run_results: List[RunResult] = []

    for profile, run_count in RUN_COUNTS.items():
        if run_count <= 0:
            continue

        for i in range(1, run_count + 1):
            puzzle_type = PUZZLE_TYPES[(i - 1) % len(PUZZLE_TYPES)]
            started = int(time.time() * 1000)
            try:
                session = _create_session(BASE_URL, puzzle_type)
                session_id = str(session.get("session_id", uuid.uuid4()))
                events = _build_events(profile, puzzle_type, base_ts=started, rng=rng)
                answer = _default_answer(puzzle_type)

                resp = _submit(
                    base_url=BASE_URL,
                    session_id=session_id,
                    puzzle_type=puzzle_type,
                    answer=answer,
                    events=events,
                    save_json=SAVE_SERVER_JSON,
                )

                duration = int(time.time() * 1000) - started
                if resp.ok:
                    data = resp.json()
                    run_results.append(
                        RunResult(
                            profile=profile,
                            run_index=i,
                            puzzle_type=puzzle_type,
                            session_id=session_id,
                            status_code=resp.status_code,
                            is_bot=data.get("is_bot"),
                            bot_risk_score=data.get("bot_risk_score"),
                            result=data.get("result"),
                            error=None,
                            request_duration_ms=duration,
                        )
                    )
                else:
                    run_results.append(
                        RunResult(
                            profile=profile,
                            run_index=i,
                            puzzle_type=puzzle_type,
                            session_id=session_id,
                            status_code=resp.status_code,
                            is_bot=None,
                            bot_risk_score=None,
                            result=None,
                            error=resp.text[:500],
                            request_duration_ms=duration,
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                duration = int(time.time() * 1000) - started
                run_results.append(
                    RunResult(
                        profile=profile,
                        run_index=i,
                        puzzle_type=puzzle_type,
                        session_id="",
                        status_code=0,
                        is_bot=None,
                        bot_risk_score=None,
                        result=None,
                        error=str(exc),
                        request_duration_ms=duration,
                    )
                )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": BASE_URL,
        "save_server_json": SAVE_SERVER_JSON,
        "run_counts": RUN_COUNTS,
        "puzzle_types": PUZZLE_TYPES,
        "results": [r.__dict__ for r in run_results],
    }

    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[Macro Test Runner]")
    print(f"Saved local summary: {out_path}")
    if SAVE_SERVER_JSON:
        print("Server JSON logs should be under backend/test_logs (if backend is running and accepts save_json).")

    ok = sum(1 for r in run_results if r.status_code == 200)
    fail = len(run_results) - ok
    print(f"Runs: total={len(run_results)} ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
