# Script PowerShell para registrar el exportador de cuota en el Programador de Tareas (cada 30 minutos, en silencio)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ScriptDir "exporter.py"

$PythonCmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command python.exe -ErrorAction Stop
}
$PythonExe = $PythonCmd.Source

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory "$ScriptDir"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "AntigravityQuotaCloudSync" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Sincroniza el consumo de Antigravity con GitHub cada 30 minutos" -Force
Write-Host "Tarea programada 'AntigravityQuotaCloudSync' registrada con exito (cada 30 minutos usando $PythonExe)."
