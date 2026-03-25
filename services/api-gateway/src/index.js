require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 8080;

// 환경 변수
const CHALLENGE_SERVICE_URL = process.env.CHALLENGE_SERVICE_URL || 'http://localhost:3001';
const VERIFICATION_SERVICE_URL = process.env.VERIFICATION_SERVICE_URL || 'http://localhost:3002';

// 미들웨어
app.use(helmet());
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
    credentials: true
}));
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate Limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15분
    max: 100, // IP당 최대 100 요청
    message: '너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요.',
    standardHeaders: true,
    legacyHeaders: false,
});

const strictLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10, // 검증 요청은 더 엄격하게
    message: '검증 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.',
});

app.use('/api/', limiter);

// Health Check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'api-gateway',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// API Gateway 정보
app.get('/api/info', (req, res) => {
    res.json({
        name: 'VQA API Gateway',
        version: '1.0.0',
        description: 'MSA 기반 Visual Question Authentication 시스템',
        services: {
            challenge: CHALLENGE_SERVICE_URL,
            verification: VERIFICATION_SERVICE_URL
        }
    });
});

// Challenge Service 프록시
app.use('/api/challenge', createProxyMiddleware({
    target: CHALLENGE_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/api/challenge': '/api'
    },
    onError: (err, req, res) => {
        console.error('Challenge Service Error:', err.message);
        res.status(503).json({
            error: 'Challenge Service 연결 실패',
            message: '챌린지 서비스가 일시적으로 사용 불가능합니다.'
        });
    },
    onProxyReq: (proxyReq, req, res) => {
        // 요청 로깅
        console.log(`[Proxy] ${req.method} ${req.path} -> ${CHALLENGE_SERVICE_URL}`);
    }
}));

// Verification Service 프록시
app.use('/api/verify', strictLimiter, createProxyMiddleware({
    target: VERIFICATION_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/api/verify': '/api/verify'
    },
    onError: (err, req, res) => {
        console.error('Verification Service Error:', err.message);
        res.status(503).json({
            error: 'Verification Service 연결 실패',
            message: '검증 서비스가 일시적으로 사용 불가능합니다.'
        });
    },
    onProxyReq: (proxyReq, req, res) => {
        console.log(`[Proxy] ${req.method} ${req.path} -> ${VERIFICATION_SERVICE_URL}`);
    }
}));

// 404 핸들러
app.use((req, res) => {
    res.status(404).json({
        error: 'Not Found',
        message: '요청한 엔드포인트를 찾을 수 없습니다.',
        path: req.path
    });
});

// 에러 핸들러
app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(err.status || 500).json({
        error: err.message || 'Internal Server Error',
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    });
});

// 서버 시작
app.listen(PORT, () => {
    console.log('='.repeat(50));
    console.log('🚀 API Gateway Started');
    console.log('='.repeat(50));
    console.log(`📍 Port: ${PORT}`);
    console.log(`🌐 URL: http://localhost:${PORT}`);
    console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log('='.repeat(50));
    console.log('📡 Proxying to:');
    console.log(`   Challenge Service: ${CHALLENGE_SERVICE_URL}`);
    console.log(`   Verification Service: ${VERIFICATION_SERVICE_URL}`);
    console.log('='.repeat(50));
});

// Graceful Shutdown
process.on('SIGTERM', () => {
    console.log('👋 SIGTERM received, shutting down gracefully...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('👋 SIGINT received, shutting down gracefully...');
    process.exit(0);
});
