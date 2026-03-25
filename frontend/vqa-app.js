// VQA 봇 검증 시스템 Frontend

const API_GATEWAY = 'http://localhost:8080';
let currentSessionId = null;
let currentChallengeType = null;
let userAnswer = null;

// DOM 요소
const btnLogin = document.getElementById('btnLogin');
const btnRefresh = document.getElementById('btnRefresh');
const btnVerify = document.getElementById('btnVerify');
const vqaArea = document.getElementById('vqaArea');
const challengeContainer = document.getElementById('challengeContainer');
const vqaStatus = document.getElementById('vqaStatus');
const currentSessionIdEl = document.getElementById('currentSessionId');
const currentTokenEl = document.getElementById('currentToken');

// 서비스 상태 확인
async function checkServicesHealth() {
    const services = [
        { id: 'statusGateway', url: `${API_GATEWAY}/health` },
        { id: 'statusChallenge', url: `${API_GATEWAY}/api/challenge/health` },
        { id: 'statusVerification', url: `${API_GATEWAY}/api/verify/health` }
    ];
    
    for (const service of services) {
        const el = document.getElementById(service.id);
        try {
            const response = await fetch(service.url);
            if (response.ok) {
                el.textContent = '🟢 온라인';
                el.classList.add('online');
            } else {
                el.textContent = '🔴 오프라인';
                el.classList.add('offline');
            }
        } catch (error) {
            el.textContent = '🔴 오프라인';
            el.classList.add('offline');
        }
    }
}

// 로그인 버튼 클릭
btnLogin.addEventListener('click', async () => {
    const userId = document.getElementById('userId').value;
    const userPw = document.getElementById('userPw').value;
    
    if (!userId || !userPw) {
        alert('아이디와 비밀번호를 입력하세요.');
        return;
    }
    
    // VQA 챌린지 표시
    vqaArea.style.display = 'block';
    btnLogin.disabled = true;
    
    // 챌린지 로드
    await loadChallenge();
});

// 새로고침 버튼
btnRefresh.addEventListener('click', () => {
    loadChallenge();
});

// 확인 버튼
btnVerify.addEventListener('click', async () => {
    if (!currentSessionId || userAnswer === null) {
        showStatus('답변을 선택하거나 입력하세요.', 'error');
        return;
    }
    
    await verifyAnswer();
});

