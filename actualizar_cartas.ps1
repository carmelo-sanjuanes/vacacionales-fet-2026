# PowerShell script para la actualización automática de cartas y firmas FET
$ErrorActionPreference = "Continue"
$projectDir = "C:\Users\Carmelo\.gemini\antigravity\scratch\fet-cursos-vacacionales-electrica"
$logFile = "$projectDir\registro_actualizacion.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $logFile -Value "`n========================================================"
Add-Content -Path $logFile -Value "Ejecución PowerShell: $timestamp"
Add-Content -Path $logFile -Value "========================================================"

Set-Location -Path $projectDir
python "$projectDir\actualizar_cartas.py" *>> $logFile
