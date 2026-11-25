# Script PowerShell para registrar el exportador de cuota en el Programador de Tareas
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ScriptDir "exporter.py"

$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$ScriptPath`"" -WorkingDirectory "$ScriptDir"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "AntigravityQuotaCloudSync" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Sincroniza el consumo de Antigravity con GitHub cada hora" -Force
Write-Host "Tarea programada 'AntigravityQuotaCloudSync' registrada con exito."
