import logging
from pathlib import Path
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


def generate_pdf_report(report_data: Dict[str, Any], output_path: Path) -> Path:
    """
    Generates a PDF summary report using ReportLab if installed.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a")
        )
        verdict_style = ParagraphStyle(
            "VerdictStyle",
            parent=styles["Normal"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2563eb"),
            fontName="Helvetica-Bold"
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        elements = []
        # Header
        elements.append(Paragraph("CapCheck AI - Fact Verification & Media Forensic Dossier", title_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=15))

        # Basic Info
        elements.append(Paragraph(f"<b>Title:</b> {report_data.get('title', 'N/A')}", body_style))
        elements.append(Paragraph(f"<b>Input Type:</b> {report_data.get('input_type', 'N/A').upper()}", body_style))
        elements.append(Paragraph(f"<b>Overall Verdict:</b> {report_data.get('verdict_label', 'N/A')}", verdict_style))
        elements.append(Paragraph(f"<b>Confidence:</b> {report_data.get('confidence_score', 0)}% ({report_data.get('confidence_level', 'N/A')})", body_style))
        elements.append(Spacer(1, 12))

        # Report card: overall grade, percentage and per-test breakdown
        card = report_data.get("report_card") or {}
        pct = card.get("overall_percent", report_data.get("correctness_score"))
        if card or pct is not None:
            elements.append(Paragraph("<b>Report Card:</b>", styles["Heading3"]))
            grade = card.get("grade", "?")
            pct_text = "no percentage (not enough reliable evidence)" if pct is None else f"{round(pct)}% likely correct / genuine"
            elements.append(Paragraph(f"<b>Grade {grade}</b> &mdash; {pct_text}. {card.get('grade_label', '')}", body_style))
            sections = card.get("sections") or []
            if sections:
                rows = [["Check", "Result", "What it found"]]
                for sec in sections:
                    p_val = sec.get("percent")
                    rows.append([
                        Paragraph(str(sec.get("title", "")), body_style),
                        "no result" if p_val is None else f"{round(p_val)}%",
                        Paragraph(str(sec.get("detail", ""))[:260], body_style),
                    ])
                ct = Table(rows, colWidths=[130, 55, 335])
                ct.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]))
                elements.append(Spacer(1, 6))
                elements.append(ct)
            if card.get("how_calculated"):
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(f"<b>How it was worked out:</b> {card['how_calculated']}", body_style))
            if card.get("explanation"):
                elements.append(Paragraph(str(card["explanation"]), body_style))
            elements.append(Spacer(1, 12))

        # Summary
        elements.append(Paragraph("<b>Executive Summary:</b>", styles["Heading3"]))
        elements.append(Paragraph(report_data.get("summary", ""), body_style))
        elements.append(Spacer(1, 12))

        # Evidence Table
        evidence = report_data.get("evidence_items", [])
        if evidence:
            elements.append(Paragraph("<b>Key Evidence Sources:</b>", styles["Heading3"]))
            table_data = [["Source", "Stance", "Reliability", "Reference Title"]]
            for ev in evidence[:6]:
                table_data.append([
                    ev.get("source_name", "Web")[:20],
                    ev.get("stance", "NEUTRAL"),
                    f"{ev.get('credibility_score', 70)}%",
                    ev.get("title", "")[:45]
                ])
            t = Table(table_data, colWidths=[100, 70, 70, 280])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 15))

        # Limitations
        limits = report_data.get("limitations", [])
        if limits:
            elements.append(Paragraph("<b>Methodological Limitations:</b>", styles["Heading3"]))
            for lim in limits:
                elements.append(Paragraph(f"• {lim}", body_style))

        doc.build(elements)
        return output_path
    except Exception as e:
        logger.warning(f"ReportLab PDF generation error: {e}. Writing markdown summary fallback.")
        # Fallback text file
        output_txt = output_path.with_suffix(".txt")
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(f"CapCheck AI Verification Dossier\n==============================\n")
            f.write(f"Title: {report_data.get('title')}\nVerdict: {report_data.get('verdict_label')}\n")
            f.write(f"Confidence: {report_data.get('confidence_score')}%\n\nSummary:\n{report_data.get('summary')}\n")
        return output_txt
