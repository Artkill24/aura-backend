"""
AURA — PRNU (Photo Response Non-Uniformity) Analyzer
Sensor Noise Fingerprint Analysis

Ogni sensore fisico ha imperfezioni microscopiche uniche (PRNU).
Un video reale mostra un pattern di rumore coerente su tutti i frame.
Un video AI ha rumore sintetico uniforme o incoerente tra regioni.

Score: 0.0 = sensore fisico reale | 1.0 = rumore sintetico/inconsistente
"""

import cv2
import numpy as np
from typing import Optional


def _extract_noise_residual(frame: np.ndarray) -> np.ndarray:
    """
    Estrae il residuo di rumore dal frame sottraendo la versione denoised.
    Usa un filtro Wiener approssimato via gaussian blur.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    # Denoised version: gaussian blur rimuove il segnale utile, resta il rumore
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    residual = gray - denoised
    return residual


def _compute_prnu_estimate(residuals: list[np.ndarray]) -> np.ndarray:
    """
    Stima il pattern PRNU come media dei residui su tutti i frame.
    Su un sensore reale, il PRNU è costante → la media converge.
    Su AI, il rumore è casuale → la media tende a zero.
    """
    if not residuals:
        return np.zeros((1, 1))
    stack = np.stack(residuals, axis=0)
    return np.mean(stack, axis=0)


def _prnu_consistency_score(residuals: list[np.ndarray], prnu_estimate: np.ndarray) -> float:
    """
    Misura quanto ogni frame è correlato al pattern PRNU stimato.
    Alta correlazione = sensore fisico reale.
    Bassa correlazione = rumore sintetico incoerente.
    Restituisce score 0.0 (reale) → 1.0 (sintetico).
    """
    if len(residuals) < 2:
        return 0.5

    correlations = []
    prnu_flat = prnu_estimate.flatten()
    prnu_norm = np.linalg.norm(prnu_flat)

    if prnu_norm < 1e-10:
        return 0.8  # PRNU troppo debole → probabile AI

    for residual in residuals:
        res_flat = residual.flatten()
        # Pearson correlation tra residuo del frame e stima PRNU
        if np.std(res_flat) < 1e-10:
            continue
        corr = np.dot(prnu_flat, res_flat) / (prnu_norm * np.linalg.norm(res_flat) + 1e-10)
        correlations.append(abs(corr))

    if not correlations:
        return 0.7

    mean_corr = np.mean(correlations)

    # Alta correlazione → sensore fisico → score basso (AUTHENTIC)
    # Bassa correlazione → rumore incoerente → score alto (SYNTHETIC)
    # Soglie calibrate empiricamente
    min_corr = min(correlations)

    # Calibrato su dati reali:
    # WhatsApp fisico: mean=0.996, min=0.989
    # InVideo AI:      mean=0.839, min=0.025 (outlier frames = AI artifact)
    # Screen rec:      mean=0.800, min=0.614

    # Se un frame ha correlazione vicino a zero → frame AI inserito
    if min_corr < 0.1:
        return 0.9   # frame completamente scorrelato → AI quasi certo

    if mean_corr > 0.95:
        return 0.0   # sensore fisico reale
    elif mean_corr > 0.88:
        return 0.2   # PRNU presente ma non perfetto (compressione)
    elif mean_corr > 0.82:
        return 0.5   # PRNU debole — sospetto
    else:
        return 0.8   # PRNU assente — sintetico


def _spatial_noise_uniformity(prnu_estimate: np.ndarray) -> float:
    """
    Analizza la distribuzione spaziale del PRNU.
    Un sensore reale ha pattern non uniforme (imperfezioni fisiche).
    Un AI ha pattern uniforme o strutturato artificialmente.
    Restituisce score 0.0 (non uniforme = reale) → 1.0 (uniforme = AI).
    """
    if prnu_estimate.size == 0:
        return 0.5

    # Dividi in blocchi e calcola varianza locale
    h, w = prnu_estimate.shape
    block_size = max(h // 8, w // 8, 16)
    block_stds = []

    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block = prnu_estimate[y:y+block_size, x:x+block_size]
            block_stds.append(np.std(block))

    if not block_stds:
        return 0.5

    # Coefficiente di variazione delle std locali
    cv = np.std(block_stds) / (np.mean(block_stds) + 1e-10)

    # Alta variabilità tra blocchi → pattern non uniforme → sensore reale
    # Bassa variabilità → pattern uniforme → sintetico
    if cv > 0.5:
        return 0.0   # molto non uniforme → reale
    elif cv > 0.3:
        return 0.2
    elif cv > 0.15:
        return 0.5
    else:
        return 0.8   # troppo uniforme → sintetico


def _fft_noise_analysis(prnu_estimate: np.ndarray) -> float:
    """
    Analisi FFT del pattern PRNU.
    Sensori fisici → spettro di rumore 1/f (naturale, decrescente).
    AI → spettro piatto o con picchi periodici artificiali.
    Restituisce score 0.0 (spettro naturale) → 1.0 (spettro artificiale).
    """
    if prnu_estimate.size == 0:
        return 0.5

    # FFT 2D del pattern PRNU
    fft = np.fft.fft2(prnu_estimate)
    fft_shifted = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shifted)

    h, w = magnitude.shape
    cy, cx = h // 2, w // 2

    # Calcola energia per anelli concentrici (frequenza crescente)
    ring_energies = []
    max_r = min(cy, cx)
    ring_width = max(max_r // 8, 4)

    for r_start in range(0, max_r - ring_width, ring_width):
        r_end = r_start + ring_width
        y_grid, x_grid = np.ogrid[-cy:h-cy, -cx:w-cx]
        mask = (y_grid**2 + x_grid**2 >= r_start**2) & (y_grid**2 + x_grid**2 < r_end**2)
        if mask.sum() > 0:
            ring_energies.append(magnitude[mask].mean())

    if len(ring_energies) < 3:
        return 0.5

    # Verifica se lo spettro è decrescente (1/f = naturale)
    # Conta quante transizioni sono decrescenti
    decreasing = sum(1 for i in range(len(ring_energies)-1)
                     if ring_energies[i] >= ring_energies[i+1])
    ratio = decreasing / (len(ring_energies) - 1)

    # Spettro decrescente → naturale → score basso
    if ratio > 0.7:
        return 0.0
    elif ratio > 0.5:
        return 0.3
    elif ratio > 0.3:
        return 0.6
    else:
        return 0.85  # spettro piatto/crescente → sintetico


def analyze_prnu(video_path: str, max_frames: int = 30) -> dict:
    """
    Analisi PRNU completa: sensor fingerprint, spatial uniformity, FFT spectrum.

    Returns:
        dict con prnu_score (0=reale, 1=sintetico), flags, details
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "prnu_score": 0.5,
            "flags": [{"type": "PRNU_ERROR", "detail": "Cannot open video", "severity": "INFO"}],
            "details": {}
        }

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    # Campionamento uniforme
    if total_frames > 0:
        step = max(total_frames // max_frames, 1)
        sample_indices = list(range(0, total_frames, step))[:max_frames]
    else:
        sample_indices = list(range(max_frames))

    residuals = []
    frame_idx = 0
    sample_set = set(sample_indices)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx in sample_set:
            # Ridimensiona per uniformità e velocità
            frame_resized = cv2.resize(frame, (320, 240))
            residual = _extract_noise_residual(frame_resized)
            residuals.append(residual)
        frame_idx += 1

    cap.release()

    if len(residuals) < 3:
        return {
            "prnu_score": 0.5,
            "flags": [{"type": "PRNU_INSUFFICIENT_FRAMES", "detail": f"Solo {len(residuals)} frame disponibili", "severity": "INFO"}],
            "details": {"frames_analyzed": len(residuals)}
        }

    # Stima PRNU
    prnu_estimate = _compute_prnu_estimate(residuals)

    # Test 1: Consistenza frame-PRNU
    consistency_score = _prnu_consistency_score(residuals, prnu_estimate)

    # Test 2: Uniformità spaziale
    spatial_score = _spatial_noise_uniformity(prnu_estimate)

    # Test 3: Analisi FFT
    fft_score = _fft_noise_analysis(prnu_estimate)

    # Score composito PRNU
    # Pesi: consistenza è il test più importante
    prnu_score = (
        consistency_score * 0.70 +
        spatial_score     * 0.15 +
        fft_score         * 0.15
    )
    prnu_score = round(float(prnu_score), 3)

    # Flags
    flags = []
    tests_flagged = 0

    if consistency_score > 0.5:
        flags.append({
            "type": "WEAK_SENSOR_FINGERPRINT",
            "detail": f"Pattern PRNU incoerente tra frame (corr. media bassa) — possibile origine sintetica",
            "severity": "HIGH" if consistency_score > 0.7 else "MEDIUM"
        })
        tests_flagged += 1

    if spatial_score > 0.5:
        flags.append({
            "type": "UNIFORM_NOISE_DISTRIBUTION",
            "detail": f"Distribuzione rumore troppo uniforme spazialmente — mancano imperfezioni fisiche del sensore",
            "severity": "MEDIUM"
        })
        tests_flagged += 1

    if fft_score > 0.5:
        flags.append({
            "type": "SYNTHETIC_NOISE_SPECTRUM",
            "detail": f"Spettro FFT del rumore non segue distribuzione 1/f naturale — possibile rumore artificiale",
            "severity": "MEDIUM"
        })
        tests_flagged += 1

    return {
        "prnu_score": prnu_score,
        "flags": flags,
        "details": {
            "frames_analyzed": len(residuals),
            "consistency_score": round(float(consistency_score), 3),
            "spatial_uniformity_score": round(float(spatial_score), 3),
            "fft_spectrum_score": round(float(fft_score), 3),
            "tests_flagged": tests_flagged,
        }
    }
