"""
AURA — Advanced Universal Reality Authentication
Core Analysis Engine v0.1 (MVP)
"""

import os
import uuid
import time
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import shutil

from app.analyzers.metadata import analyze_metadata
from app.analyzers.visual import analyze_frames
from app.analyzers.audio import analyze_audio_sync
from app.report.generator import generate_pdf_report

# ─────────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="AURA Reality Checker",
    description="Deepfake & Media Authenticity Analysis Engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("temp")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE_MB = 100
ALLOWED_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}


# ─────────────────────────────────────────────
#  Health Check
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "online", "engine": "AURA v0.1", "ready": True}


# ─────────────────────────────────────────────
#  Main Analysis Endpoint
# ─────────────────────────────────────────────
@app.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # — Validation —
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format: {file.content_type}. Accepted: MP4, MOV, AVI, WebM",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    # — Save temp file —
    job_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix or ".mp4"
    video_path = UPLOAD_DIR / f"{job_id}{ext}"
    report_path = OUTPUT_DIR / f"AURA_Report_{job_id}.pdf"

    with open(video_path, "wb") as f:
        f.write(content)

    # — Run analysis pipeline —
    start = time.time()
    try:
        metadata_result = analyze_metadata(str(video_path))
        visual_result   = await analyze_frames(str(video_path))
        audio_result    = analyze_audio_sync(str(video_path))
        elapsed         = round(time.time() - start, 2)

        # — Build composite verdict —
        verdict = compute_verdict(metadata_result, visual_result, audio_result)

        # — Generate PDF report —
        generate_pdf_report(
            output_path=str(report_path),
            job_id=job_id,
            filename=file.filename,
            metadata=metadata_result,
            visual=visual_result,
            audio=audio_result,
            verdict=verdict,
            elapsed=elapsed,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        # Cleanup temp video after response
        background_tasks.add_task(cleanup_file, str(video_path))

    # — Return JSON summary + report link —
    return JSONResponse({
        "job_id": job_id,
        "filename": file.filename,
        "analysis_time_seconds": elapsed,
        "verdict": verdict,
        "metadata_flags": metadata_result.get("flags", []),
        "visual_score": visual_result.get("deepfake_probability", 0),
        "audio_score": audio_result.get("sync_anomaly_score", 0),
        "report_url": f"/report/{job_id}",
    })


# ─────────────────────────────────────────────
#  Report Download
# ─────────────────────────────────────────────
@app.get("/report/{job_id}")
def get_report(job_id: str):
    report_path = OUTPUT_DIR / f"AURA_Report_{job_id}.pdf"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=f"AURA_Report_{job_id}.pdf",
    )


# ─────────────────────────────────────────────
#  Verdict Logic
# ─────────────────────────────────────────────
def compute_verdict(metadata: dict, visual: dict, audio: dict) -> dict:
    """
    Composite risk scoring across three analysis layers.
    Each layer contributes weighted to the final score.
    """
    weights = {"metadata": 0.25, "visual": 0.50, "audio": 0.25}

    meta_score   = metadata.get("manipulation_score", 0.0)
    visual_score = visual.get("deepfake_probability", 0.0)
    audio_score  = audio.get("sync_anomaly_score", 0.0)

    composite = (
        meta_score   * weights["metadata"] +
        visual_score * weights["visual"] +
        audio_score  * weights["audio"]
    )
    composite = round(composite, 3)

    if composite < 0.25:
        label, color, confidence = "AUTHENTIC", "green", "HIGH"
    elif composite < 0.55:
        label, color, confidence = "SUSPICIOUS", "yellow", "MEDIUM"
    elif composite < 0.75:
        label, color, confidence = "LIKELY MANIPULATED", "orange", "HIGH"
    else:
        label, color, confidence = "SYNTHETIC / DEEPFAKE", "red", "HIGH"

    return {
        "label": label,
        "composite_score": composite,
        "risk_color": color,
        "confidence": confidence,
        "breakdown": {
            "metadata_contribution": round(meta_score * weights["metadata"], 3),
            "visual_contribution":   round(visual_score * weights["visual"], 3),
            "audio_contribution":    round(audio_score * weights["audio"], 3),
        },
    }


# ─────────────────────────────────────────────
#  Cleanup
# ─────────────────────────────────────────────
def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass
