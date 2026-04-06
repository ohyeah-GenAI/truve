# AI Scope

## Responsibilities

- CAPTCHA 모듈 설계 및 구현
- VQA/마우스 퀴즈 기반 챌린지 생성/검증
- 챌린지 내부 텔레메트리 수집 및 봇 탐지 신호 정의

## Modules

### VQA
- Image VQA
- Illusion VQA

### Mouse Quiz
- 마우스 이동 기반 퀴즈
- trajectory feature 추출 및 탐지 로직 설계

## Constraints

- 대규모 트래픽에서 low-latency 유지
- 비용 효율성 확보
- MSA로 독립 운영
