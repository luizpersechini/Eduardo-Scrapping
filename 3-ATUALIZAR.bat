@echo off
setlocal enabledelayedexpansion
title Cota - Atualizar

REM  A atualizacao sobrescreve este proprio arquivo. Um .bat que muda
REM  enquanto roda faz o cmd executar lixo (ele le o arquivo por posicao
REM  de byte, nao guarda uma copia). Entao: na primeira passada, copiamos
REM  este arquivo para a pasta temporaria e rodamos a copia de la,
REM  passando a pasta do programa como argumento.
if /i "%~1"=="RUN_FROM_TEMP" goto :run
copy /y "%~f0" "%TEMP%\cota_atualizar_run.bat" >nul
"%TEMP%\cota_atualizar_run.bat" RUN_FROM_TEMP "%~dp0"
exit /b

:run
cd /d "%~2"

echo ============================================================
echo    COTA - Atualizar para a versao mais recente
echo ============================================================
echo.
echo  Vou baixar a versao mais nova do programa da internet.
echo  Seus dados, seus resultados e sua senha NAO serao mexidos.
echo  Isso leva menos de um minuto. Aguarde.
echo.

REM  Se o Cota estiver aberto, o Python continua com os arquivos antigos
REM  na memoria e a atualizacao fica "pela metade" ate reiniciar.
REM  Melhor bloquear aqui e pedir para fechar primeiro.
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"
if errorlevel 1 (
    echo [ATENCAO] O programa Cota esta ABERTO agora.
    echo.
    echo  Feche a janela preta do Cota primeiro e depois
    echo  clique no 3-ATUALIZAR de novo.
    echo.
    pause
    exit /b 1
)

REM  Branch publicada que o Eduardo usa. Se um dia mudar, e so
REM  trocar esta linha (e a pasta em SRC, mais abaixo).
set "BRANCH=main"
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

REM  O GitHub nomeia a pasta extraida como Eduardo-Scrapping-<branch>.
set "SRC=%TMP%\Eduardo-Scrapping-main"
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

REM  Limpar codigo compilado antigo para o Python nao reaproveitar nada.
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "tests\__pycache__" rmdir /s /q "tests\__pycache__"

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
