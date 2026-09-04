@echo off
chcp 65001 > nul
title Zonaprop Hunter - Estado de la Tarea Automatica
echo ================================================================
echo   DIAGNOSTICO DE TAREA PROGRAMADA: ZonapropHunterDaily
echo ================================================================
echo.

powershell -NoProfile -Command ^
    "$t = Get-ScheduledTask -TaskName 'ZonapropHunterDaily' -ErrorAction SilentlyContinue; " ^
    "if (-not $t) { Write-Host '[-] La tarea ZonapropHunterDaily NO esta registrada.' -ForegroundColor Red; exit 1 }; " ^
    "$info = Get-ScheduledTaskInfo -TaskName 'ZonapropHunterDaily'; " ^
    "Write-Host '[+] Estado de la Tarea:      ' -NoNewline; Write-Host $t.State -ForegroundColor Cyan; " ^
    "Write-Host '[+] Ultima Ejecucion:        ' -NoNewline; Write-Host $info.LastRunTime -ForegroundColor Yellow; " ^
    "Write-Host '[+] Codigo de Resultado:     ' -NoNewline; " ^
    "if ($info.LastTaskResult -eq 0) { Write-Host '0 (EXITO / OK)' -ForegroundColor Green } else { Write-Host $info.LastTaskResult -ForegroundColor Red }; " ^
    "Write-Host '[+] Proxima Ejecucion:       ' -NoNewline; Write-Host $info.NextRunTime -ForegroundColor Yellow; " ^
    "Write-Host ''; " ^
    "if (Test-Path 'logs\task_last_run.log') { " ^
    "    Write-Host '--- ULTIMAS LINEAS DEL REGISTRO (logs\task_last_run.log) ---' -ForegroundColor DarkGray; " ^
    "    Get-Content 'logs\task_last_run.log' -Tail 15; " ^
    "} else { " ^
    "    Write-Host 'Aun no hay archivo logs\task_last_run.log' -ForegroundColor DarkGray; " ^
    "}"

echo.
echo ================================================================
if "%1"=="--no-pause" goto EXIT
echo Presiona cualquier tecla para salir...
pause > nul

:EXIT
