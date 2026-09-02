# Script de PowerShell para crear la tarea programada diaria en Windows
# Ejecuta Zonaprop Hunter automáticamente todos los días a las 23:59 PM (Cierre del día)

$TaskName = "ZonapropHunterDaily"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatPath = Join-Path $ScriptDir "run_daily.bat"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Programando ejecución diaria nocturna para Zonaprop Hunter" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ruta del script: $BatPath"

$Action = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 11:59PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Registrar la tarea
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Ejecución diaria nocturna a las 23:59 del scraper de oportunidades Zonaprop CABA" -Force
    Write-Host ""
    Write-Host "[OK] Tarea programada registrada exitosamente!" -ForegroundColor Green
    Write-Host "El script se ejecutará todos los días a las 23:59 PM (Hora Argentina)." -ForegroundColor Green
    Write-Host "Para modificar el horario, abre 'Programador de tareas' (Task Scheduler) en Windows y busca '$TaskName'."
} catch {
    Write-Host ""
    Write-Host "[Error] No se pudo crear la tarea programada: $_" -ForegroundColor Red
    Write-Host "Sugerencia: Ejecuta PowerShell como Administrador para registrar la tarea en Windows." -ForegroundColor Yellow
}
