"""AURA Memory — persistent forensic memory on CockroachDB.

Writes job state + verdict + embedding for every analysis, and
recalls similar past detections via vector search.
Fail-open: if the memory layer is unreachable, analysis proceeds.
"""
import base64
import hashlib
import json
import logging
import os

log = logging.getLogger("aura.memory")

_ENABLED = bool(os.environ.get("DATABASE_URL"))


def _conn():
    import psycopg
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=10)


def _embed_keyframe(video_path: str) -> list | None:
    """1024-dim Titan embedding of the first keyframe (fail-open)."""
    try:
        import boto3
        import cv2
        cap = cv2.VideoCapture(video_path)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return None
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            return None
        b64 = base64.b64encode(buf.tobytes()).decode()
        bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
        resp = bedrock.invoke_model(
            modelId="amazon.titan-embed-image-v1",
            body=json.dumps({"inputImage": b64}),
        )
        return json.loads(resp["body"].read())["embedding"]
    except Exception as e:
        log.warning(f"memory: embedding failed (non-blocking): {e}")
        return None


def job_start(job_id: str, filename: str, file_path: str) -> None:
    if not _ENABLED:
        return
    try:
        media_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
        with _conn() as conn:
            conn.execute(
                """INSERT INTO detections
                   (detection_id, media_hash, media_type, filename, verdict, status)
                   VALUES (%s, %s, 'video', %s, 'pending', 'running')
                   ON CONFLICT (detection_id) DO NOTHING""",
                (job_id, media_hash, filename),
            )
            conn.commit()
    except Exception as e:
        log.warning(f"memory: job_start failed (non-blocking): {e}")


def job_done(job_id: str, verdict: dict, gen_origin: dict,
             pdf_url: str, file_path: str) -> list:
    """Complete the job row and return similar past detections."""
    if not _ENABLED:
        return []
    matches = []
    try:
        emb = _embed_keyframe(file_path)
        emb_str = str(emb) if emb else None
        layer_scores = json.dumps({
            "composite": verdict.get("composite_score"),
            "label": verdict.get("label"),
            "confidence_level": verdict.get("confidence_level"),
            "origin_verdict": (gen_origin or {}).get("origin_verdict"),
            "probability_ai": (gen_origin or {}).get("probability_ai"),
            "reconciled": verdict.get("reconciled", False),
        })
        with _conn() as conn:
            if emb_str:
                matches = conn.execute(
                    """SELECT media_hash, verdict, composite_score, filename,
                              created_at::STRING, embedding <=> %s AS distance
                       FROM detections
                       WHERE embedding IS NOT NULL AND detection_id != %s
                       ORDER BY embedding <=> %s
                       LIMIT 5""",
                    (emb_str, job_id, emb_str),
                ).fetchall()
            conn.execute(
                """UPDATE detections SET
                     status = 'done',
                     verdict = %s,
                     composite_score = %s,
                     suspected_generator = %s,
                     layer_scores = %s,
                     embedding = COALESCE(%s, embedding),
                     pdf_url = %s,
                     updated_at = now()
                   WHERE detection_id = %s""",
                (verdict.get("label", "UNKNOWN"),
                 verdict.get("composite_score"),
                 (gen_origin or {}).get("generative_tool_likely"),
                 layer_scores, emb_str, pdf_url, job_id),
            )
            conn.commit()
    except Exception as e:
        log.warning(f"memory: job_done failed (non-blocking): {e}")
    return [
        {"hash": m[0][:12], "verdict": m[1],
         "score": float(m[2]) if m[2] is not None else None,
         "filename": m[3], "seen_at": m[4],
         "distance": round(float(m[5]), 4)}
        for m in matches
    ]


def job_failed(job_id: str, reason: str) -> None:
    if not _ENABLED:
        return
    try:
        with _conn() as conn:
            conn.execute(
                """UPDATE detections SET status='failed',
                   layer_scores = jsonb_build_object('error', %s::STRING),
                   updated_at = now() WHERE detection_id = %s""",
                (reason[:500], job_id),
            )
            conn.commit()
    except Exception as e:
        log.warning(f"memory: job_failed failed (non-blocking): {e}")
