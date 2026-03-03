# Architecture (Initial)

## VQA module
- `pipeline.py`: 입력 전처리 -> 모델 추론 -> 후처리
- `evaluator.py`: 정확도/F1/에러케이스 집계

## Bot Detection module
- `features.py`: 이벤트/행동 로그에서 피처 생성
- `detector.py`: 규칙 기반 + 모델 기반 스코어링

## Integration point
- 공통 입력 스키마 및 실험 로깅 규격을 공유
- 모듈 간 의존은 인터페이스 수준으로 최소화
