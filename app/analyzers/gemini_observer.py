"""
AURA — Layer 12: Gemini 2.0 Observer (frame-based, no video upload)
"""
import os, json, base64, cv2
import numpy as np
from typing import Dict, Any


async def analyze_with_gemini_observer(video_path: str) -> Dict[str, Any]:
    result = {
        "enabled": False, "is_ai_generated": None, "probability_ai": 0.0,
        "key_observations": [], "forensic_summary": None,
        "recommendation": None, "model_used": None, "error": None,
    }

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        result["error"] = "GOOGLE_API_KEY not set"
        return result

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Estrai 4 frame chiave come immagini
        cap   = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        parts = []
        # Max 3 frame per risparmiare quota Gemini
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        duration = total / fps
        n_frames = 2 if duration > 300 else 3  # max 2 frame per video >5min
        indices = [int(total * i / (n_frames + 1)) for i in range(1, n_frames + 1)]
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                parts.append(types.Part.from_bytes(data=buf.tobytes(), mime_type="image/jpeg"))
        cap.release()

        if not parts:
            result["error"] = "No frames extracted"
            return result

        # Skip per video lunghi su piano free
        fps_check = cap_check = cv2.VideoCapture(video_path)
        tot_check = int(cap_check.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_val = cap_check.get(cv2.CAP_PROP_FPS) or 25
        dur_check = tot_check / fps_val
        cap_check.release()
        if dur_check > 600:  # skip per video >10 min
            result["error"] = f"Video too long ({dur_check:.0f}s) for Gemini free tier"
            return result

        result["enabled"] = True
        parts.append(types.Part.from_text(text="""Analizza questi frame forensicamente.
Cerca: manipolazioni visive, artefatti AI, incoerenze lighting, bordi artificiali.
Rispondi SOLO con JSON:
{"is_ai_generated": true, "probability_ai": 0.85,
 "key_observations": [{"issue": "descrizione", "severity": "high"}],
 "forensic_summary": "Riassunto italiano max 100 parole",
 "recommendation": "Raccomandazione operativa"}"""))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction="Sei un perito forense deepfake.",
                response_mime_type="application/json"
            )
        )

        data = json.loads(response.text.strip())
        result["is_ai_generated"]  = data.get("is_ai_generated")
        result["probability_ai"]   = float(data.get("probability_ai", 0))
        result["key_observations"] = data.get("key_observations", [])[:5]
        result["forensic_summary"] = data.get("forensic_summary", "")
        result["recommendation"]   = data.get("recommendation", "")
        result["model_used"]       = "gemini-2.0-flash (frame-based)"
        result["error"]            = None

    except json.JSONDecodeError as e:
        result["error"] = f"JSON parse error: {str(e)[:80]}"
    except Exception as e:
        result["error"] = str(e)[:200]

    return result
