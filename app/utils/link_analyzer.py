"""
AURA — Link Analyzer (yt-dlp)
Download video da YouTube/X/TikTok/Vimeo per analisi forense.
"""
import os, re, tempfile, time
from pathlib import Path
from typing import Dict, Any, Optional


SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be", "x.com", "twitter.com",
    "tiktok.com", "vimeo.com", "instagram.com", "facebook.com",
    "dailymotion.com", "twitch.tv", "rumble.com",
]

MAX_DURATION_FREE = 180   # 3 min free tier
MAX_DURATION_PRO  = 600   # 10 min pro tier
MAX_FILESIZE_MB   = 150


def is_supported_url(url: str) -> bool:
    return any(d in url for d in SUPPORTED_DOMAINS)


def extract_video_info(url: str) -> Dict[str, Any]:
    """Estrai metadati senza scaricare."""
    try:
        import yt_dlp
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title":       info.get("title", ""),
                "uploader":    info.get("uploader", ""),
                "duration":    info.get("duration", 0),
                "view_count":  info.get("view_count", 0),
                "like_count":  info.get("like_count", 0),
                "upload_date": info.get("upload_date", ""),
                "description": (info.get("description") or "")[:500],
                "platform":    info.get("extractor_key", ""),
                "webpage_url": info.get("webpage_url", url),
                "thumbnail":   info.get("thumbnail", ""),
                "error":       None,
            }
    except Exception as e:
        return {"error": str(e)}


def download_video(url: str, output_dir: str, tier: str = "free") -> Dict[str, Any]:
    """Scarica video per analisi AURA."""
    result = {"path": None, "info": {}, "error": None}
    max_dur = MAX_DURATION_FREE if tier == "free" else MAX_DURATION_PRO

    try:
        import yt_dlp

        # Prima estrai info
        info = extract_video_info(url)
        if info.get("error"):
            result["error"] = f"Cannot fetch video info: {info['error']}"
            return result

        duration = info.get("duration", 0)
        if duration and duration > max_dur:
            result["error"] = f"Video too long ({duration}s). Max {max_dur}s for {tier} tier."
            return result

        result["info"] = info

        # Output path
        out_template = str(Path(output_dir) / "link_%(id)s.%(ext)s")

        ydl_opts = {
            "format":           "bestvideo[height<=720][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=480][vcodec^=avc]+bestaudio/best[height<=480][ext=mp4]/best[ext=mp4]/best",
            "format_sort":      ["vcodec:h264", "ext:mp4:m4a"],
            "outtmpl":          out_template,
            "quiet":            True,
            "no_warnings":      True,
            "nocheckcertificate": True,
            "proxy": f"http://{os.environ.get('PROXY_USER','')}:{os.environ.get('PROXY_PASS','')}@{os.environ.get('PROXY_HOST','')}:{os.environ.get('PROXY_PORT','')}/" if os.environ.get("PROXY_HOST") else None,
            "geo_bypass":        True,
            "sleep_interval":    1,
            "max_sleep_interval": 3,
            "max_filesize":     MAX_FILESIZE_MB * 1024 * 1024,
            "merge_output_format": "mp4",
            "postprocessors":   [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dl_info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(dl_info)
            # Gestisci estensione mp4
            if not Path(filename).exists():
                filename = filename.replace(".webm", ".mp4").replace(".mkv", ".mp4")

        if Path(filename).exists():
            result["path"] = filename
        else:
            # Cerca file scaricato nella dir
            files = sorted(Path(output_dir).glob("link_*.mp4"), key=os.path.getmtime, reverse=True)
            if files:
                result["path"] = str(files[0])
            else:
                result["error"] = "Downloaded file not found"

    except Exception as e:
        result["error"] = str(e)

    return result
