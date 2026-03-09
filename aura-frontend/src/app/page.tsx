"use client";
import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith("video/")) {
      setError("Solo file video (MP4, MOV, AVI, MKV)");
      return;
    }
    setError("");
    setFile(f);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  const analyze = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setError("");

    const messages = [
      "Initializing analysis pipeline...",
      "Extracting metadata signatures...",
      "Running visual frame analysis...",
      "Analyzing audio-visual sync...",
      "Computing signal physics...",
      "Generating forensic report...",
    ];

    let msgIdx = 0;
    setStatusMsg(messages[0]);
    const msgInterval = setInterval(() => {
      msgIdx = Math.min(msgIdx + 1, messages.length - 1);
      setStatusMsg(messages[msgIdx]);
    }, 8000);

    const progInterval = setInterval(() => {
      setProgress(p => p < 88 ? p + Math.random() * 3 : p);
    }, 500);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/backend/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      clearInterval(msgInterval);
      clearInterval(progInterval);
      setProgress(100);
      setStatusMsg("Analysis complete.");

      // Store result and redirect
      sessionStorage.setItem(`aura_result_${data.job_id}`, JSON.stringify(data));
      setTimeout(() => router.push(`/result/${data.job_id}`), 600);

    } catch (err: any) {
      clearInterval(msgInterval);
      clearInterval(progInterval);
      setUploading(false);
      setProgress(0);
      setError(err.message || "Analysis failed. Make sure the backend is running.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col">

      {/* Header */}
      <header className="border-b border-border px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border border-blue/40 flex items-center justify-center">
            <div className="w-3 h-3 bg-blue rounded-sm" style={{boxShadow: '0 0 10px var(--blue)'}} />
          </div>
          <span className="font-mono text-sm font-medium text-bright tracking-widest uppercase">AURA</span>
          <span className="font-mono text-xs text-muted tracking-wider">v0.3 — FORENSIC ENGINE</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green" style={{boxShadow: '0 0 8px var(--green)'}} />
          <span className="font-mono text-xs text-muted">SYSTEM ONLINE</span>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16">

        {/* Title block */}
        <div className="text-center mb-16 max-w-2xl">
          <div className="font-mono text-xs text-blue/70 tracking-widest uppercase mb-4">
            Advanced Universal Reality Authentication
          </div>
          <h1 className="text-4xl font-sans font-light text-bright mb-4 leading-tight">
            Detect AI-Generated<br />
            <span className="font-semibold" style={{color: 'var(--blue)'}}>Video Evidence</span>
          </h1>
          <p className="text-sm text-muted font-mono leading-relaxed">
            5-layer forensic analysis — metadata · visual · audio · signal physics · screen detection<br />
            Designed for insurance adjusters, legal teams, and digital forensics professionals.
          </p>
        </div>

        {/* Upload Zone */}
        {!uploading ? (
          <div className="w-full max-w-xl">
            <div
              onClick={() => !file && inputRef.current?.click()}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              className={`
                relative border-2 rounded-sm cursor-pointer transition-all duration-300
                ${dragging
                  ? 'border-blue bg-blue/5 pulse-border'
                  : file
                  ? 'border-green/50 bg-green/5 cursor-default'
                  : 'border-border hover:border-blue/40 hover:bg-blue/3'
                }
              `}
              style={{ padding: '48px 32px' }}
            >
              {/* Corner decorators */}
              <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2"
                style={{borderColor: dragging ? 'var(--blue)' : file ? 'var(--green)' : 'var(--muted)'}} />
              <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2"
                style={{borderColor: dragging ? 'var(--blue)' : file ? 'var(--green)' : 'var(--muted)'}} />
              <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2"
                style={{borderColor: dragging ? 'var(--blue)' : file ? 'var(--green)' : 'var(--muted)'}} />
              <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2"
                style={{borderColor: dragging ? 'var(--blue)' : file ? 'var(--green)' : 'var(--muted)'}} />

              {file ? (
                <div className="text-center">
                  <div className="font-mono text-xs text-muted mb-2 uppercase tracking-widest">File loaded</div>
                  <div className="font-mono text-sm text-bright mb-1 truncate max-w-xs mx-auto">{file?.name}</div>
                  <div className="font-mono text-xs text-muted">
                    {(file!.size / 1024 / 1024).toFixed(1)} MB — {file.type}
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  {/* Icon */}
                  <div className="mx-auto mb-5 w-14 h-14 border border-muted/50 flex items-center justify-center">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="1.5">
                      <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="font-mono text-sm text-text mb-1">
                    {dragging ? "Release to load" : "Drop video file here"}
                  </div>
                  <div className="font-mono text-xs text-muted">or click to browse — MP4, MOV, AVI, MKV</div>
                </div>
              )}
            </div>

            <input ref={inputRef} type="file" accept="video/*" className="hidden"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />

            {error && (
              <div className="mt-3 font-mono text-xs text-red border border-red/20 px-3 py-2 bg-red/5">
                ⚠ {error}
              </div>
            )}

            {file && (
              <div className="mt-4 flex gap-3">
                <button
                  onClick={analyze}
                  className="flex-1 font-mono text-sm font-medium py-3 px-6 transition-all duration-200"
                  style={{
                    background: 'var(--blue)',
                    color: 'var(--bg)',
                    border: '1px solid var(--blue)',
                  }}
                  onMouseEnter={e => {
                    (e.target as HTMLElement).style.background = 'transparent';
                    (e.target as HTMLElement).style.color = 'var(--blue)';
                  }}
                  onMouseLeave={e => {
                    (e.target as HTMLElement).style.background = 'var(--blue)';
                    (e.target as HTMLElement).style.color = 'var(--bg)';
                  }}
                >
                  INITIATE ANALYSIS →
                </button>
                <button
                  onClick={() => { setFile(null); setError(""); }}
                  className="font-mono text-xs py-3 px-4 border border-border text-muted hover:border-muted hover:text-text transition-colors"
                >
                  CLEAR
                </button>
              </div>
            )}
          </div>

        ) : (
          /* Analysis Progress */
          <div className="w-full max-w-xl">
            <div className="border border-border p-8 relative">
              {/* Scanning line */}
              <div
                className="absolute left-0 right-0 h-px pointer-events-none"
                style={{
                  background: 'linear-gradient(90deg, transparent, var(--blue), transparent)',
                  animation: 'scan 2s linear infinite',
                  opacity: 0.6,
                }}
              />

              <div className="font-mono text-xs text-muted uppercase tracking-widest mb-6">
                Analysis in progress
              </div>

              {/* Progress bar */}
              <div className="mb-6">
                <div className="flex justify-between font-mono text-xs text-muted mb-2">
                  <span>{statusMsg}</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-1 bg-border w-full">
                  <div
                    className="h-full transition-all duration-500"
                    style={{
                      width: `${progress}%`,
                      background: 'linear-gradient(90deg, var(--blue), var(--green))',
                      boxShadow: '0 0 10px var(--blue)',
                    }}
                  />
                </div>
              </div>

              {/* File info */}
              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div>
                  <div className="text-muted mb-1">FILE</div>
                  <div className="text-text truncate">{file?.name}</div>
                </div>
                <div>
                  <div className="text-muted mb-1">SIZE</div>
                  <div className="text-text">{(file!.size / 1024 / 1024).toFixed(1)} MB</div>
                </div>
              </div>

              <div className="mt-4 font-mono text-xs text-muted flex items-center gap-2">
                <span className="blink text-blue">█</span>
                <span>Do not close this window</span>
              </div>
            </div>
          </div>
        )}

        {/* Feature tags */}
        {!uploading && !file && (
          <div className="mt-16 flex flex-wrap gap-2 justify-center max-w-lg">
            {["Metadata Forensics", "HuggingFace Visual AI", "A/V Sync Analysis", "Signal Physics", "Screen Recording Detection", "PDF Report Export"].map(t => (
              <span key={t} className="font-mono text-xs px-3 py-1 border border-border text-muted">
                {t}
              </span>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-8 py-4 flex items-center justify-between">
        <span className="font-mono text-xs text-muted">AURA FORENSIC ENGINE — NOT FOR CONSUMER USE</span>
        <span className="font-mono text-xs text-muted">5-LAYER DETECTION PIPELINE</span>
      </footer>
    </div>
  );
}
