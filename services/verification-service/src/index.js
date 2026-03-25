require('dotenv').config();
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const redis = require('redis');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3002;
const JWT_SECRET = process.env.JWT_SECRET || 'vqa-secret-key-change-in-production';
const CHALLENGE_SERVICE_URL = process.env.CHALLENGE_SERVICE_URL || 'http://localhost:3001';
const MAX_ATTEMPTS = 3;

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
        redisClient = null;
    }
}

// 미들웨어
app.use(cors());
app.use(express.json());

// Health Check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'verification-service',
        redis: redisClient ? 'connected' : 'disconnected',
        timestamp: new Date().toISOString()
    });
});

// 답변 검증
app.post('/api/verify', async (req, res) => {
    try {
        const { sessionId, answer } = req.body;
        
        if (!sessionId || answer === undefined) {
            return res.status(400).json({
                error: '잘못된 요청',
                message: 'sessionId와 answer가 필요합니다.'
            });
        }
        
        // 실패 시도 횟수 확인
        const attempts = await getAttempts(sessionId);
        if (attempts >= MAX_ATTEMPTS) {
            return res.status(429).json({
                verified: false,
                error: '시도 횟수 초과',
                message: '너무 많은 실패 시도가 있었습니다. 새로운 챌린지를 요청하세요.',
                attemptsLeft: 0
            });
        }
        
        // Challenge Service에서 챌린지 정보 조회
        let challengeData;
        try {
            const response = await axios.get(
                `${CHALLENGE_SERVICE_URL}/api/challenge/${sessionId}`
            );
            challengeData = response.data;
        } catch (error) {
            return res.status(404).json({
                verified: false,
                error: '챌린지를 찾을 수 없음',
                message: '세션이 만료되었거나 존재하지 않습니다.'
            });
        }
        
        // 답변 검증
        const isCorrect = verifyAnswer(challengeData, answer);
        
        if (isCorrect) {
            // 검증 성공 - JWT 토큰 발급
            const token = jwt.sign(
                {
                    sessionId,
                    verified: true,
                    timestamp: Date.now()
                },
                JWT_SECRET,
                { expiresIn: '1h' }
            );
            
            // Redis에서 챌린지 삭제 (재사용 방지)
            if (redisClient) {
                await redisClient.del(`challenge:${sessionId}`);
                await redisClient.del(`attempts:${sessionId}`);
            }
            
            return res.json({
                verified: true,
                token,
                message: '검증 성공! 사람임이 확인되었습니다.',
                expiresIn: 3600
            });
        } else {
            // 검증 실패
            await incrementAttempts(sessionId);
            const newAttempts = attempts + 1;
            const attemptsLeft = MAX_ATTEMPTS - newAttempts;
            
            return res.status(400).json({
                verified: false,
                error: '검증 실패',
                message: '답변이 올바르지 않습니다.',
                attemptsLeft,
                shouldRenew: attemptsLeft === 0
            });
        }
        
    } catch (error) {
        console.error('Verification Error:', error);
        res.status(500).json({
            verified: false,
            error: '검증 처리 실패',
            message: error.message
        });
    }
});

// 답변 검증 로직
function verifyAnswer(challengeData, userAnswer) {
    const { type, answer: correctAnswer } = challengeData;
    
    switch (type) {
        case 'image_selection':
            // 배열 비교
            if (!Array.isArray(userAnswer) || !Array.isArray(correctAnswer)) {
                return false;
            }
            if (userAnswer.length !== correctAnswer.length) {
                return false;
            }
            const sortedUser = [...userAnswer].sort((a, b) => a - b);
            const sortedCorrect = [...correctAnswer].sort((a, b) => a - b);
            return sortedUser.every((val, idx) => val === sortedCorrect[idx]);
            
        case 'text_distorted':
        case 'math_question':
            // 문자열 비교 (대소문자 무시)
            return userAnswer.toString().toUpperCase() === correctAnswer.toString().toUpperCase();
            
        case 'slider_puzzle':
            // 오차 범위 내 비교
            const tolerance = challengeData.tolerance || 5;
            const diff = Math.abs(parseFloat(userAnswer) - parseFloat(correctAnswer));
            return diff <= tolerance;
            
        case 'simple_click':
            // 단순 클릭 확인
            return userAnswer === 'clicked' || userAnswer === true;
            
        default:
            return false;
    }
}

// 실패 시도 횟수 조회
async function getAttempts(sessionId) {
    if (!redisClient) return 0;
    
    try {
        const attempts = await redisClient.get(`attempts:${sessionId}`);
        return attempts ? parseInt(attempts) : 0;
    } catch (error) {
        console.error('Get Attempts Error:', error);
        return 0;
    }
}

// 실패 시도 횟수 증가
async function incrementAttempts(sessionId) {
    if (!redisClient) return;
    
    try {
        const key = `attempts:${sessionId}`;
        const current = await redisClient.get(key);
        const newValue = current ? parseInt(current) + 1 : 1;
        await redisClient.setEx(key, 300, newValue.toString());
    } catch (error) {
        console.error('Increment Attempts Error:', error);
    }
}

// 토큰 검증 엔드포인트
app.post('/api/verify-token', (req, res) => {
    try {
        const { token } = req.body;
        
        if (!token) {
            return res.status(400).json({
                valid: false,
                error: '토큰이 필요합니다.'
            });
        }
        
        const decoded = jwt.verify(token, JWT_SECRET);
        
        res.json({
            valid: true,
            verified: decoded.verified,
            sessionId: decoded.sessionId,
            issuedAt: new Date(decoded.iat * 1000).toISOString(),
            expiresAt: new Date(decoded.exp * 1000).toISOString()
        });
        
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({
                valid: false,
                error: '토큰이 만료되었습니다.'
            });
        } else if (error.name === 'JsonWebTokenError') {
            return res.status(401).json({
                valid: false,
                error: '유효하지 않은 토큰입니다.'
            });
        }
        
        res.status(500).json({
            valid: false,
            error: '토큰 검증 실패',
            message: error.message
        });
    }
});

// 서버 시작
async function start() {
    await connectRedis();
    
    app.listen(PORT, () => {
        console.log('='.repeat(50));
        console.log('✅ Verification Service Started');
        console.log('='.repeat(50));
        console.log(`📍 Port: ${PORT}`);
        console.log(`🌐 URL: http://localhost:${PORT}`);
        console.log(`💾 Redis: ${redisClient ? 'Connected' : 'Disconnected'}`);
        console.log(`🔑 JWT Secret: ${JWT_SECRET.substring(0, 10)}...`);
        console.log('='.repeat(50));
    });
}

start();
