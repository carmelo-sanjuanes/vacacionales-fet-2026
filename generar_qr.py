#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Código QR de Alta Calidad y Tarjeta para WhatsApp
Cursos Vacacionales FET 2026 - Ingeniería Eléctrica
"""

import os
import shutil
import qrcode
from PIL import Image, ImageDraw, ImageFont

TARGET_URL = "https://carmelo-sanjuanes.github.io/vacacionales-fet-2026/"
WORKSPACE_DIR = r"C:\Users\Carmelo\.gemini\antigravity\scratch\fet-cursos-vacacionales-electrica"
ARTIFACT_DIR = r"C:\Users\Carmelo\.gemini\antigravity\brain\f091cbd4-7664-4cb8-954b-17cd6f8044a5"

def generate_qr():
    # 1. Generar Código QR puro en alta resolución
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=3,
    )
    qr.add_data(TARGET_URL)
    qr.make(fit=True)

    # QR nítido con color institucional verde oscuro FET (#043d1a) y fondo blanco puro
    qr_img = qr.make_image(fill_color="#043d1a", back_color="#ffffff").convert("RGBA")
    
    qr_pure_path = os.path.join(WORKSPACE_DIR, "qr_acceso.png")
    qr_img.save(qr_pure_path, "PNG")
    print(f"QR puro guardado en: {qr_pure_path}")

    # 2. Diseñar Tarjeta / Flyer oficial para compartir en WhatsApp (1080 x 1350 px)
    W, H = 1080, 1350
    card = Image.new("RGBA", (W, H), "#f8fafc")
    draw = ImageDraw.Draw(card)

    # Fuentes
    font_dir = r"C:\Windows\Fonts"
    try:
        font_header = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 38)
        font_sub = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 30)
        font_title = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 46)
        font_lead = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 32)
        font_scan = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 34)
        font_url = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 30)
        font_badge = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 28)
        font_footer = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 24)
    except Exception:
        font_header = font_sub = font_title = font_lead = font_scan = font_url = font_badge = font_footer = ImageFont.load_default()

    # Encabezado verde institucional FET
    header_h = 280
    draw.rectangle([(0, 0), (W, header_h)], fill="#043d1a")
    # Barra de acento dorado FET (#d4af37)
    draw.rectangle([(0, header_h - 10), (W, header_h)], fill="#d4af37")

    # Textos Encabezado
    draw.text((W / 2, 60), "FUNDACIÓN ESCUELA TECNOLÓGICA DE NEIVA", font=font_header, fill="#e2e8f0", anchor="mm")
    draw.text((W / 2, 115), "FACULTAD DE INGENIERÍA • PROGRAMA DE INGENIERÍA ELÉCTRICA", font=font_sub, fill="#94a3b8", anchor="mm")
    draw.text((W / 2, 185), "CURSOS VACACIONALES 2026", font=font_title, fill="#ffd700", anchor="mm")
    draw.text((W / 2, 238), "Sistema de Registro y Firma Digital de Solicitud", font=font_lead, fill="#ffffff", anchor="mm")

    # Contenedor central blanco para el QR con sombra
    box_w, box_h = 700, 720
    box_x = (W - box_w) // 2
    box_y = 330
    
    # Sombra suave
    draw.rounded_rectangle([(box_x + 6, box_y + 8), (box_x + box_w + 6, box_y + box_h + 8)], radius=24, fill="#cbd5e1")
    # Tarjeta blanca
    draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], radius=24, fill="#ffffff", outline="#e2e8f0", width=3)

    # Texto indicador sobre el QR
    draw.text((W / 2, box_y + 45), "📲 ESCANEA CON TU CELULAR", font=font_scan, fill="#043d1a", anchor="mm")
    draw.text((W / 2, box_y + 85), "Apunta con la cámara o WhatsApp para firmar", font=font_lead, fill="#64748b", anchor="mm")

    # Pegar el QR en el centro del contenedor
    qr_display_size = 460
    qr_resized = qr_img.resize((qr_display_size, qr_display_size), Image.Resampling.LANCZOS)
    qr_paste_x = (W - qr_display_size) // 2
    qr_paste_y = box_y + 125
    card.paste(qr_resized, (qr_paste_x, qr_paste_y), qr_resized)

    # Enlace escrito debajo del QR dentro de la caja
    url_box_y = box_y + box_h - 75
    draw.rounded_rectangle([(box_x + 40, url_box_y), (box_x + box_w - 40, url_box_y + 50)], radius=10, fill="#f1f5f9", outline="#cbd5e1", width=1)
    draw.text((W / 2, url_box_y + 25), "carmelo-sanjuanes.github.io/vacacionales-fet-2026/", font=font_url, fill="#043d1a", anchor="mm")

    # Banner de llamado a la acción (Caja destacada inferior)
    cta_y = 1090
    cta_w = 900
    cta_x = (W - cta_w) // 2
    draw.rounded_rectangle([(cta_x, cta_y), (cta_x + cta_w, cta_y + 130)], radius=16, fill="#043d1a")
    draw.rectangle([(cta_x, cta_y), (cta_x + 12, cta_y + 130)], fill="#d4af37")

    draw.text((W / 2 + 10, cta_y + 42), "⚡ ¡TU FIRMA ES DECISIVA PARA ABRIR LAS ASIGNATURAS!", font=font_badge, fill="#ffd700", anchor="mm")
    draw.text((W / 2 + 10, cta_y + 88), "Se requieren mínimo 10 estudiantes por curso para radicar la carta", font=font_lead, fill="#ffffff", anchor="mm")

    # Footer
    draw.text((W / 2, 1285), "Representación Estudiantil de Ingeniería Eléctrica • FET 2026", font=font_footer, fill="#94a3b8", anchor="mm")

    # Guardar Flyer
    flyer_path = os.path.join(WORKSPACE_DIR, "qr_vacacionales_fet_tarjeta.png")
    card.save(flyer_path, "PNG")
    print(f"Tarjeta guardada en: {flyer_path}")

    # Copiar también al directorio de artefactos para visualización directa
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    art_qr = os.path.join(ARTIFACT_DIR, "qr_acceso.png")
    art_flyer = os.path.join(ARTIFACT_DIR, "qr_vacacionales_fet_tarjeta.png")
    shutil.copy2(qr_pure_path, art_qr)
    shutil.copy2(flyer_path, art_flyer)
    print(f"Copiados a artefactos: {art_qr} y {art_flyer}")

if __name__ == "__main__":
    generate_qr()
