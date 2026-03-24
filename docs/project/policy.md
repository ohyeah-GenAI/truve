# Policy & Experiment Plan

## Challenge Policy

- 어떤 접속자에게 CAPTCHA를 적용할지 정책 필요
- 의심 트래픽 우선 적용 또는 샘플링 적용 가능
- 정책은 코드 하드코딩 대신 config/feature-flag 기반으로 운영

## Experiment Plan

- LLM 오답률 vs 사람 정답률 비교
- 챌린지 난이도별 성공률 측정
- latency/비용 영향 측정

## Metrics

- pass rate (human)
- fail rate (bot)
- P95 latency
- cost per challenge
