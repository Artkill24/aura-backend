"""
AURA — Forensic Heatmap Generator
ELA (Error Level Analysis) + Signal anomaly map per PDF report.
"""
import cv2
import numpy as np
import tempfile
import os
from pathlib import Path
from typing import Optional


def generate_ela_heatmap(frame_bgr: np.ndarray, quality: int = 90) -> np.ndarray:
    """
    Error Level Analysis: confronta originale vs re-compresso.
    Aree manipolate mostrano errori diversi dal resto.
    """
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    cv2.imwrite(tmp_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    recompressed = cv2.imread(tmp_path)
    os.unlink(tmp_path)

    if recompressed is None or recompressed.shape != frame_bgr.shape:
        return np.zeros_like(frame_bgr)

    # ELA = differenza amplificata
    ela = cv2.absdiff(frame_bgr.astype(np.float32), recompressed.astype(np.float32))
    ela = np.clip(ela * 10, 0, 255).astype(np.uint8)

    # Converti in heatmap colorata
    ela_gray = cv2.cvtColor(ela, cv2.COLOR_BGR2GRAY)
    heatmap = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(frame_bgr, 0.4, heatmap, 0.6, 0)
    return overlay


def generate_signal_heatmap(frame_bgr: np.ndarray) -> np.ndarray:
    """
    Block uniformity map: visualizza dove la compressione è artificialmente uniforme.
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # Divide in blocchi 8x8 (DCT standard) e calcola varianza locale
    h, w = gray.shape
    block_size = 8
    variance_map = np.zeros_like(gray)

    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block = gray[y:y+block_size, x:x+block_size]
            var = np.var(block)
            variance_map[y:y+block_size, x:x+block_size] = var

    # Normalizza e inverti (bassa varianza = sospetto = rosso)
    variance_norm = cv2.normalize(variance_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    inverted = 255 - variance_norm
    heatmap = cv2.applyColorMap(inverted, cv2.COLORMAP_HOT)
    overlay = cv2.addWeighted(frame_bgr, 0.35, heatmap, 0.65, 0)
    return overlay


def extract_key_frame(video_path: str, target_frame: int = None) -> Optional[np.ndarray]:
    """Estrai il frame più rappresentativo per l'analisi."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if target_frame is None:
        target_frame = total // 3  # primo terzo del video

    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None


def generate_forensic_heatmaps(video_path: str, output_dir: str, job_id: str) -> dict:
    """
    Genera ELA + Signal heatmap e le salva come PNG.
    Ritorna dict con i path delle immagini.
    """
    frame = extract_key_frame(video_path)
    if frame is None:
        return {"ela": None, "signal": None}

    # Ridimensiona per PDF (max 600px width)
    h, w = frame.shape[:2]
    if w > 600:
        scale = 600 / w
        frame = cv2.resize(frame, (600, int(h * scale)))

    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    ela_path = str(out / f"{job_id}_ela.png")
    signal_path = str(out / f"{job_id}_signal.png")

    ela_img = generate_ela_heatmap(frame)
    signal_img = generate_signal_heatmap(frame)

    cv2.imwrite(ela_path, ela_img)
    cv2.imwrite(signal_path, signal_img)

    return {"ela": ela_path, "signal": signal_path}
