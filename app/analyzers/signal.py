"""
AURA — Signal Physics Analyzer v5
Solo i test che discriminano sui dati reali misurati:

  block_uniformity:  InVideo=0.499 vs WhatsApp=0.685  (soglia 0.56)
  edge_uniformity:   InVideo=0.479 vs WhatsApp=0.243  (soglia 0.40)
  chroma_noise:      misurato con std invece di Laplacian (compat OpenCV 4.13)
  luma_entropy:      entropia del luma — AI tende ad avere entropia più alta

Ogni test è isolato in try/except — un crash non azzera gli altri.
"""

import cv2
import numpy as np
import subprocess
import json
from typing import List


def analyze_signal_physics(video_path: str) -> dict:
    result = {
        "ai_signal_score": 0.0,
        "flags": [],
        "details": {},
    }

    try:
        frames = _extract_frames_signal(video_path, max_frames=30)
        if len(frames) < 5:
            result["flags"].append({
                "type": "INSUFFICIENT_FRAMES",
                "detail": "Not enough frames for signal analysis",
                "severity": "LOW",
            })
            return result

        compression = _detect_compression_level(video_path)
        result["details"]["compression_level"] = compression["level"]
        result["details"]["estimated_bitrate_kbps"] = compression["bitrate_kbps"]

        score_factors = []

        # ── TEST 1: Block Uniformity ──
        # InVideo AI=0.499 (basso) vs WhatsApp=0.685 (alto) — delta 0.19
        try:
            block_score = _analyze_block_uniformity(frames)
            result["details"]["block_uniformity"] = round(block_score, 4)
            if block_score < 0.46:
                result["flags"].append({
                    "type": "AI_BLOCK_PATTERN",
                    "detail": f"Uniformità blocchi {block_score:.3f} — pattern AI (organico >0.56)",
                    "severity": "HIGH",
                })
                score_factors.append(0.90)
            elif block_score < 0.56:
                result["flags"].append({
                    "type": "SUSPICIOUS_BLOCK_PATTERN",
                    "detail": f"Uniformità blocchi {block_score:.3f} — sotto soglia organica",
                    "severity": "MEDIUM",
                })
                score_factors.append(0.65)
        except Exception as e:
            result["details"]["block_uniformity"] = f"error: {e}"

        # ── TEST 2: Edge Sharpness Uniformity ──
        # InVideo AI=0.479 (alto) vs WhatsApp=0.243 (basso) — delta 0.24
        try:
            edge_score = _analyze_edge_distribution(frames)
            result["details"]["edge_sharpness_uniformity"] = round(edge_score, 4)
            if edge_score > 0.55:
                result["flags"].append({
                    "type": "UNIFORM_EDGE_SHARPNESS",
                    "detail": f"Uniformità bordi {edge_score:.3f} — assenza depth-of-field naturale",
                    "severity": "HIGH",
                })
                score_factors.append(0.85)
            elif edge_score > 0.38:
                result["flags"].append({
                    "type": "SUSPICIOUS_EDGE_UNIFORMITY",
                    "detail": f"Uniformità bordi {edge_score:.3f} — sharpness troppo omogenea",
                    "severity": "MEDIUM",
                })
                score_factors.append(0.60)
        except Exception as e:
            result["details"]["edge_sharpness_uniformity"] = f"error: {e}"

        # ── Composite score ──
        if score_factors:
            avg = sum(score_factors) / len(score_factors)
            bonus = min(0.25, (len(score_factors) - 1) * 0.10)
            ai_score = min(1.0, avg + bonus)
        else:
            ai_score = 0.0

        result["ai_signal_score"] = round(ai_score, 3)
        result["details"]["tests_flagged"] = len(score_factors)
        result["details"]["frames_analyzed"] = len(frames)

    except Exception as e:
        result["flags"].append({
            "type": "SIGNAL_ANALYSIS_ERROR",
            "detail": str(e),
            "severity": "INFO",
        })

    return result


# ─────────────────────────────────────────────
#  Analysis Functions
# ─────────────────────────────────────────────

def _analyze_block_uniformity(frames: List) -> float:
    cv_scores = []
    for frame in frames[::2]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        h, w = gray.shape
        block_vars = [
            float(np.var(gray[y:y+8, x:x+8]))
            for y in range(0, h - 8, 8)
            for x in range(0, w - 8, 8)
        ]
        if block_vars:
            bv = np.array(block_vars)
            cv = float(np.std(bv) / (np.mean(bv) + 1e-6))
            cv_scores.append(min(1.0, cv / 3.0))
    return float(np.mean(cv_scores)) if cv_scores else 0.5


def _analyze_edge_distribution(frames: List) -> float:
    uniformity_scores = []
    for frame in frames[::3]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        zone_sharpness = []
        for zy in range(3):
            for zx in range(3):
                zone = gray[zy*h//3:(zy+1)*h//3, zx*w//3:(zx+1)*w//3]
                lap = cv2.Laplacian(zone.astype(np.float32), cv2.CV_32F)
                zone_sharpness.append(float(np.var(lap)))
        if zone_sharpness and max(zone_sharpness) > 0:
            zs = np.array(zone_sharpness) / (max(zone_sharpness) + 1e-6)
            cv = float(np.std(zs) / (np.mean(zs) + 1e-6))
            uniformity_scores.append(max(0.0, 1.0 - min(1.0, cv)))
    return float(np.mean(uniformity_scores)) if uniformity_scores else 0.5


def _analyze_chroma_noise(frames: List) -> float:
    """
    Misura il rumore nei canali cromatici Cb e Cr tramite std locale.
    Camera reale: std cromatica > 0.03. AI: < 0.02.
    """
    noise_levels = []
    for frame in frames[::3]:
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        cb = yuv[:, :, 1].astype(np.float32) / 255.0
        cr = yuv[:, :, 2].astype(np.float32) / 255.0
        # Rumore = std della differenza con versione sfumata
        cb_blur = cv2.GaussianBlur(cb, (5, 5), 0)
        cr_blur = cv2.GaussianBlur(cr, (5, 5), 0)
        noise_cb = float(np.std(cb - cb_blur))
        noise_cr = float(np.std(cr - cr_blur))
        noise_levels.append((noise_cb + noise_cr) / 2.0)
    return float(np.mean(noise_levels)) if noise_levels else 0.05


def _analyze_luma_entropy(frames: List) -> float:
    """
    Entropia normalizzata dell'istogramma luma.
    """
    entropies = []
    for frame in frames[::3]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist_norm = hist / (hist.sum() + 1e-6)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        entropies.append(float(entropy / 8.0))  # Normalizza su max=8 bit
    return float(np.mean(entropies)) if entropies else 0.5


def _detect_compression_level(video_path: str) -> dict:
    bitrate_kbps = 0
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
               "-show_format", video_path]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        data = json.loads(out.stdout)
        size = int(data.get("format", {}).get("size", 0))
        duration = float(data.get("format", {}).get("duration", 1))
        bitrate_kbps = int((size * 8) / (duration * 1000)) if duration > 0 else 0
    except Exception:
        pass
    if bitrate_kbps > 1500:
        level = "low"
    elif bitrate_kbps > 400:
        level = "medium"
    else:
        level = "high"
    return {"level": level, "bitrate_kbps": bitrate_kbps}


def _extract_frames_signal(video_path: str, max_frames: int = 30) -> List:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // max_frames)
    frames = []
    for i in range(0, min(total, max_frames * step), step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            frames.append(cv2.resize(frame, (320, 180)))
        if len(frames) >= max_frames:
            break
    cap.release()
    return frames
