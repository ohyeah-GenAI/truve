from __future__ import annotations

import os

# 보안 레벨 → 챌린지 모듈 순서 (env로 관리 → 코드 수정 없이 정책 변경 가능)
SECURITY_POLICY: dict[str, list[str]] = {
    "LOW":    os.getenv("POLICY_LOW",    "mouse-quiz").split(","),
    "MEDIUM": os.getenv("POLICY_MEDIUM", "mouse-quiz,vqa-image").split(","),
    "HIGH":   os.getenv("POLICY_HIGH",   "mouse-quiz,vqa-illusion").split(","),
}

MODULE_URLS: dict[str, str] = {
    "vqa-image":    os.getenv("VQA_IMAGE_URL",    "http://localhost:8002"),
    "vqa-illusion": os.getenv("VQA_ILLUSION_URL", "http://localhost:8001"),
    "mouse-quiz":   os.getenv("MOUSE_QUIZ_URL",   "http://localhost:8003"),
}

DEDUP_TTL = 60          # VQA 동일 문제 재출제 금지 TTL (초)
DEDUP_MAX_RETRY = 5     # dedup 충돌 시 최대 재시도 횟수
FLOW_SESSION_TTL = 600  # 다단계 챌린지 세션 유효 시간 (초)
VERIFIED_TTL = 600      # 통과 사용자 캐시 유효 시간 (초)
PERF_LEVEL_CACHE_TTL = 300  # security_level Redis 캐시 TTL (초)
