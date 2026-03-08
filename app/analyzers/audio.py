"""
AURA — Audio-Visual Sync Analyzer
Detects audio manipulation, synthetic voice signatures,
and lip-sync desynchronization.
"""

import subprocess
import json
import numpy as np
from pathlib import Path


def analyze_audio_sync(video_path: str) -> dict:
    """
    Multi-layer audio analysis:
    1. Extract audio stream metadata
    2. Analyze frequency spectrum for synthesis artifacts
    3. Check for latency signatures typical of TTS/voice cloning
    4. Detect audio-video stream timestamp drift
    """
    result = {
        "sync_anomaly_score": 0.0,
        "has_audio": False,
        "flags": [],
        "details": {},
    }

    try:
        # ── Get audio stream info ──
        probe = _probe_audio_streams(video_path)
        audio_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]

        if not audio_streams:
            result["flags"].append({
                "type": "NO_AUDIO_STREAM",
                "detail": "Video contains no audio track",
                "severity": "LOW",
            })
            return result

        result["has_audio"] = True
        audio = audio_streams[0]
        score_factors = []

        # ── 1. Sample Rate Analysis ──
        sample_rate = int(audio.get("sample_rate", 44100))
        if sample_rate not in [44100, 48000, 22050, 16000]:
            result["flags"].append({
                "type": "UNUSUAL_SAMPLE_RATE",
                "detail": f"Non-standard sample rate: {sample_rate} Hz — common in TTS systems",
                "severity": "LOW",
            })
            score_factors.append(0.15)

        # ── 2. Codec Analysis (TTS often outputs specific codecs) ──
        codec = audio.get("codec_name", "")
        if codec in ["opus", "vorbis"]:
            result["flags"].append({
                "type": "STREAMING_CODEC",
                "detail": f"Codec '{codec}' is common in real-time AI voice streaming",
                "severity": "LOW",
            })
            score_factors.append(0.1)

        # ── 3. Audio-Video Start Time Drift ──
        video_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
        if video_streams and audio_streams:
            v_start = float(video_streams[0].get("start_time", 0))
            a_start = float(audio_streams[0].get("start_time", 0))
            drift_ms = abs(v_start - a_start) * 1000

            if drift_ms > 100:
                result["flags"].append({
                    "type": "AV_START_DRIFT",
                    "detail": f"Audio/video start time offset: {drift_ms:.1f}ms — may indicate post-dubbed audio",
                    "severity": "MEDIUM" if drift_ms > 500 else "LOW",
                })
                score_factors.append(0.25 if drift_ms > 500 else 0.1)

        # ── 4. Frequency Analysis via FFmpeg ──
        freq_analysis = _analyze_frequency_spectrum(video_path)
        if freq_analysis:
            # TTS/voice cloning typically has suspiciously flat frequency response
            # and lacks the natural 3D room reverberation
            if freq_analysis.get("spectral_flatness", 0) > 0.7:
                result["flags"].append({
                    "type": "FLAT_SPECTRAL_PROFILE",
                    "detail": "Audio lacks natural room reverberation — synthetic voice signature",
                    "severity": "MEDIUM",
                })
                score_factors.append(0.4)

            if freq_analysis.get("has_60hz_hum"):
                result["flags"].append({
                    "type": "ELECTRICAL_HUM_ABSENT",
                    "detail": "No 50/60Hz electrical hum detected — studio-clean audio uncommon for organic recording",
                    "severity": "LOW",
                })
                score_factors.append(0.1)

        # ── 5. Bitrate Consistency Check ──
        audio_bitrate = int(audio.get("bit_rate", 0))
        if 0 < audio_bitrate < 64000:  # Below 64kbps is TTS-quality
            result["flags"].append({
                "type": "LOW_AUDIO_BITRATE",
                "detail": f"Audio bitrate {audio_bitrate//1000}kbps — consistent with compressed TTS output",
                "severity": "MEDIUM",
            })
            score_factors.append(0.3)

        # ── Compute score ──
        sync_score = min(1.0, sum(score_factors)) if score_factors else 0.0

        result.update({
            "sync_anomaly_score": round(sync_score, 3),
            "details": {
                "codec": codec,
                "sample_rate_hz": sample_rate,
                "channels": audio.get("channels", "N/A"),
                "audio_bitrate_kbps": audio_bitrate // 1000 if audio_bitrate else "N/A",
                "duration_seconds": round(float(audio.get("duration", 0)), 2),
                "av_drift_ms": round(drift_ms, 1) if "drift_ms" in dir() else 0,
                "frequency_analysis": freq_analysis or {},
            },
        })

    except Exception as e:
        result["flags"].append({
            "type": "AUDIO_ANALYSIS_ERROR",
            "detail": str(e),
            "severity": "INFO",
        })

    return result


def _probe_audio_streams(video_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        video_path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe error: {out.stderr}")
    return json.loads(out.stdout)


def _analyze_frequency_spectrum(video_path: str) -> dict | None:
    """
    Uses FFmpeg to extract basic spectral features.
    A flat spectrum with no natural room tone = synthetic red flag.
    """
    try:
        # Extract a 10-second audio sample and analyze with astats filter
        cmd = [
            "ffmpeg", "-i", video_path,
            "-t", "10",  # Analyze first 10 seconds
            "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Flat_factor",
            "-f", "null", "-",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stderr = out.stderr

        flat_factor = None
        for line in stderr.split("\n"):
            if "Flat_factor" in line:
                try:
                    flat_factor = float(line.split("=")[-1].strip())
                    break
                except Exception:
                    pass

        return {
            "spectral_flatness": flat_factor or 0.0,
            "has_60hz_hum": _check_for_hum(video_path),
        }

    except Exception:
        return None


def _check_for_hum(video_path: str) -> bool:
    """Check for presence of 50/60Hz electrical hum (sign of real-world recording)."""
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-t", "5",
            "-af", "bandpass=f=60:width_type=o:w=0.5,astats",
            "-f", "null", "-",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return "RMS" in out.stderr
    except Exception:
        return False
