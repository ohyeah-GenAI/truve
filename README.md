# NAVER VQA - 이미지 질문 답변 서비스

네이버 스타일의 VQA(Visual Question Answering) 데모 페이지입니다. 이미지를 업로드하고 질문을 입력하면 AI가 답변을 제공하는 웹 인터페이스를 제공합니다.

![NAVER VQA Demo](https://img.shields.io/badge/NAVER-VQA-03C75A?style=for-the-badge)

## 📸 주요 기능

- **이미지 업로드**: 드래그 앤 드롭 또는 클릭하여 이미지 업로드
- **이미지 미리보기**: 업로드된 이미지 실시간 미리보기
- **질문 입력**: 이미지에 대한 자연어 질문 입력
- **답변 생성**: AI 기반 자동 답변 생성 (데모 모드)
- **히스토리**: 질문-답변 히스토리 관리
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **네이버 UI**: 네이버 브랜드 아이덴티티를 반영한 깔끔한 디자인

## 🚀 시작하기

### 설치 및 실행

별도의 설치 과정 없이 바로 실행할 수 있습니다:

1. 프로젝트 폴더에서 `index.html` 파일을 웹 브라우저로 엽니다
2. 또는 Live Server를 사용하여 로컬 서버로 실행합니다

```bash
# Live Server 사용 (VS Code 확장 프로그램)
# 또는 Python 간단한 HTTP 서버
python -m http.server 8000

# 브라우저에서 접속
# http://localhost:8000
```

## 💡 사용 방법

1. **이미지 업로드**
   - 이미지 업로드 영역을 클릭하거나
   - 이미지 파일을 드래그 앤 드롭합니다
   - 지원 형식: JPG, PNG, GIF (최대 10MB)

2. **질문 입력**
   - 이미지가 업로드되면 질문 입력창이 활성화됩니다
   - 이미지에 대한 질문을 입력합니다
   - Enter 키 또는 전송 버튼을 클릭하여 제출합니다

3. **답변 확인**
   - AI가 생성한 답변을 확인합니다
   - 여러 질문을 계속해서 입력할 수 있습니다
   - 질문-답변 히스토리는 시간순으로 표시됩니다

## 🔧 실제 API 연동하기

현재는 데모 모드로 동작하며, 실제 VQA API를 연동하려면 `script.js` 파일의 `callVQAAPI` 함수를 수정해야 합니다.

### NAVER CLOVA Vision API 연동 예시

```javascript
async function callVQAAPI(image, question) {
    const response = await fetch('https://naveropenapi.apigw.ntruss.com/vision/v1/vqa', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-NCP-APIGW-API-KEY-ID': 'YOUR_CLIENT_ID',
            'X-NCP-APIGW-API-KEY': 'YOUR_CLIENT_SECRET'
        },
        body: JSON.stringify({
            version: 'V2',
            requestId: Date.now().toString(),
            images: [{
                format: 'jpg',
                name: 'demo',
                data: image.split(',')[1] // base64 데이터
            }],
            question: question,
            lang: 'ko'
        })
    });
    
    const data = await response.json();
    return data.answer || '답변을 생성할 수 없습니다.';
}
```

### 지원 가능한 VQA API

1. **NAVER CLOVA Vision API**
   - 한국어 지원 우수
   - [공식 문서](https://api.ncloud-docs.com/docs/ai-naver-clovaocr-ocr)

2. **OpenAI GPT-4 Vision**
   - 강력한 이미지 이해 능력
   - [공식 문서](https://platform.openai.com/docs/guides/vision)

3. **Google Cloud Vision API**
   - 다양한 이미지 분석 기능
   - [공식 문서](https://cloud.google.com/vision)

4. **AWS Rekognition + Bedrock**
   - AWS 생태계 통합
   - [공식 문서](https://aws.amazon.com/rekognition/)

## 📁 프로젝트 구조

```
ticketing/
├── index.html      # 메인 HTML 페이지
├── style.css       # 스타일시트 (네이버 UI)
├── script.js       # JavaScript 로직
└── README.md       # 프로젝트 문서
```

## 🎨 디자인 특징

- **네이버 그린**: 브랜드 컬러 (#03C75A) 사용
- **깔끔한 레이아웃**: 직관적이고 사용하기 쉬운 인터페이스
- **부드러운 애니메이션**: 사용자 경험 향상
- **반응형 웹 디자인**: 모든 디바이스에서 최적화된 표시

## 🛠️ 기술 스택

- **HTML5**: 시맨틱 마크업
- **CSS3**: Flexbox, 애니메이션, 반응형 디자인
- **JavaScript (ES6+)**: 모던 JavaScript 문법
- **No Dependencies**: 별도의 라이브러리 없이 순수 JavaScript로 구현

## 🔒 보안 고려사항

- **XSS 방지**: 사용자 입력 이스케이프 처리
- **파일 크기 제한**: 최대 10MB
- **파일 타입 검증**: 이미지 파일만 허용
- **HTTPS 사용 권장**: 실제 서비스에서는 HTTPS 필수

## 📝 향후 개선 사항

- [ ] 실제 VQA API 연동
- [ ] 다국어 지원 (영어, 일본어 등)
- [ ] 이미지 편집 기능 (자르기, 회전 등)
- [ ] 음성 질문 입력 (Web Speech API)
- [ ] 답변 음성 출력 (TTS)
- [ ] 질문 추천 기능
- [ ] 히스토리 저장 및 내보내기
- [ ] 다크 모드 지원

## 🙏 참고 자료

- [NAVER CLOVA API](https://www.ncloud.com/product/aiService/ocr)
- [Visual Question Answering](https://visualqa.org/)
- [Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)

## 📄 라이선스

이 프로젝트는 교육용 데모 프로젝트입니다.

## 👤 개발자

KT Cloud Tech Up 프로그램 - Ticketing 프로젝트

---

**Note**: 이것은 데모 버전입니다. 실제 서비스를 위해서는 백엔드 서버와 VQA API 연동이 필요합니다.
