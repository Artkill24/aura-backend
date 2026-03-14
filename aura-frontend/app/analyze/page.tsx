"use client";
import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

const STEPS = [
  { id: "meta",    label: "Metadata extraction",       icon: "◈" },
  { id: "visual",  label: "Visual frame analysis",      icon: "◉" },
  { id: "audio",   label: "Audio sync check",           icon: "◈" },
  { id: "signal",  label: "Signal physics",             icon: "◉" },
  { id: "prnu",    label: "PRNU sensor fingerprint",    icon: "◈" },
  { id: "vcam",    label: "Virtual cam detection",      icon: "◉" },
  { id: "rppg",    label: "rPPG cardiac signal",        icon: "◈" },
  { id: "report",  label: "AI narrative + PDF report",  icon: "◉" },
];

export default function AnalyzePage() {
  const [dragging, setDragging]   = useState(false);
  const [file, setFile]           = useState<File | null>(null);
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
    const mimeType = MediaRecorder.isTypeSupported("video/mp4") ? "video/mp4"
      : MediaRecorder.isTypeSupported("video/webm;codecs=vp9") ? "video/webm;codecs=vp9"
      : "video/webm";
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

  const analyze = async () => {
    if (!file) return;
    setUploading(true); setProgress(0); setStepIdx(0); setError("");

    const stepInterval = setInterval(() => {
      setStepIdx(i => Math.min(i + 1, STEPS.length - 1));
    }, 22000);
    const progInterval = setInterval(() => {
      setProgress(p => p < 90 ? p + Math.random() * 2.5 : p);
    }, 600);

    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch("/api/backend/analyze", {
        method: "POST", body: fd, signal: AbortSignal.timeout(300000),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      clearInterval(stepInterval); clearInterval(progInterval);
      setProgress(100); setStepIdx(STEPS.length - 1);
      sessionStorage.setItem(`aura_result_${data.job_id}`, JSON.stringify(data));
      setTimeout(() => router.push(`/result/${data.job_id}`), 700);
    } catch (err: unknown) {
      clearInterval(stepInterval); clearInterval(progInterval);
      setUploading(false); setProgress(0); setStepIdx(0);
      setError((err as Error).message || "Analysis failed.");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes scanline { from{transform:translateY(-100%)} to{transform:translateY(100vh)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
        .drop-zone:hover { border-color: #00e5ff44 !important; }
        .btn-analyze:hover { background: #00c4d9 !important; box-shadow: 0 0 24px #00e5ff44 !important; }
        .btn-cam:hover { border-color: #00e5ff66 !important; color: #00e5ff !important; background: #00e5ff08 !important; }
        .btn-clear:hover { border-color: #ffffff22 !important; color: #ccccdd !important; }
        ::-webkit-scrollbar { width: 3px; } ::-webkit-scrollbar-thumb { background: #00e5ff22; }
      `}</style>

      {/* Grid bg */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", backgroundImage: `linear-gradient(#00e5ff06 1px, transparent 1px), linear-gradient(90deg, #00e5ff06 1px, transparent 1px)`, backgroundSize: "48px 48px", zIndex: 0 }} />

      {/* Scanline */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden", opacity: 0.025 }}>
        <div style={{ position: "absolute", width: "100%", height: "2px", background: `linear-gradient(transparent, ${CYAN}, transparent)`, animation: "scanline 10s linear infinite" }} />
      </div>

      {/* NAV */}
      <nav style={{ position: "relative", zIndex: 10, borderBottom: "1px solid #ffffff08", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(5,5,8,0.9)", backdropFilter: "blur(12px)" }}>
        <a href="/" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
          <div style={{ width: "26px", height: "26px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em", color: "#e8e8f0" }}>AURA</span>
          <span style={{ color: "#ffffff22", fontSize: "10px" }}>v0.9</span>
        </a>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#00e87a", boxShadow: "0 0 8px #00e87a", animation: "pulse 3s infinite" }} />
          <span style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.1em" }}>SISTEMA ONLINE</span>
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
            <div style={{ position: "relative", border: `1px solid ${recording ? RED : cameraReady ? CYAN + "66" : "#ffffff0a"}`, maxWidth: "540px", width: "100%" }}>
              {/* Corners */}
              {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
                <div key={v+h} style={{ position: "absolute", [v]: 8, [h]: 8, width: 14, height: 14,
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
                <button onClick={startRecording} disabled={!cameraReady} style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: 700, padding: "12px 28px", background: cameraReady ? RED : "#ffffff08", color: cameraReady ? "#fff" : "#444455", border: `1px solid ${cameraReady ? RED : "#ffffff08"}`, cursor: cameraReady ? "pointer" : "not-allowed", letterSpacing: "0.1em" }}>
                  ● INIZIA REC
                </button>
              ) : (
                <button onClick={stopRecording} style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: 700, padding: "12px 28px", background: RED, color: "#fff", border: `1px solid ${RED}`, cursor: "pointer", letterSpacing: "0.1em" }}>
                  ■ STOP E ANALIZZA
                </button>
              )}
              <button onClick={closeCamera} style={{ fontFamily: "inherit", fontSize: "11px", padding: "12px 16px", background: "transparent", color: "#444455", border: "1px solid #ffffff08", cursor: "pointer" }}>ANNULLA</button>
            </div>
            <p style={{ fontSize: "11px", color: "#444455" }}>{recording ? "Premi STOP quando hai finito — il video sarà analizzato automaticamente" : "Punta la camera sul soggetto · Premi INIZIA REC"}</p>
          </div>
        )}

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "3rem", animation: "fadeIn 0.5s ease both" }}>
          <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.2em", marginBottom: "1rem" }}>ADVANCED UNIVERSAL REALITY AUTHENTICATION</div>
          <h1 style={{ fontSize: "clamp(1.8rem, 5vw, 3rem)", fontWeight: 700, lineHeight: 1.1, marginBottom: "0.75rem" }}>
            Analisi Forense<br />
            <span style={{ color: CYAN }}>Video Evidence</span>
          </h1>
          <p style={{ fontSize: "12px", color: "#444455", lineHeight: 1.8, maxWidth: "480px", margin: "0 auto" }}>
            8 layer · metadata · visual · audio · signal physics · moiré · PRNU · virtual cam · rPPG<br />
            Per periti assicurativi, studi legali e forensics professionals.
          </p>
        </div>

        {/* Upload / Analysis area */}
        <div style={{ width: "100%", maxWidth: "520px", animation: "fadeIn 0.5s ease 0.1s both" }}>

          {!uploading ? (
            <>
              {/* Drop zone */}
              <div
                className="drop-zone"
                onClick={() => !file && inputRef.current?.click()}
                onDrop={onDrop}
                onDragOver={e => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                style={{
                  position: "relative", border: `1px solid ${dragging ? CYAN : file ? "#00e87a44" : "#ffffff0a"}`,
                  padding: "3rem 2rem", cursor: file ? "default" : "pointer",
                  background: dragging ? "#00e5ff05" : file ? "#00e87a05" : "transparent",
                  textAlign: "center", transition: "all 0.2s",
                }}
              >
                {/* Corner decorations */}
                {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
                  <div key={v+h} style={{ position: "absolute", [v]: 6, [h]: 6, width: 12, height: 12,
                    borderTop: v==="top" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff22"}` : "none",
                    borderBottom: v==="bottom" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff22"}` : "none",
                    borderLeft: h==="left" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff22"}` : "none",
                    borderRight: h==="right" ? `2px solid ${dragging?CYAN:file?"#00e87a":"#ffffff22"}` : "none",
                  }} />
                ))}

                {file ? (
                  <div>
                    <div style={{ fontSize: "28px", marginBottom: "0.75rem", color: "#00e87a" }}>✓</div>
                    <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.1em", marginBottom: "0.5rem" }}>FILE CARICATO</div>
                    <div style={{ fontSize: "14px", color: "#e8e8f0", marginBottom: "0.25rem", fontWeight: 600 }}>{file.name}</div>
                    <div style={{ fontSize: "11px", color: "#444455" }}>{(file.size / 1024 / 1024).toFixed(1)} MB</div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: "36px", marginBottom: "1rem", opacity: 0.2 }}>▶</div>
                    <div style={{ fontSize: "14px", color: "#ccccdd", marginBottom: "0.5rem" }}>{dragging ? "Rilascia il file" : "Trascina il video qui"}</div>
                    <div style={{ fontSize: "11px", color: "#444455" }}>o clicca per sfogliare · MP4, MOV, AVI, MKV</div>
                  </div>
                )}
              </div>

              <input ref={inputRef} type="file" accept="video/*" style={{ display: "none" }}
                onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />

              {/* Camera button */}
              {!file && (
                <button onClick={openCamera} className="btn-cam" style={{
                  width: "100%", marginTop: "10px", fontFamily: "inherit", fontSize: "12px",
                  padding: "11px 24px", background: "transparent", color: "#444466",
                  border: "1px solid #ffffff0a", cursor: "pointer", letterSpacing: "0.1em",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", transition: "all 0.2s",
                }}>
                  <span style={{ fontSize: "14px" }}>◉</span> CATTURA DA CAMERA
                </button>
              )}

              {/* Error */}
              {error && (
                <div style={{ marginTop: "12px", fontSize: "11px", color: RED, border: `1px solid ${RED}22`, padding: "10px 14px", background: `${RED}08`, display: "flex", gap: "8px", alignItems: "flex-start" }}>
                  <span>⚠</span><span>{error}</span>
                </div>
              )}

              {/* Actions */}
              {file && (
                <div style={{ marginTop: "14px", display: "flex", gap: "10px" }}>
                  <button onClick={analyze} className="btn-analyze" style={{
                    flex: 1, fontFamily: "inherit", fontSize: "13px", fontWeight: 700,
                    padding: "13px 24px", background: CYAN, color: "#050508",
                    border: "none", cursor: "pointer", letterSpacing: "0.08em", transition: "all 0.2s",
                  }}>
                    AVVIA ANALISI →
                  </button>
                  <button onClick={() => { setFile(null); setError(""); }} className="btn-clear" style={{
                    fontFamily: "inherit", fontSize: "11px", padding: "13px 16px",
                    background: "transparent", color: "#444455", border: "1px solid #ffffff08",
                    cursor: "pointer", transition: "all 0.2s",
                  }}>
                    CLEAR
                  </button>
                </div>
              )}
            </>
          ) : (
            /* Analysis progress */
            <div style={{ border: "1px solid #ffffff0a", background: "#07070d", padding: "2rem" }}>
              <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1.5rem", fontWeight: 700 }}>ANALISI IN CORSO</div>

              {/* Progress bar */}
              <div style={{ marginBottom: "2rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#444455", marginBottom: "8px" }}>
                  <span>{STEPS[stepIdx]?.label}</span>
                  <span style={{ color: CYAN }}>{Math.round(progress)}%</span>
                </div>
                <div style={{ height: "2px", background: "#ffffff08", width: "100%", position: "relative" }}>
                  <div style={{ height: "100%", width: `${progress}%`, background: `linear-gradient(90deg, ${CYAN}, #00e87a)`, transition: "width 0.5s ease", boxShadow: `0 0 12px ${CYAN}66` }} />
                </div>
              </div>

              {/* Steps list */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "1.5rem" }}>
                {STEPS.map((step, i) => {
                  const done    = i < stepIdx;
                  const active  = i === stepIdx;
                  const pending = i > stepIdx;
                  return (
                    <div key={step.id} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{ width: "18px", height: "18px", border: `1px solid ${done ? "#00e87a" : active ? CYAN : "#ffffff0a"}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "9px", color: done ? "#00e87a" : active ? CYAN : "#333344", flexShrink: 0, transition: "all 0.3s" }}>
                        {done ? "✓" : active ? <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>◌</span> : step.icon}
                      </div>
                      <span style={{ fontSize: "11px", color: done ? "#00e87a" : active ? CYAN : "#333344", transition: "color 0.3s", letterSpacing: "0.05em" }}>
                        {step.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div style={{ fontSize: "11px", color: "#333344", borderTop: "1px solid #ffffff05", paddingTop: "1rem" }}>
                <span style={{ color: "#444455" }}>{file?.name}</span> · {((file?.size || 0) / 1024 / 1024).toFixed(1)} MB
                <br />
                <span style={{ color: "#ff2d5566" }}>█ Non chiudere questa finestra</span>
              </div>
            </div>
          )}
        </div>

        {/* Layer badges */}
        {!uploading && !file && (
          <div style={{ marginTop: "3rem", display: "flex", flexWrap: "wrap", gap: "8px", justifyContent: "center", maxWidth: "520px", animation: "fadeIn 0.5s ease 0.2s both" }}>
            {["Metadata","Visual AI","Audio Sync","Signal Physics","Moiré","PRNU","Virtual Cam","rPPG Cardiac"].map((l, i) => (
              <div key={l} style={{ fontSize: "10px", color: i % 2 === 0 ? CYAN : "#444466", border: `1px solid ${i % 2 === 0 ? CYAN + "33" : "#ffffff08"}`, padding: "4px 10px", letterSpacing: "0.08em" }}>
                {l}
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ position: "relative", zIndex: 1, borderTop: "1px solid #ffffff08", padding: "1rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "10px", color: "#222233", letterSpacing: "0.1em" }}>AURA REALITY FIREWALL — NOT FOR CONSUMER USE</span>
        <a href="/" style={{ fontSize: "10px", color: "#333344", textDecoration: "none", letterSpacing: "0.08em" }}>← Landing</a>
      </footer>
    </div>
  );
}
