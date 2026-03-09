# MSA VQA 시스템 실행 스크립트 (PowerShell)

Write-Host "================================" -ForegroundColor Green
Write-Host "MSA VQA 시스템 시작" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Docker 및 Docker Compose 확인
Write-Host "✅ Docker 확인 중..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "Docker Desktop을 설치해주세요: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}
Write-Host "   $dockerVersion" -ForegroundColor Cyan

Write-Host "✅ Docker Compose 확인 중..." -ForegroundColor Yellow
$composeVersion = docker-compose --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Compose가 설치되어 있지 않습니다." -ForegroundColor Red
    exit 1
}
Write-Host "   $composeVersion" -ForegroundColor Cyan
Write-Host ""

# 기존 컨테이너 확인 및 중지
Write-Host "🔍 기존 컨테이너 확인 중..." -ForegroundColor Yellow
$existingContainers = docker ps -a --filter "name=vqa-" --format "{{.Names}}" 2>$null
if ($existingContainers) {
    Write-Host "   기존 VQA 컨테이너 발견: " -ForegroundColor Cyan
    $existingContainers | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
    
    $response = Read-Host "기존 컨테이너를 중지하고 삭제하시겠습니까? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "   컨테이너 중지 및 삭제 중..." -ForegroundColor Yellow
        docker-compose down 2>$null
        Write-Host "   ✅ 완료" -ForegroundColor Green
    }
}
Write-Host ""

# 서비스 빌드 및 시작
Write-Host "🔨 서비스 빌드 및 시작 중..." -ForegroundColor Yellow
Write-Host "   이 작업은 처음 실행 시 몇 분이 걸릴 수 있습니다." -ForegroundColor Gray
docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 서비스 시작 실패" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 서비스 시작 대기
Write-Host "⏳ 서비스 시작 대기 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 서비스 상태 확인
Write-Host "📊 서비스 상태 확인 중..." -ForegroundColor Yellow
Write-Host ""

$services = @(
    @{Name="Redis"; Url="http://localhost:6379"},
    @{Name="API Gateway"; Url="http://localhost:8080/health"},
    @{Name="Challenge Service"; Url="http://localhost:3001/health"},
    @{Name="Verification Service"; Url="http://localhost:3002/health"}
)

foreach ($service in $services) {
    Write-Host "   $($service.Name): " -NoNewline -ForegroundColor Cyan
    
    if ($service.Name -eq "Redis") {
        $redisRunning = docker ps --filter "name=vqa-redis" --filter "status=running" --format "{{.Names}}"
        if ($redisRunning) {
            Write-Host "🟢 실행 중" -ForegroundColor Green
        } else {
            Write-Host "🔴 중지됨" -ForegroundColor Red
        }
    } else {
        try {
            $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing 2>$null
            if ($response.StatusCode -eq 200) {
                Write-Host "🟢 실행 중" -ForegroundColor Green
            } else {
                Write-Host "🟡 응답 없음" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "🔴 연결 실패" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "🎉 MSA VQA 시스템 시작 완료!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 접속 정보:" -ForegroundColor Cyan
Write-Host "   Frontend:     http://localhost:3000/vqa-demo.html" -ForegroundColor White
Write-Host "   API Gateway:  http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "💡 Frontend를 실행하려면:" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   python -m http.server 3000" -ForegroundColor Gray
Write-Host "   또는" -ForegroundColor Gray
Write-Host "   npx http-server -p 3000" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 로그 확인:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 서비스 중지:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host ""
