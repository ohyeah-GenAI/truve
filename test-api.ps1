# VQA API 테스트 스크립트 (PowerShell)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "MSA VQA API 테스트" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$API_GATEWAY = "http://localhost:8080"

# 1. Health Check
Write-Host "1️⃣ Health Check 테스트" -ForegroundColor Yellow
Write-Host "   요청: GET $API_GATEWAY/health" -ForegroundColor Gray
try {
    $health = Invoke-RestMethod -Uri "$API_GATEWAY/health" -Method Get
    Write-Host "   ✅ 성공!" -ForegroundColor Green
    Write-Host "   응답: $($health | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 실패: $_" -ForegroundColor Red
}
Write-Host ""

# 2. 챌린지 생성 (이미지 선택)
Write-Host "2️⃣ 챌린지 생성 테스트 (이미지 선택)" -ForegroundColor Yellow
Write-Host "   요청: POST $API_GATEWAY/api/challenge/create" -ForegroundColor Gray
try {
    $createBody = @{
        type = "image_selection"
        difficulty = "medium"
    } | ConvertTo-Json
    
    $challenge = Invoke-RestMethod -Uri "$API_GATEWAY/api/challenge/create" -Method Post -ContentType "application/json" -Body $createBody
    Write-Host "   ✅ 챌린지 생성 성공!" -ForegroundColor Green
    Write-Host "   Session ID: $($challenge.sessionId)" -ForegroundColor Cyan
    Write-Host "   타입: $($challenge.challengeType)" -ForegroundColor Cyan
    Write-Host "   질문: $($challenge.question)" -ForegroundColor Cyan
    
    $sessionId = $challenge.sessionId
} catch {
    Write-Host "   ❌ 실패: $_" -ForegroundColor Red
    $sessionId = $null
}
Write-Host ""

# 3. 올바른 답변으로 검증 (데모용 - 실제로는 랜덤 답변)
if ($sessionId) {
    Write-Host "3️⃣ 답변 검증 테스트" -ForegroundColor Yellow
    Write-Host "   요청: POST $API_GATEWAY/api/verify" -ForegroundColor Gray
    
    # 랜덤 답변 생성
    $randomAnswer = @(
        (Get-Random -Minimum 0 -Maximum 9),
        (Get-Random -Minimum 0 -Maximum 9)
    ) | Sort-Object -Unique
    
    try {
        $verifyBody = @{
            sessionId = $sessionId
            answer = $randomAnswer
        } | ConvertTo-Json
        
        Write-Host "   제출한 답변: $randomAnswer" -ForegroundColor Gray
        
        $result = Invoke-RestMethod -Uri "$API_GATEWAY/api/verify" -Method Post -ContentType "application/json" -Body $verifyBody
        
        if ($result.verified) {
            Write-Host "   ✅ 검증 성공!" -ForegroundColor Green
            Write-Host "   토큰: $($result.token.Substring(0, 50))..." -ForegroundColor Cyan
        } else {
            Write-Host "   ❌ 검증 실패 (예상됨 - 랜덤 답변)" -ForegroundColor Yellow
            Write-Host "   메시지: $($result.message)" -ForegroundColor Gray
            Write-Host "   남은 시도: $($result.attemptsLeft)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ❌ 검증 요청 실패: $_" -ForegroundColor Red
    }
}
Write-Host ""

# 4. 다른 챌린지 타입 테스트
Write-Host "4️⃣ 다양한 챌린지 타입 테스트" -ForegroundColor Yellow

$challengeTypes = @("text_distorted", "math_question", "simple_click")

foreach ($type in $challengeTypes) {
    Write-Host "   타입: $type" -ForegroundColor Cyan
    try {
        $body = @{
            type = $type
            difficulty = "medium"
        } | ConvertTo-Json
        
        $ch = Invoke-RestMethod -Uri "$API_GATEWAY/api/challenge/create" -Method Post -ContentType "application/json" -Body $body
        Write-Host "      ✅ 생성 성공 - 질문: $($ch.question)" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ 실패" -ForegroundColor Red
    }
}
Write-Host ""

# 5. Rate Limiting 테스트
Write-Host "5️⃣ Rate Limiting 테스트 (여러 요청 발송)" -ForegroundColor Yellow
Write-Host "   10개의 요청을 연속으로 발송..." -ForegroundColor Gray

$successCount = 0
$failCount = 0

for ($i = 1; $i -le 10; $i++) {
    try {
        $null = Invoke-RestMethod -Uri "$API_GATEWAY/health" -Method Get -TimeoutSec 2
        $successCount++
        Write-Host "." -NoNewline -ForegroundColor Green
    } catch {
        $failCount++
        Write-Host "X" -NoNewline -ForegroundColor Red
    }
    Start-Sleep -Milliseconds 100
}

Write-Host ""
Write-Host "   성공: $successCount / 실패: $failCount" -ForegroundColor Cyan
Write-Host ""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "테스트 완료!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 팁: Frontend에서 실제 VQA를 테스트해보세요!" -ForegroundColor Yellow
Write-Host "   http://localhost:3000/vqa-demo.html" -ForegroundColor Gray
Write-Host ""
