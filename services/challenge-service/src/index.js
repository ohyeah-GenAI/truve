require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 3001;

// Redis 클라이언트
let redisClient;

// Redis 연결
async function connectRedis() {
    try {
        redisClient = redis.createClient({
            url: process.env.REDIS_URL || 'redis://localhost:6379'
        });

        redisClient.on('error', (err) => console.error('Redis Error:', err));
        redisClient.on('connect', () => console.log('✅ Redis Connected'));

        await redisClient.connect();
    } catch (error) {
        console.error('Failed to connect to Redis:', error);
        // Redis 없이도 동작하도록 메모리 캐시 사용
        redisClient = null;
    }
}

// 미들웨어
app.use(cors());
app.use(express.json());

// 챌린지 타입 정의
const CHALLENGE_TYPES = {
    IMAGE_SELECTION: 'image_selection',
    TEXT_DISTORTED: 'text_distorted',
    SLIDER_PUZZLE: 'slider_puzzle',
    MATH_QUESTION: 'math_question',
    SIMPLE_CLICK: 'simple_click'
};

// Health Check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'challenge-service',
        redis: redisClient ? 'connected' : 'disconnected',
        timestamp: new Date().toISOString()
    });
});

// 챌린지 생성
app.post('/api/create', async (req, res) => {
    try {
        const { type, difficulty = 'medium' } = req.body;
        
        // 챌린지 타입 결정 (지정되지 않으면 랜덤)
        const challengeType = type || getRandomChallengeType();
        
        // 세션 ID 생성
        const sessionId = uuidv4();
        
        // 챌린지 생성
        const challenge = await generateChallenge(challengeType, difficulty);
        
        // Redis에 챌린지 저장 (5분 만료)
        const challengeData = {
            sessionId,
            type: challengeType,
            answer: challenge.answer, // 정답 저장
            createdAt: Date.now(),
            difficulty
        };
        
        if (redisClient) {
            await redisClient.setEx(
                `challenge:${sessionId}`,
                300, // 5분
                JSON.stringify(challengeData)
            );
        }
        
        // 클라이언트에게는 정답 제외하고 전송
        const { answer, ...clientChallenge } = challenge;
        
        res.json({
            sessionId,
            challengeType,
            difficulty,
            expiresIn: 300,
            ...clientChallenge
        });
        
    } catch (error) {
        console.error('Challenge Creation Error:', error);
        res.status(500).json({
            error: '챌린지 생성 실패',
            message: error.message
        });
    }
});

// 챌린지 타입별 생성 함수
async function generateChallenge(type, difficulty) {
    switch (type) {
        case CHALLENGE_TYPES.IMAGE_SELECTION:
            return generateImageSelection(difficulty);
        case CHALLENGE_TYPES.TEXT_DISTORTED:
            return generateDistortedText(difficulty);
        case CHALLENGE_TYPES.SLIDER_PUZZLE:
            return generateSliderPuzzle(difficulty);
        case CHALLENGE_TYPES.MATH_QUESTION:
            return generateMathQuestion(difficulty);
        case CHALLENGE_TYPES.SIMPLE_CLICK:
            return generateSimpleClick(difficulty);
        default:
            throw new Error('Unknown challenge type');
    }
}

// 이미지 선택형 챌린지
function generateImageSelection(difficulty) {
    const categories = ['자동차', '신호등', '횡단보도', '자전거', '버스'];
    const selectedCategory = categories[Math.floor(Math.random() * categories.length)];
    
    // 난이도에 따라 그리드 크기 결정
    const gridSize = difficulty === 'easy' ? 6 : difficulty === 'hard' ? 12 : 9;
    
    // 정답 인덱스 생성 (1~3개)
    const answerCount = Math.floor(Math.random() * 3) + 1;
    const answer = [];
    while (answer.length < answerCount) {
        const idx = Math.floor(Math.random() * gridSize);
        if (!answer.includes(idx)) {
            answer.push(idx);
        }
    }
    
    // 이미지 URL 생성 (실제로는 이미지 서비스에서 제공)
    const images = Array.from({ length: gridSize }, (_, i) => ({
        id: i,
        url: `/api/images/grid/${i}?category=${selectedCategory}&has=${answer.includes(i)}`
    }));
    
    return {
        question: `${selectedCategory}가 포함된 이미지를 모두 선택하세요`,
        images,
        gridSize: Math.sqrt(gridSize),
        answer: answer.sort((a, b) => a - b)
    };
}

