# Working Notes

코드 작업 중 계속 확인해야 하는 기준을 모아둡니다.

## 1. 모듈 경계

- 챌린지 생성/검증은 `services/challenge-service/` 가이드 기준
- VQA/Mouse Quiz 구현은 각 서비스 폴더에서만 진행

## 2. 세션/스토리지 원칙

- Redis에는 검증에 필요한 최소 정보만 저장
- 대용량 리소스는 외부 스토리지에 보관
- 결과/통계는 비동기 기록

## 3. API/스키마 기준

- 타입별 payload/정답 스키마는 `challenge-gen`/`verification-answer` 문서 참고
- reason code 표준안을 유지

## 4. 품질 기준

- P95 latency 및 cost per challenge를 기록
- 챌린지 난이도 변경 시 사람 정답률/LLM 오답률 같이 기록

## 5. 작업 방식

- 생성/검증/정책 변경은 분리 PR
- 문서 업데이트와 함께 코드 변경
