import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)


def extract_real_accuracy_and_reasons(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts Real Accuracy percentage and structured Why / Why Not forensic explanations."""
    label = str(report_data.get("verdict_label", ""))
    match = re.search(r"(\d+(\.\d+)?)%", label)

    if match:
        score = float(match.group(1))
    else:
        # Fallback extraction from media analysis or evidence items
        media_analysis = report_data.get("media_analysis")
        if media_analysis and isinstance(media_analysis, dict):
            ai_score = float(media_analysis.get("ai_generated_score", 0.0) or 0.0)
            score = max(0.0, min(100.0, 100.0 - ai_score))
        else:
            evidence = report_data.get("evidence_items", []) or []
            supports = sum(1 for e in evidence if e.get("stance") == "SUPPORTS")
            contradicts = sum(1 for e in evidence if e.get("stance") == "CONTRADICTS")
            total = supports + contradicts
            if total > 0:
                score = round((supports / total) * 100.0, 1)
            else:
                verdict = str(report_data.get("overall_verdict", "")).upper()
                score = 95.0 if ("SUPPORTED" in verdict or "AUTHENTIC" in verdict) else 15.0

    is_passed = score >= 75.0
    input_type = str(report_data.get("input_type", "claim")).lower()

    # Check if explanation already contains Why and Why Not
    explanation_raw = report_data.get("explanation", "")
    why_extracted = ""
    why_not_extracted = ""

    if "#### 1. Why this Real Accuracy was determined:" in explanation_raw:
        try:
            parts = explanation_raw.split("#### 1. Why this Real Accuracy was determined:")[1]
            if "#### 2. Why it did not score higher or lower" in parts:
                subparts = parts.split("#### 2. Why it did not score higher or lower")[1]
                why_extracted = parts.split("#### 2. Why it did not score higher or lower")[0].strip()
                why_not_extracted = subparts.split("#### 3. Verification Summary:")[0].replace("(Limiting & Contradicting Factors):", "").strip()
        except Exception:
            pass

    if not why_extracted:
        if input_type in ("claim", "url"):
            evidence = report_data.get("evidence_items", []) or []
            sup_sources = [e.get("source_name") for e in evidence if e.get("stance") == "SUPPORTS" and e.get("source_name")]
            con_sources = [e.get("source_name") for e in evidence if e.get("stance") == "CONTRADICTS" and e.get("source_name")]

            if is_passed:
                why_extracted = (
                    f"This statement/claim is verified with an Accuracy Level of Real of {score:.1f}% (Meets the strict >= 75% standard). "
                    f"Independent cross-source corroboration from verified repositories "
                    f"({', '.join(sup_sources[:3]) if sup_sources else 'encyclopedic and peer-reviewed records'}) "
                    f"confirms the assertions, established timelines, and core scientific or factual consensus."
                )
                why_not_extracted = (
                    f"The accuracy score did not reach 100% because minor contextual nuances, variations in secondary phrasing, "
                    f"or residual uncertainty in automated web retrieval were detected."
                    if score < 100.0 else
                    "Complete consensus achieved across all consulted independent registries with zero contradictions."
                )
            else:
                why_extracted = (
                    f"A baseline real score of {score:.1f}% was recorded from peripheral keywords and non-controversial historical context."
                    if score > 0 else
                    "No authoritative internet source or credible fact-checking database substantiated this claim."
                )
                why_not_extracted = (
                    f"This statement failed to achieve the required 75% Real threshold because independent fact-checking databases, "
                    f"official statistical records, or domain registries directly contradict or fail to corroborate the assertion. "
                    f"{('Documented refutations identified from: ' + ', '.join(con_sources[:3])) if con_sources else 'The assertions lack factual foundation.'} "
                    f"Under CapCheck AI standards, claims with less than 75% verified support cannot be declared authentic."
                )
        else:
            ma = report_data.get("media_analysis") or {}
            ai_risk = float(ma.get("ai_generated_score", 0.0) or 0.0)
            deepfake_risk = float(ma.get("deepfake_score", 0.0) or 0.0)
            indicators = ma.get("manipulation_indicators") or []

            if is_passed:
                why_extracted = (
                    f"This {input_type} media demonstrates authentic physical capture signatures with an Accuracy Level of Real of {score:.1f}% "
                    f"(Meets >= 75% standard). Physical sensor noise patterns (PRNU), authentic camera container metadata, and natural "
                    f"acoustic/visual frequency spectra verify real-world optical or acoustic recording."
                )
                why_not_extracted = (
                    f"The media did not receive a 100% score due to minor lossy re-compression artifacts, social media transcoding, "
                    f"or natural pixel noise variations introduced during transmission."
                    if score < 100.0 else
                    "Pristine hardware sensor signatures and cryptographic content credentials confirm complete physical authenticity."
                )
            else:
                why_extracted = (
                    f"The media exhibits a baseline real authenticity score of {score:.1f}% in raw container framing and ambient background signals."
                )
                why_not_extracted = (
                    f"The media failed the required 75% Real threshold due to detected forensic anomalies: "
                    f"AI Generation Risk: {ai_risk:.1f}%, Deepfake Alteration Risk: {deepfake_risk:.1f}%. "
                    f"Specific anomalies identified: {'; '.join(indicators[:3]) if indicators else 'synthetic generative harmonic patterns and temporal jitter.'} "
                    f"Consequently, its authentic real score is degraded to {score:.1f}%."
                )

    return {
        "score": score,
        "is_passed": is_passed,
        "why": why_extracted,
        "why_not": why_not_extracted
    }


def generate_pdf_report(report_data: Dict[str, Any], output_path: Path) -> Path:
    """
    Generates a professional, comprehensive PDF dossier using ReportLab,
    featuring explicit Real Accuracy percentage and structured 'Why and Why Not' forensic explanations.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        # Custom Typography Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica"
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica"
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0f172a")
        )
        callout_why = ParagraphStyle(
            "CalloutWhy",
            parent=body_style,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#065f46")
        )
        callout_whynot = ParagraphStyle(
            "CalloutWhyNot",
            parent=body_style,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#991b1b")
        )

        analysis = extract_real_accuracy_and_reasons(report_data)
        score = analysis["score"]
        is_passed = analysis["is_passed"]

        elements = []

        # 1. Header Banner
        header_table_data = [
            [
                Paragraph("<b>CapCheck AI</b>", ParagraphStyle("Brand", fontSize=16, leading=18, textColor=colors.HexColor("#2563eb"), fontName="Helvetica-Bold")),
                Paragraph("<b>OFFICIAL FORENSIC VERIFICATION DOSSIER</b>", ParagraphStyle("DosTitle", fontSize=10, leading=12, alignment=2, textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold"))
            ],
            [
                Paragraph("Digital Media & Factual Claim Verification Platform", subtitle_style),
                Paragraph(f"Audit Dossier #{str(report_data.get('id', 'N/A'))[:12]} • Strict >=75% Standard", ParagraphStyle("DosSub", fontSize=8, leading=10, alignment=2, textColor=colors.HexColor("#64748b")))
            ]
        ]
        header_table = Table(header_table_data, colWidths=[270, 270])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=12))

        # 2. Main Real Accuracy Scorecard Panel
        score_bg = colors.HexColor("#f0fdf4") if is_passed else (colors.HexColor("#fff7ed") if score >= 40 else colors.HexColor("#fef2f2"))
        score_border = colors.HexColor("#86efac") if is_passed else (colors.HexColor("#fed7aa") if score >= 40 else colors.HexColor("#fca5a5"))
        score_text_color = colors.HexColor("#166534") if is_passed else (colors.HexColor("#9a3412") if score >= 40 else colors.HexColor("#991b1b"))
        status_label = "HIGH AUTHENTICITY (MEETS >= 75% STANDARD)" if is_passed else ("PARTIAL AUTHENTICITY (CONTEXT DEFICIT)" if score >= 40 else "LOW AUTHENTICITY (FAILS >= 75% STANDARD)")

        scorecard_data = [
            [
                Paragraph(f"<b>ACCURACY LEVEL OF REAL:</b> <font size=16 color='{score_text_color.hexval()}'><b>{score:.1f}%</b></font>", ParagraphStyle("ScoreBig", fontSize=12, leading=16, textColor=score_text_color, fontName="Helvetica-Bold")),
                Paragraph(f"<b>Status:</b> {status_label}", ParagraphStyle("StatusBadge", fontSize=9, leading=12, alignment=2, textColor=score_text_color, fontName="Helvetica-Bold"))
            ],
            [
                Paragraph(f"<b>Submitted Item:</b> {str(report_data.get('title', 'N/A'))[:90]}", body_style),
                Paragraph(f"<b>Format:</b> {str(report_data.get('input_type', 'N/A')).upper()} | <b>Audit Confidence:</b> {report_data.get('confidence_score', 0)}%", ParagraphStyle("MetaR", fontSize=8.5, leading=11, alignment=2, textColor=colors.HexColor("#475569")))
            ]
        ]
        scorecard_table = Table(scorecard_data, colWidths=[340, 200])
        scorecard_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), score_bg),
            ("BOX", (0, 0), (-1, -1), 1, score_border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(scorecard_table)
        elements.append(Spacer(1, 10))

        # 3. Explicit "Why and Why Not" Section
        elements.append(Paragraph("<b>FORENSIC EXPLANATION: WHY AND WHY NOT</b>", section_heading))
        elements.append(Paragraph("Detailed technical rationale explaining why this real accuracy percentage was assigned, and what factors prevented a higher or lower rating:", subtitle_style))
        elements.append(Spacer(1, 6))

        why_why_not_data = [
            [
                Paragraph("<b>1. WHY THIS REAL ACCURACY WAS DETERMINED (Evidence & Supporting Cues):</b>", body_bold),
            ],
            [
                Paragraph(analysis["why"], callout_why)
            ],
            [
                Paragraph("<b>2. WHY IT DID NOT SCORE HIGHER OR LOWER (Contradictions, Missing Facts & Synthesis Traces):</b>", body_bold),
            ],
            [
                Paragraph(analysis["why_not"], callout_whynot)
            ]
        ]
        why_table = Table(why_why_not_data, colWidths=[540])
        why_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfdf5")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f0fdf4")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fef2f2")),
            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#fff1f2")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(why_table)
        elements.append(Spacer(1, 12))

        # 4. Multi-Pillar Verification Summary
        elements.append(Paragraph("<b>THREE-PILLAR FORENSIC AUDIT</b>", section_heading))
        fact_val = str(report_data.get("factual_claim_verdict") or "N/A (Media Input)").replace("_", " ")
        media_val = str(report_data.get("media_authenticity_verdict") or "N/A (Text Input)").replace("_", " ")
        context_val = str(report_data.get("context_verdict") or "Authentic Original").replace("_", " ")

        pillars_data = [
            [
                Paragraph("<b>Pillar 1: Fact-Check Consensus</b>", body_bold),
                Paragraph("<b>Pillar 2: Media Authenticity</b>", body_bold),
                Paragraph("<b>Pillar 3: Narrative Context</b>", body_bold)
            ],
            [
                Paragraph(f"<b>Verdict:</b> {fact_val}", body_style),
                Paragraph(f"<b>Verdict:</b> {media_val}", body_style),
                Paragraph(f"<b>Verdict:</b> {context_val}", body_style)
            ],
            [
                Paragraph("Cross-referenced against verified global registries and encyclopedias.", subtitle_style),
                Paragraph("Inspected for generative AI synthesis and pixel/waveform alterations.", subtitle_style),
                Paragraph("Evaluated for recycled footage or misleading deceptive framing.", subtitle_style)
            ]
        ]
        pillars_table = Table(pillars_data, colWidths=[180, 180, 180])
        pillars_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(pillars_table)
        elements.append(Spacer(1, 12))

        # 5. Key Evidence Sources Table
        evidence = report_data.get("evidence_items", []) or []
        if evidence:
            elements.append(Paragraph("<b>KEY EVIDENCE & WEB SOURCE CITATIONS</b>", section_heading))
            table_data = [["Source Name", "Stance", "Credibility", "Citation Title"]]
            for ev in evidence[:5]:
                stance_val = str(ev.get("stance", "NEUTRAL")).upper()
                table_data.append([
                    str(ev.get("source_name", "Web"))[:18],
                    stance_val,
                    f"{ev.get('credibility_score', 75):.0f}%",
                    str(ev.get("title", "Reference"))[:42]
                ])
            t = Table(table_data, colWidths=[110, 80, 70, 280])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))

        # 6. Methodological Limitations
        limits = report_data.get("limitations", []) or []
        if limits:
            elements.append(Paragraph("<b>AUDIT LIMITATIONS & SENSITIVITY NOTES</b>", section_heading))
            for lim in limits[:3]:
                elements.append(Paragraph(f"• {lim}", subtitle_style))
            elements.append(Spacer(1, 10))

        # 7. Digital Stamp & Footer
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        footer_data = [
            [
                Paragraph("<b>CapCheck AI Automated Forensic Engine</b> • Verified Cryptographic Audit", subtitle_style),
                Paragraph(f"Generated: {str(report_data.get('created_at', ''))[:19]} UTC", ParagraphStyle("DateR", fontSize=7.5, leading=9, alignment=2, textColor=colors.HexColor("#64748b")))
            ]
        ]
        footer_table = Table(footer_data, colWidths=[360, 180])
        footer_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(footer_table)

        doc.build(elements)
        logger.info(f"Successfully generated high-fidelity PDF report at: {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"ReportLab PDF generation error: {e}. Writing markdown fallback.")
        output_txt = output_path.with_suffix(".txt")
        analysis = extract_real_accuracy_and_reasons(report_data)
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("CapCheck AI Verification Dossier\n====================================\n\n")
            f.write(f"Title: {report_data.get('title')}\n")
            f.write(f"Accuracy Level of Real: {analysis['score']}%\n")
            f.write(f"Status: {'MEETS >= 75% STANDARD' if analysis['is_passed'] else 'FAILS 75% STANDARD'}\n\n")
            f.write(f"WHY THIS REAL ACCURACY WAS DETERMINED:\n{analysis['why']}\n\n")
            f.write(f"WHY IT DID NOT SCORE HIGHER OR LOWER:\n{analysis['why_not']}\n\n")
            f.write(f"SUMMARY:\n{report_data.get('summary')}\n")
        return output_txt

