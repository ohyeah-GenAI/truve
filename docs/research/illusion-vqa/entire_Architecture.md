# System Architecture

Browser (Next.js / TypeScript) → Backend API (Spring Boot) → Challenge
Orchestrator → Python Services (VQA / Mouse Quiz) → Redis → DB

## 컴포넌트 역할

### Challenge Orchestrator

-   challenge 선택
-   세션 상태 관리
-   Python 서비스 호출

### Redis

-   session state
-   cooldown control
-   telemetry buffer

### DB

-   challenge metadata
-   telemetry feature 저장
