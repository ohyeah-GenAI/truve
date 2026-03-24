# TRUVE AI Security (VQA + Bot Detection)

뮤지컬 티켓팅 플랫폼 **TRUVE**의 공정한 예매를 위해 VQA/CAPTCHA 및 봇 탐지 모듈을 개발하는 레포입니다.
챌린지 생성/검증과 정책 설계를 분리하고, 모듈별로 확장 가능한 구조를 목표로 합니다.

## Repository layout

- `services/challenge-service/`: 챌린지 생성/검증 가이드 및 스키마
- `services/vqa-image/`: Image VQA 모듈
- `services/vqa-illusion/`: Illusion VQA 모듈
- `services/mouse-quiz/`: Mouse Quiz 모듈
- `apps/`: 타입별 데모 UI
- `src/`: 프로토타입/실험 코드
- `docs/`: 프로젝트/정책/협업 가이드
- `tests/`: 단위/통합 테스트

## Docs

- 문서 인덱스: [docs/index.md](docs/index.md)
- 챌린지 서비스 가이드: [services/challenge-service/README.md](services/challenge-service/README.md)

## Collaboration workflow

1. 이슈 생성 (`feature`, `bug`, `research`)
2. 브랜치 생성: `feature/<issue-number>-short-title`
3. 코드 + 테스트 + 문서 동시 업데이트
4. PR 생성 후 체크리스트 충족
5. 최소 1명 리뷰 승인 + CI 통과 후 머지

자세한 규칙은 아래 문서를 참고하세요.

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/collaboration/pr-rules.md](docs/collaboration/pr-rules.md)
- [docs/collaboration/engineering-principles.md](docs/collaboration/engineering-principles.md)

## Quick start (optional)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Scope

- VQA: 문제 생성/검증 인터페이스, 난이도/정책 설계
- Bot Detection: 텔레메트리 기반 신호 정의 및 위험 점수화

## Non-goals (initial)

- 대규모 분산 학습 인프라 구축
- 실시간 프로덕션 트래픽 라우팅

## License

내부 사용 기준. 필요 시 추후 OSS 라이선스로 전환.
