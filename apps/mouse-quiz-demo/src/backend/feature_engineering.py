from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

FEATURE_KEYS = [
    "solve_time",
    "event_count",
    "click_count",
    "mean_speed",
    "max_speed",
    "mean_acceleration",
    "path_curvature",
    "pause_count",
    "pause_duration",
    "direction_changes",
]

PAUSE_THRESHOLD = 0.05  # px/ms (= 50 px/s)


def _zero() -> Dict[str, float]:
    data = {"solve_time": 0.0, "event_count": 0.0, "click_count": 0.0}
    data.update(_motion_zero())
    return data


def _motion_zero() -> Dict[str, float]:
    return {
        "mean_speed": 0.0,
        "max_speed": 0.0,
        "mean_acceleration": 0.0,
        "path_curvature": 0.0,
        "pause_count": 0.0,
        "pause_duration": 0.0,
        "direction_changes": 0.0,
    }


def extract_motion_features(events: List[Dict[str, Any]], start_time: Optional[int] = None) -> Dict[str, float]:
    """학습 파이프라인과 동일한 이벤트 기반 피처를 추출한다."""

    if not events:
        return _zero()

    normalized = []
    for e in events:
        try:
            normalized.append(
                {
                    "type": str(e.get("type", "")).lower(),
                    "x": float(e.get("x", 0.0)),
                    "y": float(e.get("y", 0.0)),
                    "timestamp": int(e.get("timestamp", 0)),
                }
            )
        except Exception:
            continue

    if not normalized:
        return _zero()

    moves = [e for e in normalized if e["type"] == "mousemove"]
    clicks = [e for e in normalized if e["type"] == "mousedown"]

    if start_time is None:
        start_time = normalized[0]["timestamp"]

    end_time = normalized[-1]["timestamp"]
    solve_time = max(float(end_time - start_time), 1.0)

    base: Dict[str, float] = {
        "solve_time": solve_time,
        "event_count": float(len(normalized)),
        "click_count": float(len(clicks)),
    }

    if len(moves) < 2:
        base.update(_motion_zero())
        return base

    xs = [float(e["x"]) for e in moves]
    ys = [float(e["y"]) for e in moves]
    ts = [int(e["timestamp"]) for e in moves]

    speeds: List[float] = []
    distances: List[float] = []
    angles: List[float] = []
    pause_count = 0
    pause_duration = 0.0
    in_pause = False
    pause_start = 0

    for i in range(1, len(moves)):
        dx = xs[i] - xs[i - 1]
        dy = ys[i] - ys[i - 1]
        dt = max(float(ts[i] - ts[i - 1]), 1.0)
        d = math.sqrt(dx * dx + dy * dy)
        s = d / dt

        distances.append(d)
        speeds.append(s)
        angles.append(math.atan2(dy, dx))

        if s < PAUSE_THRESHOLD:
            if not in_pause:
                in_pause = True
                pause_start = ts[i - 1]
                pause_count += 1
        else:
            if in_pause:
                in_pause = False
                pause_duration += ts[i] - pause_start

    if in_pause:
        pause_duration += ts[-1] - pause_start

    accs: List[float] = []
    for i in range(1, len(speeds)):
        dt = max(float(ts[i + 1] - ts[i]), 1.0)
        accs.append(abs(speeds[i] - speeds[i - 1]) / dt)

    direction_changes = 0
    for i in range(1, len(angles)):
        diff = abs(angles[i] - angles[i - 1])
        if diff > math.pi:
            diff = 2 * math.pi - diff
        if diff > math.pi / 4:
            direction_changes += 1

    total_path = sum(distances)
    direct = math.sqrt((xs[-1] - xs[0]) ** 2 + (ys[-1] - ys[0]) ** 2)
    curvature = total_path / max(direct, 1.0)

    base.update(
        {
            "mean_speed": round(sum(speeds) / len(speeds), 6),
            "max_speed": round(max(speeds), 6),
            "mean_acceleration": round(sum(accs) / len(accs), 6) if accs else 0.0,
            "path_curvature": round(curvature, 4),
            "pause_count": float(pause_count),
            "pause_duration": round(pause_duration, 2),
            "direction_changes": float(direction_changes),
        }
    )
    return base
