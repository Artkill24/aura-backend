"""
Aggiunge PRNU e Moire alla tabella Score Breakdown nel PDF.
Esegui: python3 breakdown_patch.py
"""
path = '/home/saad/aura-backend/app/report/generator.py'

with open(path, 'r') as f:
    content = f.read()

# 1. Aggiorna firma funzione
content = content.replace(
    'def _build_score_table(metadata, visual, audio, signal, verdict, styles):',
    'def _build_score_table(metadata, visual, audio, signal, verdict, styles, moire=None, prnu=None):'
)

# 2. Aggiunge score moire e prnu dopo signal_score
content = content.replace(
    '    signal_score = signal.get("ai_signal_score", 0.0)\n    def score_cell',
    '    signal_score = signal.get("ai_signal_score", 0.0)\n    moire_score  = moire.get("screen_recording_score", 0.0) if moire else 0.0\n    prnu_score   = prnu.get("prnu_score", 0.0) if prnu else 0.0\n    def score_cell'
)

# 3. Aggiorna pesi Signal Physics da 40% a 35%
content = content.replace(
    '            Paragraph("40%", styles["TableCell"]),\n            Paragraph(f"{breakdown.get(\'signal_contribution\', 0):.3f}", styles["TableCell"]),\n            Paragraph(str(len(signal.get("flags", []))), styles["TableCell"]),',
    '            Paragraph("35%", styles["TableCell"]),\n            Paragraph(f"{breakdown.get(\'signal_contribution\', 0):.3f}", styles["TableCell"]),\n            Paragraph(str(len(signal.get("flags", []))), styles["TableCell"]),'
)

# 4. Aggiunge righe Moire e PRNU prima della chiusura rows
old_rows_end = '''        [
            Paragraph("Signal Physics", styles["TableCell"]),
            score_cell(signal_score),
            Paragraph("35%", styles["TableCell"]),
            Paragraph(f"{breakdown.get('signal_contribution', 0):.3f}", styles["TableCell"]),
            Paragraph(str(len(signal.get("flags", []))), styles["TableCell"]),
        ],
    ]'''

new_rows_end = '''        [
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
    ]'''

content = content.replace(old_rows_end, new_rows_end)

# 5. Aggiorna chiamata a _build_score_table nel corpo principale
content = content.replace(
    'story += _build_score_table(metadata_result, visual_result, audio_result, signal_result, verdict, styles)',
    'story += _build_score_table(metadata_result, visual_result, audio_result, signal_result, verdict, styles, moire=moire_result, prnu=prnu_result)'
)

# Fallback se usa variabili senza _result
content = content.replace(
    'story += _build_score_table(metadata, visual, audio, signal, verdict, styles)',
    'story += _build_score_table(metadata, visual, audio, signal, verdict, styles, moire=moire, prnu=prnu)'
)

with open(path, 'w') as f:
    f.write(content)
print("Done — PRNU e Moire aggiunti alla Score Breakdown table")
