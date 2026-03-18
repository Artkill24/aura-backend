"use client";
import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

const STEPS = [
  { id: "download", label: "Download video",              icon: "◈" },
  { id: "meta",     label: "Metadata extraction",         icon: "◉" },
  { id: "visual",   label: "Visual frame analysis",       icon: "◈" },
  { id: "audio",    label: "Audio sync check",            icon: "◉" },
  { id: "signal",   label: "Signal physics",              icon: "◈" },
  { id: "prnu",     label: "PRNU sensor fingerprint",     icon: "◉" },
  { id: "vcam",     label: "Virtual cam detection",       icon: "◈" },
  { id: "rppg",     label: "rPPG cardiac signal",         icon: "◉" },
  { id: "semantic", label: "Semantic AI analysis",        icon: "◈" },
  { id: "report",   label: "Blockchain + PDF report",     icon: "◉" },
];

const UPLOAD_STEPS = STEPS.slice(1); // senza download

const SUPPORTED = ["youtube.com", "youtu.be", "x.com", "twitter.com", "tiktok.com", "vimeo.com", "instagram.com"];

function isSupportedUrl(url: string) {
  return SUPPORTED.some(d => url.includes(d));
}

export default function AnalyzePage() {
  const [tab, setTab]             = useState<"upload" | "link">("upload");
  const [dragging, setDragging]   = useState(false);
  const [file, setFile]           = useState<File | null>(null);
  const [linkUrl, setLinkUrl]     = useState("");
  const [linkValid, setLinkValid] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress]   = useState(0);
  const [stepIdx, setStepIdx]     = useState(0);
  const [error, setError]         = useState("");
  const [cameraMode, setCameraMode]   = useState(false);
  const [recording, setRecording]     = useState(false);
  const [cameraReady, setCameraReady] = useState(false);

  const inputRef    = useRef<HTMLInputElement>(null);
  const videoRef    = useRef<HTMLVideoElement>(null);
  const streamRef   = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef   = useRef<Blob[]>([]);
  const router      = useRouter();

  const CYAN = "#00e5ff";
  const RED  = "#ff2d55";
  const PURPLE = "#8247E5";

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith("video/") && !f.type.startsWith("image/")) {
      setError("Solo file video (MP4, MOV, AVI, MKV)"); return;
    }
    setError(""); setFile(f);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if (f) handleFile(f);
  }, [handleFile]);

  const handleLinkChange = (v: string) => {
    setLinkUrl(v);
    setLinkValid(isSupportedUrl(v));
    setError("");
  };

  const openCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });
      streamRef.current = stream;
      setCameraMode(true); setCameraReady(false);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => setCameraReady(true);
        }
      }, 100);
    } catch (err: unknown) {
      setError("Camera non disponibile: " + ((err as Error).message || "permesso negato"));
    }
  };

  const startRecording = () => {
    if (!streamRef.current) return;
    chunksRef.current = [];
    const mimeType = MediaRecorder.isTypeSupported("video/mp4") ? "video/mp4" : "video/webm";
    const recorder = new MediaRecorder(streamRef.current, { mimeType });
    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType });
      const ext = mimeType.includes("mp4") ? "mp4" : "webm";
      setFile(new File([blob], `aura_capture_${Date.now()}.${ext}`, { type: mimeType }));
      closeCamera();
    };
    recorder.start();
    recorderRef.current = recorder;
    setRecording(true);
  };

  const stopRecording = () => { recorderRef.current?.stop(); setRecording(false); };
  const closeCamera   = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setCameraMode(false); setCameraReady(false); setRecording(false);
  };

  const analyzeFile = async () => {
    if (!file) return;
    setUploading(true); setProgress(0); setStepIdx(0); setError("");
    const steps = UPLOAD_STEPS;
    const stepInterval = setInterval(() => setStepIdx(i => Math.min(i + 1, steps.length - 1)), 22000);
    const progInterval = setInterval(() => setProgress(p => p < 90 ? p + Math.random() * 2.5 : p), 600);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch("/api/backend/analyze", { method: "POST", body: fd, signal: AbortSignal.timeout(300000) });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      clearInterval(stepInterval); clearInterval(progInterval);
      setProgress(100);
      sessionStorage.setItem(`aura_result_${data.job_id}`, JSON.stringify(data));
      setTimeout(() => router.push(`/result/${data.job_id}`), 700);
    } catch (err: unknown) {
      clearInterval(stepInterval); clearInterval(progInterval);
      setUploading(false); setProgress(0); setStepIdx(0);
      setError((err as Error).message || "Analysis failed.");
    }
  };

  const analyzeLink = async () => {
    if (!linkUrl || !linkValid) return;
    setUploading(true); setProgress(0); setStepIdx(0); setError("");
    const steps = STEPS;
    const stepInterval = setInterval(() => setStepIdx(i => Math.min(i + 1, steps.length - 1)), 18000);
    const progInterval = setInterval(() => setProgress(p => p < 88 ? p + Math.random() * 2 : p), 600);
    try {
      const fd = new FormData();
      fd.append("url", linkUrl);
      fd.append("language", "it");
      const res = await fetch("/api/backend/analyze-link", { method: "POST", body: fd, signal: AbortSignal.timeout(300000) });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `Server error: ${res.status}` }));
        throw new Error(err.detail || `Server error: ${res.status}`);
      }
      const data = await res.json();
      clearInterval(stepInterval); clearInterval(progInterval);
      setProgress(100);
      sessionStorage.setItem(`aura_result_${data.job_id}`, JSON.stringify(data));
      setTimeout(() => router.push(`/result/${data.job_id}`), 700);
    } catch (err: unknown) {
      clearInterval(stepInterval); clearInterval(progInterval);
      setUploading(false); setProgress(0); setStepIdx(0);
      setError((err as Error).message || "Link analysis failed.");
    }
  };

  const activeSteps = tab === "link" ? STEPS : UPLOAD_STEPS;

  return (
    <div style={{ minHeight: "100vh", background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes scanline { from{transform:translateY(-100%)} to{transform:translateY(100vh)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        .btn-analyze:hover { background: #00c4d9 !important; box-shadow: 0 0 24px #00e5ff44 !important; }
        .btn-link:hover { background: #6a35c4 !important; box-shadow: 0 0 24px #8247E544 !important; }
        .btn-cam:hover { border-color: #00e5ff55 !important; color: #00e5ff !important; }
        .btn-clear:hover { border-color: #ffffff22 !important; color: #ccccdd !important; }
        .tab-btn:hover { color: #e8e8f0 !important; }
        ::-webkit-scrollbar { width: 3px; } ::-webkit-scrollbar-thumb { background: #00e5ff22; }
        .link-input:focus { outline: none; border-color: #8247E566 !important; }
        .drop-zone:hover { border-color: #00e5ff33 !important; }
      `}</style>

      {/* Grid bg */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", backgroundImage: `linear-gradient(#00e5ff05 1px, transparent 1px), linear-gradient(90deg, #00e5ff05 1px, transparent 1px)`, backgroundSize: "48px 48px", zIndex: 0 }} />
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden", opacity: 0.02 }}>
        <div style={{ position: "absolute", width: "100%", height: "2px", background: `linear-gradient(transparent, ${CYAN}, transparent)`, animation: "scanline 12s linear infinite" }} />
      </div>

      {/* NAV */}
      <nav style={{ position: "relative", zIndex: 10, borderBottom: "1px solid #ffffff06", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(5,5,8,0.9)", backdropFilter: "blur(12px)" }}>
        <a href="/" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
          <div style={{ width: "26px", height: "26px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em", color: "#e8e8f0" }}>AURA</span>
          <span style={{ color: "#ffffff18", fontSize: "10px" }}>v1.2</span>
        </a>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#00e87a", boxShadow: "0 0 8px #00e87a", animation: "pulse 3s infinite" }} />
          <span style={{ fontSize: "10px", color: "#333344", letterSpacing: "0.1em" }}>SISTEMA ONLINE</span>
        </div>
      </nav>

      {/* MAIN */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "3rem 1.5rem", position: "relative", zIndex: 1 }}>

        {/* Camera Modal */}
        {cameraMode && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(5,5,8,0.97)", zIndex: 200, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "1.5rem" }}>
            <div style={{ fontSize: "10px", color: recording ? RED : CYAN, letterSpacing: "0.2em", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
              {recording && <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: RED, display: "inline-block", animation: "pulse 1s infinite" }} />}
              {recording ? "REGISTRAZIONE IN CORSO" : cameraReady ? "CAMERA PRONTA" : "INIZIALIZZAZIONE..."}
            </div>
            <div style={{ position: "relative", border: `1px solid ${recording ? RED : cameraReady ? CYAN + "55" : "#ffffff08"}`, maxWidth: "540px", width: "100%" }}>
              {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
                <div key={v+h} style={{ position: "absolute", [v]: 8, [h]: 8, width: 12, height: 12,
                  borderTop: v==="top" ? `2px solid ${recording?RED:CYAN}` : "none",
                  borderBottom: v==="bottom" ? `2px solid ${recording?RED:CYAN}` : "none",
                  borderLeft: h==="left" ? `2px solid ${recording?RED:CYAN}` : "none",
                  borderRight: h==="right" ? `2px solid ${recording?RED:CYAN}` : "none",
                }} />
              ))}
              <video ref={videoRef} autoPlay muted playsInline style={{ width: "100%", display: "block", maxHeight: "340px", objectFit: "cover", background: "#000" }} />
            </div>
            <div style={{ display: "flex", gap: "12px" }}>
              {!recording ? (
                <button onClick={startRecording} disabled={!cameraReady} style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: 700, padding: "12px 28px", background: cameraReady ? RED : "#ffffff08", color: cameraReady ? "#fff" : "#333344", border: `1px solid ${cameraReady ? RED : "#ffffff08"}`, cursor: cameraReady ? "pointer" : "not-allowed", letterSpacing: "0.1em" }}>● INIZIA REC</button>
              ) : (
                <button onClick={stopRecording} style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: 700, padding: "12px 28px", background: RED, color: "#fff", border: `1px solid ${RED}`, cursor: "pointer", letterSpacing: "0.1em" }}>■ STOP E ANALIZZA</button>
              )}
              <button onClick={closeCamera} style={{ fontFamily: "inherit", fontSize: "11px", padding: "12px 16px", background: "transparent", color: "#444455", border: "1px solid #ffffff08", cursor: "pointer" }}>ANNULLA</button>
            </div>
          </div>
        )}

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem", animation: "fadeIn 0.5s ease both" }}>
          <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.2em", marginBottom: "0.75rem" }}>ADVANCED UNIVERSAL REALITY AUTHENTICATION</div>
          <h1 style={{ fontSize: "clamp(1.6rem, 4vw, 2.5rem)", fontWeight: 700, lineHeight: 1.1, marginBottom: "0.5rem" }}>
            Analisi Forense <span style={{ color: CYAN }}>Video</span>
          </h1>
          <p style={{ fontSize: "11px", color: "#333355", maxWidth: "440px", margin: "0 auto", lineHeight: 1.7 }}>
            9 layer · rPPG · C2PA EU AI Act · Blockchain Polygon · Semantic AI
          </p>
        </div>

        {/* TAB SWITCHER */}
        <div style={{ display: "flex", marginBottom: "1.5rem", border: "1px solid #ffffff08", background: "#07070d", animation: "fadeIn 0.5s ease 0.1s both" }}>
          <button
            className="tab-btn"
            onClick={() => { setTab("upload"); setError(""); }}
            style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: tab === "upload" ? 700 : 400, padding: "10px 24px", background: tab === "upload" ? "#0a141a" : "transparent", color: tab === "upload" ? CYAN : "#444455", border: "none", borderRight: "1px solid #ffffff08", cursor: "pointer", letterSpacing: "0.08em", borderBottom: tab === "upload" ? `2px solid ${CYAN}` : "2px solid transparent" }}
          >
            ▶ CARICA FILE
          </button>
          <button
            className="tab-btn"
            onClick={() => { setTab("link"); setError(""); }}
            style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: tab === "link" ? 700 : 400, padding: "10px 24px", background: tab === "link" ? "#0d0a18" : "transparent", color: tab === "link" ? PURPLE : "#444455", border: "none", cursor: "pointer", letterSpacing: "0.08em", borderBottom: tab === "link" ? `2px solid ${PURPLE}` : "2px solid transparent" }}
          >
            ⛓ ANALIZZA LINK
          </button>
        </div>

        {/* CONTENT */}
        <div style={{ width: "100%", maxWidth: "520px", animation: "fadeIn 0.5s ease 0.15s both" }}>
          {!uploading ? (
            <>
              {/* ── UPLOAD TAB ── */}
              {tab === "upload" && (
                <>
                  <div
                    className="drop-zone"
                    onClick={() => !file && inputRef.current?.click()}
                    onDrop={onDrop}
                    onDragOver={e => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    style={{ position: "relative", border: `1px solid ${dragging ? CYAN : file ? "#00e87a44" : "#ffffff08"}`, padding: "3rem 2rem", cursor: file ? "default" : "pointer", background: dragging ? "#00e5ff04" : file ? "#00e87a04" : "transparent", textAlign: "center", transition: "all 0.2s" }}
                  >
                    {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
                      <div key={v+h} style={{ position: "absolute", [v]: 6, [h]: 6, width: 10, height: 10,
                        borderTop: v==="top" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff18"}` : "none",
                        borderBottom: v==="bottom" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff18"}` : "none",
                        borderLeft: h==="left" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff18"}` : "none",
                        borderRight: h==="right" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff18"}` : "none",
                      }} />
                    ))}
                    {file ? (
                      <div>
                        <div style={{ fontSize: "24px", marginBottom: "0.5rem", color: "#00e87a" }}>✓</div>
                        <div style={{ fontSize: "10px", color: "#333355", letterSpacing: "0.1em", marginBottom: "0.4rem" }}>FILE CARICATO</div>
                        <div style={{ fontSize: "14px", color: "#e8e8f0", fontWeight: 600, marginBottom: "0.25rem" }}>{file.name}</div>
                        <div style={{ fontSize: "11px", color: "#333355" }}>{(file.size / 1024 / 1024).toFixed(1)} MB</div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ fontSize: "32px", marginBottom: "0.75rem", opacity: 0.15 }}>▶</div>
                        <div style={{ fontSize: "13px", color: "#ccccdd", marginBottom: "0.4rem" }}>{dragging ? "Rilascia il file" : "Trascina il video qui"}</div>
                        <div style={{ fontSize: "11px", color: "#333355" }}>o clicca per sfogliare · MP4, MOV, AVI, MKV</div>
                      </div>
                    )}
                  </div>
                  <input ref={inputRef} type="file" accept="video/*" style={{ display: "none" }} onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />

                  {!file && (
                    <button onClick={openCamera} className="btn-cam" style={{ width: "100%", marginTop: "8px", fontFamily: "inherit", fontSize: "12px", padding: "11px 24px", background: "transparent", color: "#333355", border: "1px solid #ffffff06", cursor: "pointer", letterSpacing: "0.1em", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", transition: "all 0.2s" }}>
                      <span>◉</span> CATTURA DA CAMERA
                    </button>
                  )}

                  {file && (
                    <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
                      <button onClick={analyzeFile} className="btn-analyze" style={{ flex: 1, fontFamily: "inherit", fontSize: "13px", fontWeight: 700, padding: "13px 24px", background: CYAN, color: "#050508", border: "none", cursor: "pointer", letterSpacing: "0.08em", transition: "all 0.2s" }}>
                        AVVIA ANALISI →
                      </button>
                      <button onClick={() => { setFile(null); setError(""); }} className="btn-clear" style={{ fontFamily: "inherit", fontSize: "11px", padding: "13px 14px", background: "transparent", color: "#333355", border: "1px solid #ffffff06", cursor: "pointer", transition: "all 0.2s" }}>✕</button>
                    </div>
                  )}
                </>
              )}

              {/* ── LINK TAB ── */}
              {tab === "link" && (
                <>
                  {/* URL input */}
                  <div style={{ position: "relative", marginBottom: "10px" }}>
                    <div style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)", fontSize: "14px", color: linkValid ? PURPLE : "#333355" }}>
                      {linkValid ? "⛓" : "◈"}
                    </div>
                    <input
                      className="link-input"
                      type="url"
                      placeholder="https://youtube.com/watch?v=... · X · TikTok · Vimeo"
                      value={linkUrl}
                      onChange={e => handleLinkChange(e.target.value)}
                      style={{ width: "100%", padding: "14px 14px 14px 40px", background: "#07070d", border: `1px solid ${linkValid ? PURPLE + "55" : "#ffffff08"}`, color: "#e8e8f0", fontFamily: "inherit", fontSize: "12px", letterSpacing: "0.04em", transition: "border-color 0.2s" }}
                    />
                    {linkValid && (
                      <div style={{ position: "absolute", right: "14px", top: "50%", transform: "translateY(-50%)", fontSize: "10px", color: PURPLE, fontWeight: 700, letterSpacing: "0.1em" }}>✓ OK</div>
                    )}
                  </div>

                  {/* Platform badges */}
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "16px" }}>
                    {["YouTube", "X/Twitter", "TikTok", "Vimeo", "Instagram"].map(p => (
                      <div key={p} style={{ fontSize: "9px", color: "#333355", border: "1px solid #ffffff06", padding: "3px 8px", letterSpacing: "0.08em" }}>{p}</div>
                    ))}
                    <div style={{ fontSize: "9px", color: "#222233", border: "1px solid #ffffff04", padding: "3px 8px", letterSpacing: "0.08em" }}>max 3 min free</div>
                  </div>

                  {/* Info box */}
                  <div style={{ border: `1px solid ${PURPLE}22`, background: `${PURPLE}08`, padding: "12px 14px", marginBottom: "12px", fontSize: "11px", color: "#555566", lineHeight: 1.7 }}>
                    <span style={{ color: PURPLE }}>⛓</span> Download · 9 layer forensi · Semantic AI · Blockchain Polygon<br />
                    <span style={{ color: "#333344" }}>Tempo stimato: 2-4 minuti · Report PDF con QR verificabile</span>
                  </div>

                  <button
                    onClick={analyzeLink}
                    disabled={!linkValid}
                    className={linkValid ? "btn-link" : ""}
                    style={{ width: "100%", fontFamily: "inherit", fontSize: "13px", fontWeight: 700, padding: "13px 24px", background: linkValid ? PURPLE : "#0a0a14", color: linkValid ? "#fff" : "#333344", border: `1px solid ${linkValid ? PURPLE : "#ffffff06"}`, cursor: linkValid ? "pointer" : "not-allowed", letterSpacing: "0.08em", transition: "all 0.2s" }}
                  >
                    {linkValid ? "ANALIZZA LINK →" : "INSERISCI URL VALIDO"}
                  </button>
                </>
              )}

              {/* Error */}
              {error && (
                <div style={{ marginTop: "12px", fontSize: "11px", color: RED, border: `1px solid ${RED}22`, padding: "10px 14px", background: `${RED}06`, display: "flex", gap: "8px" }}>
                  <span>⚠</span><span>{error}</span>
                </div>
              )}

              {/* Layer badges */}
              {!file && tab === "upload" && (
                <div style={{ marginTop: "2.5rem", display: "flex", flexWrap: "wrap", gap: "6px", justifyContent: "center" }}>
                  {["Metadata","Visual AI","Audio Sync","Signal Physics","Moiré","PRNU","Virtual Cam","rPPG Cardiac","C2PA"].map((l, i) => (
                    <div key={l} style={{ fontSize: "9px", color: i === 8 ? "#4455aa" : i % 2 === 0 ? CYAN + "99" : "#333355", border: `1px solid ${i === 8 ? "#2233aa44" : "#ffffff06"}`, padding: "3px 8px", letterSpacing: "0.06em" }}>{l}</div>
                  ))}
                </div>
              )}
            </>
          ) : (
            /* ── PROGRESS ── */
            <div style={{ border: `1px solid ${tab === "link" ? PURPLE + "33" : "#ffffff08"}`, background: "#07070d", padding: "2rem" }}>
              <div style={{ fontSize: "10px", color: tab === "link" ? PURPLE : CYAN, letterSpacing: "0.15em", marginBottom: "1.5rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ animation: "blink 1s infinite" }}>█</span>
                {tab === "link" ? "ANALISI LINK IN CORSO" : "ANALISI IN CORSO"}
              </div>

              {/* Progress bar */}
              <div style={{ marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#333355", marginBottom: "8px" }}>
                  <span>{activeSteps[stepIdx]?.label}</span>
                  <span style={{ color: tab === "link" ? PURPLE : CYAN }}>{Math.round(progress)}%</span>
                </div>
                <div style={{ height: "2px", background: "#ffffff06", width: "100%" }}>
                  <div style={{ height: "100%", width: `${progress}%`, background: tab === "link" ? `linear-gradient(90deg, ${PURPLE}, ${CYAN})` : `linear-gradient(90deg, ${CYAN}, #00e87a)`, transition: "width 0.5s ease", boxShadow: `0 0 12px ${tab === "link" ? PURPLE : CYAN}55` }} />
                </div>
              </div>

              {/* Steps */}
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "1.5rem" }}>
                {activeSteps.map((step, i) => {
                  const done   = i < stepIdx;
                  const active = i === stepIdx;
                  const accent = tab === "link" ? PURPLE : CYAN;
                  return (
                    <div key={step.id} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{ width: "16px", height: "16px", border: `1px solid ${done ? "#00e87a" : active ? accent : "#ffffff08"}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "8px", color: done ? "#00e87a" : active ? accent : "#222233", flexShrink: 0, transition: "all 0.3s" }}>
                        {done ? "✓" : active ? <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>◌</span> : step.icon}
                      </div>
                      <span style={{ fontSize: "10px", color: done ? "#00e87a44" : active ? accent : "#222233", transition: "color 0.3s", letterSpacing: "0.04em" }}>{step.label}</span>
                    </div>
                  );
                })}
              </div>

              <div style={{ fontSize: "10px", color: "#222233", borderTop: "1px solid #ffffff04", paddingTop: "1rem" }}>
                {tab === "link" ? (
                  <><span style={{ color: "#333344" }}>{linkUrl.slice(0, 50)}{linkUrl.length > 50 ? "..." : ""}</span><br /></>
                ) : (
                  <><span style={{ color: "#333344" }}>{file?.name}</span> · {((file?.size || 0) / 1024 / 1024).toFixed(1)} MB<br /></>
                )}
                <span style={{ color: "#ff2d5533" }}>█ Non chiudere questa finestra</span>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer style={{ position: "relative", zIndex: 1, borderTop: "1px solid #ffffff06", padding: "1rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "10px", color: "#1a1a2e", letterSpacing: "0.08em" }}>AURA v1.2 — NOT FOR CONSUMER USE</span>
        <a href="/" style={{ fontSize: "10px", color: "#222233", textDecoration: "none" }}>← Landing</a>
      </footer>
    </div>
  );
}
