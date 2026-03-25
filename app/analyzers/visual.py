"""
AURA — Visual Layer (HF Inference API)
Dual-model deepfake detection via HuggingFace Inference API.
Zero RAM — chiamata HTTP esterna.
"""
import os, base64, cv2
import numpy as np
from typing import Dict, Any


HF_TOKEN   = os.environ.get("HF_TOKEN", "")
MODEL_A    = "dima806/deepfake_vs_real_image_detection"
MODEL_B    = "umm-maybe/AI-image-detector"
API_BASE   = "https://api-inference.huggingface.co/models"


def _frame_to_b64(frame: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf.tobytes()).decode()


def _infer_hf(model_id: str, image_b64: str) -> float:
    """Chiama HF Inference API e ritorna probabilità fake."""
    try:
        import httpx
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        img_bytes = base64.b64decode(image_b64)
        resp = httpx.post(
            f"{API_BASE}/{model_id}",
            content=img_bytes,
            headers={**headers, "Content-Type": "image/jpeg"},
            timeout=15.0,
        )
        if resp.status_code != 200:
            return 0.0
        data = resp.json()
        if isinstance(data, list):
            for item in data:
                label = (item.get("label") or "").lower()
                score = float(item.get("score", 0))
                if any(k in label for k in ["fake", "deepfake", "ai", "synthetic", "manipulated"]):
                    return score
        return 0.0
    except Exception:
        return 0.0


async def analyze_frames(video_path: str) -> Dict[str, Any]:
    result = {
        "deepfake_probability": 0.0,
        "flags": [],
        "model_a_score": 0.0,
        "model_b_score": 0.0,
        "frames_analyzed": 0,
    }

    if not HF_TOKEN:
        result["flags"].append({
            "type": "MODEL_NOT_AVAILABLE",
            "detail": "HF_TOKEN not set — visual models disabled",
            "severity": "INFO",
        })
        return result

    try:
        cap   = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Prendi 3 frame rappresentativi
        indices = [int(total * 0.25), int(total * 0.50), int(total * 0.75)]
        frames_b64 = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, idx))
            ret, frame = cap.read()
            if ret:
                frames_b64.append(_frame_to_b64(frame))
        cap.release()

        if not frames_b64:
            return result

        result["frames_analyzed"] = len(frames_b64)

        # Analisi con entrambi i modelli sul frame centrale
        main_frame = frames_b64[len(frames_b64)//2]
        score_a = _infer_hf(MODEL_A, main_frame)
        score_b = _infer_hf(MODEL_B, main_frame)

        result["model_a_score"] = round(score_a, 3)
        result["model_b_score"] = round(score_b, 3)

        # Media pesata
        combined = score_a * 0.6 + score_b * 0.4
        result["deepfake_probability"] = round(combined, 3)

        if combined > 0.7:
            result["flags"].append({
                "type": "DEEPFAKE_DETECTED",
                "detail": f"Dual-model consensus: {combined:.0%} probabilità deepfake",
                "severity": "HIGH",
            })
        elif combined > 0.4:
            result["flags"].append({
                "type": "SUSPICIOUS_VISUAL",
                "detail": f"Visual anomaly detected: {combined:.0%}",
                "severity": "MEDIUM",
            })

    except Exception as e:
        result["flags"].append({
            "type": "VISUAL_ERROR",
            "detail": str(e)[:100],
            "severity": "INFO",
        })

    return result
