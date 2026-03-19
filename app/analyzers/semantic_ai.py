"""
AURA — Semantic AI + Generative Origin Detector (Layer 10)
Usa Groq Llama-3.3-70B per analisi semantica + rilevamento origine generativa.
Distingue: AI-PRODUCED (Sora/Kling/Veo/Runway) vs MANUAL/EDITED vs SCREEN-RECORDED.
"""
import os, base64, json, cv2
from typing import Dict, Any, List


def extract_keyframes(video_path: str, n_frames: int = 8) -> List[str]:
    """Estrai N frame chiave come base64 JPEG."""
    frames_b64 = []
    try:
        cap   = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        intervals = [int(total * i / (n_frames + 1)) for i in range(1, n_frames + 1)]
        for idx in intervals:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frames_b64.append(base64.b64encode(buf).decode())
        cap.release()
    except Exception:
        pass
    return frames_b64


def describe_frames_visually(frames_b64: List[str]) -> str:
    """Genera descrizione testuale dei frame per il prompt (senza vision API)."""
    descriptions = []
    for i, b64 in enumerate(frames_b64[:6]):
        try:
            import numpy as np
            data = base64.b64decode(b64)
            arr  = np.frombuffer(data, np.uint8)
            img  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            h, w = img.shape[:2]

            # Analisi base del frame
            gray      = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur      = cv2.Laplacian(gray, cv2.CV_64F).var()
            brightness = gray.mean()
            hsv       = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            sat_mean  = hsv[:,:,1].mean()
            sat_std   = hsv[:,:,1].std()

            # Edge density
            edges     = cv2.Canny(gray, 50, 150)
            edge_dens = edges.mean()

            desc = (
                f"Frame {i+1}/{len(frames_b64)}: "
                f"res={w}x{h}, "
                f"sharpness={blur:.1f}({'sharp' if blur>100 else 'soft/blurry'}), "
                f"brightness={brightness:.0f}({'normal' if 40<brightness<200 else 'abnormal'}), "
                f"saturation={sat_mean:.0f}±{sat_std:.0f}({'vivid' if sat_mean>80 else 'flat/grey'}), "
                f"edge_density={edge_dens:.1f}({'rich_detail' if edge_dens>15 else 'smooth_areas'})"
            )
            descriptions.append(desc)
        except Exception as e:
            descriptions.append(f"Frame {i+1}: analysis_error={str(e)[:50]}")

    return "\n".join(descriptions)


