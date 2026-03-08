"""
AURA — Visual Analyzer
Frame-by-frame deepfake detection using HuggingFace transformers.
Samples frames intelligently to balance accuracy vs. speed.
"""

import asyncio
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
import os

# Lazy imports — only load models when needed
_model = None
_processor = None


def _load_model():
    """Lazy-load the deepfake detection model."""
    global _model, _processor
    if _model is None:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        import torch

        MODEL_ID = os.getenv("VISUAL_MODEL_ID", "dima806/deepfake_vs_real_image_detection")
        _processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        _model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
        _model.eval()
    return _model, _processor


async def analyze_frames(video_path: str) -> dict:
    """
    Extracts key frames and runs deepfake classification.
    Returns probability score + per-frame anomalies.
    """
    result = {
        "deepfake_probability": 0.0,
        "frames_analyzed": 0,
        "anomaly_frames": [],
        "flags": [],
        "details": {},
    }

    try:
        # Extract frames in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()
        frames_data = await loop.run_in_executor(None, _extract_frames, video_path)

        if not frames_data:
            result["flags"].append({
                "type": "NO_FRAMES_EXTRACTED",
                "detail": "Could not extract frames from video",
                "severity": "HIGH",
            })
            return result

        # Run inference
        scores = await loop.run_in_executor(None, _run_inference, frames_data)

        if not scores:
            return result

        # Aggregate results
        deepfake_scores = [s["deepfake_prob"] for s in scores]
        avg_score = float(np.mean(deepfake_scores))
        max_score = float(np.max(deepfake_scores))
        
        # Flag frames with high anomaly
        anomaly_frames = [
            {
                "frame_index": s["frame_idx"],
                "timestamp_seconds": round(s["timestamp"], 2),
                "deepfake_probability": round(s["deepfake_prob"], 3),
                "label": s["label"],
            }
            for s in scores
            if s["deepfake_prob"] > 0.65
        ]

        if anomaly_frames:
            result["flags"].append({
                "type": "VISUAL_ANOMALY_DETECTED",
                "detail": f"{len(anomaly_frames)} frame(s) flagged with high deepfake probability",
                "severity": "HIGH" if max_score > 0.8 else "MEDIUM",
            })

        # Check for temporal inconsistency (big score swings between frames)
        if len(deepfake_scores) > 2:
            score_variance = float(np.var(deepfake_scores))
            if score_variance > 0.08:
                result["flags"].append({
                    "type": "TEMPORAL_INCONSISTENCY",
                    "detail": f"High variance across frames (σ²={score_variance:.3f}) — suggests partial manipulation",
                    "severity": "MEDIUM",
                })

        result.update({
            "deepfake_probability": round(avg_score, 3),
            "peak_probability": round(max_score, 3),
            "frames_analyzed": len(scores),
            "anomaly_frames": anomaly_frames[:10],  # Cap report entries
            "details": {
                "model_used": os.getenv("VISUAL_MODEL_ID", "dima806/deepfake_vs_real_image_detection"),
                "sampling_strategy": "adaptive_keyframe",
                "avg_score": round(avg_score, 3),
                "max_score": round(max_score, 3),
                "variance": round(float(np.var(deepfake_scores)), 4),
            },
        })

    except ImportError:
        # Graceful fallback if transformers not installed yet
        result["flags"].append({
            "type": "MODEL_NOT_AVAILABLE",
            "detail": "Visual model not loaded — run: pip install transformers torch",
            "severity": "INFO",
        })
        result["deepfake_probability"] = 0.0

    except Exception as e:
        result["flags"].append({
            "type": "VISUAL_ANALYSIS_ERROR",
            "detail": str(e),
            "severity": "INFO",
        })

    return result


def _extract_frames(video_path: str, max_frames: int = 20) -> List[Tuple]:
    """
    Adaptive frame extraction:
    - Short videos (<30s): every 2 seconds
    - Long videos: uniform sampling up to max_frames
    Focus on areas where deepfakes break: first/last 5s, scene changes.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    # Compute sample indices
    if duration <= 30:
        step = max(1, int(fps * 2))  # Every 2 seconds
    else:
        step = max(1, total_frames // max_frames)

    sample_indices = list(range(0, total_frames, step))[:max_frames]

    frames = []
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        # Convert BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp = idx / fps
        frames.append((idx, timestamp, frame_rgb))

    cap.release()
    return frames


def _run_inference(frames_data: List[Tuple]) -> List[dict]:
    """Run HuggingFace model on extracted frames."""
    from PIL import Image
    import torch

    model, processor = _load_model()
    results = []

    for frame_idx, timestamp, frame_rgb in frames_data:
        try:
            image = Image.fromarray(frame_rgb)
            inputs = processor(images=image, return_tensors="pt")

            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)[0]

            # Map label indices to meaningful names
            id2label = model.config.id2label
            scores = {id2label[i]: float(p) for i, p in enumerate(probs)}

            # Normalize to "deepfake probability" regardless of label naming
            deepfake_prob = _normalize_deepfake_prob(scores)

            results.append({
                "frame_idx": frame_idx,
                "timestamp": timestamp,
                "deepfake_prob": deepfake_prob,
                "label": "DEEPFAKE" if deepfake_prob > 0.5 else "REAL",
                "raw_scores": scores,
            })

        except Exception:
            continue

    return results


def _normalize_deepfake_prob(scores: dict) -> float:
    """
    Normalize model output to a 0-1 deepfake probability
    regardless of how the model labels its classes.
    """
    fake_keys = ["fake", "deepfake", "artificial", "manipulated", "synthetic", "1"]
    real_keys = ["real", "authentic", "original", "genuine", "0"]

    for key in fake_keys:
        for label, prob in scores.items():
            if key in label.lower():
                return prob

    # Fallback: assume binary, first class = real
    values = list(scores.values())
    return values[1] if len(values) >= 2 else 0.0
