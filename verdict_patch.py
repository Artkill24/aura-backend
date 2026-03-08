"""
Applica il nuovo compute_verdict (tiered, 7 livelli + confidence bands) su main.py
Esegui: python3 verdict_patch.py
"""
import re

path = '/home/saad/aura-backend/app/main.py'

with open(path, 'r') as f:
    content = f.read()

# Trova e sostituisce l'intera funzione compute_verdict
new_fn = '''def compute_verdict(metadata: dict, visual: dict, audio: dict, signal: dict, moire: dict, prnu: dict = None) -> dict:
    """
    Pesi v0.5 — Tiered verdicts con confidence bands.

    metadata : 0.10
    visual   : 0.10
    audio    : 0.10
    signal   : 0.35  (physics)
    moire    : 0.10  (screen recording)
    prnu     : 0.25  (sensor fingerprint)
    """
    weights = {"metadata": 0.10, "visual": 0.10, "audio": 0.10, "signal": 0.35, "moire": 0.10, "prnu": 0.25}

    meta_score   = metadata.get("manipulation_score", 0.0)
    visual_score = visual.get("deepfake_probability", 0.0)
    audio_score  = audio.get("sync_anomaly_score", 0.0)
    signal_score = signal.get("ai_signal_score", 0.0)
    moire_score  = moire.get("screen_recording_score", 0.0)
    prnu_score   = prnu.get("prnu_score", 0.0) if prnu else 0.0

    # Shield: azzera signal solo se è vera screen recording (non AI)
    is_screen_recording = moire_score >= 0.5 and prnu_score < 0.4
    if is_screen_recording:
        signal_score = 0.0

    composite = (
        meta_score   * weights["metadata"] +
        visual_score * weights["visual"] +
        audio_score  * weights["audio"] +
        signal_score * weights["signal"] +
        moire_score  * weights["moire"] +
        prnu_score   * weights["prnu"]
    )
    composite = round(composite, 3)

    # Conta layer indipendenti sopra soglia
    layers_flagged = sum([
        meta_score   > 0.30,
        visual_score > 0.40,
        audio_score  > 0.30,
        signal_score > 0.50,
        prnu_score   > 0.50,
    ])

    # Confidence: quanti layer concordano
    if layers_flagged >= 3:
        confidence_level = "HIGH"
        confidence_pct   = min(95, 70 + layers_flagged * 8)
    elif layers_flagged == 2:
        confidence_level = "MEDIUM"
        confidence_pct   = 60
    elif layers_flagged == 1:
        confidence_level = "LOW"
        confidence_pct   = 40
    else:
        confidence_level = "HIGH"
        confidence_pct   = min(95, int((1.0 - composite) * 100))

    # Tiered verdicts — 7 livelli
    if composite < 0.12:
        label = "AUTHENTIC"
        tier  = 1
        color = "green"
        interpretation = "Nessuna anomalia rilevata. Compatibile con registrazione diretta da sensore fisico."
    elif composite < 0.22:
        label = "PROBABLY AUTHENTIC"
        tier  = 2
        color = "green"
        interpretation = "Lievi anomalie (es. compressione social, WhatsApp). Non indicative di manipolazione."
    elif composite < 0.35:
        label = "MINOR EDITS DETECTED"
        tier  = 3
        color = "yellow"
        interpretation = "Tracce di post-produzione o recompressione. Possibile editing innocuo."
    elif composite < 0.50:
        label = "SUSPICIOUS"
        tier  = 4
        color = "yellow"
        interpretation = "Multipli segnali anomali. Richiede revisione manuale prima di accettare come prova."
    elif composite < 0.65:
        label = "LIKELY MANIPULATED"
        tier  = 5
        color = "orange"
        interpretation = "Forte evidenza di manipolazione o generazione AI. Non attendibile come prova primaria."
    elif composite < 0.80:
        label = "HIGHLY LIKELY SYNTHETIC"
        tier  = 6
        color = "red"
        interpretation = "Pattern fortemente indicativi di contenuto generato o alterato da AI."
    else:
        label = "SYNTHETIC / DEEPFAKE"
        tier  = 7
        color = "red"
        interpretation = "Evidenza convergente da layer multipli. Contenuto quasi certamente sintetico."

    return {
        "label": label,
        "tier": tier,
        "composite_score": composite,
        "risk_color": color,
        "confidence": confidence_level,
        "confidence_pct": confidence_pct,
        "layers_flagged": layers_flagged,
        "interpretation": interpretation,
        "breakdown": {
            "metadata_contribution":  round(meta_score   * weights["metadata"], 3),
            "visual_contribution":    round(visual_score * weights["visual"], 3),
            "audio_contribution":     round(audio_score  * weights["audio"], 3),
            "signal_contribution":    round(signal_score * weights["signal"], 3),
            "moire_contribution":     round(moire_score  * weights["moire"], 3),
            "prnu_contribution":      round(prnu_score   * weights["prnu"], 3),
        },
    }'''

# Regex: sostituisce tutto da "def compute_verdict" fino a "def cleanup_file"
pattern = r'def compute_verdict\(.*?\n(?=def cleanup_file)'
new_content = re.sub(pattern, new_fn + '\n\n\n', content, flags=re.DOTALL)

if new_content == content:
    print("ERRORE: pattern non trovato — controlla manualmente")
else:
    with open(path, 'w') as f:
        f.write(new_content)
    print("OK — compute_verdict aggiornato a v0.5 (7 tier + confidence bands)")
