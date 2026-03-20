"""
AURA — Layer 11: Temporal Coherence Module
Analizza continuità temporale per rilevare deepfake avanzati (Sora/Kling/Veo).
Segnali: blink rate, motion consistency, lighting stability, micro-movement proxy.
"""
import cv2
import numpy as np
from typing import Dict, Any, List


def analyze_temporal_coherence(video_path: str) -> Dict[str, Any]:
    result = {
        "temporal_score":        0.35,
        "blink_rate_anomaly":    False,
        "motion_consistency":    0.0,
        "lighting_stability":    0.0,
        "micro_movement_score":  0.0,
        "face_continuity":       0.0,
        "frames_analyzed":       0,
        "flags":                 [],
        "error":                 None,
    }

    try:
        cap   = cv2.VideoCapture(video_path)
        fps   = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total / fps

        if total < 10:
            result["error"] = "Video too short for temporal analysis"
            result["temporal_score"] = 0.20
            return result

        # Campiona max 120 frame distribuiti nel video
        max_frames = min(120, total)
        indices    = [int(total * i / max_frames) for i in range(max_frames)]

        frames       = []
        gray_frames  = []
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                gray_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        cap.release()

        if len(frames) < 10:
            result["error"] = "Not enough frames"
            return result

        result["frames_analyzed"] = len(frames)

        # ── 1. MOTION CONSISTENCY (optical flow tra frame consecutivi) ──────────
        flow_mags = []
        for i in range(1, min(60, len(gray_frames))):
            flow = cv2.calcOpticalFlowFarneback(
                gray_frames[i-1], gray_frames[i],
                None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            flow_mags.append(mag.mean())

        if flow_mags:
            flow_arr  = np.array(flow_mags)
            flow_mean = flow_arr.mean()
            flow_std  = flow_arr.std()
            # CV (Coefficient of Variation) — basso = movimento troppo uniforme
            flow_cv   = flow_std / (flow_mean + 1e-6)
            # Score: CV troppo basso (< 0.3) = movimento innaturalmente uniforme
            motion_score = 1.0 - min(1.0, flow_cv / 0.5)
            result["motion_consistency"] = round(float(motion_score), 3)

            if flow_cv < 0.20:
                result["flags"].append({
                    "type": "UNNATURAL_MOTION_CONSISTENCY",
                    "detail": f"Movimento troppo uniforme (CV={flow_cv:.2f}) — caratteristico di video AI-generated",
                    "severity": "HIGH"
                })
            elif flow_cv > 0.90:  # movimento eccessivamente caotico = AI noise
                result["flags"].append({
                    "type": "CHAOTIC_MOTION_PATTERN",
                    "detail": f"Pattern di movimento caotico (CV={flow_cv:.2f}) — tipico di AI con movimenti generati",
                    "severity": "MEDIUM"
                })

        # ── 2. LIGHTING STABILITY (variazione luminosità globale) ───────────────
        brightness_vals = [g.mean() for g in gray_frames]
        brightness_arr  = np.array(brightness_vals)
        bright_std      = brightness_arr.std()
        bright_mean     = brightness_arr.mean()
        bright_cv       = bright_std / (bright_mean + 1e-6)

        # Lighting troppo stabile = AI; troppo variabile = screen recording
        if bright_cv < 0.015:  # soglia più stretta
            lighting_score = 0.70
            result["flags"].append({
                "type": "STATIC_LIGHTING_ANOMALY",
                "detail": f"Illuminazione eccessivamente stabile (CV={bright_cv:.3f}) — tipica di CGI/AI",
                "severity": "MEDIUM"
            })
        elif bright_cv < 0.04:
            lighting_score = 0.35  # moderatamente stabile — comune in video compressi
        elif bright_cv > 0.30:
            lighting_score = 0.35  # variazioni eccessive
        else:
            lighting_score = 0.10  # normale variazione organica
        result["lighting_stability"] = round(float(lighting_score), 3)

        # ── 3. FACE CONTINUITY + BLINK PROXY ────────────────────────────────────
        face_sizes     = []
        face_positions = []
        face_detected  = 0

        for i, frame in enumerate(frames[::3]):  # ogni 3 frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_sizes.append(w * h)
                face_positions.append((x + w//2, y + h//2))
                face_detected += 1

        face_ratio = face_detected / max(1, len(frames[::3]))
        result["face_continuity"] = round(float(face_ratio), 3)

        # Analisi stabilità dimensione volto
        if face_sizes and len(face_sizes) > 5:
            size_arr = np.array(face_sizes, dtype=float)
            size_cv  = size_arr.std() / (size_arr.mean() + 1e-6)
            if size_cv < 0.05:
                result["flags"].append({
                    "type": "FACE_SIZE_TOO_STABLE",
                    "detail": f"Dimensione volto innaturalmente costante (CV={size_cv:.3f}) — possibile avatar AI",
                    "severity": "MEDIUM"
                })

            # Blink rate proxy: cerca frame dove regione occhi è più scura del solito
            if face_positions:
                blink_proxy = _estimate_blink_rate(frames, face_positions, fps)
                if blink_proxy is not None:
                    if blink_proxy < 5:  # meno di 5 blink/min = anomalo
                        result["blink_rate_anomaly"] = True
                        result["flags"].append({
                            "type": "LOW_BLINK_RATE",
                            "detail": f"Frequenza ammiccamento bassa (~{blink_proxy:.0f}/min) — deepfake spesso non replicano blink naturali",
                            "severity": "HIGH"
                        })
                    elif blink_proxy > 35:  # troppo alto
                        result["flags"].append({
                            "type": "HIGH_BLINK_RATE",
                            "detail": f"Frequenza ammiccamento anomala (~{blink_proxy:.0f}/min)",
                            "severity": "LOW"
                        })

        # ── 4. MICRO-MOVEMENT PROXY (camera shake / micro-expression) ───────────
        if len(gray_frames) > 20:
            # Analisi movimento globale (camera shake)
            global_flows = []
            for i in range(1, min(30, len(gray_frames))):
                diff = cv2.absdiff(gray_frames[i], gray_frames[i-1])
                global_flows.append(diff.mean())

            gf_arr = np.array(global_flows)
            micro_cv = gf_arr.std() / (gf_arr.mean() + 1e-6)

            if micro_cv < 0.2:
                micro_score = 0.65
                result["flags"].append({
                    "type": "NO_MICRO_MOVEMENT",
                    "detail": "Assenza di micro-movimenti naturali (camera shake, respirazione) — caratteristico di AI",
                    "severity": "MEDIUM"
                })
            else:
                micro_score = max(0.05, 0.4 - micro_cv * 0.3)
            result["micro_movement_score"] = round(float(micro_score), 3)

        # ── 5. CALCOLO SCORE FINALE ───────────────────────────────────────────────
        high_flags   = sum(1 for f in result["flags"] if f.get("severity") == "HIGH")
        medium_flags = sum(1 for f in result["flags"] if f.get("severity") == "MEDIUM")

        # Score conservativo — contribuisce solo con evidenza forte
        if high_flags >= 2:
            final_score = 0.70  # forte evidenza temporale
        elif high_flags == 1 and medium_flags >= 1:
            final_score = 0.55
        elif high_flags == 1:
            final_score = 0.45
        elif medium_flags >= 2:
            final_score = 0.40
        elif medium_flags == 1:
            final_score = 0.30
        else:
            final_score = 0.15  # nessun flag = organico

        result["temporal_score"] = round(float(final_score), 3)

    except Exception as e:
        result["error"]          = str(e)
        result["temporal_score"] = 0.25

    return result


def _estimate_blink_rate(frames: list, face_positions: list, fps: float) -> float:
    """Stima frequenza blink analizzando variazioni rapide nella regione occhi."""
    if not face_positions or len(frames) < 10:
        return None

    blink_count = 0
    prev_eye_brightness = None

    for i, frame in enumerate(frames[:60]):
        if i >= len(face_positions):
            break
        cx, cy = face_positions[min(i, len(face_positions)-1)]
        h, w   = frame.shape[:2]

        # Regione occhi (1/4 superiore del volto)
        eye_y1 = max(0, cy - 40)
        eye_y2 = max(0, cy - 10)
        eye_x1 = max(0, cx - 30)
        eye_x2 = min(w, cx + 30)

        if eye_y2 <= eye_y1 or eye_x2 <= eye_x1:
            continue

        eye_region  = frame[eye_y1:eye_y2, eye_x1:eye_x2]
        gray_eye    = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
        brightness  = gray_eye.mean()

        if prev_eye_brightness is not None:
            # Drop rapido di luminosità = possibile blink
            if prev_eye_brightness - brightness > 15:
                blink_count += 1
        prev_eye_brightness = brightness

    # Converti in blink/minuto
    duration_analyzed = len(frames[:60]) / fps
    if duration_analyzed > 0:
        return (blink_count / duration_analyzed) * 60
    return None
