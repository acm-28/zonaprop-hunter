@echo off
chcp 65001 > nul
title Zonaprop Hunter - Oportunidades CABA
echo =========================================================
echo    ZONAPROP HUNTER CABA - OPORTUNIDADES INMOBILIARIAS
echo =========================================================
echo.

cd /d %~dp0

echo [1/3] Ejecutando rastreo diario en Zonaprop (Publicados hoy)...
python scraper_main.py --no-browser
set SCRAPER_EXIT=%ERRORLEVEL%

if not "%SCRAPER_EXIT%"=="0" (
    echo [ERROR] Ocurrio un fallo durante la ejecucion del scraper.
    goto END
)

echo.
echo [2/3] Verificando novedades para GitHub y Vercel...
git add index.html output/ history.json check_status.bat scraper_main.py

git diff --staged --quiet
if errorlevel 1 (
    echo [3/3] Nuevas oportunidades detectadas. Sincronizando con GitHub...
    git commit -m "chore(data): auto-update daily opportunities & analytics [skip ci]"
    git push origin main
    echo.
    echo =========================================================
    echo [OK] Cambios subidos a GitHub exitosamente!
    echo Vercel esta compilando la version actualizada del sitio.
    echo =========================================================
) else (
    echo [3/3] No hay datos nuevos respecto a la ultima corrida.
)

:END
echo.
if "%1"=="--scheduled" goto EXIT
if "%1"=="--no-pause" goto EXIT

echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul

:EXIT
exit /b %SCRAPER_EXIT%
