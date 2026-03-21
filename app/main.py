from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone
"""
AURA — Advanced Universal Reality Authentication
Core Analysis Engine v0.3
"""

import os, tempfile, hashlib
import uuid
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.analyzers.metadata import analyze_metadata
from app.analyzers.visual import analyze_frames
from app.analyzers.audio import analyze_audio_sync
from app.analyzers.signal import analyze_signal_physics
from app.analyzers.moire import analyze_moire
from app.analyzers.prnu import analyze_prnu
from app.analyzers.virtual_cam import analyze_virtual_cam
from app.analyzers.heatmap import generate_forensic_heatmaps
from app.analyzers.forensic_inference import get_forensic_conclusion
from app.analyzers.ai_narrative import generate_forensic_narrative
from app.utils.blockchain import notarize_report, verify_on_chain
from app.utils.feedback import save_feedback, run_prompt_refinement
from app.utils.link_analyzer import download_video, extract_video_info, is_supported_url
from app.analyzers.semantic_ai import analyze_semantic, analyze_generative_origin
from app.analyzers.c2pa import check_c2pa
from app.analyzers.temporal_coherence import analyze_temporal_coherence
from app.utils.qr_verify import save_qr_png
from app.analyzers.rppg import analyze_rppg
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
    "video/mp4", "video/quicktime", "video/x-msvideo", "video/avi", "video/msvideo", "video/x-matroska", "video/mkv", "video/avi", "video/msvideo", "video/x-matroska", "video/mkv", "video/webm",
    "application/octet-stream",
}



def upload_pdf_to_supabase(pdf_path: str, job_id: str) -> str:
    """Upload PDF su Supabase Storage e ritorna URL pubblico."""
    try:
        from supabase import create_client
        sb = create_client(
            os.environ.get("SUPABASE_URL", "https://vtqrojazozbqbhgozbor.supabase.co"),
            os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0cXJvamF6b3picWJoZ296Ym9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NjIzNDMsImV4cCI6MjA4OTUzODM0M30.5oGA-s21e-JkN1faCVupinwxwC1bheuKppbFUvWZv5g")
        )
        filename = f"AURA_Report_{job_id}.pdf"
        with open(pdf_path, "rb") as f:
            sb.storage.from_("aura-reports").upload(
                filename, f.read(),
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
        url = sb.storage.from_("aura-reports").get_public_url(filename)
        return url
    except Exception as e:
        return ""


def save_analysis_to_db(job_id: str, filename: str, verdict_label: str,
                         composite_score: float, origin_verdict: str,
                         pdf_url: str, blockchain_tx: str = "", user_email: str = ""):
    """Salva analisi su Supabase per dashboard utente."""
    try:
        from supabase import create_client
        sb = create_client(
            os.environ.get("SUPABASE_URL", "https://vtqrojazozbqbhgozbor.supabase.co"),
            os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0cXJvamF6b3picWJoZ296Ym9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NjIzNDMsImV4cCI6MjA4OTUzODM0M30.5oGA-s21e-JkN1faCVupinwxwC1bheuKppbFUvWZv5g")
        )
        sb.table("aura_analyses").insert({
            "job_id": job_id, "user_email": user_email or "anonymous",
            "filename": filename[:200], "verdict_label": verdict_label,
            "composite_score": composite_score, "origin_verdict": origin_verdict,
            "pdf_url": pdf_url, "blockchain_tx": blockchain_tx,
        }).execute()
    except Exception:
        pass  # Non bloccare l'analisi se DB fallisce

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
    heatmaps = {}

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
    pdf_public_url = ""
    gen_origin = {}
    try:
        import hashlib as _hl
        file_sha256 = _hl.sha256(open(video_path,"rb").read()).hexdigest()
        temporal_result = analyze_temporal_coherence(str(video_path))
        c2pa_result     = check_c2pa(str(video_path))
        metadata_result = analyze_metadata(str(video_path))
        visual_result   = await analyze_frames(str(video_path))
        audio_result    = analyze_audio_sync(str(video_path))
        signal_result   = analyze_signal_physics(str(video_path))
        moire_result    = analyze_moire(str(video_path))
        prnu_result     = analyze_prnu(str(video_path))
        vcam_result     = analyze_virtual_cam(str(video_path))
        rppg_result     = analyze_rppg(str(video_path))
        verdict = compute_verdict(metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result, vcam_result, rppg_result, c2pa_result)
        forensic        = get_forensic_conclusion(metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result, vcam_result, rppg_result, verdict)
        elapsed         = round(time.time() - start, 2)

        # Salva metadata per endpoint /verify
        import json as _json
        _meta = {
            "verdict_label": verdict.get("label"),
            "composite_score": verdict.get("composite_score"),
            "filename": file.filename,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with open(OUTPUT_DIR / f"{job_id}_meta.json", "w") as _mf:
            _json.dump(_meta, _mf)

        # Genera QR code di verifica
        qr_path, verify_url = save_qr_png(job_id, file_sha256, str(OUTPUT_DIR))
        ai_narrative    = generate_forensic_narrative(verdict, metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result, vcam_result, rppg_result, forensic)
        # Blockchain notarization
        blockchain = notarize_report(
            job_id=job_id,
            sha256_hash=file_sha256,
            verdict=verdict.get("label","UNKNOWN"),
            score=verdict.get("composite_score",0)
        )

        heatmaps        = generate_forensic_heatmaps(str(video_path), str(OUTPUT_DIR), job_id)

        gen_origin = analyze_generative_origin(
            video_path=str(video_path),
            layer_scores={
                "signal": signal_result.get("ai_signal_score",0),
                "prnu": prnu_result.get("prnu_score",0) if prnu_result else 0,
                "rppg": rppg_result.get("rppg_score",0) if rppg_result else 0,
                "vcam": vcam_result.get("virtual_cam_score",0) if vcam_result else 0,
                "visual": visual_result.get("deepfake_probability",0),
            }
        )
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
            vcam=vcam_result,
            heatmaps=heatmaps,
            rppg=rppg_result,
            forensic=forensic,
            qr_path=qr_path,
            ai_narrative=ai_narrative.get("narrative"),
            blockchain=blockchain,
            gen_origin=gen_origin,
            verify_url=verify_url,
            verdict=verdict,
            elapsed=elapsed,
        )

        # Upload PDF su Supabase Storage
        pdf_public_url = upload_pdf_to_supabase(str(report_path), job_id)
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
        "virtual_cam_score": vcam_result.get("virtual_cam_score", 0),
            "rppg_score": rppg_result.get("rppg_score", 0),
            "rppg_bpm": rppg_result.get("bpm_detected"),
            "rppg_quality": rppg_result.get("signal_quality"),
            "forensic_conclusion": forensic,
            "verify_url": verify_url,
            "ai_narrative": ai_narrative.get("narrative"),
            "ai_model": ai_narrative.get("model"),
            "blockchain": blockchain,
            "c2pa": c2pa_result,
        "generative_origin": gen_origin,
        "temporal_coherence": temporal_result,
        "report_url": f"/report/{job_id}",
        "pdf_url": pdf_public_url if pdf_public_url else f"/report/{job_id}",
    })






