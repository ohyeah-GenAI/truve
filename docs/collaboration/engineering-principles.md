# Engineering Principles

## 1) Reproducibility first
- 실험은 seed, 데이터 버전, 하이퍼파라미터, 프롬프트 버전을 문서화합니다.
- 결과는 코드/설정과 함께 재현 가능해야 합니다.

## 2) Explainability for teammates
- VQA/퀴즈 생성 로직은 의도 중심의 짧은 주석을 남깁니다.
- PR 본문에 설계 선택 이유와 대안을 비교합니다.

## 3) Small and reviewable changes
- 챌린지 생성/검증/정책 변경은 분리 PR로 나눕니다.
- 리팩터링과 기능 변경을 한 PR에 섞지 않습니다.

## 4) Guardrails over heroics
- 테스트/체크리스트 기반으로 품질을 유지합니다.
- 특정 개인 의존이 아닌 문서화된 운영을 지향합니다.

## 5) Latency and cost awareness
- P95 latency와 cost per challenge를 주요 지표로 관리합니다.
- 보안/난이도 개선은 성능/비용 변화와 함께 기록합니다.
