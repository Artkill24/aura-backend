"""
AURA — PDF Report Generator
Produces a forensic-grade report that a lawyer or insurance expert can print and sign.
Built with ReportLab Platypus for structured, multi-page output.
"""

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF


# ─────────────────────────────────────────────
#  Brand Colors
# ─────────────────────────────────────────────
AURA_DARK   = colors.HexColor("#0D0D1A")
AURA_BLUE   = colors.HexColor("#1A1AFF")
AURA_CYAN   = colors.HexColor("#00E5FF")
AURA_GREEN  = colors.HexColor("#00C853")
AURA_YELLOW = colors.HexColor("#FFD600")
AURA_ORANGE = colors.HexColor("#FF6D00")
AURA_RED    = colors.HexColor("#D50000")
AURA_LIGHT  = colors.HexColor("#F5F5F5")
AURA_GRAY   = colors.HexColor("#9E9E9E")
AURA_BORDER = colors.HexColor("#E0E0E0")

VERDICT_COLORS = {
    "green":  AURA_GREEN,
    "yellow": AURA_YELLOW,
    "orange": AURA_ORANGE,
    "red":    AURA_RED,
}

SEVERITY_COLORS = {
    "HIGH":   AURA_RED,
    "MEDIUM": AURA_ORANGE,
    "LOW":    AURA_YELLOW,
    "INFO":   AURA_GRAY,
}


def generate_pdf_report(
    output_path: str,
    job_id: str,
    filename: str,
    metadata: dict,
    visual: dict,
    audio: dict,
    signal: dict,
    verdict: dict,
    elapsed: float,
    moire: dict = None,
    prnu: dict = None,
):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        title=f"AURA Authenticity Report — {filename}",
        author="AURA Reality Firewall",
    )

    styles = _build_styles()
    story = []

    # ── Cover Header ──
    story += _build_header(styles, job_id, filename, elapsed)
    story.append(Spacer(1, 6 * mm))

    # ── Verdict Banner ──
    story += _build_verdict_banner(verdict, styles)
    story.append(Spacer(1, 6 * mm))

    # ── Score Breakdown ──
    story += _build_score_table(metadata, visual, audio, signal, verdict, styles)
    story.append(Spacer(1, 6 * mm))

    # ── Metadata Section ──
    story += _build_section(
        "1. Metadata Analysis",
        metadata,
        styles,
        extra_table=_metadata_details_table(metadata.get("details", {}), styles),
    )
    story.append(Spacer(1, 5 * mm))

    # ── Visual Section ──
    story += _build_section(
        "2. Visual / Frame Analysis",
        visual,
        styles,
        extra_table=_anomaly_frames_table(visual.get("anomaly_frames", []), styles),
    )
    story.append(Spacer(1, 5 * mm))

    # ── Audio Section ──
    story += _build_section(
        "3. Audio-Visual Sync Analysis",
        audio,
        styles,
        extra_table=_audio_details_table(audio.get("details", {}), styles),
    )
    story.append(Spacer(1, 5 * mm))

    # ── Signal Physics Section ──
    story += _build_section(
        "4. Signal Physics Analysis (Sensor / Motion / Frequency)",
        signal,
        styles,
        extra_table=_metadata_details_table(signal.get("details", {}), styles),
    )
    story.append(Spacer(1, 8 * mm))

    # ── Legal Disclaimer ──
    story += _build_disclaimer(styles)

    # ── Footer handled via onPage ──
    doc.build(
        story,
        onFirstPage=_add_footer,
        onLaterPages=_add_footer,
    )


# ─────────────────────────────────────────────
#  Section Builders
# ─────────────────────────────────────────────

def _build_header(styles, job_id, filename, elapsed):
    elements = []

    # Top bar
    elements.append(
        Table(
            [[
                Paragraph("AURA", styles["BrandTitle"]),
                Paragraph(
                    "Advanced Universal Reality Authentication<br/>"
                    "<font color='#9E9E9E'>Media Authenticity Report</font>",
                    styles["BrandSubtitle"],
                ),
            ]],
            colWidths=["25%", "75%"],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), AURA_DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (0, -1), 10),
                ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
            ]),
        )
    )

    elements.append(Spacer(1, 4 * mm))

    # Meta info row
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    meta_rows = [[
        Paragraph(f"<b>File:</b> {filename}", styles["MetaInfo"]),
        Paragraph(f"<b>Job ID:</b> {job_id[:16]}...", styles["MetaInfo"]),
        Paragraph(f"<b>Analysis:</b> {elapsed}s", styles["MetaInfo"]),
        Paragraph(f"<b>Date:</b> {now}", styles["MetaInfo"]),
    ]]

    elements.append(
        Table(
            meta_rows,
            colWidths=["30%", "25%", "20%", "25%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), AURA_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.3, AURA_BORDER),
            ]),
        )
    )

    return elements


