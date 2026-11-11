@echo off
title Projeto Nexo - Launcher
echo ========================================================
echo Iniciando Projeto Nexo (Back-End + Front-End)
echo ========================================================

echo 1. Inicializando Banco SQL e Seeds...
cd /d "%~dp0backend"
python -m app.db.scripts.init_db

echo 2. Subindo Back-End em nova janela (Porta 8000)...
start "Nexo Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --reload --port 8000"

echo 3. Subindo Front-End em nova janela...
start "Nexo Frontend (React/Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo ========================================================
echo Pronto! 
echo Frontend: http://localhost:5173
echo Backend API Docs: http://localhost:8000/docs
echo ========================================================
pause
