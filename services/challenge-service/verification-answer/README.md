# Answer Verification Guide

이 폴더는 CAPTCHA/VQA 답안 검증 기준을 정의합니다.
검증은 `session_id` 기반으로 Redis 세션을 조회해 수행합니다.

## 1. 책임 범위

- 제출 답안 검증
- 실패 사유(reason codes) 반환
- 세션 상태 업데이트 및 시도 횟수 관리

## 2. 공통 인터페이스(샘플)

### 2.1 요청

```json
{
  "session_id": "uuid",
  "type": "vqa-image",
  "answer": [0, 2, 5],
  "elapsed_ms": 18340
}
```

### 2.2 응답

```json
{
  "verified": true,
  "bot_risk": "low",
  "reason_codes": [],
  "attempts": 1
}
```

## 3. 타입별 제출 스키마(샘플)

### 3.1 vqa-image

```json
{
  "type": "vqa-image",
  "answer": [0, 2, 5]
}
```

### 3.2 vqa-illusion

```json
{
  "type": "vqa-illusion",
  "answer": 0
}
```

### 3.3 mouse-quiz

```json
{
  "type": "mouse-quiz",
  "answer": {
    "points": [[12, 18, 0], [15, 20, 30], [21, 24, 60]],
    "duration_ms": 18450
  }
}
```

## 4. 검증 규칙(샘플)

### 3.1 vqa-image
- 정답 index 집합 비교
- 부분 정답 허용 여부는 정책으로 분리

### 3.2 vqa-illusion
- 정답 텍스트/선택지 비교
- 모호한 답안 처리 기준 필요

### 3.3 mouse-quiz
- 좌표 오차 허용치 기준 필요
- 이동 궤적 특징(속도/가속도) 검증 가능

## 5. reason code 표준안(초안)

- `not_found` (세션 없음)
- `expired` (세션 만료)
- `attempts_exceeded` (시도 초과)
- `invalid_payload` (형식 오류)
- `invalid_answer` (정답 불일치)
- `checksum_mismatch` (정답 해시 불일치)
- `policy_blocked` (정책 상 차단)
- `rate_limited` (요청 제한)

## 6. 세션 상태 업데이트

- verified/pass 시 상태 변경
- 실패 시 attempts 증가
- attempts 초과 시 session invalidate

## 7. 결정 필요사항

- 각 타입별 정답 포맷/스키마
- 부분 정답/유사도 처리 정책
- bot_risk 산정 방식
