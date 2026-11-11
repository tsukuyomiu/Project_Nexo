# ==============================================================================
# PROJETO NEXO - INICIADOR RÁPIDO DO PROJETO COMPLETO (Back-End + Front-End)
# ==============================================================================
Write-Host ">>> Iniciando o Projeto Nexo (Back-End + Front-End)..." -ForegroundColor Cyan

# 1. Garante inicialização do banco de dados e seeds
Write-Host ">>> Verificando e inicializando banco de dados SQL..." -ForegroundColor Yellow
python -m app.db.scripts.init_db

# 2. Inicia o Back-End em uma nova janela
Write-Host ">>> Abrindo servidor Back-End (Porta 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python -m uvicorn app.main:app --reload --port 8000"

# 3. Inicia o Front-End em outra janela
Write-Host ">>> Abrindo servidor Front-End (Vite)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Tudo rodando!" -ForegroundColor Green
Write-Host "Front-End: http://localhost:5173" -ForegroundColor White
Write-Host "Back-End Swagger UI: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Ver Logs no Terminal: cd backend; python -m app.db.scripts.inspect_logs" -ForegroundColor White
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