@app.post("/analyze-link")
async def analyze_link(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    language: str = Form(default="it"),
):
    """Analisi forense da URL (YouTube, X, TikTok, Vimeo...)."""
    if not is_supported_url(url):
        raise HTTPException(status_code=400, detail=f"URL non supportato. Piattaforme: YouTube, X, TikTok, Vimeo, Instagram")

    job_id   = str(uuid.uuid4())
    tmp_dir  = tempfile.mkdtemp()
    report_path = OUTPUT_DIR / f"{job_id}.pdf"

    temporal_result = {}
    pdf_link_url = ""
    try:
        # Download video
        dl = download_video(url, tmp_dir, tier="free")
        if dl.get("error") or not dl.get("path"):
            raise HTTPException(status_code=422, detail=f"Download failed: {dl.get('error','unknown')}")

        video_path = dl["path"]
        video_info = dl["info"]
        file_sha256 = hashlib.sha256(open(video_path,"rb").read()).hexdigest()

        # Pipeline forense standard (stessa di /analyze)
        c2pa_result     = check_c2pa(video_path)
        metadata_result = analyze_metadata(video_path)
        visual_result   = await analyze_frames(video_path)
        audio_result    = analyze_audio_sync(video_path)
        signal_result   = analyze_signal_physics(video_path)
        moire_result    = analyze_moire(video_path)
        prnu_result     = analyze_prnu(video_path)
        vcam_result     = analyze_virtual_cam(video_path)
        rppg_result     = analyze_rppg(video_path)

        verdict  = compute_verdict(metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result, vcam_result, rppg_result, c2pa_result, temporal_result)
        forensic = get_forensic_conclusion(metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result, vcam_result, rppg_result, verdict)
        elapsed  = 0

        # Layer scores per semantic
        layer_scores = {
            "signal":   signal_result.get("ai_signal_score", 0),
            "prnu":     prnu_result.get("prnu_score", 0) if prnu_result else 0,
            "rppg":     rppg_result.get("rppg_score", 0) if rppg_result else 0,
            "vcam":     vcam_result.get("virtual_cam_score", 0) if vcam_result else 0,
            "visual":   visual_result.get("deepfake_probability", 0),
        }

        # Layer 11 Temporal Coherence
        temporal_result = analyze_temporal_coherence(video_path)

        # Layer 11 Temporal Coherence

        # Layer 10 Generative Origin
        gen_origin = analyze_generative_origin(
            video_path=video_path,
            layer_scores=layer_scores,
        )

        # Semantic AI (Qwen2-VL o Groq fallback)
        semantic = analyze_semantic(
            video_path=video_path,
            url=url,
            video_info=video_info,
            layer_scores=layer_scores,
            language=language,
        )

        # AI narrative + blockchain + QR
        ai_narrative = generate_forensic_narrative(verdict, metadata_result, visual_result, audio_result, signal_result, moire_result, prnu_result, vcam_result, rppg_result, forensic, language=language)
        blockchain   = notarize_report(job_id=job_id, sha256_hash=file_sha256, verdict=verdict.get("label","UNKNOWN"), score=verdict.get("composite_score",0))
        qr_path, verify_url = save_qr_png(job_id, file_sha256, str(OUTPUT_DIR))
        heatmaps = generate_forensic_heatmaps(video_path, str(OUTPUT_DIR), job_id)

        generate_pdf_report(
            output_path=str(report_path),
            job_id=job_id,
            filename=url,
            video_path=video_path,
            metadata=metadata_result,
            visual=visual_result,
            audio=audio_result,
            signal=signal_result,
            moire=moire_result,
            prnu=prnu_result,
            vcam=vcam_result,
            heatmaps=heatmaps,
            rppg=rppg_result,
            forensic=forensic,
            qr_path=qr_path,
            ai_narrative=ai_narrative.get("narrative"),
            blockchain=blockchain,
            gen_origin=gen_origin,
            verify_url=verify_url,
            verdict=verdict,
            elapsed=elapsed,
        )

        pdf_link_url = upload_pdf_to_supabase(str(report_path), job_id)

        # Salva meta per /verify
        import json as _json
        with open(OUTPUT_DIR / f"{job_id}_meta.json", "w") as _mf:
            _json.dump({"verdict_label": verdict.get("label"), "composite_score": verdict.get("composite_score"), "filename": url, "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, _mf)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Link analysis failed: {str(e)}")
    finally:
        background_tasks.add_task(cleanup_file, tmp_dir)

    return JSONResponse({
        "job_id":       job_id,
        "url":          url,
        "video_info":   video_info,
        "verdict":      verdict,
        "semantic_ai":  semantic,
        "blockchain":   blockchain,
        "c2pa":         c2pa_result,
            "generative_origin": gen_origin,
        "temporal_coherence": temporal_result,
        "pdf_url": pdf_link_url if pdf_link_url else None,
        "report_url":   f"/report/{job_id}",
        "verify_url":   verify_url,
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



@app.post("/feedback")
async def submit_feedback(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    feedback: str = Form(...),
    verdict_label: str = Form(default=""),
    composite_score: float = Form(default=0.0),
    origin_verdict: str = Form(default=""),
    attack_vector: str = Form(default=""),
    comment: str = Form(default=""),
):
    """Salva feedback utente + triggera refinement automatico ogni 20 feedback."""
    result = save_feedback(
        job_id=job_id,
        feedback=feedback,
        verdict_label=verdict_label,
        composite_score=composite_score,
        origin_verdict=origin_verdict,
        attack_vector=attack_vector,
        comment=comment,
    )
    if result.get("trigger_refinement"):
        background_tasks.add_task(run_prompt_refinement)
    return JSONResponse({
        "saved": result["saved"],
        "error": result["error"],
        "refinement_triggered": result.get("trigger_refinement", False),
    })

@app.get("/verify/{job_id}")
async def verify_report(job_id: str, h: str = ""):
    # Check on-chain
    on_chain = verify_on_chain(job_id)
    """Endpoint di verifica pubblica — scansionato dal QR nel PDF."""
    report_path = OUTPUT_DIR / f"AURA_Report_{job_id}.pdf"
    
    if not report_path.exists():
        return {
            "status": "NOT_FOUND",
            "job_id": job_id,
            "message": "Report non trovato o scaduto.",
        }
    
    # Ricalcola hash del PDF
    import hashlib
    with open(report_path, "rb") as f:
        pdf_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Cerca metadata dal job (se salvato)
    meta_path = OUTPUT_DIR / f"{job_id}_meta.json"
    meta = {}
    if meta_path.exists():
        import json
        with open(meta_path) as f:
            meta = json.load(f)
    
    hash_match = pdf_hash[:16] == h if h else None
    
    return {
        "status": "VERIFIED" if hash_match else "UNVERIFIED",
        "job_id": job_id,
        "pdf_sha256_prefix": pdf_hash[:16],
        "hash_match": hash_match,
        "on_chain": on_chain,
        "verdict": meta.get("verdict_label", "N/A"),
        "composite_score": meta.get("composite_score", "N/A"),
        "filename": meta.get("filename", "N/A"),
        "analysis_timestamp": meta.get("timestamp", "N/A"),
        "engine": "AURA Reality Firewall v0.7.0",
        "message": "✅ Report autentico — hash verificato." if hash_match else "⚠️ Hash non corrispondente — report potrebbe essere stato modificato.",
    }


def compute_verdict(metadata: dict, visual: dict, audio: dict, signal: dict, moire: dict, prnu: dict = None, vcam: dict = None, rppg: dict = None, c2pa_result: dict = None, temporal: dict = None) -> dict:
    """
    Pesi v0.5 — Tiered verdicts con confidence bands.

    metadata : 0.10
    visual   : 0.10
    audio    : 0.10
    signal   : 0.30  (physics)
    moire    : 0.08  (screen recording)
    prnu     : 0.22  (sensor fingerprint)
    vcam     : 0.20  (virtual camera)
    """
    weights = {"metadata": 0.07, "visual": 0.05, "audio": 0.07, "signal": 0.22, "moire": 0.07, "prnu": 0.12, "vcam": 0.11, "rppg": 0.16, "c2pa": 0.08, "temporal": 0.05}

    meta_score   = metadata.get("manipulation_score", 0.0)
    visual_score = visual.get("deepfake_probability", 0.0)
    audio_score  = audio.get("sync_anomaly_score", 0.0)
    signal_score = signal.get("ai_signal_score", 0.0)
    moire_score  = moire.get("screen_recording_score", 0.0)
    prnu_score   = prnu.get("prnu_score", 0.0) if prnu else 0.0
    vcam_score   = vcam.get("virtual_cam_score", 0.0) if vcam else 0.0
    rppg_score   = rppg.get("rppg_score", 0.0) if rppg else 0.0
    c2pa_score     = c2pa_result.get("c2pa_score", 0.35) if c2pa_result else 0.35
    temporal_score = temporal.get("temporal_score", 0.20) if temporal else 0.20

    # Shield: azzera signal solo se è vera screen recording (non AI)
    is_screen_recording = moire_score >= 0.5 and prnu_score < 0.4
    if is_screen_recording:
        signal_score = 0.0
        visual_score = min(visual_score, 0.20)

    composite = (
        meta_score   * weights["metadata"] +
        visual_score * weights["visual"] +
        audio_score  * weights["audio"] +
        signal_score * weights["signal"] +
        moire_score  * weights["moire"] +
        prnu_score   * weights["prnu"] +
        vcam_score   * weights["vcam"] +
        rppg_score   * weights["rppg"] +
        c2pa_score   * weights["c2pa"] +
        temporal_score * weights["temporal"]
    )
    composite = round(composite, 3)

    # Conta layer indipendenti sopra soglia
    layers_flagged = sum([
        meta_score   > 0.30,
        visual_score > 0.40,
        audio_score  > 0.30,
        signal_score > 0.50,
        prnu_score   > 0.50,
        vcam_score   > 0.50,
        rppg_score   > 0.60,
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
            "vcam_contribution":      round(vcam_score   * weights["vcam"], 3),
            "rppg_contribution":      round(rppg_score   * weights["rppg"], 3),
        },
    }


def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass
