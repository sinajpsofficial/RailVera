"""
Generate sample input documents for the Rajesh Kumar promotion test case.
Run: venv\\Scripts\\python.exe generate_sample_docs.py
Output: sample_docs/ folder with 3 PDFs ready for upload.
"""
import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

os.makedirs("sample_docs", exist_ok=True)

NAVY   = colors.HexColor("#1A2F5A")
GOLD   = colors.HexColor("#C49A22")
LGRAY  = colors.HexColor("#F4F6F9")
DKGRAY = colors.HexColor("#4A4A4A")
GREEN  = colors.HexColor("#1B6B3A")
RED    = colors.HexColor("#8B0000")

styles = getSampleStyleSheet()

def h(text, size=12, bold=True, color=NAVY, align=TA_LEFT):
    return Paragraph(text, ParagraphStyle(
        "h", fontSize=size, fontName="Helvetica-Bold" if bold else "Helvetica",
        textColor=color, alignment=align, spaceAfter=4
    ))

def p(text, size=10, color=DKGRAY, align=TA_LEFT):
    return Paragraph(text, ParagraphStyle(
        "p", fontSize=size, fontName="Helvetica",
        textColor=color, alignment=align, spaceAfter=3
    ))

def gov_header(story, title, subtitle="Ministry of Railways — Government of India"):
    story.append(Spacer(1, 0.2*cm))
    story.append(h("🚂  INDIAN RAILWAYS", size=16, color=NAVY, align=TA_CENTER))
    story.append(h(subtitle, size=9, bold=False, color=GOLD, align=TA_CENTER))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=6))
    story.append(h(title, size=14, color=NAVY, align=TA_CENTER))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))


# ══════════════════════════════════════════════════════════════════════════════
# 1. SERVICE BOOK
# ══════════════════════════════════════════════════════════════════════════════
def gen_service_book():
    path = "sample_docs/service_book.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    gov_header(story, "SERVICE BOOK",
               subtitle="Eastern Railway — Howrah Division | Transportation (Power) Dept.")

    # Personal Details table
    personal = [
        ["EMPLOYEE DETAILS", "", "", ""],
        ["Employee Name:", "Rajesh Kumar", "Employee ID:", "EMP-RK-2801"],
        ["Date of Birth:", "15-07-1985", "Gender:", "Male"],
        ["Father's Name:", "Ramesh Kumar", "Religion:", "Hindu"],
        ["Permanent Address:", "42, Railway Colony, Howrah, WB - 711101", "", ""],
    ]
    t = Table(personal, colWidths=[4.5*cm, 5.5*cm, 4*cm, 4.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 10),
        ("SPAN",         (0,0), (-1,0)),
        ("ALIGN",        (0,0), (-1,0), "CENTER"),
        ("BACKGROUND",   (0,1), (-1,-1), LGRAY),
        ("FONTSIZE",     (0,1), (-1,-1), 9),
        ("FONTNAME",     (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (2,1), (2,-1), "Helvetica-Bold"),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGRAY]),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("PADDING",      (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Service details
    service = [
        ["SERVICE & APPOINTMENT DETAILS", "", "", ""],
        ["Department:", "Transportation (Power)", "Division:", "Howrah"],
        ["Designation:", "Goods Driver", "Grade Pay:", "₹ 2800"],
        ["Pay Level:", "Level 4 (7th CPC)", "Pay Scale:", "₹ 25,500 – 81,100"],
        ["Date of Appointment:", "15-08-2016", "Appointment Type:", "Direct Recruitment"],
        ["Date of Joining:", "15-08-2016", "Joining Station:", "Howrah Loco Shed"],
        ["Date of Confirmation:", "15-08-2017", "Retirement Date:", "31-07-2045"],
    ]
    t2 = Table(service, colWidths=[4.5*cm, 5.5*cm, 4*cm, 4.5*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 10),
        ("SPAN",         (0,0), (-1,0)),
        ("ALIGN",        (0,0), (-1,0), "CENTER"),
        ("FONTSIZE",     (0,1), (-1,-1), 9),
        ("FONTNAME",     (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (2,1), (2,-1), "Helvetica-Bold"),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGRAY]),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("PADDING",      (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    # Promotion history
    story.append(h("PROMOTION / INCREMENT HISTORY", size=11, color=NAVY))
    promo = [
        ["Date", "From Post", "To Post / Grade", "Order No.", "Authority"],
        ["15-08-2016", "—", "Goods Driver (Trainee)", "HWH/APPT/2016/142", "DRM Howrah"],
        ["15-08-2017", "Goods Driver (Trainee)", "Goods Driver (Confirmed)", "HWH/CONF/2017/88", "DRM Howrah"],
        ["01-01-2023", "Goods Driver", "Sr. Scale Increment", "HWH/INCR/2023/14", "DRM Howrah"],
    ]
    tp = Table(promo, colWidths=[2.8*cm, 4*cm, 4.5*cm, 4*cm, 3.2*cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), GOLD),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGRAY]),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("PADDING",      (0,0), (-1,-1), 5),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(tp)
    story.append(Spacer(1, 0.4*cm))

    # Penalty history
    story.append(h("DISCIPLINARY / PENALTY RECORD", size=11, color=NAVY))
    penalty = [
        ["Year", "Nature of Penalty", "Order No.", "Status"],
        ["NIL", "No penalty or disciplinary proceedings on record", "—", "Clean Record ✓"],
    ]
    tpen = Table(penalty, colWidths=[2.5*cm, 8*cm, 4*cm, 4*cm])
    tpen.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), GREEN),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white]),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("PADDING",      (0,0), (-1,-1), 6),
        ("SPAN",         (1,1), (1,1)),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(tpen)
    story.append(Spacer(1, 0.6*cm))

    # Certification
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 0.2*cm))
    story.append(p(
        "Certified that the entries in this Service Book have been verified with "
        "the original documents and are correct to the best of my knowledge. "
        "The employee has completed <b>8 years of satisfactory service</b> as on 23-06-2024.",
        size=9
    ))
    story.append(Spacer(1, 0.8*cm))
    sig = [
        ["", "Sd/-", ""],
        ["", "Senior Personnel Officer", ""],
        ["", "Howrah Division, Eastern Railway", ""],
        ["Date: 23-06-2024", "", "Office Seal"],
    ]
    tsig = Table(sig, colWidths=[5*cm, 9*cm, 4.5*cm])
    tsig.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("FONTNAME", (1,1), (1,2), "Helvetica-Bold"),
        ("ALIGN",    (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(tsig)

    doc.build(story)
    print(f"[OK] Generated: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. APAR REPORT (Last 3 Years)
# ══════════════════════════════════════════════════════════════════════════════
def gen_apar_report():
    path = "sample_docs/apar_report.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    gov_header(story, "ANNUAL PERFORMANCE ASSESSMENT REPORT (APAR)",
               subtitle="Confidential — Eastern Railway | Last 3 Assessment Years")

    story.append(h("EMPLOYEE IDENTIFICATION", size=11, color=NAVY))
    ident = [
        ["Name:", "Rajesh Kumar", "Employee ID:", "EMP-RK-2801"],
        ["Designation:", "Goods Driver", "Department:", "Transportation (Power)"],
        ["Division:", "Howrah", "Assessment Period:", "2021–22, 2022–23, 2023–24"],
    ]
    tid = Table(ident, colWidths=[3.5*cm, 6.5*cm, 4*cm, 4.5*cm])
    tid.setStyle(TableStyle([
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("GRID",      (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LGRAY]),
        ("PADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(tid)
    story.append(Spacer(1, 0.4*cm))

    for year, ro, ao, score, bench, grade in [
        ("2021–2022", "Sh. A.K. Singh, Loco Foreman", "Sh. P. Mehta, DRM",
         "9.2 / 10", "Met", "Outstanding"),
        ("2022–2023", "Sh. A.K. Singh, Loco Foreman", "Sh. P. Mehta, DRM",
         "9.5 / 10", "Met", "Outstanding"),
        ("2023–2024", "Sh. R. Verma, Sr. Loco Foreman", "Sh. S. Kaur, DRM",
         "9.4 / 10", "Met", "Outstanding"),
    ]:
        story.append(KeepTogether([
            h(f"Assessment Year: {year}", size=10, color=GOLD),
            Table([
                ["Reporting Officer:", ro, "Reviewing Officer:", ao],
                ["Overall Score:", score, "Benchmark Met:", bench],
                ["APAR Grading:", grade, "", ""],
            ], colWidths=[3.5*cm, 6.5*cm, 4*cm, 4.5*cm],
            style=TableStyle([
                ("FONTSIZE",  (0,0), (-1,-1), 9),
                ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
                ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
                ("GRID",      (0,0), (-1,-1), 0.5, colors.grey),
                ("BACKGROUND",(1,2), (1,2), colors.HexColor("#DFF0D8")),
                ("FONTNAME",  (1,2), (1,2), "Helvetica-Bold"),
                ("TEXTCOLOR", (1,2), (1,2), GREEN),
                ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LGRAY]),
                ("PADDING",   (0,0), (-1,-1), 6),
            ])),
            Spacer(1, 0.4*cm),
        ]))

    # Summary
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 0.2*cm))
    story.append(h("APAR SUMMARY — 3-YEAR CONSOLIDATED", size=11, color=NAVY))
    summary = [
        ["Year", "Score", "Grading", "Benchmark", "Status"],
        ["2021–22", "9.2/10", "Outstanding", "Met", "✓ Eligible"],
        ["2022–23", "9.5/10", "Outstanding", "Met", "✓ Eligible"],
        ["2023–24", "9.4/10", "Outstanding", "Met", "✓ Eligible"],
        ["3-Year Average", "9.37/10", "OUTSTANDING", "Consistently Met", "✓ ELIGIBLE FOR PROMOTION"],
    ]
    ts = Table(summary, colWidths=[3*cm, 3*cm, 4*cm, 4*cm, 4.5*cm])
    ts.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND",   (0,4), (-1,4), colors.HexColor("#DFF0D8")),
        ("FONTNAME",     (0,4), (-1,4), "Helvetica-Bold"),
        ("TEXTCOLOR",    (0,4), (-1,4), GREEN),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,3), [colors.white, LGRAY]),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("PADDING",      (0,0), (-1,-1), 6),
    ]))
    story.append(ts)
    story.append(Spacer(1, 0.6*cm))
    story.append(p(
        "<b>Certified:</b> The above APAR gradings are authentic and have been "
        "reviewed and accepted by the Reviewing Authority. The employee has received "
        "an <b>Outstanding</b> rating for all three consecutive assessment years, "
        "meeting the benchmark criteria for departmental promotion.",
        size=9
    ))
    story.append(Spacer(1, 0.8*cm))
    story.append(p("Sd/-    Sr. Personnel Officer, Howrah Division    Date: 23-06-2024",
                   size=9, align=TA_RIGHT))

    doc.build(story)
    print(f"[OK] Generated: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. DEPARTMENTAL EXAM RESULT
# ══════════════════════════════════════════════════════════════════════════════
def gen_exam_result():
    path = "sample_docs/exam_result.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    gov_header(story, "DEPARTMENTAL PROMOTIONAL EXAMINATION — RESULT CERTIFICATE",
               subtitle="Railway Training School, Howrah | GDCE / LDCE Examination Cell")

    story.append(h("RESULT NOTIFICATION", size=11, color=NAVY))
    story.append(p(
        "This is to certify that the following employee appeared in the "
        "<b>Grade-based Departmental Competitive Examination (GDCE)</b> conducted "
        "for promotion to <b>Senior Driver / Motorman (Grade Pay 4200)</b> and "
        "has been declared <b>PASS</b> as per the result tabulated below:",
        size=10
    ))
    story.append(Spacer(1, 0.3*cm))

    cand = [
        ["CANDIDATE DETAILS", "", "", ""],
        ["Candidate Name:", "Rajesh Kumar", "Roll Number:", "GDCE/HWH/2024/0312"],
        ["Employee ID:", "EMP-RK-2801", "Category:", "OBC (Non-Creamy Layer)"],
        ["Present Designation:", "Goods Driver", "Department:", "Transportation (Power)"],
        ["Division:", "Howrah", "Exam Centre:", "Railway Training School, Howrah"],
        ["Date of Examination:", "10-03-2024", "Result Date:", "05-05-2024"],
    ]
    tc = Table(cand, colWidths=[4.5*cm, 5.5*cm, 4*cm, 4.5*cm])
    tc.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 10),
        ("SPAN",         (0,0), (-1,0)),
        ("ALIGN",        (0,0), (-1,0), "CENTER"),
        ("FONTSIZE",     (0,1), (-1,-1), 9),
        ("FONTNAME",     (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (2,1), (2,-1), "Helvetica-Bold"),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGRAY]),
        ("PADDING",      (0,0), (-1,-1), 6),
    ]))
    story.append(tc)
    story.append(Spacer(1, 0.4*cm))

    story.append(h("MARKS DETAILS", size=11, color=NAVY))
    marks = [
        ["Subject / Paper", "Max Marks", "Marks Obtained", "Percentage", "Status"],
        ["Paper I — Technical (Loco Operation)", "100", "82", "82%", "Pass"],
        ["Paper II — Rules & Regulations", "100", "78", "78%", "Pass"],
        ["Paper III — Safety & Emergency Procedures", "100", "85", "85%", "Pass"],
        ["Practical Assessment", "50", "44", "88%", "Pass"],
        ["TOTAL / AGGREGATE", "350", "289", "82.57%", "PASS ✓"],
    ]
    tm = Table(marks, colWidths=[6*cm, 3*cm, 3.5*cm, 3*cm, 3*cm])
    tm.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), GOLD),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND",   (0,5), (-1,5), colors.HexColor("#DFF0D8")),
        ("FONTNAME",     (0,5), (-1,5), "Helvetica-Bold"),
        ("TEXTCOLOR",    (0,5), (-1,5), GREEN),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,4), [colors.white, LGRAY]),
        ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        ("PADDING",      (0,0), (-1,-1), 6),
    ]))
    story.append(tm)
    story.append(Spacer(1, 0.4*cm))

    story.append(h("RESULT DECLARATION", size=11, color=NAVY))
    result_box = Table([[
        Paragraph(
            "RESULT:  <font color='#1B6B3A'><b>PASS</b></font><br/><br/>"
            "Rajesh Kumar (Roll No: GDCE/HWH/2024/0312) has successfully passed "
            "the GDCE examination with an aggregate of <b>82.57%</b>, which is above "
            "the minimum qualifying mark of 60%. The candidate is declared <b>ELIGIBLE</b> "
            "for consideration for promotion to Senior Driver grade (Grade Pay 4200) "
            "subject to availability of vacancies and seniority norms.",
            ParagraphStyle("rb", fontSize=10, fontName="Helvetica",
                           leftIndent=6, rightIndent=6)
        )
    ]], colWidths=[17.5*cm])
    result_box.setStyle(TableStyle([
        ("BOX",     (0,0), (-1,-1), 1.5, GREEN),
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F0FFF4")),
        ("PADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(result_box)
    story.append(Spacer(1, 0.8*cm))

    # Signatories
    sig = [
        ["Sd/-", "", "Sd/-"],
        ["Principal / Chief Instructor", "", "Controller of Examinations"],
        ["Railway Training School, Howrah", "", "Eastern Railway, Kolkata"],
        ["Date: 05-05-2024", "", "Date: 05-05-2024"],
    ]
    tsig = Table(sig, colWidths=[6*cm, 5.5*cm, 6*cm])
    tsig.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,0), "Helvetica-Bold"),
        ("ALIGN",    (0,0), (0,-1), "LEFT"),
        ("ALIGN",    (2,0), (2,-1), "RIGHT"),
    ]))
    story.append(tsig)

    doc.build(story)
    print(f"[OK] Generated: {path}")


if __name__ == "__main__":
    print("Generating sample documents for Rajesh Kumar promotion test case...\n")
    gen_service_book()
    gen_apar_report()
    gen_exam_result()
    print("\n[DONE] All 3 documents saved to: sample_docs/")
    print("   - sample_docs/service_book.pdf")
    print("   - sample_docs/apar_report.pdf")
    print("   - sample_docs/exam_result.pdf")

