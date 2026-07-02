@echo off
setlocal enabledelayedexpansion
title Cota - Atualizar
cd /d "%~dp0"

echo ============================================================
echo    COTA - Atualizar para a versao mais recente
echo ============================================================
echo.
echo  Vou baixar a versao mais nova do programa da internet.
echo  Seus dados, seus resultados e sua senha NAO serao mexidos.
echo  Isso leva menos de um minuto. Aguarde.
echo.

REM  Branch publicada que o Eduardo usa. Se um dia mudar, e so
REM  trocar esta linha (e a pasta em SRC, mais abaixo).
set "BRANCH=feature/cvm-quota-ingest"
set "ZIPURL=https://github.com/luizpersechini/Eduardo-Scrapping/archive/refs/heads/%BRANCH%.zip"
set "TMP=%TEMP%\cota_update"
set "ZIP=%TEMP%\cota_update.zip"

REM  Limpar sobras de uma tentativa anterior.
if exist "%TMP%" rmdir /s /q "%TMP%"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>nul

echo  1/3  Baixando...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri '%ZIPURL%' -OutFile '%ZIP%' -UseBasicParsing } catch { exit 1 }"
if errorlevel 1 (
    echo.
    echo [ERRO] Nao consegui baixar a atualizacao.
    echo  Verifique se a internet esta funcionando e tente de novo.
    echo.
    pause
    exit /b 1
)

echo  2/3  Preparando...
powershell -NoProfile -Command "try { Expand-Archive -Path '%ZIP%' -DestinationPath '%TMP%' -Force } catch { exit 1 }"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao abrir a atualizacao. Tente de novo.
    echo.
    pause
    exit /b 1
)

REM  O GitHub troca a barra "/" da branch por "-" no nome da pasta.
set "SRC=%TMP%\Eduardo-Scrapping-feature-cvm-quota-ingest"
if not exist "%SRC%" (
    echo.
    echo [ERRO] O conteudo da atualizacao nao veio como esperado.
    echo  Me avise que eu ajusto.
    echo.
    pause
    exit /b 1
)

echo  3/3  Aplicando...
REM  Copia o codigo novo por cima do antigo. /IS forca a copia mesmo
REM  quando o arquivo parece igual. O zip do GitHub NAO contem venv,
REM  instance (seu banco), results (suas planilhas) nem o arquivo de
REM  senha, entao nada seu e tocado; ainda assim excluimos por seguranca.
robocopy "%SRC%" "%CD%" /E /IS /XF EDUARDO_CREDENTIALS.txt /XD venv instance results __pycache__ >nul
if errorlevel 8 (
    echo.
    echo [ERRO] Falha ao copiar os arquivos novos.
    echo  Feche o programa Cota se estiver aberto e tente de novo.
    echo.
    pause
    exit /b 1
)

REM  Garantir que qualquer componente novo seja instalado (rapido se
REM  nao mudou nada). So roda se o ambiente ja existir.
if exist "venv\Scripts\python.exe" (
    call venv\Scripts\activate.bat
    python -m pip install -r requirements.txt >nul 2>nul
)

REM  Limpar temporarios.
if exist "%TMP%" rmdir /s /q "%TMP%"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>nul

echo.
echo ============================================================
echo    PRONTO! O programa esta atualizado.
echo.
echo    Para usar, clique no arquivo:
echo        2-ABRIR-COTA
echo ============================================================
echo.
pause
endlocal