def _build_verdict_banner(verdict: dict, styles):
    label = verdict.get("label", "UNKNOWN")
    score = verdict.get("composite_score", 0.0)
    confidence = verdict.get("confidence", "—")
    risk_color_key = verdict.get("risk_color", "green")
    color = VERDICT_COLORS.get(risk_color_key, AURA_GREEN)

    pct = int(score * 100)
    bar_total = 160  # mm-scale representation

    banner = Table(
        [[
            Paragraph(
                f"<font color='white'><b>VERDICT</b></font>",
                styles["VerdictLabel"],
            ),
            Paragraph(
                f"<font color='white'><b>{label}</b></font><br/>"
                f"<font color='#BDBDBD'>Risk Score: {pct}% | Confidence: {confidence}</font>",
                styles["VerdictText"],
            ),
        ]],
        colWidths=["22%", "78%"],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), AURA_DARK),
            ("BACKGROUND", (0, 0), (0, 0), color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 2, color),
        ]),
    )
    return [banner]


def _build_score_table(metadata, visual, audio, signal, verdict, styles):
    elements = [Paragraph("Score Breakdown", styles["SectionTitle"])]

    breakdown = verdict.get("breakdown", {})
    meta_score   = metadata.get("manipulation_score", 0.0)
    visual_score = visual.get("deepfake_probability", 0.0)
    audio_score  = audio.get("sync_anomaly_score", 0.0)
    signal_score = signal.get("ai_signal_score", 0.0)

    def score_cell(score):
        pct = int(score * 100)
        if pct < 25:   c = AURA_GREEN
        elif pct < 55: c = AURA_YELLOW
        elif pct < 75: c = AURA_ORANGE
        else:          c = AURA_RED
        return Paragraph(
            f"<font color='white'><b>{pct}%</b></font>",
            ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=11,
                           backColor=c, textColor=colors.white,
                           alignment=TA_CENTER, leading=18),
        )

    rows = [
        [
            Paragraph("<b>Layer</b>", styles["TableHeader"]),
            Paragraph("<b>Raw Score</b>", styles["TableHeader"]),
            Paragraph("<b>Weight</b>", styles["TableHeader"]),
            Paragraph("<b>Weighted Contribution</b>", styles["TableHeader"]),
            Paragraph("<b>Flags</b>", styles["TableHeader"]),
        ],
        [
            Paragraph("Metadata", styles["TableCell"]),
            score_cell(meta_score),
            Paragraph("20%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('metadata_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(metadata.get("flags", []))), styles["TableCell"]),
        ],
        [
            Paragraph("Visual / Frames", styles["TableCell"]),
            score_cell(visual_score),
            Paragraph("20%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('visual_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(visual.get("flags", []))), styles["TableCell"]),
        ],
        [
            Paragraph("Audio Sync", styles["TableCell"]),
            score_cell(audio_score),
            Paragraph("20%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('audio_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(audio.get("flags", []))), styles["TableCell"]),
        ],
        [
            Paragraph("Signal Physics", styles["TableCell"]),
            score_cell(signal_score),
            Paragraph("40%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('signal_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(signal.get("flags", []))), styles["TableCell"]),
        ],
    ]

    table = Table(
        rows,
        colWidths=["25%", "15%", "12%", "28%", "20%"],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AURA_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AURA_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, AURA_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 1), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]),
    )
    elements.append(table)
    return elements


def _build_section(title: str, data: dict, styles, extra_table=None):
    elements = [
        Spacer(1, 2 * mm),
        Paragraph(title, styles["SectionTitle"]),
    ]

    flags = data.get("flags", [])
    if not flags:
        elements.append(Paragraph("No anomalies detected in this layer.", styles["Normal"]))
    else:
        flag_rows = [[
            Paragraph("<b>Type</b>", styles["TableHeader"]),
            Paragraph("<b>Detail</b>", styles["TableHeader"]),
            Paragraph("<b>Severity</b>", styles["TableHeader"]),
        ]]
        for flag in flags:
            severity = flag.get("severity", "INFO")
            sev_color = SEVERITY_COLORS.get(severity, AURA_GRAY)
            flag_rows.append([
                Paragraph(flag.get("type", ""), styles["FlagType"]),
                Paragraph(flag.get("detail", ""), styles["TableCell"]),
                Paragraph(
                    f"<font color='white'><b>{severity}</b></font>",
                    ParagraphStyle("sev", fontName="Helvetica-Bold", fontSize=8,
                                   backColor=sev_color, textColor=colors.white,
                                   alignment=TA_CENTER, leading=14),
                ),
            ])

        flag_table = Table(
            flag_rows,
            colWidths=["30%", "55%", "15%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AURA_LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.3, AURA_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]),
        )
        elements.append(flag_table)

    if extra_table:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("Technical Details", styles["SubSection"]))
        elements.append(extra_table)

    return elements


def _metadata_details_table(details: dict, styles):
    if not details:
        return Paragraph("No metadata details available.", styles["Normal"])
    rows = [[Paragraph(k, styles["TableCell"]), Paragraph(str(v), styles["TableCell"])]
            for k, v in details.items()]
    return Table(
        rows,
        colWidths=["40%", "60%"],
        style=TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [AURA_LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.3, AURA_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ]),
    )


def _anomaly_frames_table(frames: list, styles):
    if not frames:
        return Paragraph("No frame-level anomalies detected.", styles["Normal"])
    rows = [[
        Paragraph("<b>Frame</b>", styles["TableHeader"]),
        Paragraph("<b>Timestamp</b>", styles["TableHeader"]),
        Paragraph("<b>Deepfake Prob.</b>", styles["TableHeader"]),
        Paragraph("<b>Label</b>", styles["TableHeader"]),
    ]]
    for f in frames:
        rows.append([
            Paragraph(str(f.get("frame_index", "")), styles["TableCell"]),
            Paragraph(f"{f.get('timestamp_seconds', 0)}s", styles["TableCell"]),
            Paragraph(f"{int(f.get('deepfake_probability', 0) * 100)}%", styles["TableCell"]),
            Paragraph(f.get("label", ""), styles["TableCell"]),
        ])
    return Table(
        rows,
        colWidths=["20%", "25%", "30%", "25%"],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AURA_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, AURA_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ]),
    )


def _audio_details_table(details: dict, styles):
    return _metadata_details_table(details, styles)


def _build_disclaimer(styles):
    return [
        HRFlowable(width="100%", thickness=1, color=AURA_BORDER),
        Spacer(1, 3 * mm),
        Paragraph("Legal Disclaimer & Methodology", styles["SubSection"]),
        Paragraph(
            "This report is generated by AURA (Advanced Universal Reality Authentication) v0.1 and is provided "
            "for informational and investigative support purposes only. The analysis is based on automated "
            "statistical models and does not constitute legal proof, expert witness testimony, or conclusive "
            "forensic evidence. Results should be reviewed by a qualified digital forensics expert before "
            "being presented in legal proceedings. Scores represent probabilistic assessments; a low risk "
            "score does not guarantee authenticity, and a high risk score does not confirm manipulation. "
            "AURA is not liable for decisions made solely on the basis of this report.",
            styles["Disclaimer"],
        ),
    ]


# ─────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────

def _add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(AURA_GRAY)
    w, h = A4
    canvas.drawString(18 * mm, 12 * mm, "AURA Reality Firewall — Confidential Forensic Report")
    canvas.drawRightString(w - 18 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ─────────────────────────────────────────────
#  Style Definitions
# ─────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()

    def s(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    return {
        "BrandTitle": s("BrandTitle",
            fontName="Helvetica-Bold", fontSize=22,
            textColor=AURA_CYAN, alignment=TA_LEFT, leading=28,
        ),
        "BrandSubtitle": s("BrandSubtitle",
            fontName="Helvetica", fontSize=10,
            textColor=colors.white, alignment=TA_LEFT, leading=16,
        ),
        "MetaInfo": s("MetaInfo",
            fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#424242"),
        ),
        "SectionTitle": s("SectionTitle",
            fontName="Helvetica-Bold", fontSize=12,
            textColor=AURA_DARK, spaceBefore=4, spaceAfter=4,
            borderPad=4,
        ),
        "SubSection": s("SubSection",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=colors.HexColor("#37474F"), spaceBefore=3, spaceAfter=3,
        ),
        "VerdictLabel": s("VerdictLabel",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "VerdictText": s("VerdictText",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=colors.white, leading=20,
        ),
        "TableHeader": s("TableHeader",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=colors.white,
        ),
        "TableCell": s("TableCell",
            fontName="Helvetica", fontSize=8,
            textColor=AURA_DARK, leading=12,
        ),
        "FlagType": s("FlagType",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=AURA_DARK,
        ),
        "Normal": s("NormalAura",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#616161"), leading=14,
        ),
        "Disclaimer": s("Disclaimer",
            fontName="Helvetica", fontSize=7.5,
            textColor=AURA_GRAY, leading=12, alignment=TA_JUSTIFY,
        ),
    }
