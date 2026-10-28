@echo off
title Digital Currency Platform - Automated Test Suite
cd /d "%~dp0.."
echo =====================================================================
echo  Running Django Automated Test Suite & Multi-Relational ML Tests
echo =====================================================================
py -3.11 manage.py test users
pause
