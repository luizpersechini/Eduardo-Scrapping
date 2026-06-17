@echo off
setlocal
title Cota - Raspador ANBIMA
cd /d "%~dp0"

REM Se ainda nao foi instalado, avisar e parar.
if not exist "venv\Scripts\activate.bat" (
    echo ============================================================
    echo    O programa ainda nao foi instalado.
    echo.
    echo    Clique primeiro no arquivo  1-INSTALAR  e aguarde terminar.
    echo    Depois volte e clique em  2-ABRIR-COTA .
    echo ============================================================
    echo.
    pause
    exit /b 1
)

REM Modo local: sem tela de login (uso pessoal neste computador).
set COTA_NO_LOGIN=1

call venv\Scripts\activate.bat

echo ============================================================
echo    COTA - abrindo no seu navegador...
echo.
echo    DEIXE esta janela preta ABERTA enquanto usa o programa.
echo    Para FECHAR o programa: feche esta janela preta.
echo ============================================================
echo.

REM Abre o navegador sozinho depois de alguns segundos (sem aspas aninhadas).
start "" /min cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:8501"

REM Inicia o programa (fica rodando nesta janela).
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true --browser.gatherUsageStats=false

echo.
echo  O programa foi encerrado.
pause
endlocal
