"""
AURA — AI Forensic Narrative (Groq + Llama-3.3-70B)
Genera conclusione forense in linguaggio legale naturale.
"""
import os
from typing import Dict, Any


def generate_forensic_narrative(
    verdict: dict,
    metadata: dict,
    visual: dict,
    audio: dict,
    signal: dict,
    moire: dict,
    prnu: dict,
    vcam: dict,
    rppg: dict,
    forensic: dict,
    language: str = "it"
) -> Dict[str, Any]:

    result = {"narrative": None, "model": None, "error": None}

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        result["error"] = "GROQ_API_KEY not set"
        return result

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        # Raccogli dati chiave
        composite  = verdict.get("composite_score", 0)
        label      = verdict.get("label", "N/A")
        confidence = verdict.get("confidence", "N/A")
        attack_vec = forensic.get("attack_vector", "UNKNOWN")
        rppg_q     = rppg.get("signal_quality", "N/A") if rppg else "N/A"
        rppg_bpm   = rppg.get("bpm_detected") if rppg else None
        prnu_s     = prnu.get("prnu_score", 0) if prnu else 0
        moire_s    = moire.get("screen_recording_score", 0) if moire else 0
        signal_s   = signal.get("ai_signal_score", 0)
        vcam_s     = vcam.get("virtual_cam_score", 0) if vcam else 0
        audio_s    = audio.get("sync_anomaly_score", 0)

        # Flags rilevanti
        all_flags = []
        for src in [metadata, visual, audio, signal, moire or {}, prnu or {}, vcam or {}, rppg or {}]:
            for f in src.get("flags", []):
                if f.get("severity") in ("HIGH", "MEDIUM"):
                    all_flags.append(f.get("detail", ""))
        flags_text = "\n".join(f"- {f}" for f in all_flags[:8]) or "Nessun flag critico"

        if language == "it":
            system_prompt = (
                "Sei un perito forense digitale certificato, esperto in analisi di deepfake e manipolazioni video. "
                "Scrivi conclusioni forensi in italiano tecnico-legale, chiaro e diretto. "
                "Usa un tono professionale, cita i layer rilevanti, e fornisci sempre una raccomandazione operativa. "
                "Massimo 200 parole. Non usare markdown, solo testo semplice."
            )
            user_prompt = f"""Analizza questi risultati forensi e scrivi una conclusione professionale:

VERDETTO: {label} (Score composito: {composite:.1%}, Confidenza: {confidence})
VETTORE DI ATTACCO: {attack_vec.replace('_', ' ')}

LAYER SCORES:
- Signal Physics: {signal_s:.1%} (anomalie compressione)
- PRNU Sensore: {prnu_s:.1%} (fingerprint dispositivo)
- Moiré Screen: {moire_s:.1%} (registrazione schermo)
- Virtual Cam: {vcam_s:.1%} (iniezione virtuale)
- Audio Sync: {audio_s:.1%} (discrepanza audio-video)
- rPPG Cardiaco: qualità={rppg_q}, BPM={rppg_bpm}

FLAG CRITICI RILEVATI:
{flags_text}

Scrivi la conclusione forense (max 200 parole) con: analisi tecnica, vettore d'attacco probabile, e raccomandazione legale."""

        else:
            system_prompt = (
                "You are a certified digital forensics expert specializing in deepfake and video manipulation analysis. "
                "Write forensic conclusions in clear technical-legal English. "
                "Be professional, cite relevant layers, always provide an operational recommendation. "
                "Maximum 200 words. Plain text only, no markdown."
            )
            user_prompt = f"""Analyze these forensic results and write a professional conclusion:

VERDICT: {label} (Composite Score: {composite:.1%}, Confidence: {confidence})
ATTACK VECTOR: {attack_vec.replace('_', ' ')}

LAYER SCORES:
- Signal Physics: {signal_s:.1%}
- PRNU Sensor: {prnu_s:.1%}
- Moiré Screen: {moire_s:.1%}
- Virtual Cam: {vcam_s:.1%}
- Audio Sync: {audio_s:.1%}
- rPPG Cardiac: quality={rppg_q}, BPM={rppg_bpm}

CRITICAL FLAGS:
{flags_text}

Write the forensic conclusion (max 200 words) with: technical analysis, probable attack vector, legal recommendation."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.3,
        )

        narrative = response.choices[0].message.content.strip()
        result["narrative"] = narrative
        result["model"] = "llama-3.3-70b-versatile (Groq)"

    except Exception as e:
        result["error"] = str(e)

    return result
