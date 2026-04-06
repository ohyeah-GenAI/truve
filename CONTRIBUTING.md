# Contributing Guide

## Branch strategy
- 기본 브랜치: `main`
- 기능 개발: `feature/<issue-number>-<topic>`
- 버그 수정: `fix/<issue-number>-<topic>`
- 실험/리서치: `research/<issue-number>-<topic>`

## Commit convention
- `feat:` 기능 추가
- `fix:` 버그 수정
- `docs:` 문서 변경
- `test:` 테스트 추가/수정
- `refactor:` 리팩터링(동작 변경 없음)

예시:
- `feat(vqa): add baseline inference pipeline`
- `fix(bot): handle missing user-agent field`

## Pull request rules
- PR 크기: 가능하면 400 LOC 이하 권장
- 하나의 PR은 하나의 목적만 포함
- 테스트 결과와 재현 방법을 PR 본문에 명시
- 모델/임계값 변경 시 성능 비교 표 필수

## Review expectations
- 최소 1명 승인
- blocking 코멘트 해결 전 머지 금지
- 리뷰어는 재현 가능성/회귀 위험 중심으로 검토

## Definition of done
- 코드 구현 완료
- 테스트 작성 및 통과
- 문서 업데이트 완료
- 관측 가능한 로그/메트릭 반영(필요 시)
