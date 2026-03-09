"""
AURA — Advanced Universal Reality Authentication
Core Analysis Engine v0.3
"""

import os
import uuid
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.analyzers.metadata import analyze_metadata
from app.analyzers.visual import analyze_frames
from app.analyzers.audio import analyze_audio_sync
from app.analyzers.signal import analyze_signal_physics
from app.analyzers.moire import analyze_moire
from app.analyzers.prnu import analyze_prnu
from app.report.generator import generate_pdf_report

app = FastAPI(
    title="AURA Reality Checker",
    description="Deepfake & Media Authenticity Analysis Engine",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("temp")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE_MB = 500
ALLOWED_TYPES = {
    "video/mp4", "video/quicktime", "video/x-msvideo", "video/avi", "video/msvideo", "video/x-matroska", "video/mkv", "video/webm",
    "application/octet-stream",
}


@app.get("/health")
def health():
    return {"status": "online", "engine": "AURA v0.3", "ready": True}


@app.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format: {file.content_type}. Accepted: MP4, MOV, AVI, WebM",
        )

    job_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix or ".mp4"
    video_path = UPLOAD_DIR / f"{job_id}{ext}"
    report_path = OUTPUT_DIR / f"AURA_Report_{job_id}.pdf"

    # Streaming write — non carica tutto in RAM
    size = 0
    with open(video_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            size += len(chunk)
            if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                f.close()
                os.remove(video_path)
                raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")
            f.write(chunk)

    start = time.time()
    try:
        metadata_result = analyze_metadata(str(video_path))
        visual_result   = await analyze_frames(str(video_path))
        audio_result    = analyze_audio_sync(str(video_path))
        signal_result   = analyze_signal_physics(str(video_path))
        moire_result    = analyze_moire(str(video_path))
        prnu_result     = analyze_prnu(str(video_path))
        elapsed         = round(time.time() - start, 2)

        verdict = compute_verdict(metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result)

        generate_pdf_report(
            output_path=str(report_path),
            job_id=job_id,
            filename=file.filename,
            video_path=str(video_path),
            metadata=metadata_result,
            visual=visual_result,
            audio=audio_result,
            signal=signal_result,
            moire=moire_result,
            prnu=prnu_result,
            verdict=verdict,
            elapsed=elapsed,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        background_tasks.add_task(cleanup_file, str(video_path))

    return JSONResponse({
        "job_id": job_id,
        "filename": file.filename,
        "analysis_time_seconds": elapsed,
        "verdict": verdict,
        "metadata_flags": metadata_result.get("flags", []),
        "visual_score": visual_result.get("deepfake_probability", 0),
        "audio_score": audio_result.get("sync_anomaly_score", 0),
        "signal_score": signal_result.get("ai_signal_score", 0),
        "screen_recording_score": moire_result.get("screen_recording_score", 0),
        "prnu_score": prnu_result.get("prnu_score", 0),
        "report_url": f"/report/{job_id}",
    })


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


def compute_verdict(metadata: dict, visual: dict, audio: dict, signal: dict, moire: dict, prnu: dict = None) -> dict:
    """
    Pesi v0.5 — Tiered verdicts con confidence bands.

    metadata : 0.10
    visual   : 0.10
    audio    : 0.10
    signal   : 0.35  (physics)
    moire    : 0.10  (screen recording)
    prnu     : 0.25  (sensor fingerprint)
    """
    weights = {"metadata": 0.10, "visual": 0.10, "audio": 0.10, "signal": 0.35, "moire": 0.10, "prnu": 0.25}

    meta_score   = metadata.get("manipulation_score", 0.0)
    visual_score = visual.get("deepfake_probability", 0.0)
    audio_score  = audio.get("sync_anomaly_score", 0.0)
    signal_score = signal.get("ai_signal_score", 0.0)
    moire_score  = moire.get("screen_recording_score", 0.0)
    prnu_score   = prnu.get("prnu_score", 0.0) if prnu else 0.0

    # Shield: azzera signal solo se è vera screen recording (non AI)
    is_screen_recording = moire_score >= 0.5 and prnu_score < 0.4
    if is_screen_recording:
        signal_score = 0.0

    composite = (
        meta_score   * weights["metadata"] +
        visual_score * weights["visual"] +
        audio_score  * weights["audio"] +
        signal_score * weights["signal"] +
        moire_score  * weights["moire"] +
        prnu_score   * weights["prnu"]
    )
    composite = round(composite, 3)

    # Conta layer indipendenti sopra soglia
    layers_flagged = sum([
        meta_score   > 0.30,
        visual_score > 0.40,
        audio_score  > 0.30,
        signal_score > 0.50,
        prnu_score   > 0.50,
    ])

    # Confidence: quanti layer concordano
    if layers_flagged >= 3:
        confidence_level = "HIGH"
        confidence_pct   = min(95, 70 + layers_flagged * 8)
    elif layers_flagged == 2:
        confidence_level = "MEDIUM"
        confidence_pct   = 60
    elif layers_flagged == 1:
        confidence_level = "LOW"
        confidence_pct   = 40
    else:
        confidence_level = "HIGH"
        confidence_pct   = min(95, int((1.0 - composite) * 100))

    # Tiered verdicts — 7 livelli
    if composite < 0.12:
        label = "AUTHENTIC"
        tier  = 1
        color = "green"
        interpretation = "Nessuna anomalia rilevata. Compatibile con registrazione diretta da sensore fisico."
    elif composite < 0.22:
        label = "PROBABLY AUTHENTIC"
        tier  = 2
        color = "green"
        interpretation = "Lievi anomalie (es. compressione social, WhatsApp). Non indicative di manipolazione."
    elif composite < 0.35:
        label = "MINOR EDITS DETECTED"
        tier  = 3
        color = "yellow"
        interpretation = "Tracce di post-produzione o recompressione. Possibile editing innocuo."
    elif composite < 0.50:
        label = "SUSPICIOUS"
        tier  = 4
        color = "yellow"
        interpretation = "Multipli segnali anomali. Richiede revisione manuale prima di accettare come prova."
    elif composite < 0.65:
        label = "LIKELY MANIPULATED"
        tier  = 5
        color = "orange"
        interpretation = "Forte evidenza di manipolazione o generazione AI. Non attendibile come prova primaria."
    elif composite < 0.80:
        label = "HIGHLY LIKELY SYNTHETIC"
        tier  = 6
        color = "red"
        interpretation = "Pattern fortemente indicativi di contenuto generato o alterato da AI."
    else:
        label = "SYNTHETIC / DEEPFAKE"
        tier  = 7
        color = "red"
        interpretation = "Evidenza convergente da layer multipli. Contenuto quasi certamente sintetico."

    return {
        "label": label,
        "tier": tier,
        "composite_score": composite,
        "risk_color": color,
        "confidence": confidence_level,
        "confidence_pct": confidence_pct,
        "layers_flagged": layers_flagged,
        "interpretation": interpretation,
        "breakdown": {
            "metadata_contribution":  round(meta_score   * weights["metadata"], 3),
            "visual_contribution":    round(visual_score * weights["visual"], 3),
            "audio_contribution":     round(audio_score  * weights["audio"], 3),
            "signal_contribution":    round(signal_score * weights["signal"], 3),
            "moire_contribution":     round(moire_score  * weights["moire"], 3),
            "prnu_contribution":      round(prnu_score   * weights["prnu"], 3),
        },
    }


def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass
