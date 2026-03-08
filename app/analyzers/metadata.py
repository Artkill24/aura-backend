"""
AURA — Metadata Analyzer
Extracts and cross-validates file metadata for tampering signals.
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime


# Known editing software signatures found in metadata
EDITING_SOFTWARE_SIGNATURES = [
    "adobe premiere", "after effects", "davinci resolve", "final cut",
    "capcut", "filmora", "kdenlive", "handbrake",
    "ffmpeg",  # Not always suspicious but notable
    "runway", "pika", "sora", "gen-2", "stable diffusion",
    "deepfacelab", "faceswap", "reface",
]

# AI video generation signatures
AI_GENERATION_SIGNATURES = [
    "runway", "pika labs", "sora", "gen-2", "kling", "luma", "stable video",
    "animatediff", "deforum", "zeroscope",
]


def analyze_metadata(video_path: str) -> dict:
    """
    Extracts metadata from video file using ffprobe.
    Returns structured analysis with flags and manipulation score.
    """
    result = {
        "raw": {},
        "flags": [],
        "manipulation_score": 0.0,
        "details": {},
    }

    try:
        # — Run ffprobe for container metadata —
        probe_data = _run_ffprobe(video_path)
        result["raw"] = probe_data

        flags = []
        score_factors = []

        format_info = probe_data.get("format", {})
        streams     = probe_data.get("streams", [])
        tags        = format_info.get("tags", {})

        # ── 1. Software / Encoder Check ──
        encoder = (
            tags.get("encoder", "") +
            tags.get("Encoder", "") +
            tags.get("software", "") +
            tags.get("Software", "") +
            tags.get("comment", "") +
            format_info.get("format_name", "")
        ).lower()

        for sig in EDITING_SOFTWARE_SIGNATURES:
            if sig in encoder:
                flags.append({
                    "type": "EDITING_SOFTWARE_DETECTED",
                    "detail": f"Encoder signature found: '{sig}'",
                    "severity": "MEDIUM",
                })
                score_factors.append(0.4)
                break

        for sig in AI_GENERATION_SIGNATURES:
            if sig in encoder:
                flags.append({
                    "type": "AI_GENERATION_TOOL_DETECTED",
                    "detail": f"Known AI video tool signature: '{sig}'",
                    "severity": "HIGH",
                })
                score_factors.append(0.9)
                break

        # ── 2. Creation vs Modification Time Discrepancy ──
        creation_time = tags.get("creation_time", "")
        file_mtime = Path(video_path).stat().st_mtime if Path(video_path).exists() else None

        if creation_time and file_mtime:
            try:
                ct = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
                mt = datetime.fromtimestamp(file_mtime)
                delta_days = abs((mt - ct.replace(tzinfo=None)).days)
                if delta_days > 30:
                    flags.append({
                        "type": "TIMESTAMP_DISCREPANCY",
                        "detail": f"Creation time vs file modification: {delta_days} days gap",
                        "severity": "LOW",
                    })
                    score_factors.append(0.2)
            except Exception:
                pass

        # ── 3. Frame Rate Anomalies ──
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        for stream in video_streams:
            fps_raw = stream.get("r_frame_rate", "0/1")
            fps = _parse_fraction(fps_raw)
            if fps and fps not in [24, 25, 30, 60, 23.976, 29.97, 59.94]:
                flags.append({
                    "type": "UNUSUAL_FRAME_RATE",
                    "detail": f"Non-standard frame rate: {fps:.3f} fps",
                    "severity": "LOW",
                })
                score_factors.append(0.15)

        # ── 4. Codec / Container Mismatch ──
        format_name = format_info.get("format_name", "")
        for stream in video_streams:
            codec = stream.get("codec_name", "")
            # e.g. H.265 video in MP4 container is normal, but some combos flag AI tools
            if codec in ["av1", "vp9"] and "mp4" in format_name:
                flags.append({
                    "type": "UNUSUAL_CODEC_CONTAINER",
                    "detail": f"Codec '{codec}' in '{format_name}' — uncommon for organic recordings",
                    "severity": "LOW",
                })
                score_factors.append(0.1)

        # ── 5. Missing Expected Metadata (GPS, Device Model) ──
        has_location = any(k in tags for k in ["location", "com.apple.quicktime.location.ISO6709"])
        has_device   = any(k in tags for k in ["make", "model", "com.apple.quicktime.model"])

        if not has_device:
            flags.append({
                "type": "NO_DEVICE_SIGNATURE",
                "detail": "No camera/device model found in metadata — could indicate synthetic origin",
                "severity": "LOW",
            })
            score_factors.append(0.1)

        # ── 6. Duration vs Bitrate Sanity Check ──
        duration = float(format_info.get("duration", 0))
        size_bytes = int(format_info.get("size", 0))
        if duration > 0 and size_bytes > 0:
            bitrate_kbps = (size_bytes * 8) / (duration * 1000)
            if bitrate_kbps < 50:  # Suspiciously low for any real video
                flags.append({
                    "type": "ABNORMAL_BITRATE",
                    "detail": f"Bitrate {bitrate_kbps:.1f} kbps is unusually low",
                    "severity": "MEDIUM",
                })
                score_factors.append(0.3)

        # ── Compute score ──
        manipulation_score = min(1.0, sum(score_factors)) if score_factors else 0.0

        result.update({
            "flags": flags,
            "manipulation_score": round(manipulation_score, 3),
            "details": {
                "format": format_name,
                "duration_seconds": round(duration, 2),
                "file_size_mb": round(size_bytes / (1024 * 1024), 2),
                "encoder_tag": encoder[:100] if encoder else "N/A",
                "has_gps": has_location,
                "has_device_model": has_device,
                "creation_time": creation_time or "N/A",
                "video_codec": video_streams[0].get("codec_name", "N/A") if video_streams else "N/A",
                "resolution": (
                    f"{video_streams[0].get('width')}x{video_streams[0].get('height')}"
                    if video_streams else "N/A"
                ),
            },
        })

    except Exception as e:
        result["flags"].append({
            "type": "ANALYSIS_ERROR",
            "detail": str(e),
            "severity": "INFO",
        })
        result["manipulation_score"] = 0.0

    return result


def _run_ffprobe(video_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {out.stderr}")
    return json.loads(out.stdout)


def _parse_fraction(frac_str: str) -> float | None:
    try:
        parts = frac_str.split("/")
        if len(parts) == 2:
            return float(parts[0]) / float(parts[1])
        return float(frac_str)
    except Exception:
        return None

