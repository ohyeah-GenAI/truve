# Engineering Principles

## 1) Reproducibility first
- 실험은 seed, 데이터 버전, 하이퍼파라미터를 문서화합니다.
- 결과는 코드와 함께 재현 가능해야 합니다.

## 2) Explainability for teammates
- 복잡한 로직에는 의도 중심의 짧은 주석 추가
- PR 본문에 설계 선택 이유와 대안 비교를 적습니다.

## 3) Small and reviewable changes
- 큰 기능은 단계별 PR로 분리합니다.
- 리팩터링과 기능 변경을 한 PR에 섞지 않습니다.

## 4) Guardrails over heroics
- 테스트/린트/체크리스트 기반으로 품질을 유지합니다.
- 특정 개인 의존이 아닌 문서화된 운영을 지향합니다.
