@echo off
title Digital Currency Analytics Platform - Django 5.x
cd /d "%~dp0.."
echo =====================================================================
echo  Unified Digital Currency Management & Analytics Platform
echo =====================================================================
echo [INFO] Python: Python 3.11
echo [INFO] Django Engine: 5.2.18
echo [INFO] Scikit-Learn: 1.9.1
echo [INFO] Starting Django Web Server on http://127.0.0.1:8000 ...
echo =====================================================================
py -3.11 manage.py runserver 127.0.0.1:8000
if %errorlevel% neq 0 (
    "C:\Users\pramo\AppData\Local\Programs\Python\Python311\python.exe" manage.py runserver 127.0.0.1:8000
)
pause
