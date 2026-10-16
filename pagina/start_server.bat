@echo off
title Anonymous Tactical HUD Server
echo ======================================================================
echo    Iniciando Servidor Web Tactico Anonymous en 0.0.0.0:8080...
echo    Transmitiendo por senal Wi-Fi y Localhost
echo ======================================================================
cd /d "%~dp0"
python server.py --port 8080
pause
