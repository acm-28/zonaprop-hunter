# Script de PowerShell para crear o actualizar la tarea programada en Windows
# Ejecuta Zonaprop Hunter automáticamente 2 veces al día: 08:30 AM y 17:00 PM (5:00 PM)
# Incluye sincronización automática a GitHub para que Vercel despliegue la webapp.

$TaskName = "ZonapropHunterDaily"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatPath = Join-Path $ScriptDir "run_daily.bat"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Configurando automatización local (08:30 AM y 17:00 PM)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ruta del script: $BatPath"

$Action = New-ScheduledTaskAction -Execute $BatPath -Argument "--scheduled" -WorkingDirectory $ScriptDir

# 2 disparadores diarios: 08:30 AM y 17:00 PM
$TriggerMorning = New-ScheduledTaskTrigger -Daily -At 8:30AM
$TriggerAfternoon = New-ScheduledTaskTrigger -Daily -At 5:00PM
$Triggers = @($TriggerMorning, $TriggerAfternoon)

# Ajustes: Ejecutar con batería, y si el equipo estaba suspendido/apagado, ejecutar apenas se encienda
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Registrar la tarea en Windows Task Scheduler
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Description "Ejecución diaria programada a las 08:30 AM y 17:00 PM de Zonaprop Hunter con sincronización automática a GitHub y Vercel" -Force
    Write-Host ""
    Write-Host "[OK] Tarea programada registrada exitosamente en Windows!" -ForegroundColor Green
    Write-Host "Horarios configurados:" -ForegroundColor Yellow
    Write-Host "  1. 08:30 AM (Mañana)" -ForegroundColor Green
    Write-Host "  2. 17:00 PM (Tarde)" -ForegroundColor Green
    Write-Host ""
    Write-Host "En cada corrida el script rastreará Zonaprop y hará push a GitHub automáticamente para actualizar Vercel." -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "[Error] No se pudo crear la tarea programada: $_" -ForegroundColor Red
    Write-Host "Sugerencia: Ejecuta PowerShell como Administrador para registrar la tarea en Windows." -ForegroundColor Yellow
}
