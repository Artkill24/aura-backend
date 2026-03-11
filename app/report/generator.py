"""
AURA — PDF Report Generator
Produces a forensic-grade report that a lawyer or insurance expert can print and sign.
Built with ReportLab Platypus for structured, multi-page output.
"""

import hashlib
import os
from datetime import datetime, timezone
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
#  Chain of Custody
# ─────────────────────────────────────────────
AURA_ENGINE_VERSION = "0.5.0"
AURA_MODELS = {
    "visual_a": "dima806/deepfake_vs_real_image_detection",
    "visual_b": "umm-maybe/AI-image-detector",
    "signal":   "AURA-SignalPhysics-v5 (calibrated)",
    "prnu":     "AURA-PRNU-v1 (sensor fingerprint)",
    "moire":    "AURA-Moire-v1 (LCD pixel grid)",
}

def _compute_file_hash(file_path: str) -> dict:
    """Calcola SHA256 e MD5 del file video originale."""
    sha256 = hashlib.sha256()
    md5    = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
                md5.update(chunk)
        return {
            "sha256": sha256.hexdigest(),
            "md5":    md5.hexdigest(),
            "size_bytes": os.path.getsize(file_path),
        }
    except Exception:
        return {"sha256": "N/A", "md5": "N/A", "size_bytes": 0}

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
    vcam: dict = None,
    video_path: str = None,
):
    # Chain of custody
    analysis_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    file_hash = _compute_file_hash(video_path) if video_path else {"sha256": "N/A", "md5": "N/A", "size_bytes": 0}

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
    story += _build_score_table(metadata, visual, audio, signal, verdict, styles, moire=moire, prnu=prnu)
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
    # ── Chain of Custody ──────────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=AURA_CYAN))
    story.append(Spacer(1, 4 * mm))

    custody_title_style = ParagraphStyle(
        "CustodyTitle", parent=styles["Normal"],
        fontName="Courier-Bold", fontSize=8,
        textColor=AURA_CYAN, spaceAfter=4, letterSpacing=2,
    )
    custody_val_style = ParagraphStyle(
        "CustodyVal", parent=styles["Normal"],
        fontName="Courier", fontSize=7,
        textColor=colors.HexColor("#888888"), spaceAfter=2,
    )
    story.append(Paragraph("CHAIN OF CUSTODY  /  CERTIFICATE OF ANALYSIS", custody_title_style))
    story.append(Spacer(1, 2 * mm))

    custody_data = [
        ["Job ID",          job_id],
        ["Timestamp (UTC)", analysis_timestamp],
        ["File",            filename],
        ["SHA-256",         file_hash["sha256"]],
        ["MD5",             file_hash["md5"]],
        ["Size",            f"{file_hash['size_bytes']:,} bytes"],
        ["Engine",          f"AURA Reality Firewall v{AURA_ENGINE_VERSION}"],
        ["Visual Model A",  AURA_MODELS["visual_a"]],
        ["Visual Model B",  AURA_MODELS["visual_b"]],
        ["Signal Layer",    AURA_MODELS["signal"]],
        ["PRNU Layer",      AURA_MODELS["prnu"]],
        ["Moire Layer",     AURA_MODELS["moire"]],
    ]
    custody_table = Table(custody_data, colWidths=[38 * mm, 138 * mm], hAlign="LEFT")
    custody_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Courier-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Courier"),
        ("FONTSIZE",    (0, 0), (-1, -1), 7),
        ("TEXTCOLOR",   (0, 0), (0, -1), AURA_CYAN),
        ("TEXTCOLOR",   (1, 0), (1, -1), colors.HexColor("#AAAAAA")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#0A0A14"), colors.HexColor("#0D0D1A")]),
        ("TOPPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW",   (0, -1), (-1, -1), 0.3, AURA_CYAN),
    ]))
    story.append(custody_table)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "This report was generated automatically by AURA Reality Firewall. "
        "The SHA-256 hash uniquely identifies the analyzed file. "
        "Any modification to the original file will produce a different hash, "
        "invalidating this certificate. Results should be reviewed by a qualified "
        "forensic expert before use in legal proceedings.",
        ParagraphStyle("Disc", parent=styles["Normal"], fontName="Courier",
                       fontSize=6, textColor=colors.HexColor("#555555"), leading=8)
    ))

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


def _build_score_table(metadata, visual, audio, signal, verdict, styles, moire=None, prnu=None):
    elements = [Paragraph("Score Breakdown", styles["SectionTitle"])]

    breakdown = verdict.get("breakdown", {})
    meta_score   = metadata.get("manipulation_score", 0.0)
    visual_score = visual.get("deepfake_probability", 0.0)
    audio_score  = audio.get("sync_anomaly_score", 0.0)
    signal_score = signal.get("ai_signal_score", 0.0)
    moire_score  = moire.get("screen_recording_score", 0.0) if moire else 0.0
    prnu_score   = prnu.get("prnu_score", 0.0) if prnu else 0.0

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
            Paragraph("35%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('signal_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(signal.get("flags", []))), styles["TableCell"]),
        ],
        [
            Paragraph("Moire / Screen", styles["TableCell"]),
            score_cell(moire_score),
            Paragraph("10%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('moire_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(moire.get("flags", [])) if moire else 0), styles["TableCell"]),
        ],
        [
            Paragraph("PRNU Sensor", styles["TableCell"]),
            score_cell(prnu_score),
            Paragraph("25%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('prnu_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(prnu.get("flags", [])) if prnu else 0), styles["TableCell"]),
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
            "This report is generated by AURA Reality Firewall v0.5.0 and is provided "
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
