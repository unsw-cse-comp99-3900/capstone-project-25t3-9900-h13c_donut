@echo off
echo ====================================
echo Starting BE-5 ASR Service (Port 8001)
echo ====================================
echo.

set BACKEND_DIR=%~dp0
cd /d "%BACKEND_DIR%asr"

echo Current directory: %CD%
echo.

if exist "%BACKEND_DIR%.env" (
    echo Loading environment variables...
    for /f "usebackq tokens=1,2 delims==" %%a in ("%BACKEND_DIR%.env") do (
        set %%a=%%b
    )
)

echo Starting ASR service...
C:\Users\Bryan\AppData\Roaming\Python\Python313\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8001 --reload

pause

