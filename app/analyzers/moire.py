import cv2, numpy as np, subprocess, json
from typing import List

def analyze_moire(video_path: str) -> dict:
    result = {"screen_recording_score": 0.0, "flags": [], "details": {}}
    try:
        frames = _extract_frames(video_path, max_frames=30)
        if len(frames) < 5:
            return result
        fps = _get_video_fps(video_path)
        result["details"]["video_fps"] = round(fps, 3)
        score_factors = []
        try:
            moire_score, md = _detect_moire_fft(frames)
            result["details"]["moire_fft_score"] = round(moire_score, 4)
            result["details"]["moire_peaks"] = md["peaks"]
            if moire_score > 0.70:
                result["flags"].append({"type": "MOIRE_PATTERN_DETECTED", "detail": f"Pattern Moire rilevato ({moire_score:.2f}) — ripresa di schermo", "severity": "HIGH"})
                score_factors.append(0.90)
            elif moire_score > 0.45:
                result["flags"].append({"type": "POSSIBLE_MOIRE", "detail": f"Possibile Moire ({moire_score:.2f})", "severity": "MEDIUM"})
                score_factors.append(0.50)
        except Exception as e:
            result["details"]["moire_error"] = str(e)
        try:
            ref_score, hz = _detect_refresh_rate(frames, fps)
            result["details"]["refresh_rate_score"] = round(ref_score, 4)
            result["details"]["detected_screen_hz"] = hz
            if ref_score > 0.65:
                result["flags"].append({"type": "SCREEN_REFRESH_DETECTED", "detail": f"Refresh schermo ~{hz}Hz rilevato", "severity": "HIGH"})
                score_factors.append(0.85)
            elif ref_score > 0.40:
                result["flags"].append({"type": "POSSIBLE_SCREEN_FLICKER", "detail": f"Possibile flicker {hz}Hz", "severity": "MEDIUM"})
                score_factors.append(0.45)
        except Exception as e:
            result["details"]["refresh_error"] = str(e)
        try:
            grid = _detect_pixel_grid(frames)
            result["details"]["pixel_grid_score"] = round(grid, 4)
            if grid > 0.65:
                result["flags"].append({"type": "LCD_PIXEL_GRID", "detail": f"Griglia sub-pixel LCD ({grid:.2f})", "severity": "HIGH"})
                score_factors.append(0.80)
        except Exception as e:
            result["details"]["grid_error"] = str(e)
        if score_factors:
            avg = sum(score_factors) / len(score_factors)
            bonus = min(0.20, (len(score_factors) - 1) * 0.08)
            result["screen_recording_score"] = round(min(1.0, avg + bonus), 3)
        result["details"]["tests_flagged"] = len(score_factors)
    except Exception as e:
        result["flags"].append({"type": "MOIRE_ERROR", "detail": str(e), "severity": "INFO"})
    return result

def _detect_moire_fft(frames):
    peak_scores, total_peaks = [], 0
    for frame in frames[::3]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        f = np.fft.fftshift(np.fft.fft2(gray))
        mag = 20 * np.log(np.abs(f) + 1)
        h, w = mag.shape; cy, cx = h//2, w//2
        mag[cy-5:cy+5, cx-5:cx+5] = 0
        mag_norm = (mag - mag.min()) / (mag.max() - mag.min() + 1e-6)
        peaks = np.sum(mag_norm > 0.85)
        if peaks > 4:
            pm = mag_norm > 0.85
            sym = np.sum(pm & np.flip(np.flip(pm,0),1)) / (peaks + 1e-6)
            if sym > 0.6:
                peak_scores.append(sym); total_peaks += peaks
    if not peak_scores: return 0.0, {"peaks": 0}
    avg = float(np.mean(peak_scores))
    return min(1.0, avg * (1 + min(total_peaks,20)/40)), {"peaks": int(total_peaks//len(peak_scores))}

def _detect_refresh_rate(frames, fps):
    b = [float(np.mean(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))) for f in frames]
    if len(b) < 10: return 0.0, 0
    s = np.array(b) - np.mean(b)
    fft_v = np.abs(np.fft.rfft(s))
    freqs = np.fft.rfftfreq(len(s), d=1.0/fps)
    fft_n = fft_v / (fft_v.max() + 1e-6)
    best_s, best_hz = 0.0, 0
    for sf in [50, 60, 75, 100, 120, 144]:
        beat = abs(sf - fps) if sf > fps else sf % fps
        if 0 < beat < fps/2:
            idx = np.argmin(np.abs(freqs - beat))
            if idx < len(fft_n) and fft_n[idx] > best_s:
                best_s, best_hz = float(fft_n[idx]), sf
    return min(1.0, best_s * 2), best_hz

def _detect_pixel_grid(frames):
    scores = []
    for frame in frames[::4]:
        ch_scores = []
        for ch in range(3):
            c = frame[:,:,ch].astype(np.float32)
            f = np.fft.fftshift(np.fft.fft2(c))
            mag = np.abs(f); h,w = mag.shape; cy,cx = h//2,w//2
            mag[cy-3:cy+3,cx-3:cx+3] = 0
            hp = mag[cy,:]; hp[cx-3:cx+3] = 0
            if hp.max() > 0:
                n = np.sum(hp/hp.max() > 0.7)
                ch_scores.append(min(1.0, n/4.0))
        if ch_scores: scores.append(float(np.mean(ch_scores)))
    return float(np.mean(scores)) if scores else 0.0

def _get_video_fps(path):
    try:
        out = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_streams",path], capture_output=True, text=True, timeout=15)
        for s in json.loads(out.stdout).get("streams",[]):
            if s.get("codec_type") == "video":
                p = s.get("r_frame_rate","30/1").split("/")
                return float(p[0])/float(p[1])
    except: pass
    return 30.0

def _extract_frames(path, max_frames=30):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened(): return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total//max_frames); frames = []
    for i in range(0, min(total, max_frames*step), step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret: frames.append(cv2.resize(frame, (320,180)))
        if len(frames) >= max_frames: break
    cap.release(); return frames
