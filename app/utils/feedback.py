"""
AURA — Adaptive Feedback Loop
Salva feedback utente su Supabase + refinement prompt automatico via Groq.
"""
import os, json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vtqrojazozbqbhgozbor.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0cXJvamF6b3picWJoZ296Ym9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NjIzNDMsImV4cCI6MjA4OTUzODM0M30.5oGA-s21e-JkN1faCVupinwxwC1bheuKppbFUvWZv5g")


def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def save_feedback(
    job_id: str,
    feedback: str,  # 'correct' | 'incorrect' | 'partial'
    verdict_label: str = "",
    composite_score: float = 0.0,
    origin_verdict: str = "",
    attack_vector: str = "",
    comment: str = "",
) -> Dict[str, Any]:
    result = {"saved": False, "error": None, "trigger_refinement": False}
    try:
        sb = get_supabase()
        sb.table("aura_feedback").insert({
            "job_id":          job_id,
            "feedback":        feedback,
            "verdict_label":   verdict_label,
            "composite_score": composite_score,
            "origin_verdict":  origin_verdict,
            "attack_vector":   attack_vector,
            "comment":         comment,
        }).execute()
        result["saved"] = True

        # Conta feedback totali — ogni 20 triggera refinement
        count_res = sb.table("aura_feedback").select("id", count="exact").execute()
        total = count_res.count or 0
        if total > 0 and total % 20 == 0:
            result["trigger_refinement"] = True

    except Exception as e:
        result["error"] = str(e)
    return result


def get_prompt_version() -> Dict[str, Any]:
    """Recupera il prompt corrente per Layer 10."""
    try:
        sb = get_supabase()
        res = sb.table("aura_prompt_versions").select("*").order("version", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return {"version": 1, "prompt_text": "", "feedback_count": 0}


def run_prompt_refinement() -> Dict[str, Any]:
    """
    Invia batch di feedback a Groq e aggiorna il prompt base per Layer 10.
    Chiamato automaticamente ogni 20 feedback.
    """
    result = {"refined": False, "new_version": None, "error": None}
    try:
        sb = get_supabase()

        # Prendi ultimi 20 feedback
        feedbacks = sb.table("aura_feedback").select("*").order("created_at", desc=True).limit(20).execute()
        if not feedbacks.data or len(feedbacks.data) < 5:
            result["error"] = "Not enough feedback yet"
            return result

        # Prompt corrente
        current = get_prompt_version()

        # Crea batch per Groq
        batch_text = "\n".join([
            f"- JobID: {f['job_id'][:8]} | Verdict: {f['verdict_label']} | Origin: {f['origin_verdict']} | Score: {f['composite_score']:.0%} | Feedback: {f['feedback']} | Comment: {f.get('comment','')}"
            for f in feedbacks.data
        ])

        refinement_prompt = f"""Sei il sistema di auto-miglioramento di AURA, un tool forense per deepfake detection.

Prompt attuale per Layer 10 (Generative Origin Detector):
"{current['prompt_text'][:500]}"

Ultimi {len(feedbacks.data)} feedback utenti reali:
{batch_text}

Analizza i pattern di errore (feedback 'incorrect' o 'partial') e genera un prompt migliorato per il Layer 10.
Il nuovo prompt deve:
1. Correggere i falsi positivi/negativi più comuni
2. Essere più preciso nel distinguere AI-generated da manuale
3. Restare conciso (max 300 parole)

Rispondi SOLO con il nuovo testo del prompt, niente altro."""

        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": refinement_prompt}],
            max_tokens=400,
            temperature=0.4,
        )
        new_prompt = response.choices[0].message.content.strip()

        # Salva nuova versione
        new_version = current["version"] + 1
        sb.table("aura_prompt_versions").insert({
            "version":       new_version,
            "prompt_text":   new_prompt,
            "feedback_count": len(feedbacks.data),
        }).execute()

        result["refined"]     = True
        result["new_version"] = new_version

    except Exception as e:
        result["error"] = str(e)
    return result
