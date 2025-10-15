@echo off
echo ====================================
echo Starting WebSocket Main Server (端口 8000)
echo ====================================
echo.

echo Current Directory: %CD%
echo.

REM 加载环境变量
if exist .env (
    echo 加载环境变量...
) else (
    echo 警告: .env 文件不存在！
    echo 请复制 env.example 到 .env 并配置
    pause
    exit /b 1
)

echo Starting Main Server...
C:\Users\Bryan\AppData\Roaming\Python\Python313\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload

pause

