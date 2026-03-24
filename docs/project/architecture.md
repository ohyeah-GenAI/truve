# Architecture Overview

본 문서는 TRUVE의 CAPTCHA/VQA 모듈 아키텍처 요약입니다.
상세 구현은 각 서비스 문서를 참고하세요.

## 1. 핵심 구성

- Main Service (Gateway)
- Challenge Service (문제 생성/검증)
- Redis (세션/정답 최소 정보)
- External Storage (이미지/대용량 리소스)

## 2. 요청 흐름

1) 사용자 요청 수신
2) 정책 판단 (샘플링/의심 트래픽)
3) Challenge 생성
4) 사용자 제출
5) Verification 및 결과 반환
6) 통과 시 예매 흐름 continue

## 3. 데이터 저장 원칙

- Redis에는 검증에 필요한 최소 필드만 저장
- 대용량 리소스는 외부 스토리지에 보관
- 결과/통계는 별도 DB로 비동기 기록

## 4. 정책/확장

- 정책은 config/feature-flag 기반 교체 가능
- 챌린지 타입별로 모듈 분리
- 모듈별 독립 배포/스케일링

## 5. 관련 문서

- Challenge Service: ../../services/challenge-service/README.md
- Challenge Gen: ../../services/challenge-service/challenge-gen/README.md
- Verification Answer: ../../services/challenge-service/verification-answer/README.md
