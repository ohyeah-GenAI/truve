from __future__ import annotations

import os

# 프론트가 넘긴 risk_level → 챌린지 단계 순서
SECURITY_POLICY: dict[str, list[str]] = {
    "LOW": ["mouse-slider"],
    "MEDIUM": ["mouse-slider", "vqa-image"],
    "HIGH": ["mouse-slider", "vqa-illusion"],
}

MODULE_URLS: dict[str, str] = {
    "mouse": os.getenv("MOUSE_QUIZ_URL", "http://localhost:8003"),
    "vqa-image": os.getenv("VQA_IMAGE_URL", "http://localhost:8002"),
    "vqa-illusion": os.getenv("VQA_ILLUSION_URL", "http://localhost:8001"),
}

STEP_CATALOG: dict[str, dict[str, object]] = {
    "mouse-slider": {
        "module": "mouse",
        "challenge_type": "slider",
        "generate_type": "slider",
        "supports_events": True,
    },
    "vqa-image": {
        "module": "vqa-image",
        "challenge_type": "vqa-image",
        "generate_type": "vqa-image",
        "supports_events": False,
    },
    "vqa-illusion": {
        "module": "vqa-illusion",
        "challenge_type": "vqa-illusion",
        "generate_type": "vqa-illusion",
        "supports_events": False,
    },
}

DEDUP_TTL = 60          # VQA 동일 문제 재출제 금지 TTL (초)
DEDUP_MAX_RETRY = 5     # dedup 충돌 시 최대 재시도 횟수
FLOW_SESSION_TTL = 600  # 다단계 챌린지 세션 유효 시간 (초)
PERF_LEVEL_CACHE_TTL = 300  # security_level Redis 캐시 TTL (초)
MAX_ATTEMPTS_PER_STEP = 2   # 단계별 최대 시도 횟수 (초과 시 차단)
VERIFY_RESULT_TTL = 3600    # 챌린지 통과 결과 보관 TTL (초, 1시간)
