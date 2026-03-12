"""
AURA — Forensic Inference Engine
Correlazione cross-layer: ragiona sulle combinazioni di segnali
e genera conclusioni forensi come un perito umano.
"""
from typing import Dict, Any


def get_forensic_conclusion(
    metadata: dict,
    visual: dict,
    audio: dict,
    signal: dict,
    moire: dict,
    prnu: dict,
    vcam: dict,
    rppg: dict,
    verdict: dict,
) -> Dict[str, Any]:

    # Estrai score
    meta_s   = metadata.get("manipulation_score", 0.0)
    visual_s = visual.get("deepfake_probability", 0.0)
    audio_s  = audio.get("sync_anomaly_score", 0.0)
    signal_s = signal.get("ai_signal_score", 0.0)
    moire_s  = moire.get("screen_recording_score", 0.0) if moire else 0.0
    prnu_s   = prnu.get("prnu_score", 0.0) if prnu else 0.0
    vcam_s   = vcam.get("virtual_cam_score", 0.0) if vcam else 0.0
    rppg_s   = rppg.get("rppg_score", 0.0) if rppg else 0.0
    rppg_q   = rppg.get("signal_quality", "N/A") if rppg else "N/A"
    bpm      = rppg.get("bpm_detected") if rppg else None
    composite = verdict.get("composite_score", 0.0)

    conclusions = []
    attack_vector = "UNKNOWN"
    confidence = "MEDIUM"

    # ── Pattern 1: Replay Attack (schermo fisico + virtual cam) ──────────────
    if moire_s >= 0.5 and vcam_s >= 0.4:
        conclusions.append(
            "REPLAY ATTACK RILEVATO: Il video mostra pattern di griglia LCD (Moiré) "
            "combinati con assenza di rumore sensore fisico. Il flusso è quasi certamente "
            "una ripresa fisica di uno schermo che emula una webcam (es. telefono che riprende monitor)."
        )
        attack_vector = "REPLAY_ATTACK"
        confidence = "HIGH"

    # ── Pattern 2: Deepfake con virtual cam injection ─────────────────────────
    if vcam_s >= 0.5 and rppg_s >= 0.6 and moire_s < 0.4:
        conclusions.append(
            "INIEZIONE VIRTUALE CON VOLTO SINTETICO: Rilevata assenza di rumore sensore fisico "
            "(Virtual Cam) e mancanza di segnale cardiaco biologico (rPPG). "
            "Pattern coerente con tool di deepfake real-time (Deep-Live-Cam, OBS + AI face swap)."
        )
        attack_vector = "VIRTUAL_CAM_DEEPFAKE"
        confidence = "HIGH"

    # ── Pattern 3: Post-production deepfake ──────────────────────────────────
    if signal_s >= 0.6 and prnu_s >= 0.5 and rppg_s >= 0.7:
        conclusions.append(
            "MANIPOLAZIONE POST-PRODUZIONE: Anomalie nei pattern di compressione (Signal Physics) "
            "e fingerprint sensore incoerente (PRNU) suggeriscono alterazione digitale del video originale. "
            "L'assenza di segnale cardiaco biologico (rPPG) conferma sostituzione facciale (Inpainting/Deepfake)."
        )
        attack_vector = "POST_PRODUCTION_DEEPFAKE"
        confidence = "HIGH"

    # ── Pattern 4: AI-generated synthetic video ───────────────────────────────
    if visual_s >= 0.5 and rppg_s >= 0.7 and signal_s >= 0.5:
        conclusions.append(
            "VIDEO SINTETICO AI: I modelli di analisi visiva rilevano pattern di generazione artificiale. "
            "L'assenza di pulsazione biologica (rPPG) e le anomalie nei blocchi di compressione "
            "sono coerenti con video generato interamente da AI (Sora, Runway, HeyGen o simili)."
        )
        attack_vector = "AI_GENERATED"
        confidence = "HIGH"

    # ── Pattern 5: Metadata stripping (WhatsApp/Telegram relay) ──────────────
    if meta_s < 0.1 and composite < 0.3 and prnu_s < 0.3:
        conclusions.append(
            "METADATI RIMOSSI — ORIGINE INCERTA: Il file è privo di firma dispositivo e metadati EXIF. "
            "Questo è comune con video condivisi tramite app di messaggistica (WhatsApp, Telegram) "
            "che rimuovono automaticamente i metadati. Non costituisce prova di manipolazione."
        )
        attack_vector = "METADATA_STRIPPED"
        confidence = "LOW"

    # ── Pattern 6: Screen recording legittimo ────────────────────────────────
    if moire_s >= 0.5 and prnu_s < 0.3 and vcam_s < 0.3 and composite < 0.4:
        conclusions.append(
            "SCREEN RECORDING: Il pattern Moiré indica registrazione da schermo fisico, "
            "ma l'assenza di altri segnali di manipolazione suggerisce una registrazione legittima "
            "(es. tutorial, condivisione schermo). Non rilevati segnali di deepfake o injection."
        )
        attack_vector = "SCREEN_RECORDING_LEGIT"
        confidence = "MEDIUM"

    # ── Pattern 7: Audio-video desync (dubbing/lip-sync AI) ──────────────────
    if audio_s >= 0.5 and visual_s >= 0.3:
        conclusions.append(
            "ANOMALIA AUDIO-VIDEO: Rilevata discrepanza nella sincronizzazione audio-video. "
            "Pattern coerente con sostituzione della traccia audio (voice cloning) "
            "o lip-sync AI applicato post-produzione."
        )
        if attack_vector == "UNKNOWN":
            attack_vector = "AUDIO_MANIPULATION"

    # ── Pattern 8: Weak signal — inconcludente ────────────────────────────────
    if not conclusions:
        if composite >= 0.35:
            conclusions.append(
                "ANOMALIE ISOLATE NON CONVERGENTI: Rilevate irregolarità in layer singoli "
                "senza pattern di correlazione chiaro. Il contenuto presenta caratteristiche "
                "atipiche ma insufficienti per determinare il vettore di attacco con certezza. "
                "Si raccomanda revisione manuale dei frame anomali."
            )
            attack_vector = "INCONCLUSIVE"
        else:
            conclusions.append(
                "NESSUN PATTERN DI MANIPOLAZIONE RILEVATO: I layer di analisi non mostrano "
                "correlazioni significative. Il contenuto presenta caratteristiche coerenti "
                "con un video organico. La probabilità di manipolazione è bassa."
            )
            attack_vector = "AUTHENTIC"
            confidence = "HIGH"

    # ── Raccomandazione operativa ─────────────────────────────────────────────
    recommendations = []
    if composite >= 0.65:
        recommendations.append("Sospendere immediatamente qualsiasi procedura basata su questo contenuto.")
        recommendations.append("Richiedere video originale da fonte primaria con metadati intatti.")
        recommendations.append("Inviare a laboratorio forense certificato per analisi approfondita.")
    elif composite >= 0.35:
        recommendations.append("Verificare l'identità del mittente tramite canale secondario indipendente.")
        recommendations.append("Richiedere conferma video in diretta con challenge visivo (es. mostrare oggetto specifico).")
    else:
        recommendations.append("Nessuna azione urgente richiesta. Archiviare il report come documentazione.")

    # rPPG summary
    rppg_summary = None
    if rppg_q == "ABSENT":
        rppg_summary = f"Nessuna pulsazione biologica rilevata (SNR critico). BPM stimato: {bpm} — fuori range fisiologico."
    elif rppg_q == "WEAK":
        rppg_summary = f"Segnale cardiaco debole o inconsistente. BPM stimato: {bpm}."
    elif rppg_q == "PRESENT" and bpm:
        rppg_summary = f"Segnale cardiaco presente. BPM stimato: {bpm} — nel range fisiologico normale."

    return {
        "attack_vector": attack_vector,
        "confidence": confidence,
        "conclusions": conclusions,
        "recommendations": recommendations,
        "rppg_summary": rppg_summary,
    }
