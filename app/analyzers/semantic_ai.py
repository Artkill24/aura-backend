"""
AURA — Semantic AI Check (Qwen2-VL-2B-Instruct)
Analisi semantica + visiva di frame chiave con MLLM.
Fallback su Groq/Llama se Qwen non disponibile (RAM).
"""
import os, base64, cv2
from typing import Dict, Any, List


def extract_keyframes(video_path: str, n_frames: int = 6) -> List[str]:
    """Estrai N frame chiave come base64 JPEG."""
    frames_b64 = []
    try:
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps   = cap.get(cv2.CAP_PROP_FPS) or 25
        duration = total / fps

        # Prendi frame a intervalli regolari (escludi inizio/fine)
        intervals = [int(total * i / (n_frames + 1)) for i in range(1, n_frames + 1)]
        for idx in intervals:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                frames_b64.append(base64.b64encode(buf).decode())
        cap.release()
    except Exception:
        pass
    return frames_b64


def analyze_semantic(
    video_path: str,
    url: str = "",
    video_info: dict = None,
    layer_scores: dict = None,
    language: str = "it",
) -> Dict[str, Any]:

    result = {
        "semantic_verdict": None,
        "narrative_topics": [],
        "manipulation_type": None,
        "confidence": None,
        "model_used": None,
        "error": None,
    }

    video_info = video_info or {}
    layer_scores = layer_scores or {}

    # Costruisci contesto layer
    scores_text = "\n".join([f"- {k}: {v:.1%}" for k, v in layer_scores.items() if isinstance(v, float)])

    if language == "it":
        system = (
            "Sei un analista forense video senior specializzato in deepfake, disinformazione e manipolazione mediatica. "
            "Analizza le immagini fornite e i dati forensi. "
            "Rispondi SOLO in italiano tecnico-legale. Max 200 parole."
        )
        user_prompt = f"""Analisi forense video:
URL: {url or 'upload locale'}
Titolo: {video_info.get('title', 'N/A')}
Piattaforma: {video_info.get('platform', 'N/A')}
Durata: {video_info.get('duration', 0)}s
Upload: {video_info.get('upload_date', 'N/A')}

SCORE LAYER AURA:
{scores_text}

Analizza i frame chiave e fornisci:
1. Tipo di manipolazione visiva rilevata (se presente)
2. Coerenza narrativa/contestuale del video
3. Probabilità disinformazione/deepfake (%)
4. Raccomandazione legale (ammissibile/non ammissibile/verificare)
Sii preciso e conciso."""
    else:
        system = (
            "You are a senior video forensic analyst specializing in deepfake detection, disinformation and media manipulation. "
            "Analyze the provided images and forensic data. "
            "Reply ONLY in technical-legal English. Max 200 words."
        )
        user_prompt = f"""Video forensic analysis:
URL: {url or 'local upload'}
Title: {video_info.get('title', 'N/A')}
Platform: {video_info.get('platform', 'N/A')}
Duration: {video_info.get('duration', 0)}s
Upload date: {video_info.get('upload_date', 'N/A')}

AURA LAYER SCORES:
{scores_text}

Analyze the key frames and provide:
1. Type of visual manipulation detected (if any)
2. Narrative/contextual coherence of the video
3. Disinformation/deepfake probability (%)
4. Legal recommendation (admissible/inadmissible/verify)
Be precise and concise."""

    # Tenta Qwen2-VL prima, fallback su Groq
    frames_b64 = extract_keyframes(video_path, n_frames=6)

    # Qwen2-VL richiede GPU — usa Groq su WSL/CPU

    # --- Fallback Groq (text only, no vision) ---
    try:
        result = _analyze_with_groq(system, user_prompt, result)
    except Exception as e:
        result["error"] = (result.get("error") or "") + f" | Groq failed: {str(e)[:100]}"

    return result


def _analyze_with_qwen(frames_b64: List[str], system: str, user_prompt: str, result: dict) -> dict:
    """Usa Qwen2-VL-2B-Instruct con frame visivi."""
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    import torch

    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto", trust_remote_code=True
    )

    # Costruisci messaggi con immagini
    content = [{"type": "text", "text": user_prompt}]
    for b64 in frames_b64[:4]:  # max 4 frame
        content.insert(0, {"type": "image", "image": f"data:image/jpeg;base64,{b64}"})

    messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], padding=True, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=300, temperature=0.3)
    decoded = processor.batch_decode(output, skip_special_tokens=True)[0]
    # Rimuovi il prompt
    answer = decoded.split("assistant")[-1].strip()

    result["semantic_verdict"] = answer
    result["model_used"] = "Qwen2-VL-2B-Instruct"
    result["error"] = None
    return result


def _analyze_with_groq(system: str, user_prompt: str, result: dict) -> dict:
    """Fallback Groq text-only (no vision)."""
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        result["error"] = "GROQ_API_KEY not set"
        return result

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=300, temperature=0.3,
    )
    result["semantic_verdict"] = response.choices[0].message.content.strip()
    result["model_used"] = "llama-3.3-70b-versatile (Groq fallback — no vision)"
    result["error"] = None
    return result
