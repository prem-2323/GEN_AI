@echo off
TITLE DocLink - Stable Diffusion Forge (Image Generation API)
COLOR 0E

echo ====================================================================
echo         STABLE DIFFUSION FORGE - IMAGE GENERATION API
echo ====================================================================
echo.

REM Forge installation directory (override: pass as first arg or set FORGE_DIR)
set "FORGE_DIR=C:\Users\premk\Music\gen ai\stable-diffusion-webui-forge"
if not "%~1"=="" set "FORGE_DIR=%~1"

if not exist "%FORGE_DIR%\webui.bat" (
    echo [ERROR] Forge not found at: %FORGE_DIR%
    echo Update FORGE_DIR in start_forge.bat or pass the path:
    echo   start_forge.bat "D:\path\to\stable-diffusion-webui-forge"
    pause
    exit /b 1
)

echo [OK] Forge directory: %FORGE_DIR%
echo [..] Starting WebUI in API mode on http://127.0.0.1:7860 ...
echo      (first launch downloads models and can take several minutes)
echo.

cd /d "%FORGE_DIR%"

REM API mode so Backend/image can reach /sdapi/v1/txt2img
REM VRAM offload keeps the 4GB GPU within budget alongside other services
set COMMANDLINE_ARGS=--api --listen --port 7860 --always-offload-from-vram --cuda-malloc --opt-sdp-attention --skip-python-version-check

call webui.bat
pause
