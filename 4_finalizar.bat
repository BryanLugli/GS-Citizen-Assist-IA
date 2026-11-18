@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  Gerando o notebook final (1 a 2 minutos)...
echo  Os resultados ja salvos sao reaproveitados.
echo ============================================
call .venv\Scripts\activate.bat
jupyter nbconvert --to notebook --execute --inplace notebooks\citizen_assist_ai.ipynb --ExecutePreprocessor.timeout=3600 > avaliacao_log.txt 2>&1
echo FIM >> avaliacao_log.txt
echo.
echo  Terminou! Pode fechar esta janela e avisar o Claude.
pause
