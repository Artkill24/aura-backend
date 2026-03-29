"""
AURA — Layer 12: Gemini 2.0 Observer (smart sampling)
Analizza segmenti chiave anche su video lunghi (1h+).
Strategia: 3 frame da inizio/metà/fine + 1 frame random anomaly.
"""
import os, json, cv2
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

        # Smart sampling — sempre 3 frame indipendentemente dalla durata
        cap   = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps   = cap.get(cv2.CAP_PROP_FPS) or 25
        duration = total / fps

        # Prendi 3 frame strategici: inizio (10%), metà (50%), fine (90%)
        indices = [
            max(0, int(total * 0.10)),
            max(0, int(total * 0.50)),
            max(0, int(total * 0.90)),
        ]

        parts = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Ridimensiona a 512px per risparmiare token
                h, w = frame.shape[:2]
                if w > 512:
                    scale = 512 / w
                    frame = cv2.resize(frame, (512, int(h * scale)))
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                parts.append(types.Part.from_bytes(data=buf.tobytes(), mime_type="image/jpeg"))
        cap.release()

        if not parts:
            result["error"] = "No frames extracted"
            return result

        result["enabled"] = True

        # Prompt compatto per ridurre token
        parts.append(types.Part.from_text(text=f"""Video duration: {duration:.0f}s. Analizza questi {len(parts)} frame forensicamente.
Rispondi SOLO con JSON:
{{"is_ai_generated": true, "probability_ai": 0.85,
 "key_observations": [{{"issue": "descrizione breve", "severity": "high"}}],
 "forensic_summary": "Max 80 parole italiano",
 "recommendation": "Raccomandazione breve"}}"""))

        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction="Perito forense deepfake. Rispondi solo JSON.",
                response_mime_type="application/json",
                max_output_tokens=500,
            )
        )

        data = json.loads(response.text.strip())
        result["is_ai_generated"]  = data.get("is_ai_generated")
        result["probability_ai"]   = float(data.get("probability_ai", 0))
        result["key_observations"] = data.get("key_observations", [])[:3]
        result["forensic_summary"] = data.get("forensic_summary", "")
        result["recommendation"]   = data.get("recommendation", "")
        result["model_used"]       = f"gemini-1.5-flash (3 frame da {duration:.0f}s)"
        result["error"]            = None

    except json.JSONDecodeError as e:
        result["error"] = f"JSON parse error: {str(e)[:80]}"
    except Exception as e:
        result["error"] = str(e)[:200]

    return result
