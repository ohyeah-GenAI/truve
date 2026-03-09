# MSA 기반 VQA (Visual Question Authentication) 시스템

로그인 시 사람인지 판단하는 봇 검증 시스템을 마이크로서비스 아키텍처로 구현한 프로젝트입니다.

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                     (port: 8080)                            │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼─────────┐            ┌────────▼──────────┐
    │ Challenge Service │            │ Verification      │
    │  (port: 3001)    │            │  Service          │
    │                  │            │  (port: 3002)     │
    │ - 문제 생성      │            │ - 답변 검증       │
    │ - 이미지 제공    │            │ - 세션 관리       │
    │ - 챌린지 타입    │            │ - 토큰 발급       │
    └──────────────────┘            └───────────────────┘
             │
    ┌────────▼─────────┐
    │  Redis Cache     │
    │  (port: 6379)    │
    │                  │
    │ - 세션 저장      │
    │ - 챌린지 캐싱    │
    └──────────────────┘
```

## 📦 마이크로서비스 구성

### 1. API Gateway
- **기술**: Node.js + Express
- **역할**: 모든 요청의 진입점, 라우팅, 인증
- **포트**: 8080

### 2. Challenge Service
- **기술**: Node.js + Express
- **역할**: 
  - 다양한 유형의 챌린지 생성 (이미지 선택, 텍스트 왜곡, 슬라이더 퍼즐 등)
  - 챌린지 이미지 제공
  - 난이도 조절
- **포트**: 3001

### 3. Verification Service
- **기술**: Node.js + Express
- **역할**:
  - 사용자 답변 검증
  - 세션 관리
  - 검증 토큰 발급
  - 실패 횟수 추적
- **포트**: 3002

### 4. Redis Cache
- **기술**: Redis
- **역할**: 
  - 챌린지 세션 저장
  - 검증 토큰 임시 저장
  - 실패 시도 카운트
- **포트**: 6379

## 🎯 VQA 챌린지 타입

1. **이미지 선택형** (Image Selection)
   - "자동차가 포함된 이미지를 모두 선택하세요"
   - 3x3 그리드 이미지

2. **텍스트 왜곡형** (Distorted Text)
   - 왜곡된 텍스트 입력
   - 노이즈 추가

3. **슬라이더 퍼즐** (Slider Puzzle)
   - 이미지 조각 맞추기
   - 드래그하여 완성

4. **간단한 수학 문제** (Math Challenge)
   - "3 + 5 = ?"
   - 이미지로 렌더링

## 🚀 실행 방법

### Docker Compose 사용

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### 개별 서비스 실행

```bash
# API Gateway
cd services/api-gateway
npm install
npm start

# Challenge Service
cd services/challenge-service
npm install
npm start

# Verification Service
cd services/verification-service
npm install
npm start

# Redis
docker run -d -p 6379:6379 redis:alpine
```

## 📝 API 엔드포인트

### Challenge API

```http
POST /api/challenge/create
챌린지 생성 및 세션 ID 반환

Response:
{
  "sessionId": "uuid",
  "challengeType": "image_selection",
  "question": "자동차가 포함된 이미지를 모두 선택하세요",
  "images": [...],
  "expiresIn": 300
}
```

### Verification API

```http
POST /api/verify
답변 검증

Request:
{
  "sessionId": "uuid",
  "answer": [0, 2, 5]
}

Response:
{
  "verified": true,
  "token": "jwt-token",
  "message": "검증 성공"
}
```

## 🔒 보안 기능

- ✅ 세션 만료 시간 설정 (5분)
- ✅ 실패 횟수 제한 (3회)
- ✅ IP 기반 Rate Limiting
- ✅ JWT 토큰 기반 인증
- ✅ CORS 설정
- ✅ 챌린지 재사용 방지

## 🛠️ 기술 스택

- **Backend**: Node.js, Express
- **Cache**: Redis
- **Container**: Docker, Docker Compose
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Image Processing**: Canvas API, Sharp (Node.js)

## 📊 모니터링

각 서비스는 헬스 체크 엔드포인트를 제공합니다:

```http
GET /health
```

## 🔄 확장 가능성

- Kubernetes로 오케스트레이션
- 각 서비스 독립적 스케일링
- 메시지 큐 추가 (RabbitMQ/Kafka)
- 모니터링 도구 통합 (Prometheus, Grafana)
- AI 기반 챌린지 생성 (ML 서비스 추가)

## 📁 프로젝트 구조

```
ticketing/
├── services/
│   ├── api-gateway/
│   │   ├── src/
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── challenge-service/
│   │   ├── src/
│   │   ├── package.json
│   │   └── Dockerfile
│   └── verification-service/
│       ├── src/
│       ├── package.json
│       └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── docker-compose.yml
└── README.md
```

## 🎓 사용 예시

1. 사용자가 로그인 페이지 접속
2. Frontend에서 Challenge API 호출
3. 챌린지(이미지 선택) 표시
4. 사용자가 답변 제출
5. Verification API로 검증
6. 성공 시 JWT 토큰 발급
7. 로그인 프로세스 계속 진행

---

**개발**: KT Cloud Tech Up - MSA VQA Project
