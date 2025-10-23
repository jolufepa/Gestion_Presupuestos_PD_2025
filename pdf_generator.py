import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime


# Asume que esta función existe en db.py y te permite obtener todos los detalles de un presupuesto
from config import CLINIC_CONFIG, PDF_DIR
from db import decrypt_field, obtener_presupuesto_completo_para_pdf
import sys
def resource_path(relative_path):
    """ Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



# <-- NUEVA FUNCIÓN DE AYUDA PARA PROTEGER DATOS
def mask_dni(dni):
    """
    Oculta parte de un DNI/NIE para proteger la privacidad en el PDF.
    Muestra los primeros 4 caracteres y reemplaza el resto con asteriscos.
    """
    if not dni or len(dni) <= 4:
        # Si el DNI está vacío o es muy corto, lo devuelve tal cual
        return dni
    # Muestra los primeros 4 caracteres y el resto como asteriscos
    return dni[:4] + '*' * (len(dni) - 4)


# <-- MEJORA: Estilos definidos a nivel de módulo para mayor eficiencia
# Se crean una sola vez al importar el módulo, no en cada llamada a la función.
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    name='PresupuestoTitle',
    parent=styles['Heading1'],
    fontSize=16,
    alignment=1,  # Centrado
    spaceAfter=12
)

def generate_pdf(presupuesto_id):
    """
    Genera el presupuesto final en formato PDF.
    Devuelve la ruta del archivo si tiene éxito, o un mensaje de error.
    """
    
    # 1. Recuperar datos
    try:
        data = obtener_presupuesto_completo_para_pdf(presupuesto_id)
        if not data:
            return "Error: No se encontraron datos para el presupuesto."
            
        presupuesto_data, paciente_data, detalles_list = data
        
    except Exception as e:
        return f"Error al recuperar datos para PDF: {e}"

    # <-- CORRECCIÓN: Asignación de datos usando nombres de columna (más robusto)
    # Esto funciona si obtener_presupuesto_completo_para_pdf usa conn.row_factory = sqlite3.Row
    presupuesto_num = presupuesto_data['numero_presupuesto']
    fecha_presupuesto = presupuesto_data['fecha'][:10]
    subtotal = presupuesto_data['subtotal']
    descuento_monto = presupuesto_data['descuento']
    iva_porcentaje = presupuesto_data['iva_porcentaje']
    total_final = presupuesto_data['total']
    notas = presupuesto_data['notas']

    paciente_nombre_completo = f"{paciente_data['nombre']} {paciente_data['apellidos']}"
    paciente_dni = paciente_data['dni_nie']
    paciente_telefono = decrypt_field(paciente_data['telefono_enc']) # <-- Se necesita importar decrypt_field si no está
    paciente_email = decrypt_field(paciente_data['email_enc'])   # <-- Se necesita importar decrypt_field si no está
    
    # Configuración del PDF
    pdf_filename = os.path.join(PDF_DIR, f"Presupuesto_{presupuesto_num}.pdf")
    doc = SimpleDocTemplate(
        pdf_filename, 
        pagesize=A4,
        topMargin=inch/2, 
        bottomMargin=inch/2,
        leftMargin=inch/2,
        rightMargin=inch/2
    )
    
    # Story es la lista de elementos que se añadirán al PDF
    Story = []

    # 2. CABECERA (LOGO y DATOS DE LA CLÍNICA)
    # <-- MEJORA: Usar la configuración centralizada
    clinic_info = [
        Paragraph(f"<b>{CLINIC_CONFIG['name']}</b>", styles['Heading2']),
        Paragraph(f"<b>{CLINIC_CONFIG['cif']}</b>", styles['Normal']),
        Paragraph(CLINIC_CONFIG['address'], styles['Normal']),
        Paragraph(f"<b>{CLINIC_CONFIG['postal_code']}</b>", styles['Normal']),
        Paragraph(f"Teléfono: {CLINIC_CONFIG['phone']} | Email: {CLINIC_CONFIG['email']}", styles['Normal']),
        Spacer(1, 0.2 * inch)
    ]
    Story.extend(clinic_info)

    # Título del Documento y Número
    title_text = f"PRESUPUESTO ODONTOLÓGICO NÚMERO: {presupuesto_num}"
    Story.append(Paragraph(title_text, title_style))
    
    # 3. DATOS DEL PACIENTE
    Story.append(Paragraph("<b>Datos del Paciente</b>", styles['Heading4']))
    paciente_dni_masked = mask_dni(paciente_data['dni_nie'])
    
    paciente_data_table = [
        ['Nombre:', paciente_nombre_completo],
        ['DNI/NIE:', paciente_dni_masked],  # <-- USAMOS LA VARIABLE ENMASCARADA
        ['Teléfono:', paciente_telefono],
        ['Email:', paciente_email],
        ['Fecha:', fecha_presupuesto]
    ]
    
    paciente_table = Table(paciente_data_table, colWidths=[1.5*inch, 5*inch])
    paciente_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F0F0F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))
    Story.append(paciente_table)
    Story.append(Spacer(1, 0.3 * inch))

    # 4. TABLA DE DETALLES
    Story.append(Paragraph("<b>Detalle de Tratamientos y Servicios</b>", styles['Heading4']))
    
    table_data = [['DESCRIPCIÓN', 'CANTIDAD', 'PRECIO U. (€)', 'SUBTOTAL (€)']]
    
    for item in detalles_list:
        # <-- CORRECCIÓN: Acceso a datos por nombre
        # item: (id, presupuesto_id, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal)
        descripcion = item['nombre_manual']
        cantidad = item['cantidad']
        precio_unitario = f"{item['precio_unitario']:.2f}"
        subtotal_item = f"{item['subtotal']:.2f}"
        table_data.append([descripcion, cantidad, precio_unitario, subtotal_item])

    # Estilos de la tabla de detalles
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#B0E0E6')), # Azul claro para cabecera
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ])
    
    # ColWidths: Descripción, Cantidad, Precio U., Subtotal
    detail_table = Table(table_data, colWidths=[4*inch, inch, inch, inch])
    detail_table.setStyle(table_style)
    Story.append(detail_table)
    Story.append(Spacer(1, 0.3 * inch))

    # 5. RESUMEN DE TOTALES
    Story.append(Paragraph("<b>Resumen Económico</b>", styles['Heading4']))
    
    resumen_data = [
        ['Subtotal (Base):', f"{subtotal:.2f} €"],
        ['Descuento Aplicado:', f"-{descuento_monto:.2f} €"],
        ['Subtotal con Descuento:', f"{(subtotal - descuento_monto):.2f} €"],
        ['IVA ({:.2f}%):'.format(iva_porcentaje), f"{((subtotal - descuento_monto) * iva_porcentaje/100):.2f} €"],
        ['TOTAL FINAL:', f"{total_final:.2f} €"]
    ]
    
    resumen_table = Table(resumen_data, colWidths=[2.5*inch, 2*inch])
    resumen_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'), # Total en negrita
        ('LINEBELOW', (0, 3), (-1, 3), 1, colors.black),
    ]))
    Story.append(resumen_table)
    Story.append(Spacer(1, 0.3 * inch))

    # 6. NOTAS Y PIE
    if notas:
        Story.append(Paragraph("<b>Notas:</b>", styles['Heading4']))
        Story.append(Paragraph(notas.replace('\n', '<br/>'), styles['Normal']))

    Story.append(Spacer(1, 0.5 * inch))
    Story.append(Paragraph("<i>Presupuesto válido por 30 días. Para cualquier duda, contáctenos.</i>", styles['Italic']))

    # <-- CORRECCIÓN: Construcción del PDF dentro de un bloque try...except
    try:
        doc.build(Story)
        return f"✅ PDF generado con éxito: {pdf_filename}"
    except Exception as e:
        # Esto evita que la aplicación entera se cierre si hay un error al generar el PDF
        return f"Error al construir el PDF: {e}"
