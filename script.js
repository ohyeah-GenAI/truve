// DOM 요소 선택
const imageUploadArea = document.getElementById('imageUploadArea');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');
const removeImageBtn = document.getElementById('removeImageBtn');
const questionInput = document.getElementById('questionInput');
const submitBtn = document.getElementById('submitBtn');
const answerSection = document.getElementById('answerSection');
const answerList = document.getElementById('answerList');
const loadingIndicator = document.getElementById('loadingIndicator');

// 상태 관리
let uploadedImage = null;
let imageFile = null;

// 이미지 업로드 영역 클릭 이벤트
imageUploadArea.addEventListener('click', (e) => {
    if (e.target !== removeImageBtn && !uploadedImage) {
        imageInput.click();
    }
});

// 파일 선택 이벤트
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleImageFile(file);
    }
});

// 드래그 앤 드롭 이벤트
imageUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (!uploadedImage) {
        imageUploadArea.classList.add('drag-over');
    }
});

imageUploadArea.addEventListener('dragleave', () => {
    imageUploadArea.classList.remove('drag-over');
});

imageUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    imageUploadArea.classList.remove('drag-over');
    
    if (!uploadedImage) {
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageFile(file);
        } else {
            alert('이미지 파일만 업로드할 수 있습니다.');
        }
    }
});

// 이미지 파일 처리
function handleImageFile(file) {
    // 파일 크기 검증 (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('파일 크기는 10MB 이하여야 합니다.');
        return;
    }

    // 파일 타입 검증
    if (!file.type.startsWith('image/')) {
        alert('이미지 파일만 업로드할 수 있습니다.');
        return;
    }

    imageFile = file;
    
    // 이미지 미리보기
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadedImage = e.target.result;
        previewImage.src = uploadedImage;
        previewImage.style.display = 'block';
        uploadPlaceholder.style.display = 'none';
        removeImageBtn.style.display = 'flex';
        imageUploadArea.classList.add('has-image');
        
        // 질문 입력 활성화
        enableQuestionInput();
    };
    reader.readAsDataURL(file);
}

// 이미지 제거
removeImageBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    uploadedImage = null;
    imageFile = null;
    previewImage.src = '';
    previewImage.style.display = 'none';
    uploadPlaceholder.style.display = 'block';
    removeImageBtn.style.display = 'none';
    imageUploadArea.classList.remove('has-image');
    imageInput.value = '';
    
    // 질문 입력 비활성화
    disableQuestionInput();
    
    // 답변 영역 숨기기
    answerSection.style.display = 'none';
    answerList.innerHTML = '';
});

// 질문 입력 활성화
function enableQuestionInput() {
    questionInput.disabled = false;
    questionInput.placeholder = '이미지에 대해 질문해주세요 (예: 이 이미지에 무엇이 있나요?)';
    submitBtn.disabled = false;
    document.querySelector('.hint-text').textContent = '질문을 입력하고 전송 버튼을 눌러주세요';
}

// 질문 입력 비활성화
function disableQuestionInput() {
    questionInput.disabled = true;
    questionInput.value = '';
    questionInput.placeholder = '이미지에 대해 질문해주세요';
    submitBtn.disabled = true;
    document.querySelector('.hint-text').textContent = '먼저 이미지를 업로드해주세요';
}

// 질문 제출
submitBtn.addEventListener('click', () => {
    submitQuestion();
});

questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !submitBtn.disabled) {
        submitQuestion();
    }
});

// 질문 제출 처리
async function submitQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        alert('질문을 입력해주세요.');
        return;
    }

    if (!uploadedImage) {
        alert('먼저 이미지를 업로드해주세요.');
        return;
    }

    // 로딩 표시
    showLoading();
    
    // 입력 필드 비활성화
    questionInput.disabled = true;
    submitBtn.disabled = true;

    try {
        // VQA API 호출 (데모용 mock 응답)
        const answer = await callVQAAPI(uploadedImage, question);
        
        // 답변 표시
        displayAnswer(question, answer);
        
        // 입력 필드 초기화
        questionInput.value = '';
        
    } catch (error) {
        console.error('VQA API 호출 중 오류:', error);
        alert('답변을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        // 로딩 숨김
        hideLoading();
        
        // 입력 필드 다시 활성화
        questionInput.disabled = false;
        submitBtn.disabled = false;
        questionInput.focus();
    }
}

// 로딩 표시
function showLoading() {
    loadingIndicator.style.display = 'block';
}

// 로딩 숨김
function hideLoading() {
    loadingIndicator.style.display = 'none';
}

// VQA API 호출 (데모용 mock 함수)
async function callVQAAPI(image, question) {
    // 실제 환경에서는 여기에 VQA API 호출 로직을 구현합니다
    // 예: NAVER CLOVA OCR, Vision API, OpenAI GPT-4 Vision 등
    
    // 데모용 지연 시간
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // 질문 키워드 기반 mock 응답
    const lowerQuestion = question.toLowerCase();
    
    if (lowerQuestion.includes('무엇') || lowerQuestion.includes('what')) {
        return '이미지에는 다양한 객체들이 포함되어 있습니다. 더 구체적인 질문을 하시면 상세한 답변을 드릴 수 있습니다.';
    } else if (lowerQuestion.includes('색') || lowerQuestion.includes('color')) {
        return '이미지의 주요 색상은 다채로운 색상들로 구성되어 있습니다.';
    } else if (lowerQuestion.includes('몇') || lowerQuestion.includes('how many')) {
        return '정확한 개수를 파악하기 위해서는 이미지 분석이 필요합니다. 현재는 데모 모드로 동작 중입니다.';
    } else if (lowerQuestion.includes('어디') || lowerQuestion.includes('where')) {
        return '이미지의 위치나 장소에 대한 정보는 추가적인 컨텍스트가 필요합니다.';
    } else if (lowerQuestion.includes('텍스트') || lowerQuestion.includes('글자') || lowerQuestion.includes('text')) {
        return '이미지의 텍스트를 읽기 위해서는 OCR 기능이 필요합니다. 실제 서비스에서는 NAVER CLOVA OCR을 사용할 수 있습니다.';
    } else {
        return `"${question}"에 대한 답변입니다. 이것은 데모 버전으로, 실제 VQA API를 연동하면 이미지를 분석하여 정확한 답변을 제공할 수 있습니다. NAVER CLOVA Vision API, OpenAI GPT-4 Vision, Google Vision API 등을 활용하여 실제 서비스를 구현할 수 있습니다.`;
    }
}

// 답변 표시
function displayAnswer(question, answer) {
    // 답변 섹션 표시
    answerSection.style.display = 'block';
    
    // 현재 시간
    const now = new Date();
    const timestamp = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    
    // QA 아이템 생성
    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item';
    qaItem.innerHTML = `
        <div class="question-text">${escapeHtml(question)}</div>
        <div class="answer-text">${escapeHtml(answer)}</div>
        <div class="timestamp">${timestamp}</div>
    `;
    
    // 답변 목록 최상단에 추가
    answerList.insertBefore(qaItem, answerList.firstChild);
    
    // 답변 섹션으로 스크롤
    qaItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// HTML 이스케이프 (XSS 방지)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 초기화
window.addEventListener('DOMContentLoaded', () => {
    console.log('NAVER VQA 데모 페이지가 로드되었습니다.');
    console.log('실제 VQA API를 연동하려면 script.js의 callVQAAPI 함수를 수정하세요.');
});

// 실제 API 연동 예시 (주석 처리)
/*
async function callVQAAPI(image, question) {
    // NAVER CLOVA Vision API 예시
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
*/