// 챌린지 로드
async function loadChallenge() {
    try {
        challengeContainer.innerHTML = '<div class="challenge-loading">챌린지를 생성하는 중...</div>';
        showStatus('새로운 챌린지를 로드하고 있습니다...', 'info');
        btnVerify.disabled = true;
        userAnswer = null;
        
        const response = await fetch(`${API_GATEWAY}/api/challenge/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                difficulty: 'medium'
            })
        });
        
        if (!response.ok) {
            throw new Error('챌린지 생성 실패');
        }
        
        const data = await response.json();
        currentSessionId = data.sessionId;
        currentChallengeType = data.challengeType;
        
        // 세션 ID 표시
        currentSessionIdEl.textContent = currentSessionId;
        
        // 챌린지 렌더링
        renderChallenge(data);
        
        hideStatus();
        
    } catch (error) {
        console.error('Challenge Load Error:', error);
        challengeContainer.innerHTML = '<div class="challenge-loading">❌ 챌린지 로드 실패</div>';
        showStatus('챌린지를 로드할 수 없습니다. API Gateway가 실행 중인지 확인하세요.', 'error');
    }
}

// 챌린지 렌더링
function renderChallenge(data) {
    let html = '';
    
    switch (data.challengeType) {
        case 'image_selection':
            html = renderImageSelection(data);
            break;
        case 'text_distorted':
            html = renderTextChallenge(data);
            break;
        case 'math_question':
            html = renderMathChallenge(data);
            break;
        case 'slider_puzzle':
            html = renderSliderChallenge(data);
            break;
        case 'simple_click':
            html = renderClickChallenge(data);
            break;
        default:
            html = '<div>알 수 없는 챌린지 타입</div>';
    }
    
    challengeContainer.innerHTML = html;
    
    // 이벤트 리스너 연결
    attachChallengeListeners(data.challengeType);
}

// 이미지 선택 챌린지 렌더링
function renderImageSelection(data) {
    const emojis = {
        '자동차': '🚗',
        '신호등': '🚦',
        '횡단보도': '🚸',
        '자전거': '🚲',
        '버스': '🚌'
    };
    
    // 챌린지 질문에서 카테고리 추출
    const category = Object.keys(emojis).find(cat => data.question.includes(cat)) || '자동차';
    const emoji = emojis[category];
    
    const gridHtml = data.images.map((img, index) => {
        // 실제로는 img.url의 이미지를 사용하지만, 데모에서는 이모지 사용
        const hasTarget = Math.random() > 0.6; // 랜덤으로 대상 포함
        const displayEmoji = hasTarget ? emoji : '🏢';
        
        return `
            <div class="image-grid-item" data-index="${index}">
                <span class="image-placeholder">${displayEmoji}</span>
            </div>
        `;
    }).join('');
    
    return `
        <div class="challenge-question">${data.question}</div>
        <div class="image-grid" style="grid-template-columns: repeat(${data.gridSize}, 1fr)">
            ${gridHtml}
        </div>
    `;
}

// 텍스트 챌린지 렌더링
function renderTextChallenge(data) {
    return `
        <div class="text-challenge">
            <div class="challenge-question">${data.question}</div>
            <div class="challenge-image" style="background: #f0f0f0; padding: 2rem; font-size: 2rem; font-weight: bold; letter-spacing: 0.5em; font-family: monospace;">
                ${generateDistortedTextPreview()}
            </div>
            <input type="text" class="challenge-input" id="textAnswer" placeholder="위 문자를 입력하세요" maxlength="8">
        </div>
    `;
}

// 수학 문제 챌린지 렌더링
function renderMathChallenge(data) {
    return `
        <div class="text-challenge">
            <div class="challenge-question">${data.question}</div>
            <div class="challenge-image" style="background: #f0f0f0; padding: 2rem; font-size: 2.5rem; font-weight: bold;">
                ${data.mathExpression}
            </div>
            <input type="number" class="challenge-input" id="mathAnswer" placeholder="답을 입력하세요">
        </div>
    `;
}

// 슬라이더 챌린지 렌더링
function renderSliderChallenge(data) {
    return `
        <div class="text-challenge">
            <div class="challenge-question">${data.question}</div>
            <div style="margin: 2rem 0;">
                <input type="range" min="0" max="100" value="50" class="slider" id="sliderAnswer" style="width: 100%; height: 40px;">
                <div style="text-align: center; margin-top: 1rem; font-size: 1.5rem;" id="sliderValue">50</div>
            </div>
        </div>
    `;
}

// 클릭 챌린지 렌더링
function renderClickChallenge(data) {
    return `
        <div class="click-challenge">
            <div class="challenge-question">${data.question}</div>
            <label style="cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem; font-size: 1.2rem; margin-top: 1rem;">
                <input type="checkbox" class="checkbox-large" id="clickAnswer">
                나는 로봇이 아닙니다
            </label>
        </div>
    `;
}

// 왜곡된 텍스트 미리보기 생성 (데모용)
function generateDistortedTextPreview() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let text = '';
    for (let i = 0; i < 6; i++) {
        text += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return text;
}

// 챌린지 이벤트 리스너 연결
function attachChallengeListeners(type) {
    switch (type) {
        case 'image_selection':
            attachImageSelectionListeners();
            break;
        case 'text_distorted':
        case 'math_question':
            attachTextInputListeners();
            break;
        case 'slider_puzzle':
            attachSliderListeners();
            break;
        case 'simple_click':
            attachClickListeners();
            break;
    }
}

// 이미지 선택 리스너
function attachImageSelectionListeners() {
    userAnswer = [];
    const items = document.querySelectorAll('.image-grid-item');
    
    items.forEach(item => {
        item.addEventListener('click', () => {
            const index = parseInt(item.dataset.index);
            
            if (item.classList.contains('selected')) {
                item.classList.remove('selected');
                userAnswer = userAnswer.filter(i => i !== index);
            } else {
                item.classList.add('selected');
                userAnswer.push(index);
            }
            
            btnVerify.disabled = userAnswer.length === 0;
        });
    });
}

// 텍스트 입력 리스너
function attachTextInputListeners() {
    const input = document.getElementById('textAnswer') || document.getElementById('mathAnswer');
    
    input.addEventListener('input', () => {
        userAnswer = input.value.trim();
        btnVerify.disabled = !userAnswer;
    });
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !btnVerify.disabled) {
            verifyAnswer();
        }
    });
}

// 슬라이더 리스너
function attachSliderListeners() {
    const slider = document.getElementById('sliderAnswer');
    const valueDisplay = document.getElementById('sliderValue');
    
    slider.addEventListener('input', () => {
        userAnswer = parseInt(slider.value);
        valueDisplay.textContent = userAnswer;
        btnVerify.disabled = false;
    });
}

// 클릭 리스너
function attachClickListeners() {
    const checkbox = document.getElementById('clickAnswer');
    
    checkbox.addEventListener('change', () => {
        userAnswer = checkbox.checked ? 'clicked' : null;
        btnVerify.disabled = !checkbox.checked;
    });
}

// 답변 검증
async function verifyAnswer() {
    try {
        btnVerify.disabled = true;
        showStatus('검증 중...', 'info');
        
        const response = await fetch(`${API_GATEWAY}/api/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: currentSessionId,
                answer: userAnswer
            })
        });
        
        const data = await response.json();
        
        if (data.verified) {
            // 성공!
            showStatus('✅ 검증 성공! 사람임이 확인되었습니다.', 'success');
            currentTokenEl.textContent = data.token;
            
            // 성공 모달 표시
            setTimeout(() => {
                showSuccessModal();
            }, 500);
            
        } else {
            // 실패
            const attemptsLeft = data.attemptsLeft !== undefined ? data.attemptsLeft : 0;
            showStatus(`❌ ${data.message} (남은 시도: ${attemptsLeft}회)`, 'error');
            
            if (data.shouldRenew) {
                // 새 챌린지 로드
                setTimeout(() => {
                    loadChallenge();
                }, 2000);
            } else {
                btnVerify.disabled = false;
            }
        }
        
    } catch (error) {
        console.error('Verification Error:', error);
        showStatus('검증 중 오류가 발생했습니다.', 'error');
        btnVerify.disabled = false;
    }
}

// 상태 메시지 표시
function showStatus(message, type) {
    vqaStatus.textContent = message;
    vqaStatus.className = `vqa-status show ${type}`;
}

// 상태 메시지 숨김
function hideStatus() {
    vqaStatus.classList.remove('show');
}

// 성공 모달 표시
function showSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.style.display = 'flex';
}

// 모달 닫기
function closeModal() {
    const modal = document.getElementById('successModal');
    modal.style.display = 'none';
    
    // 페이지 리셋 또는 실제 로그인 진행
    vqaArea.style.display = 'none';
    btnLogin.disabled = false;
    document.getElementById('userId').value = '';
    document.getElementById('userPw').value = '';
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 MSA VQA 시스템 시작');
    checkServicesHealth();
    
    // 주기적으로 서비스 상태 확인 (30초마다)
    setInterval(checkServicesHealth, 30000);
});
