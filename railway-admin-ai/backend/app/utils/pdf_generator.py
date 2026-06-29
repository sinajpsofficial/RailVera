from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Line

class PDFGenerator:
    """
    Generates professional, high-quality executive decision reports for cases.
    Utilizes ReportLab templates, tables, custom styles, and page-layout controls.
    """

    @staticmethod
    def generate(case_obj, report_file_path: str):
        # 1. Page settings
        # Letter width = 612, printable width = 612 - 2 * 54 = 504
        doc = SimpleDocTemplate(
            report_file_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        # 2. Colors System
        primary_color = HexColor("#1A365D")    # Dark Navy
        secondary_color = HexColor("#4A5568")  # Slate Gray
        text_color = HexColor("#2D3748")       # Dark Charcoal
        light_bg = HexColor("#F7FAFC")         # Very light grey
        border_color = HexColor("#E2E8F0")     # Subtle border grey

        # Decision-specific Colors
        eligible_bg = HexColor("#E6F4EA")      # Soft Green
        eligible_text = HexColor("#137333")
        ineligible_bg = HexColor("#FCE8E6")    # Soft Red
        ineligible_text = HexColor("#C5221F")
        unknown_bg = HexColor("#FEF7E0")       # Soft Yellow/Orange
        unknown_text = HexColor("#B06000")

        # 3. Styles
        styles = getSampleStyleSheet()
        
        # Modify existing BodyText for custom spacing
        styles['BodyText'].textColor = text_color
        styles['BodyText'].fontSize = 10
        styles['BodyText'].leading = 14

        # Custom paragraph styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=primary_color,
            alignment=TA_LEFT,
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=secondary_color,
            alignment=TA_LEFT,
            spaceAfter=15
        )

        h1_style = ParagraphStyle(
            'SectionH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=primary_color,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12,
            textColor=primary_color
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=text_color
        )

        table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=table_cell_style,
            fontName='Helvetica-Bold'
        )

        decision_banner_style = ParagraphStyle(
            'DecisionBanner',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER
        )

        reasoning_style = ParagraphStyle(
            'ReasoningText',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=15,
            textColor=text_color
        )

        story = []

        # ── Header Section ─────────────────────────────────────────────
        story.append(Paragraph("INDIAN RAILWAYS", title_style))
        story.append(Paragraph("Departmental Administrative Eligibility Assessment Report", subtitle_style))

        # Horizontal Divider
        d = Drawing(504, 3)
        d.add(Line(0, 1, 504, 1, strokeColor=primary_color, strokeWidth=2))
        story.append(d)
        story.append(Spacer(1, 15))

        # ── Case Metadata Table ───────────────────────────────────────
        created_date = case_obj.created_at.strftime("%Y-%m-%d %H:%M") if case_obj.created_at else datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Facts mapping
        facts = case_obj.extracted_facts or {}
        emp_name = facts.get("employee_name", "N/A")
        emp_id = facts.get("employee_id") or case_obj.user_id or "N/A"
        dept = facts.get("department", "N/A")

        metadata_data = [
            [
                Paragraph("Case Reference ID:", table_header_style), 
                Paragraph(str(case_obj.id), table_cell_style),
                Paragraph("Assessment Date:", table_header_style), 
                Paragraph(created_date, table_cell_style)
            ],
            [
                Paragraph("Employee Name:", table_header_style), 
                Paragraph(str(emp_name), table_cell_style),
                Paragraph("Employee / User ID:", table_header_style), 
                Paragraph(str(emp_id), table_cell_style)
            ],
            [
                Paragraph("Department / Unit:", table_header_style), 
                Paragraph(str(dept), table_cell_style),
                Paragraph("Case Domain Type:", table_header_style), 
                Paragraph(str(case_obj.domain), table_cell_bold)
            ]
        ]
        
        # Total columns = 4 (colWidths: 120, 132, 120, 132 = 504)
        metadata_table = Table(metadata_data, colWidths=[120, 132, 120, 132])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, border_color),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 15))

        # ── Decision Banner ───────────────────────────────────────────
        decision = case_obj.decision or "Cannot Determine"
        
        # Map values to design styling
        if decision == "Eligible":
            banner_bg = eligible_bg
            banner_txt_color = eligible_text
            status_text = "ELIGIBLE - PROCEED WITH ACTION"
        elif decision == "Not Eligible":
            banner_bg = ineligible_bg
            banner_txt_color = ineligible_text
            status_text = "NOT ELIGIBLE - REQUEST DENIED"
        else:
            banner_bg = unknown_bg
            banner_txt_color = unknown_text
            status_text = "CANNOT DETERMINE - ADDITIONAL INFORMATION NEEDED"

        decision_banner_style.textColor = banner_txt_color
        
        banner_data = [[Paragraph(status_text, decision_banner_style)]]
        banner_table = Table(banner_data, colWidths=[504])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), banner_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1, banner_txt_color),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 15))

        # ── Supporting Facts Table ─────────────────────────────────────
        story.append(Paragraph("1. SUPPORTING FACTS & EXTRACTED DATA", h1_style))
        
        facts_data = [[
            Paragraph("Extracted Fact Key", table_header_style), 
            Paragraph("Verified Value / Description", table_header_style)
        ]]
        
        if facts:
            # Sort facts for consistent layout
            for key in sorted(facts.keys()):
                val = facts[key]
                # Format list/dict nicely
                if isinstance(val, list):
                    val_str = ", ".join([str(item) for item in val]) or "None"
                elif isinstance(val, dict):
                    val_str = str(val)
                else:
                    val_str = str(val)
                
                facts_data.append([
                    Paragraph(str(key).replace("_", " ").title(), table_cell_bold),
                    Paragraph(val_str, table_cell_style)
                ])
        else:
            facts_data.append([
                Paragraph("No facts extracted", table_cell_style),
                Paragraph("No facts populated in database for this case", table_cell_style)
            ])

        # Width: 180 and 324 = 504
        facts_table = Table(facts_data, colWidths=[180, 324])
        facts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), border_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), light_bg]),
            ('GRID', (0, 0), (-1, -1), 0.25, border_color),
        ]))
        story.append(facts_table)
        story.append(Spacer(1, 15))

        # ── Rules Applied Section ─────────────────────────────────────
        story.append(Paragraph("2. APPLICABLE ADMINISTRATIVE RULES & CITATIONS", h1_style))
        
        rules_applied = case_obj.rules_applied or []
        if rules_applied:
            rules_bullets = []
            for rule_ref in rules_applied:
                rules_bullets.append(
                    Paragraph(f"<b>[Rule Reference: {rule_ref}]</b> Cited in decision evaluation checks.", table_cell_style)
                )
            
            rules_table_data = [[bullet] for bullet in rules_bullets]
            rules_table = Table(rules_table_data, colWidths=[504])
            rules_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ]))
            story.append(rules_table)
        else:
            story.append(Paragraph("No rules cited in this evaluation.", table_cell_style))
        story.append(Spacer(1, 15))

        # ── Administrative Notes / Reasoning ──────────────────────────
        story.append(Paragraph("3. ADMINISTRATIVE EVALUATION NOTES & REASONING", h1_style))
        reasoning_text = case_obj.decision_reasoning or "No evaluation logic notes saved in database."
        # Clean newlines to HTML breaks for proper rendering inside Paragraph flowables
        reasoning_html = reasoning_text.replace("\n", "<br/>")
        story.append(Paragraph(reasoning_html, reasoning_style))
        story.append(Spacer(1, 20))

        # ── Sign-off Block ─────────────────────────────────────────────
        sign_off = []
        sign_off.append(Spacer(1, 15))
        sign_off_data = [
            [
                Paragraph("<b>Prepared By:</b><br/>Railway Admin AI Decision Engine", table_cell_style),
                Paragraph("<b>Reviewed & Approved By:</b><br/><br/>___________________________________<br/>Senior Personnel Officer / Division Seal", table_cell_style)
            ]
        ]
        sign_off_table = Table(sign_off_data, colWidths=[252, 252])
        sign_off_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        sign_off.append(sign_off_table)
        
        # Enforce keeping sign-off table together on the same page
        story.append(KeepTogether(sign_off))

        # Build PDF
        doc.build(story)
