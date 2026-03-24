# Challenge Service

VQA/CAPTCHA 문제 출제와 정답 검증을 하나의 서비스 내에서 관리합니다.
VQA 모델/방식은 아직 결정되지 않았으며, 결정 전까지는 인터페이스/세션/스토리지 설계를 먼저 고정합니다.

## 1. 폴더 구조

```
services/challenge-service/
├── challenge-gen/
│   └── README.md
├── verification-answer/
│   └── README.md
└── README.md
```

## 2. 역할 분리

### 2.1 challenge-gen
- 문제 출제(생성) 담당
- 챌린지 타입별 생성 로직은 하위 모듈로 분리
- 공통 인터페이스만 먼저 정의하고 구현은 VQA 결정 후 확정

### 2.2 verification-answer
- 사용자 제출 답안 검증 담당
- 챌린지 타입별 검증 로직 분리
- 공통 검증 스키마 및 실패 사유 코드 정의

## 3. 세션/저장소 원칙

- Redis는 저지연 세션 저장소로 사용
- 대용량 원본(이미지/영상)은 Redis에 저장하지 않음
- Redis에는 검증에 필요한 최소 정보만 저장

### 3.1 Redis 세션 키 예시

```
challenge:{sessionId}
```

### 3.2 Redis에 저장하는 최소 필드

- type (vqa-image, vqa-illusion, mouse-quiz 등)
- payload_ref (이미지/리소스 참조 ID 또는 URL)
- answer_hash (정답 해시)
- attempts (시도 횟수)
- expires_at / ttl
- status (created/verified/expired)

### 3.3 대용량 리소스 저장소

- S3/Blob/File Storage에 원본 저장
- Redis에는 참조 ID만 보관

## 4. 결정 필요사항 (VQA 선정 전제)

- 어떤 VQA 방식/모델을 사용할지 결정
- VQA 타입별 정답 표현(선택지/텍스트/좌표 등)
- 검증 로직과 데이터 스키마 확정

## 5. TODO

- challenge-gen 인터페이스 정의
- verification-answer 공통 응답 스키마 정의
- 실패 사유 코드 목록 합의
