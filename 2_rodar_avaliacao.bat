@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  PASSO 2 - Rodando a avaliacao (v1, v2 e juiz)
echo  Leva uns 15 a 25 minutos. NAO feche esta janela.
echo ============================================
call .venv\Scripts\activate.bat
jupyter nbconvert --to notebook --execute --inplace notebooks\citizen_assist_ai.ipynb --ExecutePreprocessor.timeout=3600 > avaliacao_log.txt 2>&1
echo FIM >> avaliacao_log.txt
echo.
echo ============================================
echo  Terminou! Pode fechar esta janela e avisar o Claude.
echo ============================================
pause
