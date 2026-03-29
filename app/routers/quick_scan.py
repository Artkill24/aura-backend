"""
AURA Quick Scan — Pre-scansione consumer leggera
4 layer veloci, risultato in <30s, semaforo verde/giallo/rosso.
"""
import os, time, uuid, tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path

from app.analyzers.metadata import analyze_metadata
from app.analyzers.signal import analyze_signal_physics
from app.analyzers.c2pa import check_c2pa
from app.analyzers.semantic_ai import analyze_generative_origin

router = APIRouter()

async def _quick_analyze(video_path: str) -> dict:
    meta   = analyze_metadata(video_path)
    signal = analyze_signal_physics(video_path)
    c2pa   = check_c2pa(video_path)
    origin = analyze_generative_origin(
        video_path=video_path,
        layer_scores={"signal": signal.get("ai_signal_score", 0)}
    )

    meta_score   = meta.get("manipulation_score", 0.0)
    signal_score = signal.get("ai_signal_score", 0.0)
    c2pa_score   = c2pa.get("c2pa_score", 0.35)
    ai_prob      = origin.get("probability_ai", 0.35) if origin else 0.35

    composite = round(
        meta_score   * 0.15 +
        signal_score * 0.35 +
        c2pa_score   * 0.15 +
        ai_prob      * 0.35, 3
    )

    if composite < 0.25:
        traffic_light = "green"
        label   = "AUTENTICO"
        message = "Nessuna anomalia significativa rilevata. Il video sembra autentico."
    elif composite < 0.50:
        traffic_light = "yellow"
        label   = "DUBBIO"
        message = "Rilevate alcune anomalie. Potrebbe essere editato o manipolato parzialmente."
    else:
        traffic_light = "red"
        label   = "SOSPETTO"
        message = "Anomalie significative rilevate. Alto rischio di manipolazione AI o deepfake."

    reasons = []
    if signal_score > 0.5:
        reasons.append("Pattern di compressione anomali nel segnale video")
    if c2pa_score > 0.3:
        reasons.append("Nessuna firma C2PA — provenienza non verificabile")
    if ai_prob > 0.6:
        reasons.append(f"Origine AI probabile ({ai_prob:.0%})")
    if meta_score > 0.3:
        reasons.append("Metadati dispositivo assenti o anomali")
    if not reasons:
        reasons.append("Nessuna anomalia critica rilevata")

    return {
        "composite": composite, "traffic_light": traffic_light,
        "label": label, "message": message, "reasons": reasons[:3],
        "origin": origin.get("origin_verdict", "UNCERTAIN") if origin else "UNCERTAIN",
        "upgrade_hint": composite > 0.3,
    }


@router.post("/quick-scan")
async def quick_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    url: str = Form(default=""),
):
    start = time.time()
    job_id = str(uuid.uuid4())[:8]
    tmp_path = None

    try:
        if file and file.filename:
            content = await file.read()
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File troppo grande (max 50MB)")
            suffix = Path(file.filename).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(content)
                tmp_path = f.name
        elif url:
            from app.utils.link_analyzer import download_video
            tmp_dir = tempfile.mkdtemp()
            dl = download_video(url, tmp_dir, tier="free")
            if dl.get("error"):
                raise HTTPException(status_code=422, detail=f"Download failed: {dl['error']}")
            tmp_path = dl["path"]
        else:
            raise HTTPException(status_code=400, detail="Fornisci file o URL")

        result = await _quick_analyze(tmp_path)
        elapsed = round(time.time() - start, 1)

        return JSONResponse({
            "job_id": job_id, "elapsed": elapsed,
            "traffic_light": result["traffic_light"],
            "label": result["label"],
            "message": result["message"],
            "score": result["composite"],
            "reasons": result["reasons"],
            "origin": result["origin"],
            "upgrade_hint": result["upgrade_hint"],
            "full_analysis": "/analyze",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(os.remove, tmp_path)
