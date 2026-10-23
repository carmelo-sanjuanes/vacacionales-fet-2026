@echo off
echo ========================================================
echo Ejecutando actualizacion de cartas y firmas - FET Neiva
echo Fecha y hora: %date% %time%
echo ========================================================
cd /d "C:\Users\Carmelo\.gemini\antigravity\scratch\fet-cursos-vacacionales-electrica"
python "C:\Users\Carmelo\.gemini\antigravity\scratch\fet-cursos-vacacionales-electrica\actualizar_cartas.py" >> "C:\Users\Carmelo\.gemini\antigravity\scratch\fet-cursos-vacacionales-electrica\registro_actualizacion.log" 2>&1
echo Proceso finalizado con codigo %errorlevel%
