@echo off
setlocal enabledelayedexpansion

echo Instalando o Sistema de Controle como um Serviço do Windows...

REM Definir o diretório de instalação
set INSTALL_DIR=%ProgramFiles%\SistemaRequisicao
set NSSM_DIR=%INSTALL_DIR%\nssm

REM Verificar se já está instalado e remover se necessário
sc query SistemaRequisicao > nul
if %ERRORLEVEL% EQU 0 (
    echo Removendo instalação anterior...
    sc stop SistemaRequisicao
    sc delete SistemaRequisicao
    timeout /t 5
)

REM Criar o diretório de instalação
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%NSSM_DIR%" mkdir "%NSSM_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

REM Copiar os arquivos
echo Copiando arquivos...
xcopy /E /I /Y "SistemaRequisicao" "%INSTALL_DIR%\SistemaRequisicao"
xcopy /E /I /Y "nssm-2.24" "%NSSM_DIR%"
copy "IniciarServico.bat" "%INSTALL_DIR%"
copy "PararServico.bat" "%INSTALL_DIR%"
copy "sistema.db" "%INSTALL_DIR%"
copy "style.css" "%INSTALL_DIR%"

REM Instalar como serviço usando NSSM
echo Instalando o serviço...
"%NSSM_DIR%\win64\nssm.exe" install SistemaRequisicao "%INSTALL_DIR%\SistemaRequisicao\SistemaRequisicao.exe"
"%NSSM_DIR%\win64\nssm.exe" set SistemaRequisicao DisplayName "Sistema de Controle de Requisição"
"%NSSM_DIR%\win64\nssm.exe" set SistemaRequisicao Description "Sistema para controle de requisições com leitura de código de barras"
"%NSSM_DIR%\win64\nssm.exe" set SistemaRequisicao AppDirectory "%INSTALL_DIR%"
"%NSSM_DIR%\win64\nssm.exe" set SistemaRequisicao Start SERVICE_AUTO_START
"%NSSM_DIR%\win64\nssm.exe" set SistemaRequisicao AppStdout "%INSTALL_DIR%\logs\servico.log"
"%NSSM_DIR%\win64\nssm.exe" set SistemaRequisicao AppStderr "%INSTALL_DIR%\logs\erro.log"

REM Iniciar o serviço
echo Iniciando o serviço...
sc start SistemaRequisicao

echo.
echo Instalação concluída com sucesso!
echo O Sistema de Controle está agora disponível como um serviço do Windows.
echo Acesse http://localhost:8501 em seu navegador para usar o sistema.
echo.
echo Pressione qualquer tecla para finalizar...
pause > nul