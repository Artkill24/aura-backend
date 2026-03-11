"""
AURA — rPPG Layer (Remote Photoplethysmography)
Rileva battito cardiaco dai micro-cambiamenti di colore del volto.
Un volto sintetico non ha pulsazione biologica coerente.
Weight: 0.15
"""
import cv2
import numpy as np
from scipy import signal as scipy_signal
from typing import Dict, Any


def analyze_rppg(video_path: str) -> Dict[str, Any]:
    result = {
        "rppg_score": 0.0,
        "bpm_detected": None,
        "signal_quality": "N/A",
        "flags": [],
        "details": {}
    }

    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return result

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        # Serve almeno 5 secondi per rilevare un battito
        if duration < 5.0:
            result["flags"].append({
                "type": "VIDEO_TOO_SHORT",
                "detail": f"Durata {duration:.1f}s — servono almeno 5s per rPPG",
                "severity": "INFO"
            })
            cap.release()
            return result

        # Campiona max 300 frame (non oltre 60 sec)
        max_frames = min(300, int(fps * 60))
        step = max(1, total_frames // max_frames)

        green_signal = []
        face_found_count = 0

        frame_idx = 0
        while frame_idx < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60,60))

            if len(faces) > 0:
                face_found_count += 1
                x, y, w_f, h_f = faces[0]

                # ROI: fronte (terzo superiore del volto)
                x1, y1 = x, y
                x2, y2 = x + w_f, y + int(h_f * 0.4)
                roi = frame[y1:y2, x1:x2]
                if roi.size > 0:
                    # Canale verde = massima sensibilità hemoglobina
                    green_mean = float(np.mean(roi[:, :, 1]))
                    green_signal.append(green_mean)
            else:
                # No face — aggiungi zero per mantenere timing
                if green_signal:
                    green_signal.append(green_signal[-1])

            frame_idx += step

        cap.release()

        result["details"]["face_detected_frames"] = face_found_count
        result["details"]["signal_length"] = len(green_signal)

        if len(green_signal) < 30:
            result["flags"].append({
                "type": "NO_FACE_DETECTED",
                "detail": f"Volto rilevato in {face_found_count} frame — impossibile analisi rPPG",
                "severity": "MEDIUM"
            })
            result["rppg_score"] = 0.3  # Sospetto: volto non rilevabile
            return result

        # ── Analisi segnale ──────────────────────────────────────────────────
        sig = np.array(green_signal, dtype=np.float64)
        sig = sig - np.mean(sig)  # detrend

        # Frequenza di campionamento effettiva
        effective_fps = fps / step

        # FFT per trovare picco frequenza cardiaca
        fft_vals = np.abs(np.fft.rfft(sig))
        fft_freqs = np.fft.rfftfreq(len(sig), d=1.0/effective_fps)

        # Banda cardiaca: 0.75–2.5 Hz (45–150 BPM)
        hr_mask = (fft_freqs >= 0.75) & (fft_freqs <= 2.5)
        # Banda noise: fuori dalla banda cardiaca
        noise_mask = (fft_freqs > 0.1) & ~hr_mask

        hr_power = float(np.sum(fft_vals[hr_mask] ** 2))
        noise_power = float(np.sum(fft_vals[noise_mask] ** 2)) + 1e-6

        snr = hr_power / noise_power
        result["details"]["snr"] = round(snr, 4)

        # BPM rilevato
        if hr_mask.any() and fft_vals[hr_mask].max() > 0:
            peak_freq = fft_freqs[hr_mask][np.argmax(fft_vals[hr_mask])]
            bpm = round(peak_freq * 60, 1)
            result["bpm_detected"] = bpm
            result["details"]["peak_freq_hz"] = round(float(peak_freq), 4)
        else:
            bpm = None

        # Varianza del segnale (segnale piatto = sintetico)
        signal_var = float(np.var(sig))
        result["details"]["signal_variance"] = round(signal_var, 6)

        # ── Scoring ──────────────────────────────────────────────────────────
        rppg_score = 0.0

        if snr < 0.5:
            # Segnale quasi piatto — nessuna pulsazione biologica
            rppg_score = max(rppg_score, 0.85)
            result["signal_quality"] = "ABSENT"
            result["flags"].append({
                "type": "NO_CARDIAC_SIGNAL",
                "detail": f"SNR {snr:.3f} — nessuna pulsazione biologica rilevata. Probabile volto sintetico.",
                "severity": "HIGH"
            })
        elif snr < 1.5:
            rppg_score = max(rppg_score, 0.55)
            result["signal_quality"] = "WEAK"
            result["flags"].append({
                "type": "WEAK_CARDIAC_SIGNAL",
                "detail": f"SNR {snr:.3f} — segnale cardiaco debole o inconsistente",
                "severity": "MEDIUM"
            })
        else:
            result["signal_quality"] = "PRESENT"

        if bpm is not None:
            if bpm < 40 or bpm > 180:
                rppg_score = max(rppg_score, 0.7)
                result["flags"].append({
                    "type": "ABNORMAL_BPM",
                    "detail": f"BPM rilevato: {bpm} — fuori range biologico (40-180)",
                    "severity": "HIGH"
                })
            else:
                result["details"]["bpm_in_range"] = True

        if signal_var < 0.01:
            rppg_score = max(rppg_score, 0.75)
            result["flags"].append({
                "type": "FLAT_SIGNAL",
                "detail": f"Varianza segnale {signal_var:.6f} — segnale piatto, volto statico o sintetico",
                "severity": "HIGH"
            })

        result["rppg_score"] = round(float(np.clip(rppg_score, 0.0, 1.0)), 4)

    except Exception as e:
        result["flags"].append({
            "type": "RPPG_ERROR",
            "detail": str(e),
            "severity": "INFO"
        })

    return result
