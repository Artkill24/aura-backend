"""
AURA — Virtual Camera Detector (Layer 7)
Per file MP4: rileva segnali di post-processing da virtual cam/deepfake tool.
Weight: 0.15
"""
import cv2
import numpy as np
from typing import Dict, Any


def analyze_virtual_cam(video_path: str) -> Dict[str, Any]:
    flags = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"virtual_cam_score": 0.0, "flags": [], "details": {}}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample = min(60, total_frames)
    step = max(1, total_frames // sample)

    frames = []
    frame_idx = 0
    while len(frames) < sample:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        frame_idx += step
    cap.release()

    if len(frames) < 10:
        return {"virtual_cam_score": 0.0, "flags": [], "details": {}}

    details = {}

    # ── 1. Noise floor — cam fisiche hanno rumore > 0.08 ─────────────────────
    noise_levels = []
    for f in frames:
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        # High-pass filter per isolare rumore sensore
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        noise = np.std(gray - blur)
        noise_levels.append(noise)
    mean_noise = float(np.mean(noise_levels))
    details["sensor_noise"] = round(mean_noise, 4)

    noise_score = 0.0
    if mean_noise < 1.5:
        noise_score = 0.85
        flags.append({"type": "ZERO_SENSOR_NOISE", "detail": f"Sensor noise {mean_noise:.2f} — cam fisiche hanno noise > 2.0", "severity": "HIGH"})
    elif mean_noise < 2.5:
        noise_score = 0.45
        flags.append({"type": "LOW_SENSOR_NOISE", "detail": f"Sensor noise {mean_noise:.2f} — sotto soglia organica", "severity": "MEDIUM"})

    # ── 2. Face region sharpness consistency ──────────────────────────────────
    # Deepfake/virtual cam: volto troppo nitido rispetto al contorno
    face_contrast_ratios = []
    for f in frames[::4]:
        h, w = f.shape[:2]
        cx, cy = w//2, h//3  # approssimazione area volto
        r = min(h, w) // 5
        face_region = f[max(0,cy-r):cy+r, max(0,cx-r):cx+r]
        border_region = f[:h//6, :]
        if face_region.size > 0 and border_region.size > 0:
            face_sharp = float(cv2.Laplacian(cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
            border_sharp = float(cv2.Laplacian(cv2.cvtColor(border_region, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
            if border_sharp > 0:
                ratio = face_sharp / (border_sharp + 1e-6)
                face_contrast_ratios.append(ratio)

    sharpness_score = 0.0
    if face_contrast_ratios:
        mean_ratio = float(np.mean(face_contrast_ratios))
        details["face_sharpness_ratio"] = round(mean_ratio, 3)
        if mean_ratio > 15.0:
            sharpness_score = 0.7
            flags.append({"type": "FACE_OVERSHARPENING", "detail": f"Face/background sharpness ratio {mean_ratio:.1f} — volto innaturalmente nitido", "severity": "HIGH"})
        elif mean_ratio > 8.0:
            sharpness_score = 0.35
            flags.append({"type": "FACE_SHARPNESS_ANOMALY", "detail": f"Face/background sharpness ratio {mean_ratio:.1f}", "severity": "MEDIUM"})

    # ── 3. Chroma noise asymmetry ─────────────────────────────────────────────
    # Virtual cam processing altera canali colore in modo asimmetrico
    chroma_vars = []
    for f in frames[::3]:
        yuv = cv2.cvtColor(f, cv2.COLOR_BGR2YUV)
        u_noise = float(np.std(yuv[:,:,1].astype(float)))
        v_noise = float(np.std(yuv[:,:,2].astype(float)))
        if u_noise > 0:
            chroma_vars.append(abs(u_noise - v_noise) / (u_noise + 1e-6))
    
    chroma_score = 0.0
    if chroma_vars:
        mean_chroma_asym = float(np.mean(chroma_vars))
        details["chroma_asymmetry"] = round(mean_chroma_asym, 4)
        if mean_chroma_asym > 0.25:
            chroma_score = 0.6
            flags.append({"type": "CHROMA_ASYMMETRY", "detail": f"U/V chroma asymmetry {mean_chroma_asym:.3f} — processing artifact", "severity": "MEDIUM"})

    # ── 4. Temporal flicker (deepfake generation artifacts) ───────────────────
    # Frame-to-frame inconsistency nel rendering AI
    flicker_scores = []
    for i in range(1, min(30, len(frames))):
        diff = cv2.absdiff(
            cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY),
            cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        ).astype(float)
        # Flicker localizzato = artefatto deepfake
        local_max = float(np.percentile(diff, 99))
        global_mean = float(np.mean(diff))
        if global_mean > 0:
            flicker_scores.append(local_max / (global_mean + 1e-6))

    flicker_score = 0.0
    if flicker_scores:
        mean_flicker = float(np.mean(flicker_scores))
        details["temporal_flicker_ratio"] = round(mean_flicker, 3)
        if mean_flicker > 25.0:
            flicker_score = 0.65
            flags.append({"type": "TEMPORAL_FLICKER", "detail": f"Flicker ratio {mean_flicker:.1f} — artefatti temporali da rendering AI", "severity": "HIGH"})
        elif mean_flicker > 15.0:
            flicker_score = 0.3

    # ── Composite ─────────────────────────────────────────────────────────────
    score = float(np.clip(
        noise_score     * 0.35 +
        sharpness_score * 0.30 +
        chroma_score    * 0.20 +
        flicker_score   * 0.15,
        0.0, 1.0
    ))

    details["frames_analyzed"] = len(frames)
    details["component_scores"] = {
        "noise":     round(noise_score, 3),
        "sharpness": round(sharpness_score, 3),
        "chroma":    round(chroma_score, 3),
        "flicker":   round(flicker_score, 3),
    }

    return {
        "virtual_cam_score": round(score, 4),
        "flags": flags,
        "details": details,
    }
