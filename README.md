# VQA + Bot Detection
Musical Ticketing Platform **TRUVE**의 
VQA(Visual Question Answering)와 봇 탐지(Bot Detection) 모듈을 함께 개발하는 실험/서비스 레포입니다.

## Why this repo
- 멀티모달 QA 파이프라인과 트래픽/행동 기반 봇 탐지 로직을 분리 개발
- 공통 PR 규칙과 재현성 기준으로 협업 품질 확보
- 다른 팀원에게 설명 가능한 문서 중심 개발

## Repository layout
- `src/vqa/`: VQA 모델/추론/평가 모듈
- `src/bot_detection/`: 봇 탐지 피처/규칙/모델 모듈
- `tests/`: 단위/통합 테스트
- `docs/`: 개발 원칙, PR 정책, 리뷰 기준
- `.github/`: PR/이슈 템플릿, 기본 협업 자동화 설정

## Collaboration workflow
1. 이슈 생성 (`feature`, `bug`, `research`)
2. 브랜치 생성: `feature/<issue-number>-short-title`
3. 코드 + 테스트 + 문서 동시 업데이트
4. PR 생성 후 체크리스트 충족
5. 최소 1명 리뷰 승인 + CI 통과 후 머지

자세한 규칙은 아래 문서를 참고하세요.
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/PR_RULES.md](docs/PR_RULES.md)
- [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md)

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Scope
- VQA: 데이터 전처리, 모델 추론, 정량 평가(accuracy/F1 등)
- Bot Detection: 피처 추출, 시그널 엔지니어링, 오탐/미탐 트래킹

## Non-goals (initial)
- 대규모 분산 학습 인프라 구축
- 실시간 프로덕션 트래픽 라우팅

## License
내부 사용 기준. 필요 시 추후 OSS 라이선스로 전환.
