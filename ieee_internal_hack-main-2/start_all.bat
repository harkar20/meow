@echo off
echo Starting Meowmeow Microservices...

echo Starting ML Engine (Port 8001)...
start "ML Engine" cmd /k "python -m uvicorn ml.ml_api:app --port 8001 --reload"

echo Starting Backend API (Port 8000)...
start "Backend API" cmd /k "python -m uvicorn backend.main:app --port 8000 --reload"

echo Starting Frontend Dev Server (Port 5173)...
cd frontend
start "Frontend UI" cmd /c "npm run dev"

echo All services are starting up in separate windows!
pause
