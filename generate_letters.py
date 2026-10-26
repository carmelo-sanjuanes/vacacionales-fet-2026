import json
import os
from collections import defaultdict

# 1. Cargar datos de estudiantes desde la base de datos de Google Sheets
DATA_PATH = r"C:\Users\Carmelo\.gemini\antigravity\brain\f091cbd4-7664-4cb8-954b-17cd6f8044a5\.system_generated\steps\401\content.md"

students_data = []
with open(DATA_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("[{"):
            students_data = json.loads(line)
            break

print(f"Total estudiantes cargados: {len(students_data)}")

# 2. Asignaturas oficiales
SUBJECTS = {
    'ELE0300218': ('ECUACIONES DIFERENCIALES', 7),
    'ELE0300735': ('SEÑALES Y CONTROL', 7),
    'ELE0300736': ('ELECTRÓNICA II TP', 7),
    'ELE0300730': ('SISTEMAS DE DISTRIBUCIÓN DE ENERGÍA', 7),
    'ELE0300731': ('CIRCUITOS ELÉCTRICOS III', 7),
    'ELE0300732': ('AUTOMATIZACIÓN', 7),
    'ELE0300733': ('MÁQUINAS ELÉCTRICAS II TP', 7),
    'ELE0300734': ('OPERACIONES Y MANTENIMIENTO I', 7),
    'ELE0300219': ('MATEMÁTICAS DISCRETAS', 8),
    'ELE0300220': ('SIMULACIÓN TP', 8),
    'ELE0300223': ('ESTADÍSTICA Y PROBABILIDAD', 8),
    'ELE0300737': ('MECÁNICA DE FLUIDOS', 8),
    'ELE0300738': ('SISTEMAS DE TRANSMISIÓN DE ENERGÍA', 8),
    'ELE0300739': ('SUBESTACIONES ELÉCTRICAS', 8),
    'ELE0300208': ('PLANEACIÓN ENERGÉTICA', 8),
    'ELE0300217': ('OPTATIVA PROFESIONAL I', 8),
    'ELE0300741': ('FORMULACIÓN Y EVALUACIÓN DE PROYECTOS', 8),
    'ELE0300221': ('MÉTODOS NUMÉRICOS', 9),
    'ELE0300742': ('ANÁLISIS DE SISTEMAS DE POTENCIA', 9),
    'ELE0300743': ('OPERACIONES Y MANTENIMIENTO II', 9),
    'ELE0300744': ('GENERACIÓN HIDRAULICA', 9),
    'ELE0300745': ('GENERACIÓN TÉRMICA', 9),
    'ELE0300747': ('OPTATIVA PROFESIONAL II', 9),
    'ELE0300837': ('ÉTICA PROFESIONAL', 9),
    'ELE0300116': ('ELECTIVA III - MARKETING PARA EMPRESARIOS', 9)
}

counts = defaultdict(list)
for s in students_data:
    for code in s.get("subjects", []):
        counts[code].append(s)

qualifying = [(code, studs) for code, studs in counts.items() if len(studs) >= 10]
qualifying.sort(key=lambda x: len(x[1]), reverse=True)

print(f"\nMaterias que cumplen con 10 o más estudiantes: {len(qualifying)}")
for code, studs in qualifying:
    name, sem = SUBJECTS[code]
    print(f"- {code}: {name} (Semestre {sem}) -> {len(studs)} estudiantes")
