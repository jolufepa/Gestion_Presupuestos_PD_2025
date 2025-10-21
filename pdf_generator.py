import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

# Asume que esta función existe en db.py y te permite obtener todos los detalles de un presupuesto
from db import obtener_presupuesto_completo_para_pdf

# Definir la carpeta donde se guardarán los PDFs
PDF_DIR = "data/presupuestos_pdf"
os.makedirs(PDF_DIR, exist_ok=True)

def generate_pdf(presupuesto_id):
    """
    Genera el presupuesto final en formato PDF.
    Devuelve la ruta del archivo si tiene éxito, o un mensaje de error.
    """
    
    # 1. Recuperar datos
    try:
        # La función obtener_presupuesto_completo_para_pdf debe devolver:
        # (presupuesto_data, paciente_data, detalles_list)
        data = obtener_presupuesto_completo_para_pdf(presupuesto_id)
        if not data:
            return "Error: No se encontraron datos para el presupuesto."
            
        presupuesto_data, paciente_data, detalles_list = data
        
    except Exception as e:
        return f"Error al recuperar datos para PDF: {e}"

    # Asignación de datos para claridad
    presupuesto_num = presupuesto_data[1]
    fecha_presupuesto = presupuesto_data[3][:10] # Solo la fecha
    subtotal = presupuesto_data[4]
    descuento_monto = presupuesto_data[5]
    iva_porcentaje = presupuesto_data[6]
    total_final = presupuesto_data[7]
    notas = presupuesto_data[8]

    paciente_nombre_completo = f"{paciente_data[1]} {paciente_data[2]}"
    paciente_dni = paciente_data[3]
    paciente_telefono = paciente_data[4]
    paciente_email = paciente_data[6]
    
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
    
    # --- CORRECCIÓN: Inicializar styles y Story dentro de la función ---
    styles = getSampleStyleSheet()
    Story = []
    # ------------------------------------------------------------------

    # 2. CABECERA (LOGO y DATOS DE LA CLÍNICA - Aquí ponemos texto simple)
    clinic_info = [
        Paragraph("<b>Clínica Dental P&D</b>", styles['Heading2']),
        Paragraph("C/ Principal, 10, 28001 Madrid", styles['Normal']),
        Paragraph("Teléfono: 91 XXX XX XX | Email: info@clinicapd.es", styles['Normal']),
        Spacer(1, 0.2 * inch)
    ]
    Story.extend(clinic_info)

    # Título del Documento y Número
    title_text = f"PRESUPUESTO ODONTOLÓGICO NÚMERO: {presupuesto_num}"
    Story.append(Paragraph(f"<font size=14>{title_text}</font>", 
                           ParagraphStyle(name='TitleStyle', fontSize=14, alignment=1, spaceAfter=12)))
    
    # 3. DATOS DEL PACIENTE
    Story.append(Paragraph("<b>Datos del Paciente</b>", styles['Heading4']))
    paciente_data_table = [
        ['Nombre:', paciente_nombre_completo],
        ['DNI/NIE:', paciente_dni],
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
        # item: (id, presupuesto_id, tratamiento_id, nombre_manual, cantidad, precio_unitario, subtotal)
        descripcion = item[3] # nombre_manual
        cantidad = item[4]
        precio_unitario = f"{item[5]:.2f}"
        subtotal_item = f"{item[6]:.2f}"
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

    # Construir el PDF
    doc.build(Story)
    
    return f"✅ PDF generado con éxito: {pdf_filename}"