# Booking Flow (with CAPTCHA)

## User Flow

1. 홈/목록: 공연 리스트 확인
2. 공연 상세: 상세 정보 확인 후 [예매하기]
3. 인증/로그인: 회원/비회원 확인
4. 날짜/회차 선택
5. 좌석 선택 (핵심): 미니맵/좌석배치도 기반 선택
6. 결제/완료

## CAPTCHA Insert Point

- 인증/로그인 이후 또는 좌석 선택 진입 전에 챌린지 적용
- 정책에 따라 부분 샘플링/의심 트래픽 우선 적용

## Diagram

![booking-flow](../assets/flow.png)
