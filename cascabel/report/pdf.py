import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from cascabel.config import CONFIG
from cascabel.optimizer.greedy import get_covered_techniques
from cascabel.orchestrator.engine import load_tests

def generate_pdf_report(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("CASCABEL Purple-Team Executive Report", styles['Title']))
    story.append(Spacer(1, 12))

    # Coverage
    tests = load_tests(CONFIG.atomics_dir)
    covered_techs = set(get_covered_techniques())
    
    story.append(Paragraph(f"Total MITRE ATT&CK Coverage: {len(covered_techs)} / {len(tests)} techniques", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Table of covered techniques
    data = [["Technique", "Name", "Tactics"]]
    for test in tests:
        if test.technique_id in covered_techs:
            data.append([test.technique_id, test.name, test.tactic])
            
    if len(data) > 1:
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No techniques have been fully emulated and proven yet.", styles['Normal']))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Generated automatically by CASCABEL AI", styles['Italic']))

    doc.build(story)
