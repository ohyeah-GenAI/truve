# MSA VQA 시스템 실행 가이드

## 🚀 빠른 시작

### 1. Docker로 전체 시스템 실행

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f api-gateway

# 서비스 상태 확인
docker-compose ps

# 서비스 중지
docker-compose down

# 볼륨까지 완전 삭제
docker-compose down -v
```

### 2. 개별 서비스 실행 (개발 모드)

#### Redis 실행
```bash
docker run -d -p 6379:6379 --name vqa-redis redis:alpine
```

#### Challenge Service
```bash
cd services/challenge-service
npm install
cp .env.example .env
npm start
```

#### Verification Service
```bash
cd services/verification-service
npm install
cp .env.example .env
npm start
```

#### API Gateway
```bash
cd services/api-gateway
npm install
cp .env.example .env
npm start
```

#### Frontend
```bash
cd frontend
# 간단한 HTTP 서버로 실행
python -m http.server 3000
# 또는
npx http-server -p 3000
```

## 📡 엔드포인트

모든 서비스 실행 후 접속 가능한 엔드포인트:

- **Frontend**: http://localhost:3000/vqa-demo.html
- **API Gateway**: http://localhost:8080
- **Challenge Service**: http://localhost:3001
- **Verification Service**: http://localhost:3002
- **Redis**: localhost:6379

## 🧪 테스트

### API 테스트 (PowerShell)

```powershell
# 1. API Gateway 상태 확인
Invoke-RestMethod -Uri "http://localhost:8080/health"

# 2. 챌린지 생성
$challenge = Invoke-RestMethod -Uri "http://localhost:8080/api/challenge/create" -Method Post -ContentType "application/json" -Body '{}'
$challenge

# 3. 답변 검증 (예시 - 이미지 선택)
$verifyBody = @{
    sessionId = $challenge.sessionId
    answer = @(0, 2, 5)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/api/verify" -Method Post -ContentType "application/json" -Body $verifyBody
```

### curl을 사용한 테스트 (Linux/Mac/Windows Git Bash)

```bash
# 챌린지 생성
curl -X POST http://localhost:8080/api/challenge/create \
  -H "Content-Type: application/json"

# 답변 검증
curl -X POST http://localhost:8080/api/verify \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"your-session-id","answer":[0,2,5]}'
```

## 🐛 문제 해결

### 포트가 이미 사용 중인 경우

```bash
# Windows에서 포트 사용 프로세스 확인
netstat -ano | findstr :8080

# 프로세스 종료
taskkill /PID <PID> /F
```

### Redis 연결 오류

```bash
# Redis 컨테이너 상태 확인
docker ps | grep redis

# Redis 재시작
docker restart vqa-redis
```

### 서비스가 시작되지 않을 때

```bash
# Docker 로그 확인
docker-compose logs api-gateway
docker-compose logs challenge-service
docker-compose logs verification-service

# 이미지 재빌드
docker-compose build --no-cache
docker-compose up -d
```

## 📊 모니터링

### 서비스 Health Check

각 서비스는 `/health` 엔드포인트를 제공합니다:

```bash
curl http://localhost:8080/health  # API Gateway
curl http://localhost:3001/health  # Challenge Service
curl http://localhost:3002/health  # Verification Service
```

### Redis 모니터링

```bash
# Redis CLI 접속
docker exec -it vqa-redis redis-cli

# 저장된 키 확인
KEYS *

# 특정 챌린지 조회
GET challenge:your-session-id
```

## 🔧 환경 변수 설정

각 서비스의 `.env` 파일에서 설정 가능:

### API Gateway
```env
PORT=8080
ALLOWED_ORIGINS=http://localhost:3000
CHALLENGE_SERVICE_URL=http://localhost:3001
VERIFICATION_SERVICE_URL=http://localhost:3002
```

### Challenge Service
```env
PORT=3001
REDIS_URL=redis://localhost:6379
```

### Verification Service
```env
PORT=3002
REDIS_URL=redis://localhost:6379
CHALLENGE_SERVICE_URL=http://localhost:3001
JWT_SECRET=your-very-secret-key
```

## 🎯 챌린지 타입

시스템이 제공하는 챌린지 타입:

1. **image_selection** - 이미지 선택 (예: 자동차가 포함된 이미지 선택)
2. **text_distorted** - 왜곡된 텍스트 입력
3. **math_question** - 간단한 수학 문제
4. **slider_puzzle** - 슬라이더 퍼즐
5. **simple_click** - 체크박스 클릭

챌린지 생성 시 타입 지정:

```json
{
  "type": "image_selection",
  "difficulty": "medium"
}
```

## 📈 성능 최적화

### Redis 캐시 설정

Redis는 챌린지 세션을 5분간 캐싱합니다. TTL 조정:

```javascript
// challenge-service/src/index.js
await redisClient.setEx(
    `challenge:${sessionId}`,
    300, // 초 단위 (300 = 5분)
    JSON.stringify(challengeData)
);
```

### Rate Limiting 조정

API Gateway의 Rate Limit 설정:

```javascript
// api-gateway/src/index.js
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15분
    max: 100 // IP당 최대 요청 수
});
```

## 🚀 프로덕션 배포

### Docker 이미지 빌드 및 푸시

```bash
# 이미지 빌드
docker-compose build

# Docker Hub에 푸시
docker tag vqa-api-gateway:latest your-registry/vqa-api-gateway:1.0.0
docker push your-registry/vqa-api-gateway:1.0.0
```

### Kubernetes 배포 (예시)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vqa-api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vqa-api-gateway
  template:
    metadata:
      labels:
        app: vqa-api-gateway
    spec:
      containers:
      - name: api-gateway
        image: your-registry/vqa-api-gateway:1.0.0
        ports:
        - containerPort: 8080
```

## 📚 추가 리소스

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [Redis 문서](https://redis.io/documentation)
- [Microservices 패턴](https://microservices.io/patterns/)

---

문제가 발생하면 GitHub Issues에 등록하거나 개발팀에 문의하세요.
