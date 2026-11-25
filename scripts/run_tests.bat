@echo off
title Digital Currency Platform - Automated Test Suite
cd /d "%~dp0.."
echo =====================================================================
echo  Running Django Integrity Checks and Automated Test Suite
echo =====================================================================
python manage.py check
python manage.py test
pause