def analyze_generative_origin(
    video_path: str,
    layer_scores: dict = None,
    language: str = "it",
) -> Dict[str, Any]:
    """
    Layer 10 — Generative Origin Detector.
    Determina se il video è AI-generated (Sora/Kling/Veo/Runway/Luma)
    o manuale/editato da umano.
    """
    result = {
        "is_ai_generated":    None,
        "probability_ai":     None,
        "probability_manual": None,
        "origin_verdict":     None,
        "key_reasons":        [],
        "generative_score":   0.35,
        "model_used":         None,
        "error":              None,
    }

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        result["error"] = "GROQ_API_KEY not set"
        return result

    layer_scores = layer_scores or {}
    frames_b64   = extract_keyframes(video_path, n_frames=8)
    frame_desc   = describe_frames_visually(frames_b64)

    scores_text = "\n".join([
        f"- {k}: {v:.1%}" for k, v in layer_scores.items()
        if isinstance(v, float)
    ])

    system_prompt = (
        "Sei un esperto forense digitale specializzato nel rilevamento di video generati da AI "
        "(Sora, Kling, Veo 2, Runway Gen-3, Luma Dream Machine, Pika, HeyGen). "
        "Analizzi caratteristiche visive per distinguere contenuto AI-generato da contenuto umano reale. "
        "Rispondi SOLO con un JSON valido, nessun testo aggiuntivo."
    )

    user_prompt = f"""Analizza questo video forensemente e determina se è AI-generato o reale.

ANALISI FRAME (campionamento automatico):
{frame_desc}

SCORE LAYER AURA (9 layer forensi):
{scores_text}

Considera questi segnali tipici di AI-generated video:
- TEMPORALI: movimenti innaturalmente fluidi o jerky, fisica irrealistica
- VISIVI: sharpness troppo uniforme, dettagli ripetitivi, texture plastiche
- LIGHTING: illuminazione perfetta e statica, ombre inconsistenti
- EDGES: blending artificiale, contorni troppo netti o troppo morbidi
- COMPRESSION: block uniformity anomala (Signal Physics alto), zero rumore sensore (PRNU basso)
- rPPG: assenza segnale cardiaco biologico = nessun soggetto reale in scena
- SEMANTICO: contesto visivo incoerente, background artificiale

Segnali di video MANUALE/REALE:
- Grain naturale, micro-sfocatura, rumore sensore organico
- Illuminazione variabile e realistica
- Movimenti umani naturali con imperfezioni
- Metadati dispositivo presenti

Rispondi ESATTAMENTE in questo formato JSON (nessun testo fuori dal JSON):
{{
  "is_ai_generated": true,
  "probability_ai": 0.85,
  "probability_manual": 0.15,
  "origin_verdict": "AI-PRODUCED",
  "generative_tool_likely": "Sora/Kling/Veo (high motion AI)",
  "key_reasons": [
    "Signal Physics 72% indica compressione artificiale uniforme",
    "rPPG assente: nessun segnale biologico — soggetto non reale",
    "PRNU 72%: fingerprint sensore assente — non acquisito da camera fisica",
    "Frame sharpness innaturalmente uniforme tra tutti i campioni",
    "Saturazione colore eccessivamente vivida e piatta"
  ],
  "confidence": "HIGH"
}}

origin_verdict deve essere: "AI-PRODUCED" o "MANUAL/EDITED" o "SCREEN-RECORDED" o "UNCERTAIN"
generative_tool_likely: indica il tool AI probabile o "Unknown AI tool" o "Real camera"
"""

    try:
        from groq import Groq
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw  = response.choices[0].message.content.strip()
        data = json.loads(raw)

        result["is_ai_generated"]    = data.get("is_ai_generated", False)
        result["probability_ai"]     = float(data.get("probability_ai", 0.5))
        result["probability_manual"] = float(data.get("probability_manual", 0.5))
        result["origin_verdict"]     = data.get("origin_verdict", "UNCERTAIN")
        result["generative_tool"]    = data.get("generative_tool_likely", "Unknown")
        result["key_reasons"]        = data.get("key_reasons", [])[:5]
        result["confidence"]         = data.get("confidence", "MEDIUM")
        result["model_used"]         = "llama-3.3-70b-versatile (Groq)"
        result["error"]              = None

        # Calcola generative_score per peso nel composite
        prob_ai = result["probability_ai"]
        if result["origin_verdict"] == "AI-PRODUCED":
            result["generative_score"] = min(0.95, prob_ai * 1.1)
        elif result["origin_verdict"] == "MANUAL/EDITED":
            result["generative_score"] = max(0.05, prob_ai * 0.5)
        elif result["origin_verdict"] == "SCREEN-RECORDED":
            result["generative_score"] = 0.20
        else:
            result["generative_score"] = 0.40

    except json.JSONDecodeError as e:
        result["error"] = f"JSON parse error: {str(e)[:100]}"
        result["generative_score"] = 0.35
    except Exception as e:
        result["error"] = str(e)[:200]
        result["generative_score"] = 0.35

    return result


def analyze_semantic(
    video_path: str,
    url: str = "",
    video_info: dict = None,
    layer_scores: dict = None,
    language: str = "it",
) -> Dict[str, Any]:
    """Analisi semantica contestuale (per /analyze-link)."""
    result = {
        "semantic_verdict": None,
        "model_used":       None,
        "error":            None,
    }

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        result["error"] = "GROQ_API_KEY not set"
        return result

    video_info   = video_info or {}
    layer_scores = layer_scores or {}
    scores_text  = "\n".join([f"- {k}: {v:.1%}" for k, v in layer_scores.items() if isinstance(v, float)])

    if language == "it":
        system = (
            "Sei un analista forense video senior specializzato in deepfake e manipolazione mediatica. "
            "Rispondi SOLO in italiano tecnico-legale. Max 200 parole."
        )
        user_prompt = f"""Analisi forense video:
URL: {url or 'upload locale'}
Titolo: {video_info.get('title', 'N/A')}
Piattaforma: {video_info.get('platform', 'N/A')}
Durata: {video_info.get('duration', 0)}s

SCORE LAYER AURA:
{scores_text}

Fornisci:
1. Tipo di manipolazione visiva rilevata
2. Coerenza narrativa/contestuale
3. Probabilità disinformazione/deepfake (%)
4. Raccomandazione legale (ammissibile/non ammissibile/verificare)"""
    else:
        system = (
            "You are a senior video forensic analyst. "
            "Reply ONLY in technical-legal English. Max 200 words."
        )
        user_prompt = f"""Video forensic analysis:
URL: {url or 'local upload'}
Title: {video_info.get('title', 'N/A')}
Platform: {video_info.get('platform', 'N/A')}
Duration: {video_info.get('duration', 0)}s

AURA LAYER SCORES:
{scores_text}

Provide:
1. Visual manipulation type detected
2. Narrative/contextual coherence
3. Disinformation/deepfake probability (%)
4. Legal recommendation"""

    try:
        from groq import Groq
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        result["semantic_verdict"] = response.choices[0].message.content.strip()
        result["model_used"]       = "llama-3.3-70b-versatile (Groq)"
        result["error"]            = None
    except Exception as e:
        result["error"] = str(e)[:200]

    return result
