"""Generate PDF report for an equipment upload."""
import os
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

from .models import EquipmentUpload


def build_pdf(upload: EquipmentUpload) -> str:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)

    story = []
    story.append(Paragraph('Chemical Equipment Parameter Report', title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f'<b>File:</b> {upload.filename}', styles['Normal']))
    story.append(Paragraph(f'<b>Uploaded:</b> {upload.created_at.strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    s = upload.summary
    story.append(Paragraph('<b>Summary</b>', styles['Heading2']))
    story.append(Paragraph(f'Total equipment count: {s["total_count"]}', styles['Normal']))
    story.append(Paragraph(
        f'Averages — Flowrate: {s["averages"]["flowrate"]}, Pressure: {s["averages"]["pressure"]}, '
        f'Temperature: {s["averages"]["temperature"]}',
        styles['Normal']
    ))
    story.append(Paragraph('Equipment type distribution:', styles['Normal']))
    dist = s.get('type_distribution', {})
    for k, v in dist.items():
        story.append(Paragraph(f'  • {k}: {v}', styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph('<b>Data</b>', styles['Heading2']))
    rows = upload.data[:50]  # cap for PDF
    if not rows:
        story.append(Paragraph('No data.', styles['Normal']))
    else:
        headers = list(rows[0].keys())
        table_data = [[h.replace('_', ' ').title() for h in headers]]
        for r in rows:
            table_data.append([str(r.get(h, '')) for h in headers])
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
        if len(upload.data) > 50:
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(f'... and {len(upload.data) - 50} more rows.', styles['Normal']))

    doc.build(story)
    buf.seek(0)
    media = Path(settings.MEDIA_ROOT)
    media.mkdir(parents=True, exist_ok=True)
    out_dir = media / 'reports'
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'report_{upload.id}.pdf'
    with open(path, 'wb') as f:
        f.write(buf.read())
    return str(path)
