# Challenge Generation Guide

이 폴더는 CAPTCHA/VQA 문제 출제(생성) 로직의 기준을 정의합니다.
구현 전제는 다음과 같습니다.

- 챌린지 타입별 생성 로직은 분리하되, 공통 인터페이스를 유지합니다.
- 세션 상태는 Redis에 저장하고, 대용량 리소스는 외부 스토리지에 보관합니다.
- 검증 로직은 verification-answer에서 수행합니다.

## 1. 책임 범위

- 챌린지 생성 요청 처리
- 챌린지 데이터 생성 및 저장
- 클라이언트 전달용 payload 구성

## 2. 공통 인터페이스(샘플)

### 2.1 요청

```json
{
  "type": "vqa-image",
  "difficulty": "medium",
  "user_key": "anon_123",
  "context": {
    "risk_score": 0.72,
    "locale": "ko"
  }
}
```

### 2.2 응답

```json
{
  "session_id": "uuid",
  "type": "vqa-image",
  "payload": {
    "question": "자동차가 포함된 이미지를 모두 선택하세요",
    "image_refs": ["img_1", "img_2", "img_3"],
    "expires_in": 300
  }
}
```

## 3. 타입별 payload/정답 스키마(샘플)

### 3.1 vqa-image

```json
{
  "payload": {
    "question": "자동차가 포함된 이미지를 모두 선택하세요",
    "image_refs": ["img_1", "img_2", "img_3", "img_4", "img_5", "img_6", "img_7", "img_8", "img_9"],
    "grid": {"rows": 3, "cols": 3}
  },
  "answer_schema": {
    "type": "index_array",
    "value": [0, 3, 5]
  }
}
```

### 3.2 vqa-illusion

```json
{
  "payload": {
    "question": "두 선의 길이는 같은가?",
    "image_ref": "illus_42",
    "options": ["같다", "다르다"],
    "option_type": "single_choice"
  },
  "answer_schema": {
    "type": "single_choice",
    "value": 0
  }
}
```

### 3.3 mouse-quiz

```json
{
  "payload": {
    "question": "별 모양을 따라 마우스를 이동하세요",
    "canvas_ref": "path_17",
    "constraints": {"max_time_ms": 20000}
  },
  "answer_schema": {
    "type": "trajectory",
    "value": {
      "path_ref": "path_17",
      "tolerance_px": 12,
      "min_coverage": 0.85
    }
  }
}
```

## 4. 저장 규칙(샘플)

- Redis key: `challenge:{session_id}`
- TTL: 180~300초
- 저장 필드 예시:

```json
{
  "type": "vqa-image",
  "payload_ref": "payload:session_id",
  "answer_hash": "sha256:...",
  "attempts": 0,
  "status": "created",
  "expires_at": "2026-03-24T12:00:00Z"
}
```

## 5. 타입별 생성 가이드

### 4.1 vqa-image
- 이미지 선택형 중심
- 질문/선택지 구성은 deterministic + 랜덤 조합
- 정답은 index 배열을 해시화하여 저장

### 4.2 vqa-illusion
- 착시/왜곡 문제는 난이도 조절이 핵심
- 정답이 모호하지 않도록 기준 문구/스코어 정의 필요

### 4.3 mouse-quiz
- 정답은 좌표/궤적 기반
- 제출 데이터 형태(좌표/시퀀스)와 검증 기준을 사전 합의

## 6. VQA 선정 전제 체크리스트

- 비용: 1회 생성/검증 비용 상한
- 지연: 생성/검증 P95 목표(ms)
- 정확도: 사람 정답률/LLM 오답률 목표
- 운영: 캐시 전략/오류 대응/장애 시 폴백
- 보안: 정답 유출 위험/회피 가능성

## 7. 결정 필요사항

- VQA 모델 선정 및 질문/정답 포맷 확정
- 난이도 정책(traffic risk 기반)
- 생성 비용/지연 허용치
