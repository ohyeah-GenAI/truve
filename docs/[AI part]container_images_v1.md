# AI 모듈 인프라 전달사항

## 서비스 구조

외부 진입점은 **ModuleController(8090)** 하나이며, AI 모듈은 내부망에서만 접근됩니다.

```
외부
  │
  ▼
ModuleController (Spring Boot, 외부포트: 8090)
  ├─► IllusionVQA   (내부포트: 8001) ← 준비 중
  ├─► ReceiptVQA    (내부포트: 8002)
  └─► MousePuzzle   (내부포트: 8003)
```

---

## AI 모듈

### ReceiptVQA (Image VQA)

| 항목 | 값 |
|------|----|
| GHCR 이미지 | `ghcr.io/ohyeah-genai/truve/vqa-image-demo:0.1.0` |
| 내부 포트 | `8002` |
| 헬스체크 | `GET /internal/ai/health → {"status": "ok"}` |
| Swagger | `GET /docs` |
| 필수 환경변수 | `SUPABASE_URL`, `SUPABASE_KEY` |
| 외부 의존성 | Supabase |

**Pull 명령어**
```bash
echo <읽기전용PAT> | docker login ghcr.io -u <계정명> --password-stdin
docker pull ghcr.io/ohyeah-genai/truve/vqa-image-demo:0.1.0
```

**실행 명령어**
```bash
docker run -d \
  -e SUPABASE_URL=<값> \
  -e SUPABASE_KEY=<값> \
  -p 8002:8002 \
  ghcr.io/ohyeah-genai/truve/vqa-image-demo:0.1.0
```

---

### MousePuzzle (Mouse Quiz)

| 항목 | 값 |
|------|----|
| GHCR 이미지 | `ghcr.io/ohyeah-genai/truve/mouse-quiz-demo:0.1.0` |
| 내부 포트 | `8003` |
| 헬스체크 | `GET /internal/ai/health → {"status": "ok"}` |
| Swagger | `GET /docs` |
| 필수 환경변수 | 없음 |
| 외부 의존성 | 없음 (로컬 모델 파일 내장) |

**Pull 명령어**
```bash
echo <읽기전용PAT> | docker login ghcr.io -u <계정명> --password-stdin
docker pull ghcr.io/ohyeah-genai/truve/mouse-quiz-demo:0.1.0
```

**실행 명령어**
```bash
docker run -d \
  -p 8003:8003 \
  ghcr.io/ohyeah-genai/truve/mouse-quiz-demo:0.1.0
```

---

### IllusionVQA

| 항목 | 값 |
|------|----|
| GHCR 이미지 | 준비 중 |
| 내부 포트 | `8001` |
| 헬스체크 | 준비 중 |
| 환경변수 | 준비 중 |

---

### ModuleController

| 항목 | 값 |
|------|----|
| GHCR 이미지 | `ghcr.io/ohyeah-genai/truve/module-controller:dev` |
| 내부 포트 | `8090` |
| 헬스체크 | `GET /internal/ai/health → {"status": "ok"}` |
| Swagger | `GET /docs` |
| 외부 의존성 | Redis, MySQL RDS, AI 모듈 3종 (내부망) |

**필수 환경변수**

| 변수 | 설명 |
|------|------|
| `REDIS_HOST` | Redis 호스트 |
| `REDIS_PORT` | Redis 포트 (기본 6379) |
| `REDIS_PASSWORD` | Redis 비밀번호 |
| `DB_HOST` | MySQL RDS 호스트 |
| `DB_PORT` | MySQL RDS 포트 (기본 3306) |
| `DB_USER` | MySQL 사용자 |
| `DB_PASSWORD` | MySQL 비밀번호 |
| `DB_NAME` | MySQL 데이터베이스명 |
| `VQA_IMAGE_URL` | vqa-image-demo 내부 주소 (예: `http://vqa-image:8002`) |
| `VQA_ILLUSION_URL` | vqa-illusion 내부 주소 (예: `http://vqa-illusion:8001`) |
| `MOUSE_QUIZ_URL` | mouse-quiz-demo 내부 주소 (예: `http://mouse-quiz:8003`) |

**선택 환경변수**

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `POLICY_LOW` | `mouse-quiz` | LOW 레벨 챌린지 순서 |
| `POLICY_MEDIUM` | `mouse-quiz,vqa-image` | MEDIUM 레벨 챌린지 순서 |
| `POLICY_HIGH` | `mouse-quiz,vqa-illusion` | HIGH 레벨 챌린지 순서 |

**Pull 명령어**
```bash
echo <읽기전용PAT> | docker login ghcr.io -u <계정명> --password-stdin
docker pull ghcr.io/ohyeah-genai/truve/module-controller:dev
```

**실행 명령어**
```bash
docker run -d \
  -e REDIS_HOST=<값> \
  -e REDIS_PORT=6379 \
  -e REDIS_PASSWORD=<값> \
  -e DB_HOST=<값> \
  -e DB_PORT=3306 \
  -e DB_USER=<값> \
  -e DB_PASSWORD=<값> \
  -e DB_NAME=<값> \
  -e VQA_IMAGE_URL=http://<vqa-image-host>:8002 \
  -e VQA_ILLUSION_URL=http://<vqa-illusion-host>:8001 \
  -e MOUSE_QUIZ_URL=http://<mouse-quiz-host>:8003 \
  -p 8090:8090 \
  ghcr.io/ohyeah-genai/truve/module-controller:dev
```

> **참고**: AI 모듈(8001·8002·8003)이 먼저 기동된 상태에서 ModuleController를 실행해야 합니다. `POLICY_MEDIUM`이나 `POLICY_LOW`로 받아오면 illusion-vqa 제외하고 구동가능합니다

---

## GHCR 인증 (Pull)

| 항목 | 값 |
|------|----|
| Registry | `ghcr.io` |
| 계정/조직 | `ohyeah-genai` |
| Pull 인증 | 읽기 전용 PAT (별도 전달) |

---

## 공통 API 명세

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/internal/ai/health` | GET | 헬스체크 |
| `/judge` | POST | 봇 판별 (ModuleController 연동용) |
| `/docs` | GET | Swagger UI |

**POST /judge 요청 예시**
```json
{
  "session_id": "string",
  "puzzle_type": "string",
  "answer": {},
  "events": []
}
```

**POST /judge 응답 예시**
```json
{
  "is_human": true,
  "module": "mouse",
  "passed": true
}
```

---

## 버전 업데이트 방법

새 버전 이미지가 필요할 경우 AI팀에 버전 태그 기준으로 요청:
- 태그 예시: `0.1.1`, `0.2.0`
- GHCR 이미지명에서 버전 부분만 교체
