@echo off
rem Запуск сайта и API: http://127.0.0.1:8124/
rem Демо-оплата включается переменной XSISET_DEMO=1 (только локально).
cd /d "%~dp0server"
python app.py
