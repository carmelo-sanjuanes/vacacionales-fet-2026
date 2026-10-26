#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rutina de actualización periódica de cartas de solicitud de cursos vacacionales FET.
Descarga los últimos inscritos y firmas de Google Sheets, preserva firmas anteriores
en una base histórica local, regenera todos los Word (.docx) y el HTML imprimible
para asignaturas con >= 10 estudiantes, y publica en GitHub Pages automáticamente.
"""

import os
import json
import urllib.request
import subprocess
import datetime
from collections import defaultdict

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_URL = "https://script.google.com/macros/s/AKfycbx7zKE41qQi23E7l7yUQNvAT5n80FBnyWD7zV7_fTNzh26eg8kujtZkOeFsf_ulhjgF/exec"
CACHE_FILE = os.path.join(BASE_DIR, "firmas_historicas.json")
BACKUP_DATA_FILE = os.path.join(BASE_DIR, "estudiantes_registrados.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "cartas_solicitud")
HTML_OUTPUT = os.path.join(BASE_DIR, "cartas_solicitud_imprimibles.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)

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

def load_historical_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Aviso leyendo cache historico: {e}")
    return {}

def save_historical_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Aviso guardando cache historico: {e}")

def fetch_students_data():
    req = urllib.request.Request(BACKEND_URL, headers={'User-Agent': 'Mozilla/5.0 (FET Updater)'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            with open(BACKUP_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
    except Exception as e:
        print(f"Error descargando datos en vivo ({e}). Intentando usar copia local...")
        if os.path.exists(BACKUP_DATA_FILE):
            with open(BACKUP_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_letter_to_doc(doc, code, name, semester, students, is_last=False):
    now_str = datetime.datetime.now().strftime("%d de %B de %Y").replace("October", "octubre").replace("November", "noviembre").replace("December", "diciembre")
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_date = p_header.add_run(f"Neiva, Huila, {now_str}\n")
    run_date.font.size = Pt(10)
    run_date.font.color.rgb = RGBColor(100, 100, 100)

    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(14)
    run_dest = p_dest.add_run(
        "Señor:\n"
        "ARQUITECTO MIGUEL ÁNGEL CANCHALA DELGADO\n"
        "Director del Programa de Ingeniería Eléctrica\n"
        "Fundación Escuela Tecnológica de Neiva \"Jesús Oviedo Pérez\" - FET\n"
        "Ciudad."
    )
    run_dest.bold = True
    run_dest.font.size = Pt(11)
    run_dest.font.color.rgb = RGBColor(4, 61, 26)

    p_subj = doc.add_paragraph()
    p_subj.paragraph_format.space_after = Pt(12)
    run_subj_label = p_subj.add_run("ASUNTO: ")
    run_subj_label.bold = True
    run_subj_label.font.size = Pt(10.5)
    run_subj_txt = p_subj.add_run(f"Solicitud formal de apertura y programación de Curso Vacacional para la asignatura {name} (Código: {code}, Semestre {semester}°).")
    run_subj_txt.bold = True
    run_subj_txt.font.size = Pt(10.5)

    p_body1 = doc.add_paragraph()
    p_body1.paragraph_format.space_after = Pt(8)
    p_body1.paragraph_format.line_spacing = 1.15
    p_body1.add_run("Respetado Arquitecto Canchala:")

    p_body2 = doc.add_paragraph()
    p_body2.paragraph_format.space_after = Pt(10)
    p_body2.paragraph_format.line_spacing = 1.15
    p_body2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body2.add_run(
        f"Por medio de la presente, nosotros, los estudiantes abajo firmantes pertenecientes al programa de "
        f"Ingeniería Eléctrica de la Fundación Escuela Tecnológica de Neiva \"Jesús Oviedo Pérez\" (FET), nos dirigimos a usted "
        f"de manera cordial y respetuosa con el propósito de solicitar formalmente la apertura y oferta académica del "
        f"CURSO VACACIONAL para la asignatura correspondiente al plan de estudios:"
    )

    p_info = doc.add_paragraph()
    p_info.paragraph_format.left_indent = Inches(0.3)
    p_info.paragraph_format.space_after = Pt(10)
    p_info.paragraph_format.line_spacing = 1.15
    r_info = p_info.add_run(
        f"• Asignatura: {name}\n"
        f"• Código Académico: {code}\n"
        f"• Semestre del Plan de Estudios: Semestre {semester}°\n"
        f"• Total de Estudiantes Solicitantes Preinscritos: {len(students)} estudiantes"
    )
    r_info.bold = True
    r_info.font.color.rgb = RGBColor(12, 74, 35)

    p_body3 = doc.add_paragraph()
    p_body3.paragraph_format.space_after = Pt(12)
    p_body3.paragraph_format.line_spacing = 1.15
    p_body3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body3.add_run(
        f"Manifestamos nuestro compromiso formal de matrícula y cumplimiento con los requerimientos académicos "
        f"y arancelarios correspondientes al curso vacacional. Dado que contamos con un grupo sólido de {len(students)} "
        f"estudiantes interesados (superando el cupo mínimo requerido de 10 estudiantes), solicitamos "
        f"su valiosa gestión ante la Coordinación Académica y la Dirección de Programa para su respectiva aprobación, "
        f"asignación docente y programación de horarios."
    )

    p_body4 = doc.add_paragraph()
    p_body4.paragraph_format.space_after = Pt(8)
    r_list = p_body4.add_run("Relación de estudiantes solicitantes y firmas de respaldo:")
    r_list.bold = True

    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(0.4), Inches(2.3), Inches(1.2), Inches(1.1), Inches(1.8)]
    for i, width in enumerate(col_widths):
        table.columns[i].width = width

    hdr_cells = table.rows[0].cells
    headers = ["N°", "Nombre del Estudiante", "Cód. Estudiantil", "Teléfono", "Firma del Estudiante"]
    for i, text in enumerate(headers):
        hdr_cells[i].width = col_widths[i]
        set_cell_background(hdr_cells[i], "043D1A")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=100, right=100)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)

    for idx, st in enumerate(students, 1):
        row_cells = table.add_row().cells
        for i, width in enumerate(col_widths):
            row_cells[i].width = width
            set_cell_margins(row_cells[i], top=100, bottom=100, left=80, right=80)

        bg_color = "F9FAF8" if idx % 2 == 0 else "FFFFFF"
        for cell in row_cells:
            set_cell_background(cell, bg_color)

        p0 = row_cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r0 = p0.add_run(str(idx))
        r0.font.size = Pt(8.5)

        p1 = row_cells[1].paragraphs[0]
        r1 = p1.add_run(st.get("name", "").strip())
        r1.bold = True
        r1.font.size = Pt(8.5)

        p2 = row_cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(str(st.get("code", "")).strip())
        r2.font.size = Pt(8.5)

        p3 = row_cells[3].paragraphs[0]
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r3 = p3.add_run(str(st.get("phone", "")).strip())
        r3.font.size = Pt(8.5)

        p4 = row_cells[4].paragraphs[0]
        p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sig_data = st.get("signature", "")
        inserted_img = False
        if sig_data and "base64," in sig_data:
            try:
                import base64
                import io
                header, base64_str = sig_data.split("base64,", 1)
                img_bytes = base64.b64decode(base64_str)
                img_stream = io.BytesIO(img_bytes)
                p4.add_run().add_picture(img_stream, height=Inches(0.32))
                inserted_img = True
            except Exception:
                inserted_img = False

        if not inserted_img:
            r4 = p4.add_run("____________________")
            r4.font.size = Pt(7.5)
            r4.font.color.rgb = RGBColor(160, 160, 160)

    p_close = doc.add_paragraph()
    p_close.paragraph_format.space_before = Pt(14)
    p_close.paragraph_format.space_after = Pt(20)
    p_close.paragraph_format.line_spacing = 1.15
    p_close.add_run(
        "Agradecemos su atención, valiosa colaboración y pronta respuesta para la apertura de esta asignatura.\n\n"
        "Atentamente,\n\n"
        "ESTUDIANTES SOLICITANTES DE INGENIERÍA ELÉCTRICA\n"
        "Fundación Escuela Tecnológica de Neiva \"Jesús Oviedo Pérez\" - FET"
    )

    if not is_last:
        doc.add_page_break()

def main():
    print("=" * 60)
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando actualización de cartas y firmas...")
    print("=" * 60)

    historical_cache = load_historical_cache()
    print(f"Firmas históricas previas en caché: {len(historical_cache)}")

    raw_data = fetch_students_data()
    if not raw_data:
        print("ERROR: No se pudieron obtener los datos de estudiantes.")
        return

    print(f"Total de registros descargados desde Google Sheets: {len(raw_data)}")

    # Normalizar estudiantes y enriquecer con firmas históricas
    processed_students = []
    signatures_found_in_cloud = 0
    signatures_restored_from_cache = 0

    for item in raw_data:
        code = str(item.get("code", "")).strip().upper()
        if not code:
            continue

        name = str(item.get("name", "")).strip()
        phone = str(item.get("phone", "")).strip()
        sig = str(item.get("signature", "")).strip()

        # Parsear materias
        subjs = item.get("subjects", [])
        if isinstance(subjs, str):
            import ast
            try:
                subjs = ast.literal_eval(subjs)
            except Exception:
                subjs = [x.strip() for x in subjs.split(",") if x.strip()]

        if not isinstance(subjs, list):
            subjs = []

        # Sincronizar firma con caché histórico
        if sig and "base64," in sig:
            signatures_found_in_cloud += 1
            historical_cache[code] = {
                "name": name,
                "phone": phone,
                "signature": sig,
                "updated_at": datetime.datetime.now().isoformat()
            }
        elif code in historical_cache and historical_cache[code].get("signature"):
            sig = historical_cache[code]["signature"]
            signatures_restored_from_cache += 1

        processed_students.append({
            "id": str(item.get("id", "")),
            "name": name,
            "code": code,
            "phone": phone,
            "subjects": subjs,
            "signature": sig,
            "date": str(item.get("date", ""))
        })

    save_historical_cache(historical_cache)
    total_with_signature = sum(1 for s in processed_students if s.get("signature"))
    print(f"Firmas en la nube: {signatures_found_in_cloud} | Restauradas de caché: {signatures_restored_from_cache} | Total con firma: {total_with_signature}")

    # Agrupar por materia
    counts = defaultdict(list)
    for s in processed_students:
        for code in s["subjects"]:
            if code in SUBJECTS:
                counts[code].append(s)

    # Filtrar asignaturas con >= 10 estudiantes
    qualifying = [(code, studs) for code, studs in counts.items() if len(studs) >= 10]
    qualifying.sort(key=lambda x: len(x[1]), reverse=True)

    print(f"Asignaturas que cumplen el cupo (>= 10 estudiantes): {len(qualifying)}")

    # 1. Generar Documento Consolidado Word
    doc_master = Document()
    for section in doc_master.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    for idx, (code, studs) in enumerate(qualifying):
        name, semester = SUBJECTS[code]
        is_last = (idx == len(qualifying) - 1)
        add_letter_to_doc(doc_master, code, name, semester, studs, is_last)

    master_path = os.path.join(OUTPUT_DIR, "Cartas_Solicitud_Vacacionales_Consolidado.docx")
    doc_master.save(master_path)
    print(f"Documento consolidado en Word generado: {master_path}")

    # 2. Generar Documentos Individuales Word
    for code, studs in qualifying:
        name, semester = SUBJECTS[code]
        doc_single = Document()
        for section in doc_single.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
        add_letter_to_doc(doc_single, code, name, semester, studs, is_last=True)

        clean_name = name.replace(" ", "_").replace("/", "_").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        filename = f"Carta_Solicitud_{code}_{clean_name}.docx"
        doc_single.save(os.path.join(OUTPUT_DIR, filename))

    # 3. Generar HTML Imprimible Interactivo
    select_options = f'<option value="all">📑 Ver Todas las Cartas ({len(qualifying)} Cursos)</option>\n'
    for c_code, c_studs in qualifying:
        c_name, c_sem = SUBJECTS[c_code]
        c_sigs = sum(1 for st in c_studs if st.get("signature"))
        select_options += f'                <option value="{c_code}">{c_code} - {c_name} ({len(c_studs)} est. - {c_sigs} firmas)</option>\n'

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cartas de Solicitud de Cursos Vacacionales - Ingeniería Eléctrica FET</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #043d1a;
            --primary-dark: #02230f;
            --gold: #ffd700;
            --gold-dark: #d4af37;
            --text-dark: #1e293b;
            --border-color: #cbd5e1;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Roboto', sans-serif;
            color: var(--text-dark);
            background-color: #e2e8f0;
            line-height: 1.5;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .toolbar {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: linear-gradient(135deg, #043d1a, #0c4a23);
            color: white;
            padding: 0.85rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            flex-wrap: wrap;
            gap: 0.75rem;
        }}
        .toolbar-title {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}
        .toolbar-title span {{ color: var(--gold); }}
        .toolbar-actions {{
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex-wrap: wrap;
        }}
        .btn-action {{
            background-color: var(--gold);
            color: #043d1a;
            font-weight: 700;
            font-size: 0.9rem;
            padding: 0.55rem 1.2rem;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
            text-decoration: none;
        }}
        .btn-action:hover {{
            background-color: #ffe44d;
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background-color: rgba(255,255,255,0.15);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        .btn-secondary:hover {{
            background-color: rgba(255,255,255,0.25);
            color: white;
        }}
        .sheets-container {{
            max-width: 860px;
            margin: 1.5rem auto;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}
        .page-sheet {{
            background-color: white;
            width: 100%;
            min-height: 1100px;
            padding: 2.8rem 3rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-radius: 4px;
            position: relative;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 0.8rem;
            margin-bottom: 1.5rem;
        }}
        .header-logo {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }}
        .header-logo i {{
            font-size: 2.2rem;
            color: var(--primary);
        }}
        .header-text h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            color: var(--primary);
            font-weight: 800;
            line-height: 1.1;
        }}
        .header-text p {{
            font-size: 0.82rem;
            color: #64748b;
            font-weight: 500;
        }}
        .header-meta {{
            text-align: right;
            font-size: 0.85rem;
            color: #475569;
        }}
        .letter-recipient {{
            margin-bottom: 1.3rem;
            line-height: 1.4;
            color: var(--primary);
        }}
        .letter-recipient .title {{
            font-weight: 700;
            font-size: 1.02rem;
        }}
        .letter-recipient .cargo {{
            font-size: 0.93rem;
            font-weight: 600;
        }}
        .letter-recipient .institution {{
            font-size: 0.9rem;
            color: #334155;
        }}
        .letter-subject {{
            background-color: #f8fafc;
            border-left: 4px solid var(--primary);
            padding: 0.6rem 0.9rem;
            margin-bottom: 1.2rem;
            font-size: 0.92rem;
            line-height: 1.4;
        }}
        .letter-subject strong {{ color: var(--primary); }}
        .letter-body {{
            font-size: 0.92rem;
            text-align: justify;
            margin-bottom: 1.2rem;
            color: #334155;
        }}
        .letter-body p {{ margin-bottom: 0.75rem; }}
        .course-summary-box {{
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin: 0.8rem 0;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
            font-size: 0.88rem;
        }}
        .course-summary-box .item strong {{ color: var(--primary); }}
        .students-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.2rem 0;
            font-size: 0.84rem;
        }}
        .students-table th {{
            background-color: var(--primary);
            color: white;
            font-weight: 600;
            text-align: left;
            padding: 0.5rem 0.6rem;
            border: 1px solid var(--primary);
        }}
        .students-table th.center, .students-table td.center {{ text-align: center; }}
        .students-table td {{
            padding: 0.45rem 0.6rem;
            border: 1px solid #cbd5e1;
            color: #1e293b;
        }}
        .students-table tr:nth-child(even) {{ background-color: #f8fafc; }}
        .signature-cell {{
            width: 130px;
            text-align: center;
            color: #94a3b8;
            font-size: 0.75rem;
        }}
        .letter-footer {{
            margin-top: 1.5rem;
            font-size: 0.9rem;
            color: #334155;
        }}
        .sign-placeholder {{
            margin-top: 2rem;
            display: inline-block;
            border-top: 1px solid #475569;
            padding-top: 0.3rem;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .counter-badge {{
            background-color: #043d1a;
            color: var(--gold);
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.8rem;
            display: inline-block;
        }}
        @media print {{
            body {{ background-color: white; }}
            .toolbar {{ display: none; }}
            .sheets-container {{ max-width: 100%; margin: 0; gap: 0; }}
            .page-sheet {{
                box-shadow: none;
                padding: 1.8cm 1.8cm;
                min-height: auto;
                page-break-after: always;
                break-after: page;
            }}
        }}
    </style>
</head>
<body>
    <div class="toolbar">
        <div class="toolbar-title">
            <i class="fa-solid fa-file-contract"></i>
            Cartas Oficiales de Solicitud de Cursos Vacacionales <span>| FET Neiva</span>
        </div>
        <div class="toolbar-actions">
            <select id="filter-select" onchange="filterLetters(this.value)" style="padding: 0.5rem 0.8rem; border-radius: 6px; font-weight: 600; font-size: 0.88rem; border: 1px solid rgba(255,255,255,0.4); background: white; color: #043d1a; cursor: pointer;">
{select_options}            </select>
            <button onclick="window.print()" class="btn-action">
                <i class="fa-solid fa-print"></i> Imprimir Selección (PDF)
            </button>
            <a href="cartas_solicitud/Cartas_Solicitud_Vacacionales_Consolidado.docx" class="btn-action btn-secondary" download>
                <i class="fa-solid fa-file-word"></i> Descargar Todo en Word
            </a>
        </div>
    </div>

    <div class="sheets-container">
"""

    for idx, (code, studs) in enumerate(qualifying, 1):
        name, semester = SUBJECTS[code]
        sigs_count = sum(1 for st in studs if st.get("signature"))

        html_content += f"""
        <!-- Hoja de Carta: {code} -->
        <article class="page-sheet" data-code="{code}">
            <header class="header-top">
                <div class="header-logo">
                    <i class="fa-solid fa-graduation-cap"></i>
                    <div class="header-text">
                        <h2>FUNDACIÓN ESCUELA TECNOLÓGICA DE NEIVA</h2>
                        <p>"Jesús Oviedo Pérez" - FET | Programa de Ingeniería Eléctrica</p>
                    </div>
                </div>
                <div class="header-meta">
                    <p><strong>Neiva, Huila</strong></p>
                    <p>Octubre de 2026</p>
                    <span class="counter-badge">{len(studs)} Estudiantes ({sigs_count} firmados)</span>
                </div>
            </header>

            <section class="letter-recipient">
                <p>Señor:</p>
                <p class="title">ARQUITECTO MIGUEL ÁNGEL CANCHALA DELGADO</p>
                <p class="cargo">Director del Programa de Ingeniería Eléctrica</p>
                <p class="institution">Fundación Escuela Tecnológica de Neiva "Jesús Oviedo Pérez" - FET</p>
                <p>Ciudad.</p>
            </section>

            <div class="letter-subject">
                <strong>ASUNTO:</strong> Solicitud formal de apertura y programación de Curso Vacacional para la asignatura <strong>{name}</strong> (Código: <strong>{code}</strong>, Semestre <strong>{semester}°</strong>).
            </div>

            <div class="letter-body">
                <p>Respetado Arquitecto Canchala:</p>
                <p>
                    Por medio de la presente, nosotros, los estudiantes abajo firmantes pertenecientes al programa de 
                    <strong>Ingeniería Eléctrica</strong> de la Fundación Escuela Tecnológica de Neiva "Jesús Oviedo Pérez" (FET), nos dirigimos a usted 
                    de manera cordial y respetuosa con el propósito de solicitar formalmente la apertura y oferta académica del 
                    <strong>CURSO VACACIONAL</strong> para la siguiente asignatura de nuestro plan de estudios:
                </p>

                <div class="course-summary-box">
                    <div class="item"><strong>Asignatura:</strong> {name}</div>
                    <div class="item"><strong>Código Académico:</strong> {code}</div>
                    <div class="item"><strong>Semestre Académico:</strong> Semestre {semester}°</div>
                    <div class="item"><strong>Estudiantes Preinscritos:</strong> {len(studs)} solicitantes ({sigs_count} firmas registradas)</div>
                </div>

                <p>
                    Esta petición responde a nuestra necesidad académica de avanzar y nivelar nuestro plan curricular, garantizando la continuidad en 
                    nuestra formación profesional. Manifestamos nuestro firme compromiso de formalizar la matrícula correspondiente y asumir las responsabilidades 
                    académicas y administrativas que determine la institución. Teniendo en cuenta que cumplimos a cabalidad con el requisito de demanda 
                    con un grupo consolidado de <strong>{len(studs)} estudiantes</strong>, solicitamos comedidamente su gestión ante la Coordinación Académica 
                    para su aprobación, designación docente y respectiva programación de fechas y horarios.
                </p>

                <p style="margin-bottom: 0.3rem;"><strong>Relación de estudiantes solicitantes y firmas de respaldo:</strong></p>
            </div>

            <table class="students-table">
                <thead>
                    <tr>
                        <th class="center" style="width: 38px;">N°</th>
                        <th>Nombre Completo del Estudiante</th>
                        <th class="center" style="width: 120px;">Cód. Estudiante</th>
                        <th class="center" style="width: 110px;">Teléfono</th>
                        <th class="center signature-cell">Firma</th>
                    </tr>
                </thead>
                <tbody>
        """

        for s_idx, st in enumerate(studs, 1):
            st_name = st.get("name", "").strip()
            st_code = str(st.get("code", "")).strip()
            st_phone = str(st.get("phone", "")).strip()
            sig_data = st.get("signature", "")

            if sig_data and "base64," in sig_data:
                sig_html = f'<img src="{sig_data}" alt="Firma {st_name}" style="max-height: 38px; max-width: 125px; object-fit: contain; display: block; margin: 0 auto;">'
            else:
                sig_html = f'<span class="sig-placeholder" data-code="{st_code}">___________________</span>'

            html_content += f"""
                    <tr data-student-code="{st_code}">
                        <td class="center"><strong>{s_idx}</strong></td>
                        <td>{st_name}</td>
                        <td class="center">{st_code}</td>
                        <td class="center">{st_phone}</td>
                        <td class="signature-cell" style="text-align: center; cursor: pointer;" onclick="openLetterSignModal('{st_code}', '{st_name}')" title="Clic para firmar">{sig_html}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>

            <footer class="letter-footer">
                <p>Agradecemos de antemano su amable atención, receptividad y pronta gestión favorable a esta solicitud.</p>
                <div class="sign-placeholder">
                    REPRESENTACIÓN ESTUDIANTIL - INGENIERÍA ELÉCTRICA<br>
                    Fundación Escuela Tecnológica de Neiva - FET
                </div>
            </footer>
        </article>
        """

    html_content += """
    </div>

    <!-- Modal Interactivo de Firma en Cartas Imprimibles -->
    <div id="letter-sig-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.65); z-index:9999; align-items:center; justify-content:center; backdrop-filter:blur(4px);">
        <div style="background:white; border-radius:12px; width:92%; max-width:460px; padding:1.5rem; box-shadow:0 20px 40px rgba(0,0,0,0.3); font-family:'Roboto',sans-serif;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e2e8f0; padding-bottom:0.75rem; margin-bottom:1rem;">
                <h3 style="font-family:'Outfit',sans-serif; color:#043d1a; font-size:1.1rem; display:flex; align-items:center; gap:0.5rem; margin:0;">
                    <i class="fa-solid fa-file-signature" style="color:#d4af37;"></i> Firmar Carta de Solicitud
                </h3>
                <button onclick="closeLetterSignModal()" style="background:none; border:none; font-size:1.4rem; cursor:pointer; color:#64748b; line-height:1;">&times;</button>
            </div>
            <p style="font-size:0.85rem; color:#475569; margin-bottom:0.8rem; line-height:1.4;">
                Estudiante: <strong id="letter-modal-student-name" style="color:#043d1a;"></strong><br>
                Código: <strong id="letter-modal-student-code" style="color:#043d1a;"></strong>
            </p>
            <div style="position:relative; width:100%; height:140px; background:#f8fafc; border:2px dashed #cbd5e1; border-radius:8px; overflow:hidden; touch-action:none; cursor:crosshair;">
                <canvas id="letter-sig-canvas" style="width:100%; height:100%; display:block; touch-action:none;"></canvas>
                <div style="position:absolute; bottom:25px; left:8%; width:84%; height:1px; background:rgba(148,163,184,0.4); pointer-events:none;"></div>
                <div id="letter-sig-placeholder" style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:0.8rem; color:#94a3b8; pointer-events:none; font-weight:600;">
                    ✍️ Dibuja tu firma con el dedo o ratón
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem;">
                <button id="btn-clear-letter-sig" onclick="clearLetterSigCanvas()" style="background:#fee2e2; color:#dc2626; border:1px solid #fca5a5; padding:0.4rem 0.8rem; border-radius:6px; font-weight:600; font-size:0.8rem; cursor:pointer;">
                    <i class="fa-solid fa-rotate-left"></i> Borrar
                </button>
                <div style="display:flex; gap:0.5rem;">
                    <button id="btn-cancel-letter-sig" onclick="closeLetterSignModal()" style="background:#f1f5f9; color:#475569; border:1px solid #cbd5e1; padding:0.4rem 0.8rem; border-radius:6px; font-weight:600; font-size:0.8rem; cursor:pointer;">Cancelar</button>
                    <button id="btn-save-letter-sig" onclick="saveLetterSignature()" style="background:#043d1a; color:#ffd700; border:none; padding:0.45rem 1rem; border-radius:6px; font-weight:700; font-size:0.85rem; cursor:pointer; transition: all 0.2s ease;">
                        <i class="fa-solid fa-check"></i> Guardar Firma
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function filterLetters(code) {
            const sheets = document.querySelectorAll('.page-sheet');
            sheets.forEach(sheet => {
                if (code === 'all' || sheet.getAttribute('data-code') === code) {
                    sheet.style.display = 'block';
                } else {
                    sheet.style.display = 'none';
                }
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            syncSignatures();
            initLetterCanvas();
        });

        const BACKEND_URL = 'https://script.google.com/macros/s/AKfycbx7zKE41qQi23E7l7yUQNvAT5n80FBnyWD7zV7_fTNzh26eg8kujtZkOeFsf_ulhjgF/exec';
        const LOCAL_STORAGE_KEY = 'fet_vacacionales_registrations';

        // Sincronización robusta con Google Sheets
        async function syncStudentToCloud(student) {
            if (!BACKEND_URL || !student) return true;
            const payload = JSON.stringify({ action: 'add', student: student });
            const canUseKeepalive = payload.length < 60000;

            let lastErr = null;
            for (let attempt = 1; attempt <= 2; attempt++) {
                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 15000);
                    const fetchOpts = {
                        method: 'POST',
                        body: payload,
                        signal: controller.signal
                    };
                    if (canUseKeepalive) fetchOpts.keepalive = true;

                    await fetch(BACKEND_URL, fetchOpts);
                    clearTimeout(timeoutId);
                    return true;
                } catch(e) {
                    lastErr = e;
                    console.warn(`[Letter Sync] Intento ${attempt} fallido:`, e);
                    if (attempt < 2) await new Promise(r => setTimeout(r, 800));
                }
            }
            throw lastErr || new Error("Error de conexión al subir firma");
        }

        function syncSignatures() {
            try {
                const local = localStorage.getItem(LOCAL_STORAGE_KEY);
                if (local) {
                    applySignaturesToDom(JSON.parse(local));
                }
            } catch(e){}

            if (BACKEND_URL) {
                fetch(BACKEND_URL).then(r => r.json()).then(data => {
                    applySignaturesToDom(data);
                    checkAndSyncPendingSignatures(data);
                }).catch(err => console.log('Offline sync:', err));
            }
        }

        // Auto-sincronizar firmas locales no reflejadas en la nube
        async function checkAndSyncPendingSignatures(cloudData) {
            if (!Array.isArray(cloudData) || !BACKEND_URL) return;
            try {
                const localRaw = localStorage.getItem(LOCAL_STORAGE_KEY);
                if (!localRaw) return;
                const localList = JSON.parse(localRaw);

                const pending = localList.filter(loc => {
                    if (!loc.signature || String(loc.signature).trim() === '') return false;
                    const rem = cloudData.find(c => c.code === loc.code);
                    return !rem || !rem.signature || String(rem.signature).trim() === '';
                });

                if (pending.length > 0) {
                    console.log(`[Auto-Sync] ${pending.length} firmas locales pendientes por subir a la nube...`);
                    for (const st of pending) {
                        try {
                            await syncStudentToCloud(st);
                            console.log(`[Auto-Sync] Firma de ${st.name} sincronizada.`);
                        } catch(e) {}
                    }
                }
            } catch(err) {}
        }

        function applySignaturesToDom(students) {
            if (!Array.isArray(students)) return;
            students.forEach(st => {
                if (st.signature) {
                    document.querySelectorAll(`tr[data-student-code="${st.code}"] .signature-cell`).forEach(cell => {
                        cell.innerHTML = `<img src="${st.signature}" alt="Firma ${st.name}" style="max-height: 38px; max-width: 125px; object-fit: contain; display: block; margin: 0 auto;">`;
                    });
                }
            });
        }

        let letterCanvas, letterCtx, letterPlaceholder;
        let isDrawing = false, hasDrawn = false, lastX = 0, lastY = 0;
        let currentSignCode = '', currentSignName = '';

        function initLetterCanvas() {
            letterCanvas = document.getElementById('letter-sig-canvas');
            letterPlaceholder = document.getElementById('letter-sig-placeholder');
            if (!letterCanvas) return;
            letterCtx = letterCanvas.getContext('2d');

            function getCoords(e) {
                const rect = letterCanvas.getBoundingClientRect();
                let clientX = e.clientX, clientY = e.clientY;
                if (e.touches && e.touches.length > 0) {
                    clientX = e.touches[0].clientX;
                    clientY = e.touches[0].clientY;
                }
                return { x: clientX - rect.left, y: clientY - rect.top };
            }

            function start(e) {
                isDrawing = true;
                const c = getCoords(e);
                lastX = c.x; lastY = c.y;
                if (letterPlaceholder) letterPlaceholder.style.opacity = '0';
            }

            function draw(e) {
                if (!isDrawing) return;
                if (e.cancelable && e.type.startsWith('touch')) e.preventDefault();
                const c = getCoords(e);
                letterCtx.beginPath();
                letterCtx.moveTo(lastX, lastY);
                letterCtx.lineTo(c.x, c.y);
                letterCtx.stroke();
                lastX = c.x; lastY = c.y;
                hasDrawn = true;
            }

            function stop() { isDrawing = false; }

            letterCanvas.addEventListener('mousedown', start);
            letterCanvas.addEventListener('mousemove', draw);
            window.addEventListener('mouseup', stop);

            letterCanvas.addEventListener('touchstart', (e) => {
                if (e.cancelable) e.preventDefault();
                start(e);
            }, { passive: false });
            letterCanvas.addEventListener('touchmove', draw, { passive: false });
            letterCanvas.addEventListener('touchend', stop);
            letterCanvas.addEventListener('touchcancel', stop);
        }

        function resizeLetterCanvas() {
            if (!letterCanvas) return;
            const rect = letterCanvas.getBoundingClientRect();
            if (rect.width === 0) return;
            const dpr = window.devicePixelRatio || 1;
            letterCanvas.width = rect.width * dpr;
            letterCanvas.height = rect.height * dpr;
            letterCtx.scale(dpr, dpr);
            letterCtx.strokeStyle = '#042a49';
            letterCtx.lineWidth = 2.4;
            letterCtx.lineCap = 'round';
            letterCtx.lineJoin = 'round';
            hasDrawn = false;
            if (letterPlaceholder) letterPlaceholder.style.opacity = '1';
        }

        window.openLetterSignModal = function(code, name) {
            currentSignCode = code;
            currentSignName = name;
            document.getElementById('letter-modal-student-name').textContent = name;
            document.getElementById('letter-modal-student-code').textContent = code;
            const modal = document.getElementById('letter-sig-modal');
            modal.style.display = 'flex';
            setTimeout(resizeLetterCanvas, 100);
        };

        window.closeLetterSignModal = function() {
            const modal = document.getElementById('letter-sig-modal');
            if (modal) modal.style.display = 'none';
        };

        window.clearLetterSigCanvas = function() {
            if (!letterCanvas) return;
            const rect = letterCanvas.getBoundingClientRect();
            letterCtx.clearRect(0, 0, rect.width, rect.height);
            hasDrawn = false;
            if (letterPlaceholder) letterPlaceholder.style.opacity = '1';
        };

        async function saveLetterSignature() {
            if (!hasDrawn) {
                alert('Por favor dibuja tu firma en el recuadro antes de guardar.');
                return;
            }

            // Normalizar a 450x180 para asegurar peso mínimo (<15KB) y soporte keepalive en celulares
            const normW = 450, normH = 180;
            const normC = document.createElement('canvas');
            normC.width = normW; normC.height = normH;
            const normX = normC.getContext('2d');
            normX.drawImage(letterCanvas, 0, 0, normW, normH);
            const sigData = normC.toDataURL('image/png');

            // 1. Reflejar en DOM inmediatamente
            document.querySelectorAll(`tr[data-student-code="${currentSignCode}"] .signature-cell`).forEach(cell => {
                cell.innerHTML = `<img src="${sigData}" alt="Firma ${currentSignName}" style="max-height: 38px; max-width: 125px; object-fit: contain; display: block; margin: 0 auto;">`;
            });

            // 2. Guardar en localStorage
            let foundStudent = null;
            try {
                let regs = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '[]');
                foundStudent = regs.find(r => r.code === currentSignCode);
                if (foundStudent) {
                    foundStudent.signature = sigData;
                    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(regs));
                }
            } catch(e){}

            // 3. Bloquear modal e informar sincronización
            const saveBtn = document.getElementById('btn-save-letter-sig');
            const cancelBtn = document.getElementById('btn-cancel-letter-sig');
            const clearBtn = document.getElementById('btn-clear-letter-sig');
            const origSaveText = saveBtn ? saveBtn.innerHTML : '';

            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Subiendo a la nube...';
                saveBtn.style.opacity = '0.9';
            }
            if (cancelBtn) cancelBtn.disabled = true;
            if (clearBtn) clearBtn.disabled = true;

            try {
                if (foundStudent) {
                    await syncStudentToCloud(foundStudent);
                }

                if (saveBtn) {
                    saveBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> ¡Sincronizado en la nube!';
                    saveBtn.style.background = '#10b981';
                    saveBtn.style.color = '#ffffff';
                }

                setTimeout(() => {
                    closeLetterSignModal();
                    if (saveBtn) {
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = origSaveText;
                        saveBtn.style.background = '#043d1a';
                        saveBtn.style.color = '#ffd700';
                        saveBtn.style.opacity = '';
                    }
                    if (cancelBtn) cancelBtn.disabled = false;
                    if (clearBtn) clearBtn.disabled = false;
                }, 850);

            } catch (err) {
                console.error("Error al sincronizar firma de carta:", err);
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.style.opacity = '';
                    saveBtn.style.background = '#dc2626';
                    saveBtn.style.color = '#ffffff';
                    saveBtn.innerHTML = '<i class="fa-solid fa-rotate-right"></i> Reintentar';
                }
                if (cancelBtn) cancelBtn.disabled = false;
                if (clearBtn) clearBtn.disabled = false;

                alert('Tu firma se guardó en este dispositivo, pero falló la conexión con la nube. Por favor presiona "Reintentar" o verifica tu señal.');
            }
        }
    </script>
</body>
</html>
"""

    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Archivo HTML Imprimible actualizado con éxito: {HTML_OUTPUT}")

    # 4. Publicar automáticamente en GitHub Pages
    try:
        print("\nSincronizando cambios con GitHub...")
        subprocess.run(["git", "add", "cartas_solicitud", "cartas_solicitud_imprimibles.html", "firmas_historicas.json", "estudiantes_registrados.json"], cwd=BASE_DIR, check=False)
        commit_msg = f"chore(auto): actualizar cartas con {len(processed_students)} estudiantes y {total_with_signature} firmas [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}]"
        res_commit = subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, capture_output=True, text=True)
        if "nothing to commit" in res_commit.stdout or "nothing to commit" in res_commit.stderr:
            print("No hay cambios nuevos respecto al último commit.")
        else:
            print(f"Commit realizado: {commit_msg}")
            res_push = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
            if res_push.returncode == 0:
                print("¡Despliegue a GitHub exitoso! Las cartas y firmas están en vivo.")
            else:
                print(f"Aviso en git push: {res_push.stderr}")
    except Exception as e:
        print(f"Aviso al intentar push a GitHub: {e}")

    print("\n" + "=" * 60)
    print("¡Rutina completada satisfactoriamente!")
    print(f"- Total Inscritos: {len(processed_students)}")
    print(f"- Total Firmantes: {total_with_signature}")
    print(f"- Cursos con Cartas Oficiales (>=10): {len(qualifying)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
