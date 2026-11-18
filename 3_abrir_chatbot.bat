@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Abrindo o chatbot no navegador... Para fechar, feche esta janela.
start "" http://127.0.0.1:5000
python app\web.py
pause
