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
REM  1) Procurar o Python (3.11 ou mais novo).
REM     Tentamos, nesta ordem:
REM       a) o lancador  py -3
REM       b) o comando   python  (se estiver no PATH)
REM       c) procurar o python.exe nas pastas padrao de instalacao
REM          (assim, mesmo com o PATH "desatualizado" logo apos
REM           instalar o Python, ainda encontramos ele)
REM ---------------------------------------------------------------
set "PYCMD="

REM a) lancador py
py -3 --version >nul 2>nul && set "PYCMD=py -3"

REM b) python no PATH
if not defined PYCMD (
    python --version >nul 2>nul && set "PYCMD=python"
)

REM c) procurar nas pastas padrao (usuario e todos os usuarios).
REM     Capturamos as variaveis de ambiente em nomes SEM parenteses
REM     (ProgramFiles(x86) quebraria o bloco "for (...)").
set "LAD=%LocalAppData%"
set "PF=%ProgramFiles%"
set "PF86=%ProgramFiles(x86)%"
if not defined PYCMD (
    for %%D in (Python314 Python313 Python312 Python311) do (
        if not defined PYCMD if exist "!LAD!\Programs\Python\%%D\python.exe" (
            set "PATH=!LAD!\Programs\Python\%%D;!LAD!\Programs\Python\%%D\Scripts;!PATH!"
            set "PYCMD=python"
        )
        if not defined PYCMD if exist "!PF!\%%D\python.exe" (
            set "PATH=!PF!\%%D;!PF!\%%D\Scripts;!PATH!"
            set "PYCMD=python"
        )
        if not defined PYCMD if exist "!PF86!\%%D\python.exe" (
            set "PATH=!PF86!\%%D;!PF86!\%%D\Scripts;!PATH!"
            set "PYCMD=python"
        )
    )
)

if not defined PYCMD (
    echo [ATENCAO] O Python nao foi encontrado.
    echo.
    echo  Se voce ACABOU de instalar o Python:
    echo     REINICIE o computador e clique no 1-INSTALAR de novo.
    echo     (O Windows so "enxerga" o Python depois de reiniciar.)
    echo.
    echo  Se voce AINDA NAO instalou o Python:
    echo     Vou abrir a pagina de download.
    echo     Na PRIMEIRA tela da instalacao, MARQUE a caixinha:
    echo         [ X ]  Add python.exe to PATH
    echo     Depois clique em "Install Now", REINICIE o computador
    echo     e clique no 1-INSTALAR de novo.
    echo.
    pause
    start "" https://www.python.org/downloads/
    exit /b 1
)
echo  - Python encontrado (!PYCMD!).

REM  Aviso se a versao for antiga (menor que 3.11), mas nao bloqueia.
%PYCMD% -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ATENCAO] Sua versao do Python parece antiga.
    echo  Recomendado: Python 3.11 ou mais novo. Vou tentar mesmo assim.
)

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
