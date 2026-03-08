"""
AURA — Visual Analyzer v2
Dual-model frame analysis:
  Model A: dima806/deepfake_vs_real_image_detection — face deepfake detector
  Model B: umm-maybe/AI-image-detector — AI-generated scene detector

Both run in parallel. Final score = weighted max of the two.
"""

import asyncio
import cv2
import numpy as np
from typing import List, Tuple
import os

# ── Lazy-loaded models ──
_model_a = None
_processor_a = None
_model_b = None
_processor_b = None

MODEL_A_ID = "dima806/deepfake_vs_real_image_detection"  # Face deepfakes
MODEL_B_ID = "umm-maybe/AI-image-detector"               # AI-generated scenes


def _load_model_a():
    global _model_a, _processor_a
    if _model_a is None:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        _processor_a = AutoImageProcessor.from_pretrained(MODEL_A_ID)
        _model_a = AutoModelForImageClassification.from_pretrained(MODEL_A_ID)
        _model_a.eval()
    return _model_a, _processor_a


def _load_model_b():
    global _model_b, _processor_b
    if _model_b is None:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        _processor_b = AutoImageProcessor.from_pretrained(MODEL_B_ID)
        _model_b = AutoModelForImageClassification.from_pretrained(MODEL_B_ID)
        _model_b.eval()
    return _model_b, _processor_b


async def analyze_frames(video_path: str) -> dict:
    result = {
        "deepfake_probability": 0.0,
        "frames_analyzed": 0,
        "anomaly_frames": [],
        "flags": [],
        "details": {},
    }

    try:
        loop = asyncio.get_event_loop()

        # Extract frames once, reuse for both models
        frames_data = await loop.run_in_executor(None, _extract_frames, video_path)
        if not frames_data:
            result["flags"].append({
                "type": "NO_FRAMES_EXTRACTED",
                "detail": "Could not extract frames from video",
                "severity": "HIGH",
            })
            return result

        # Run both models in parallel via thread pool
        scores_a, scores_b = await asyncio.gather(
            loop.run_in_executor(None, _run_inference, frames_data, "A"),
            loop.run_in_executor(None, _run_inference, frames_data, "B"),
        )

        # ── Aggregate ──
        avg_a, max_a, var_a = _aggregate(scores_a)
        avg_b, max_b, var_b = _aggregate(scores_b)

        # Model B (AI-generated) gets higher weight — more relevant for synthetic videos
        combined_avg = round(avg_a * 0.4 + avg_b * 0.6, 3)
        combined_max = round(max(max_a, max_b), 3)

        # ── Anomaly frames (both models) ──
        anomaly_frames = []
        for s in (scores_a + scores_b):
            if s["deepfake_prob"] > 0.65:
                anomaly_frames.append({
                    "frame_index": s["frame_idx"],
                    "timestamp_seconds": round(s["timestamp"], 2),
                    "deepfake_probability": round(s["deepfake_prob"], 3),
                    "label": s["label"],
                    "model": s["model"],
                })

        # Deduplicate by frame_index, keep highest score
        seen = {}
        for f in anomaly_frames:
            idx = f["frame_index"]
            if idx not in seen or f["deepfake_probability"] > seen[idx]["deepfake_probability"]:
                seen[idx] = f
        anomaly_frames = sorted(seen.values(), key=lambda x: -x["deepfake_probability"])[:10]

        if anomaly_frames:
            result["flags"].append({
                "type": "VISUAL_ANOMALY_DETECTED",
                "detail": f"{len(anomaly_frames)} frame(s) flagged — deepfake or AI-generated content",
                "severity": "HIGH" if combined_max > 0.8 else "MEDIUM",
            })

        if avg_b > 0.6:
            result["flags"].append({
                "type": "AI_GENERATED_SCENE",
                "detail": f"Scene-level AI generation detected (score: {avg_b:.2f}) — video likely synthetic",
                "severity": "HIGH",
            })
        elif avg_b > 0.4:
            result["flags"].append({
                "type": "AI_GENERATED_SCENE_POSSIBLE",
                "detail": f"Possible AI-generated content (score: {avg_b:.2f})",
                "severity": "MEDIUM",
            })

        if avg_a > 0.5:
            result["flags"].append({
                "type": "FACE_MANIPULATION_DETECTED",
                "detail": f"Face-level deepfake detected (score: {avg_a:.2f})",
                "severity": "HIGH",
            })

        if var_a > 0.08 or var_b > 0.08:
            result["flags"].append({
                "type": "TEMPORAL_INCONSISTENCY",
                "detail": "High frame-to-frame variance — partial manipulation likely",
                "severity": "MEDIUM",
            })

        result.update({
            "deepfake_probability": combined_avg,
            "peak_probability": combined_max,
            "frames_analyzed": len(frames_data),
            "anomaly_frames": anomaly_frames,
            "details": {
                "model_a": MODEL_A_ID,
                "model_b": MODEL_B_ID,
                "score_model_a_face_deepfake": round(avg_a, 3),
                "score_model_b_ai_generated": round(avg_b, 3),
                "combined_score": combined_avg,
                "peak_score": combined_max,
                "frames_analyzed": len(frames_data),
            },
        })

    except ImportError:
        result["flags"].append({
            "type": "MODEL_NOT_AVAILABLE",
            "detail": "Visual models not loaded — run: pip install transformers torch",
            "severity": "INFO",
        })

    except Exception as e:
        result["flags"].append({
            "type": "VISUAL_ANALYSIS_ERROR",
            "detail": str(e),
            "severity": "INFO",
        })

    return result


def _aggregate(scores: list) -> tuple:
    if not scores:
        return 0.0, 0.0, 0.0
    vals = [s["deepfake_prob"] for s in scores]
    return float(np.mean(vals)), float(np.max(vals)), float(np.var(vals))


def _extract_frames(video_path: str, max_frames: int = 16) -> List[Tuple]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    step = max(1, int(fps * 2)) if duration <= 30 else max(1, total_frames // max_frames)
    sample_indices = list(range(0, total_frames, step))[:max_frames]

    frames = []
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        frames.append((idx, idx / fps, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))

    cap.release()
    return frames


def _run_inference(frames_data: List[Tuple], model_key: str) -> List[dict]:
    from PIL import Image
    import torch

    model, processor = _load_model_a() if model_key == "A" else _load_model_b()
    results = []

    for frame_idx, timestamp, frame_rgb in frames_data:
        try:
            inputs = processor(images=Image.fromarray(frame_rgb), return_tensors="pt")
            with torch.no_grad():
                probs = torch.softmax(model(**inputs).logits, dim=-1)[0]

            scores = {model.config.id2label[i]: float(p) for i, p in enumerate(probs)}
            deepfake_prob = _normalize_prob(scores)

            results.append({
                "frame_idx": frame_idx,
                "timestamp": timestamp,
                "deepfake_prob": deepfake_prob,
                "label": "FAKE" if deepfake_prob > 0.5 else "REAL",
                "model": model_key,
            })
        except Exception:
            continue

    return results


def _normalize_prob(scores: dict) -> float:
    fake_keys = ["fake", "deepfake", "artificial", "manipulated", "synthetic"]
    for key in fake_keys:
        for label, prob in scores.items():
            if key in label.lower():
                return float(prob)
    # umm-maybe convention: index 0 = artificial
    values = list(scores.values())
    return float(values[0]) if values else 0.0
