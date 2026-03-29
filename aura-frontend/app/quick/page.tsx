"use client";
import { useState, useRef } from "react";

const COLORS = { green: "#00e87a", yellow: "#ffb700", red: "#ff2d55" };
const LABELS = { green: "AUTENTICO", yellow: "DUBBIO", red: "SOSPETTO" };
const EMOJIS = { green: "✓", yellow: "~", red: "✗" };

export default function QuickPage() {
  const [file, setFile]         = useState<File | null>(null);
  const [url, setUrl]           = useState("");
  const [tab, setTab]           = useState<"file" | "url">("file");
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState<any>(null);
  const [error, setError]       = useState("");
  const [progress, setProgress] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const CYAN = "#00e5ff";

  const analyze = async () => {
    if (tab === "file" && !file) return;
    if (tab === "url" && !url) return;
    setLoading(true); setError(""); setResult(null); setProgress(0);

    // Simula progress
    const interval = setInterval(() => setProgress(p => Math.min(p + 3, 90)), 500);

    try {
      const fd = new FormData();
      if (tab === "file" && file) fd.append("file", file);
      if (tab === "url" && url) fd.append("url", url);

      const res = await fetch("/api/backend/quick-scan", { method: "POST", body: fd });
      clearInterval(interval); setProgress(100);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Errore server");
      setResult(data);
    } catch (e: any) {
      clearInterval(interval);
      setError(e.message || "Errore durante l'analisi");
    }
    setLoading(false);
  };

  const color = result ? COLORS[result.traffic_light as keyof typeof COLORS] : CYAN;

  return (
    <div style={{ minHeight: "100vh", background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes glow { 0%,100%{box-shadow:0 0 20px var(--c)} 50%{box-shadow:0 0 50px var(--c),0 0 80px var(--c)} }
        @keyframes spin { to{transform:rotate(360deg)} }
        .drag-zone:hover { border-color: #00e5ff44 !important; background: #07070d !important; }
        .tab-btn:hover { color: #e8e8f0 !important; }
      `}</style>

      {/* NAV */}
      <nav style={{ padding: "0 1.5rem", height: "52px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #ffffff06", position: "sticky", top: 0, background: "rgba(5,5,8,0.95)", backdropFilter: "blur(12px)", zIndex: 100 }}>
        <a href="/" style={{ display: "flex", alignItems: "center", gap: "8px", textDecoration: "none", color: "#e8e8f0" }}>
          <div style={{ width: "22px", height: "22px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em" }}>AURA</span>
          <span style={{ color: "#ffffff18", fontSize: "10px" }}>/ QUICK SCAN</span>
        </a>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <a href="/analyze" style={{ fontSize: "10px", color: "#444455", textDecoration: "none", letterSpacing: "0.08em" }}>Analisi completa →</a>
          <a href="/login" style={{ fontSize: "10px", color: CYAN, textDecoration: "none", border: `1px solid ${CYAN}33`, padding: "4px 10px" }}>Accedi</a>
        </div>
      </nav>

      <main style={{ maxWidth: "600px", margin: "0 auto", padding: "3rem 1.5rem" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem", animation: "fadeIn 0.4s ease" }}>
          <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "0.75rem" }}>VERIFICA RAPIDA GRATUITA</div>
          <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.75rem" }}>
            È un <span style={{ color: CYAN }}>deepfake</span>?
          </h1>
          <p style={{ fontSize: "12px", color: "#555566", lineHeight: 1.7 }}>
            Risultato in meno di 30 secondi. Nessun account richiesto.<br />
            Per analisi forense completa con PDF e blockchain → <a href="/login" style={{ color: CYAN, textDecoration: "none" }}>Accedi</a>
          </p>
        </div>

        {/* Upload / URL */}
        {!loading && !result && (
          <div style={{ animation: "fadeIn 0.4s ease 0.1s both" }}>
            {/* Tabs */}
            <div style={{ display: "flex", border: "1px solid #ffffff08", marginBottom: "1rem", background: "#07070d" }}>
              {[["file", "▶ FILE"], ["url", "⛓ LINK"]].map(([t, label]) => (
                <button key={t} className="tab-btn" onClick={() => setTab(t as any)}
                  style={{ flex: 1, padding: "10px", fontFamily: "inherit", fontSize: "11px", fontWeight: tab === t ? 700 : 400, background: tab === t ? "#0a141a" : "transparent", color: tab === t ? CYAN : "#444455", border: "none", cursor: "pointer", letterSpacing: "0.08em", borderBottom: tab === t ? `2px solid ${CYAN}` : "2px solid transparent", transition: "all 0.2s" }}>
                  {label}
                </button>
              ))}
            </div>

            {tab === "file" ? (
              <div className="drag-zone" onClick={() => fileRef.current?.click()}
                style={{ border: "1px dashed #ffffff14", padding: "2.5rem", textAlign: "center", cursor: "pointer", background: "#07070d", transition: "all 0.2s", marginBottom: "1rem" }}>
                <input ref={fileRef} type="file" accept="video/*" style={{ display: "none" }}
                  onChange={e => setFile(e.target.files?.[0] || null)} />
                {file ? (
                  <div>
                    <div style={{ fontSize: "20px", marginBottom: "8px" }}>🎬</div>
                    <div style={{ fontSize: "12px", color: CYAN }}>{file.name}</div>
                    <div style={{ fontSize: "10px", color: "#444455", marginTop: "4px" }}>{(file.size / 1024 / 1024).toFixed(1)} MB</div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: "28px", marginBottom: "10px", opacity: 0.4 }}>⬆</div>
                    <div style={{ fontSize: "12px", color: "#555566" }}>Trascina video o clicca per scegliere</div>
                    <div style={{ fontSize: "10px", color: "#333344", marginTop: "6px" }}>Max 50MB · MP4, MOV, AVI, WebM</div>
                  </div>
                )}
              </div>
            ) : (
              <input type="url" value={url} onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === "Enter" && analyze()}
                placeholder="https://youtube.com/... TikTok, X, Vimeo"
                style={{ width: "100%", padding: "14px", background: "#07070d", border: "1px solid #ffffff0a", color: "#e8e8f0", fontFamily: "inherit", fontSize: "12px", marginBottom: "1rem", outline: "none" }} />
            )}

            <button onClick={analyze} disabled={tab === "file" ? !file : !url}
              style={{ width: "100%", padding: "14px", background: (tab === "file" ? file : url) ? CYAN : "#0a0a14", color: (tab === "file" ? file : url) ? "#050508" : "#333344", border: "none", fontFamily: "inherit", fontSize: "13px", fontWeight: 700, cursor: (tab === "file" ? file : url) ? "pointer" : "not-allowed", letterSpacing: "0.1em", transition: "all 0.2s" }}>
              VERIFICA ORA →
            </button>

            {/* Features */}
            <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem", fontSize: "10px", color: "#333344", justifyContent: "center" }}>
              {["4 layer forensi", "Risultato in 30s", "100% gratuito"].map(f => (
                <span key={f} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <span style={{ color: "#00e87a" }}>✓</span> {f}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: "center", animation: "fadeIn 0.3s ease", padding: "2rem" }}>
            <div style={{ width: "80px", height: "80px", border: `3px solid #ffffff08`, borderTop: `3px solid ${CYAN}`, borderRadius: "50%", margin: "0 auto 1.5rem", animation: "spin 1s linear infinite" }} />
            <div style={{ fontSize: "12px", color: "#555566", marginBottom: "1rem" }}>Analisi in corso...</div>
            <div style={{ height: "3px", background: "#ffffff06", borderRadius: "2px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${progress}%`, background: CYAN, transition: "width 0.5s ease" }} />
            </div>
            <div style={{ fontSize: "10px", color: "#333344", marginTop: "8px" }}>
              {progress < 30 ? "Download video..." : progress < 60 ? "Analisi segnale..." : progress < 85 ? "AI origin check..." : "Finalizzazione..."}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>
            <div style={{ border: "1px solid #ff2d5522", padding: "1rem", background: "#ff2d5506", marginBottom: "1rem", fontSize: "12px", color: "#ff2d55" }}>⚠ {error}</div>
            <button onClick={() => { setError(""); setResult(null); }} style={{ fontFamily: "inherit", fontSize: "11px", color: "#444455", background: "transparent", border: "1px solid #ffffff08", padding: "8px 16px", cursor: "pointer" }}>← Riprova</button>
          </div>
        )}

        {/* Result — Semaforo */}
        {result && !loading && (
          <div style={{ animation: "fadeIn 0.5s ease" }}>
            {/* Semaforo */}
            <div style={{ textAlign: "center", padding: "2.5rem", border: `1px solid ${color}33`, background: "#07070d", marginBottom: "1rem" }}>
              {/* Luce */}
              <div style={{ width: "100px", height: "100px", borderRadius: "50%", background: `${color}22`, border: `3px solid ${color}`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.5rem", fontSize: "36px", fontWeight: 700, color, "--c": color, animation: "glow 2s ease infinite" } as any}>
                {EMOJIS[result.traffic_light as keyof typeof EMOJIS]}
              </div>

              <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.15em", marginBottom: "0.5rem" }}>VERDETTO QUICK SCAN</div>
              <div style={{ fontSize: "2rem", fontWeight: 700, color, marginBottom: "0.75rem" }}>
                {LABELS[result.traffic_light as keyof typeof LABELS]}
              </div>
              <div style={{ fontSize: "12px", color: "#888899", maxWidth: "380px", margin: "0 auto", lineHeight: 1.7 }}>
                {result.message}
              </div>

              {/* Score bar */}
              <div style={{ margin: "1.5rem auto 0", maxWidth: "300px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#444455", marginBottom: "6px" }}>
                  <span>Rischio manipolazione</span>
                  <span style={{ color }}>{Math.round(result.score * 100)}%</span>
                </div>
                <div style={{ height: "4px", background: "#ffffff06", borderRadius: "2px" }}>
                  <div style={{ height: "100%", width: `${result.score * 100}%`, background: color, borderRadius: "2px", transition: "width 1s ease" }} />
                </div>
              </div>
            </div>

            {/* Reasons */}
            <div style={{ border: "1px solid #ffffff08", padding: "1.25rem", background: "#07070d", marginBottom: "1rem" }}>
              <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.12em", marginBottom: "0.75rem" }}>ANOMALIE RILEVATE</div>
              {result.reasons.map((r: string, i: number) => (
                <div key={i} style={{ display: "flex", gap: "8px", fontSize: "11px", color: "#888899", marginBottom: "6px", alignItems: "flex-start" }}>
                  <span style={{ color, flexShrink: 0 }}>→</span> {r}
                </div>
              ))}
            </div>

            {/* CTA */}
            {result.upgrade_hint && (
              <div style={{ border: `1px solid ${CYAN}22`, padding: "1.25rem", background: `${CYAN}06`, marginBottom: "1rem", textAlign: "center" }}>
                <div style={{ fontSize: "11px", color: "#888899", marginBottom: "0.75rem" }}>
                  Vuoi il <strong style={{ color: CYAN }}>report forense completo</strong> con PDF, blockchain e 11 layer?
                </div>
                <a href="/login" style={{ display: "inline-block", padding: "10px 24px", background: CYAN, color: "#050508", textDecoration: "none", fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em" }}>
                  Analisi completa gratuita →
                </a>
              </div>
            )}

            {/* Retry */}
            <button onClick={() => { setResult(null); setFile(null); setUrl(""); setProgress(0); }}
              style={{ width: "100%", padding: "10px", fontFamily: "inherit", fontSize: "11px", color: "#444455", background: "transparent", border: "1px solid #ffffff08", cursor: "pointer", letterSpacing: "0.08em" }}>
              ← Analizza un altro video
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
