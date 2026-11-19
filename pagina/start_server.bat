@echo off
title WEP-SER-IP | Anonymous
echo ======================================================================
echo    Iniciando WEP-SER-IP en 0.0.0.0:8080...
echo    Transmitiendo por senal Wi-Fi y Localhost
echo ======================================================================
cd /d "%~dp0"
python server.py --port 8080
pause