// 왜곡된 텍스트 챌린지
function generateDistortedText(difficulty) {
    const length = difficulty === 'easy' ? 4 : difficulty === 'hard' ? 8 : 6;
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // 혼동되는 문자 제외
    
    let text = '';
    for (let i = 0; i < length; i++) {
        text += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    return {
        question: '아래 이미지의 문자를 입력하세요',
        imageUrl: `/api/images/distorted?text=${text}&difficulty=${difficulty}`,
        answer: text
    };
}

// 슬라이더 퍼즐 챌린지
function generateSliderPuzzle(difficulty) {
    const imageId = Math.floor(Math.random() * 1000);
    const targetPosition = Math.floor(Math.random() * 80) + 10; // 10-90%
    
    return {
        question: '슬라이더를 움직여 퍼즐을 맞추세요',
        imageUrl: `/api/images/puzzle/${imageId}`,
        answer: targetPosition,
        tolerance: difficulty === 'easy' ? 10 : difficulty === 'hard' ? 3 : 5
    };
}

// 수학 문제 챌린지
function generateMathQuestion(difficulty) {
    let num1, num2, operator, answer;
    
    if (difficulty === 'easy') {
        num1 = Math.floor(Math.random() * 10) + 1;
        num2 = Math.floor(Math.random() * 10) + 1;
        operator = '+';
        answer = num1 + num2;
    } else if (difficulty === 'hard') {
        num1 = Math.floor(Math.random() * 20) + 10;
        num2 = Math.floor(Math.random() * 20) + 10;
        const ops = ['+', '-', '*'];
        operator = ops[Math.floor(Math.random() * ops.length)];
        answer = operator === '+' ? num1 + num2 : operator === '-' ? num1 - num2 : num1 * num2;
    } else {
        num1 = Math.floor(Math.random() * 15) + 5;
        num2 = Math.floor(Math.random() * 15) + 5;
        operator = Math.random() > 0.5 ? '+' : '-';
        answer = operator === '+' ? num1 + num2 : num1 - num2;
    }
    
    return {
        question: '다음 계산 결과를 입력하세요',
        imageUrl: `/api/images/math?q=${num1}${operator}${num2}`,
        mathExpression: `${num1} ${operator} ${num2} = ?`,
        answer: answer.toString()
    };
}

// 간단한 클릭 챌린지
function generateSimpleClick(difficulty) {
    const actions = [
        '체크박스를 클릭하세요',
        '버튼을 클릭하세요',
        '\"나는 로봇이 아닙니다\"를 클릭하세요'
    ];
    
    return {
        question: actions[Math.floor(Math.random() * actions.length)],
        answer: 'clicked',
        timeout: difficulty === 'easy' ? 10 : difficulty === 'hard' ? 3 : 5
    };
}

// 랜덤 챌린지 타입 선택
function getRandomChallengeType() {
    const types = Object.values(CHALLENGE_TYPES);
    return types[Math.floor(Math.random() * types.length)];
}

// 챌린지 조회 (Verification Service용)
app.get('/api/challenge/:sessionId', async (req, res) => {
    try {
        const { sessionId } = req.params;
        
        if (!redisClient) {
            return res.status(503).json({
                error: 'Redis 연결 없음',
                message: '챌린지 조회가 불가능합니다.'
            });
        }
        
        const data = await redisClient.get(`challenge:${sessionId}`);
        
        if (!data) {
            return res.status(404).json({
                error: '챌린지를 찾을 수 없음',
                message: '세션이 만료되었거나 존재하지 않습니다.'
            });
        }
        
        res.json(JSON.parse(data));
        
    } catch (error) {
        console.error('Challenge Retrieval Error:', error);
        res.status(500).json({
            error: '챌린지 조회 실패',
            message: error.message
        });
    }
});

// 서버 시작
async function start() {
    await connectRedis();
    
    app.listen(PORT, () => {
        console.log('='.repeat(50));
        console.log('🎯 Challenge Service Started');
        console.log('='.repeat(50));
        console.log(`📍 Port: ${PORT}`);
        console.log(`🌐 URL: http://localhost:${PORT}`);
        console.log(`💾 Redis: ${redisClient ? 'Connected' : 'Disconnected'}`);
        console.log('='.repeat(50));
    });
}

start();
