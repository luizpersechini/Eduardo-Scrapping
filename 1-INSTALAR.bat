@echo off
setlocal enabledelayedexpansion
title Cota - Instalacao
cd /d "%~dp0"

echo ============================================================
echo    COTA - Raspador de Fundos ANBIMA
echo    INSTALACAO  (faca isto apenas UMA vez)
echo ============================================================
echo.
echo  Vou preparar o programa no seu computador.
echo  Isso pode demorar alguns minutos. Aguarde.
echo.

REM ---------------------------------------------------------------
REM  1) Procurar o Python (precisa ser 3.11 ou mais novo)
REM ---------------------------------------------------------------
set "PYCMD="
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD (
    python -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul && set "PYCMD=python"
)

if not defined PYCMD (
    echo [ATENCAO] O Python nao foi encontrado no seu computador.
    echo.
    echo  Vou abrir a pagina de download do Python.
    echo.
    echo  IMPORTANTE - na primeira tela da instalacao do Python,
    echo  MARQUE a caixinha que diz:
    echo.
    echo        [ X ]  Add python.exe to PATH
    echo.
    echo  (ela fica embaixo, antes do botao "Install Now")
    echo.
    echo  Depois que terminar de instalar o Python, FECHE esta janela
    echo  e clique novamente no arquivo  1-INSTALAR .
    echo.
    pause
    start "" https://www.python.org/downloads/
    exit /b 1
)
echo  - Python encontrado.

REM ---------------------------------------------------------------
REM  2) Procurar o Google Chrome
REM ---------------------------------------------------------------
set "CHROME=0"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=1"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=1"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=1"

if "%CHROME%"=="0" (
    echo [ATENCAO] O Google Chrome nao foi encontrado.
    echo  O programa precisa do Google Chrome instalado.
    echo  Vou abrir a pagina de download. Instale o Chrome,
    echo  depois clique novamente no arquivo  1-INSTALAR .
    echo.
    pause
    start "" https://www.google.com/chrome/
    exit /b 1
)
echo  - Google Chrome encontrado.
echo.

REM ---------------------------------------------------------------
REM  3) Preparar o ambiente e baixar o que o programa precisa
REM ---------------------------------------------------------------
echo  Preparando o programa (aguarde, pode demorar)...
echo.
%PYCMD% -m venv venv
if errorlevel 1 (
    echo [ERRO] Nao foi possivel criar o ambiente.
    echo  Tente rodar de novo. Se continuar, me avise.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao baixar os componentes.
    echo  Verifique se a internet esta funcionando e rode de novo.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    PRONTO! Instalacao concluida com sucesso.
echo.
echo    Para usar o programa, clique no arquivo:
echo        2-ABRIR-COTA
echo ============================================================
echo.
pause
endlocal
