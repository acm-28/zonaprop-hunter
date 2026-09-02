@echo off
chcp 65001 > nul
title Zonaprop Hunter - Oportunidades CABA
echo =========================================================
echo    ZONAPROP HUNTER CABA - OPORTUNIDADES INMOBILIARIAS
echo =========================================================
echo.
cd /d "%~dp0"
python main.py
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul
