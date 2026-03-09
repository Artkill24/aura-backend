"""
Aggiunge chain-of-custody al PDF report di AURA:
- SHA256 hash del file originale
- Timestamp analisi (UTC)
- Versione engine + modelli
- Job ID come identificatore univoco
Esegui: python3 custody_patch.py
"""

path = '/home/saad/aura-backend/app/report/generator.py'

with open(path, 'r') as f:
    content = f.read()

# ── 1. Aggiungi import hashlib e os ──────────────────────────────────────────
if 'import hashlib' not in content:
    content = content.replace(
        'from datetime import datetime',
        'import hashlib\nimport os\nfrom datetime import datetime, timezone'
    )

# ── 2. Aggiungi funzione _compute_file_hash dopo gli import ──────────────────
hash_fn = '''
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

'''

# Inserisci dopo i colori brand
if '_compute_file_hash' not in content:
    content = content.replace(
        '# ─────────────────────────────────────────────\n#  Brand Colors',
        hash_fn + '# ─────────────────────────────────────────────\n#  Brand Colors'
    )

# ── 3. Aggiungi parametro video_path alla firma ───────────────────────────────
content = content.replace(
    'def generate_pdf_report(\n    output_path: str,\n    job_id: str,\n    filename: str,',
    'def generate_pdf_report(\n    output_path: str,\n    job_id: str,\n    filename: str,\n    video_path: str = None,'
)

# ── 4. Calcola hash all'inizio della funzione ─────────────────────────────────
old_doc = '    doc = SimpleDocTemplate('
new_doc = '''    # Chain of custody
    analysis_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    file_hash = _compute_file_hash(video_path) if video_path else {"sha256": "N/A", "md5": "N/A", "size_bytes": 0}

    doc = SimpleDocTemplate('''

if 'analysis_timestamp' not in content:
    content = content.replace(old_doc, new_doc, 1)

# ── 5. Aggiungi sezione chain-of-custody prima della fine del documento ───────
# Cerca il punto dove si chiude lo story (prima di doc.build)
custody_section = '''
    # ── Chain of Custody Section ──────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=AURA_CYAN))
    story.append(Spacer(1, 4 * mm))

    custody_title_style = ParagraphStyle(
        "CustodyTitle",
        parent=styles["Normal"],
        fontName="Courier-Bold",
        fontSize=8,
        textColor=AURA_CYAN,
        spaceAfter=4,
        letterSpacing=2,
    )
    custody_val_style = ParagraphStyle(
        "CustodyVal",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7,
        textColor=colors.HexColor("#888888"),
        spaceAfter=2,
        wordWrap="CJK",
    )

    story.append(Paragraph("CHAIN OF CUSTODY / CERTIFICATE OF ANALYSIS", custody_title_style))
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

    custody_table = Table(
        custody_data,
        colWidths=[38 * mm, 138 * mm],
        hAlign="LEFT",
    )
    custody_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Courier-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Courier"),
        ("FONTSIZE",    (0, 0), (-1, -1), 7),
        ("TEXTCOLOR",   (0, 0), (0, -1), AURA_CYAN),
        ("TEXTCOLOR",   (1, 0), (1, -1), colors.HexColor("#AAAAAA")),
        ("BACKGROUND",  (0, 0), (-1, -1), colors.HexColor("#0A0A14")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#0A0A14"), colors.HexColor("#0D0D1A")]),
        ("TOPPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW",   (0, -1), (-1, -1), 0.3, AURA_CYAN),
    ]))
    story.append(custody_table)
    story.append(Spacer(1, 3 * mm))

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6,
        textColor=colors.HexColor("#555555"),
        spaceAfter=2,
        leading=8,
    )
    story.append(Paragraph(
        "This report was generated automatically by AURA Reality Firewall. "
        "The SHA-256 hash uniquely identifies the analyzed file. "
        "Any modification to the original file will produce a different hash, "
        "invalidating this certificate. This report does not constitute legal advice. "
        "Results should be reviewed by a qualified forensic expert before use in legal proceedings.",
        disclaimer_style
    ))

'''

if 'Chain of Custody' not in content:
    content = content.replace(
        '    doc.build(story)',
        custody_section + '    doc.build(story)'
    )

with open(path, 'w') as f:
    f.write(content)

print("OK — chain-of-custody aggiunto al generator.py")
print("Ora aggiorna main.py per passare video_path a generate_pdf_report")
