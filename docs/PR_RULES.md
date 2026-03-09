# PR Rules (Team Standard)

## Mandatory checklist
- 관련 이슈 링크 포함
- 변경 목적 3줄 요약
- 테스트 수행 결과 첨부
- 리스크/롤백 방법 기재
- VQA/봇탐지 성능 영향 명시

## For model-related PRs
- 데이터셋 버전 명시
- 실험 설정(seed, split, threshold) 명시
- 이전 대비 성능 비교(표)
- 실패 사례 최소 3건 첨부

## Review SLAs
- 리뷰 요청 후 24시간 내 1차 피드백
- 변경 요청 발생 시 작성자가 48시간 내 대응

## Merge policy
- squash merge 권장
- CI 실패 시 머지 금지
- self-merge는 긴급 수정 제외 금지
