@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  PASSO 1 - Instalando o Citizen Assist AI
echo  Isso pode levar de 3 a 8 minutos. Aguarde.
echo ============================================
echo.
echo Instalacao iniciada > instalacao_log.txt
py -0p >> instalacao_log.txt 2>&1
set PY=
for %%V in (3.13 3.12 3.14) do (
  if not defined PY (
    py -%%V --version >nul 2>&1 && set PY=py -%%V
  )
)
if not defined PY (
  echo [0/4] Baixando o Python 3.13 (uma vez so^)...
  winget install -e --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements >> instalacao_log.txt 2>&1
  py -3.13 --version >nul 2>&1 && set PY=py -3.13
)
if not defined PY (
  echo [ERRO] Nao consegui preparar o Python. Avise o Claude.
  echo SEM PYTHON COMPATIVEL >> instalacao_log.txt
  pause
  exit /b
)
echo Usando: %PY% >> instalacao_log.txt
%PY% --version >> instalacao_log.txt 2>&1
echo [1/4] Criando ambiente...
if exist .venv rmdir /s /q .venv
%PY% -m venv .venv >> instalacao_log.txt 2>&1
call .venv\Scripts\activate.bat
echo [2/4] Atualizando o pip...
python -m pip install --upgrade pip >> instalacao_log.txt 2>&1
echo [3/4] Instalando bibliotecas (a parte mais demorada)...
pip install -r requirements.txt >> instalacao_log.txt 2>&1
echo [4/4] Testando...
python tests\test_guardrails.py >> instalacao_log.txt 2>&1
python -c "from citizen_assist.llm import modo_offline; print('CHAVE GROQ OK' if not modo_offline() else 'CHAVE GROQ NAO ENCONTRADA')" >> instalacao_log.txt 2>&1
echo FIM >> instalacao_log.txt
echo.
echo ============================================
echo  Terminou! Pode fechar esta janela e avisar o Claude.
echo ============================================
pause
