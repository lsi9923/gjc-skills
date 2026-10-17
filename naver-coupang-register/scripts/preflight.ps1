# preflight.ps1 - Aside 브라우저 사전 점검 및 네이버·윙 로그인 창 활성화
$ErrorActionPreference = "Stop"

$asideExe = "C:\Program Files\Aside\Application\Aside.exe"
if (-not (Test-Path $asideExe)) {
    Write-Error "Aside 실행 파일을 찾을 수 없습니다: $asideExe"
    exit 1
}

$naverUrl = "https://sell.smartstore.naver.com/#/products/create"
$wingUrl = "https://wing.coupang.com/tenants/seller-web/vendor-inventory/formV2"

# 1. Aside 메인 창 존재 여부 확인
$asideWithWindow = Get-Process Aside -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle }

if (-not $asideWithWindow) {
    Write-Host "[1/3] Aside 메인 창이 감지되지 않아 새로 실행합니다..." -ForegroundColor Yellow
    Start-Process -FilePath $asideExe
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/3] Aside 메인 창이 이미 활성화되어 있습니다 (PID: $($asideWithWindow.Id))." -ForegroundColor Green
}

# 2. 네이버 스마트스토어 및 쿠팡 윙 URL을 사용자에게 보이는 창에 열기
Write-Host "[2/3] 네이버·쿠팡 윙 탭을 가시 창에서 엽니다..." -ForegroundColor Cyan
Start-Process -FilePath $asideExe -ArgumentList $naverUrl, $wingUrl
Start-Sleep -Seconds 2

# 3. Get-Process Aside 창 제목 출력 및 검증
Write-Host "[3/3] Aside 프로세스 창 제목 검증:" -ForegroundColor Cyan
$processes = Get-Process Aside -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle }

if ($processes) {
    $processes | Select-Object Id, ProcessName, MainWindowTitle | Format-Table -AutoSize
    Write-Host "✅ 사전 점검 완료: Aside 브라우저 가시 창이 정상 확인되었습니다." -ForegroundColor Green
} else {
    Write-Warning "⚠️ Aside 프로세스는 실행 중이나 MainWindowTitle을 아직 획득하지 못했습니다. 잠시 후 다시 확인하세요."
}
