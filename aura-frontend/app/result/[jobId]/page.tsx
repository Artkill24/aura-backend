"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

export default function ResultPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router    = useRouter();
  const [result, setResult] = useState<any>(null);
  const [bars, setBars]     = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem(`aura_result_${jobId}`);
    if (stored) { setResult(JSON.parse(stored)); setTimeout(() => setBars(true), 300); }
    else router.push("/analyze");
  }, [jobId, router]);

  if (!result) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#050508", color: "#333344", fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, letterSpacing: "0.1em" }}>
      LOADING REPORT...
    </div>
  );

  const CYAN   = "#00e5ff";
  const RED    = "#ff2d55";
  const PURPLE = "#8247E5";
  const GREEN  = "#00e87a";

  const colorMap: Record<string, string> = {
    green: GREEN, yellow: "#ffb700", orange: "#ff7322", red: RED
  };
  const vc    = colorMap[result.verdict?.risk_color] || GREEN;
  const score = result.verdict?.composite_score || 0;

  const layers = [
    { label: "Metadata",       score: result.metadata_flags?.filter((f: any) => f.severity !== "INFO").length > 0 ? 0.3 : 0.03, color: "#7c8cf0" },
    { label: "Visual AI",      score: result.visual_score || 0,              color: "#a855f7" },
    { label: "Audio Sync",     score: result.audio_score || 0,               color: "#06b6d4" },
    { label: "Signal Physics", score: result.signal_score || 0,              color: CYAN },
    { label: "Moiré Screen",   score: result.screen_recording_score || 0,    color: "#f59e0b" },
    { label: "PRNU Sensor",    score: result.prnu_score || 0,                color: "#10b981" },
    { label: "Virtual Cam",    score: result.virtual_cam_score || 0,         color: "#f97316" },
    { label: "rPPG Cardiac",   score: result.rppg_score || 0,                color: RED },
    { label: "C2PA Provenance",score: result.c2pa?.c2pa_score || 0.35,       color: "#3355ff" },
  ];

  const gen   = result.generative_origin || {};
  const bc    = result.blockchain || {};
  const c2pa  = result.c2pa || {};
  const forensic = result.forensic_conclusion || {};
  const narrative = result.ai_narrative || "";

  const originColor = gen.origin_verdict === "AI-PRODUCED" ? RED
    : gen.origin_verdict === "MANUAL/EDITED" ? GREEN
    : gen.origin_verdict === "SCREEN-RECORDED" ? "#f59e0b"
    : "#666677";

  return (
    <div style={{ minHeight: "100vh", background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 3px; } ::-webkit-scrollbar-thumb { background: #00e5ff22; }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        .btn:hover { opacity: 0.8; }
      `}</style>

      {/* Grid bg */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", backgroundImage: `linear-gradient(#00e5ff04 1px, transparent 1px), linear-gradient(90deg, #00e5ff04 1px, transparent 1px)`, backgroundSize: "48px 48px", zIndex: 0 }} />

      {/* NAV */}
      <nav style={{ position: "sticky", top: 0, zIndex: 100, borderBottom: "1px solid #ffffff08", padding: "0 2rem", height: "56px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(5,5,8,0.95)", backdropFilter: "blur(12px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }} onClick={() => router.push("/")}>
          <div style={{ width: "24px", height: "24px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em" }}>AURA</span>
          <span style={{ color: "#ffffff18", fontSize: "10px" }}>/ FORENSIC REPORT</span>
        </div>
        <span style={{ fontSize: "10px", color: "#333344", letterSpacing: "0.08em" }}>JOB {result.job_id?.split("-")[0].toUpperCase()}</span>
      </nav>

      <main style={{ maxWidth: "860px", margin: "0 auto", padding: "2.5rem 1.5rem", position: "relative", zIndex: 1 }}>

        {/* ── VERDICT ── */}
        <div style={{ border: `1px solid ${vc}44`, background: `${vc}08`, padding: "2rem", marginBottom: "1.5rem", position: "relative", animation: "fadeIn 0.5s ease both" }}>
          {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
            <div key={v+h} style={{ position: "absolute", [v]: 8, [h]: 8, width: 16, height: 16,
              borderTop: v==="top" ? `2px solid ${vc}` : "none", borderBottom: v==="bottom" ? `2px solid ${vc}` : "none",
              borderLeft: h==="left" ? `2px solid ${vc}` : "none", borderRight: h==="right" ? `2px solid ${vc}` : "none",
            }} />
          ))}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1.5rem", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: "10px", color: vc, letterSpacing: "0.15em", marginBottom: "0.5rem" }}>FORENSIC VERDICT</div>
              <div style={{ fontSize: "clamp(1.2rem, 3vw, 1.8rem)", fontWeight: 700, color: vc, marginBottom: "0.5rem" }}>{result.verdict?.label}</div>
              <div style={{ fontSize: "11px", color: "#444455" }}>{result.filename || result.url}</div>
              {forensic.attack_vector && (
                <div style={{ marginTop: "0.75rem", display: "inline-flex", alignItems: "center", gap: "6px", border: `1px solid ${vc}33`, padding: "4px 10px", fontSize: "10px", color: vc, letterSpacing: "0.08em" }}>
                  ⚡ {forensic.attack_vector?.replace(/_/g, " ")}
                </div>
              )}
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "clamp(2.5rem, 6vw, 4rem)", fontWeight: 300, color: vc, lineHeight: 1 }}>{Math.round(score * 100)}</div>
              <div style={{ fontSize: "10px", color: "#444455" }}>RISK / 100</div>
              <div style={{ fontSize: "10px", color: vc, marginTop: "4px" }}>{result.verdict?.confidence} CONFIDENCE</div>
            </div>
          </div>
          <div style={{ marginTop: "1.5rem", height: "3px", background: "#ffffff06" }}>
            <div style={{ height: "100%", width: bars ? `${score * 100}%` : "0%", background: vc, transition: "width 1.2s ease-out", boxShadow: `0 0 16px ${vc}88` }} />
          </div>
          <div style={{ marginTop: "1.25rem", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", paddingTop: "1.25rem", borderTop: `1px solid ${vc}18` }}>
            {[
              ["ANALYSIS TIME", `${result.analysis_time_seconds || 0}s`],
              ["FLAGS RAISED", result.metadata_flags?.length || 0],
              ["LAYERS", "9 + Layer 10"]
            ].map(([k, v]) => (
              <div key={k}>
                <div style={{ fontSize: "9px", color: "#333344", marginBottom: "4px", letterSpacing: "0.1em" }}>{k}</div>
                <div style={{ fontSize: "13px", color: "#e8e8f0" }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── LAYER 10 — GENERATIVE ORIGIN ── */}
        {gen.origin_verdict && (
          <div style={{ border: `1px solid ${originColor}44`, background: `${originColor}08`, padding: "1.5rem", marginBottom: "1.5rem", animation: "fadeIn 0.5s ease 0.1s both" }}>
            <div style={{ fontSize: "10px", color: originColor, letterSpacing: "0.15em", marginBottom: "1rem", fontWeight: 700 }}>LAYER 10 — GENERATIVE ORIGIN DETECTOR</div>
            <div style={{ display: "flex", alignItems: "center", gap: "1.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
              <div style={{ padding: "6px 16px", background: `${originColor}18`, border: `1px solid ${originColor}66`, color: originColor, fontSize: "14px", fontWeight: 700, letterSpacing: "0.1em" }}>
                {gen.origin_verdict}
              </div>
              <div style={{ display: "flex", gap: "1.5rem" }}>
                <div>
                  <div style={{ fontSize: "9px", color: "#333344", marginBottom: "2px" }}>PROB AI</div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: RED }}>{Math.round((gen.probability_ai || 0) * 100)}%</div>
                </div>
                <div>
                  <div style={{ fontSize: "9px", color: "#333344", marginBottom: "2px" }}>PROB MANUAL</div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: GREEN }}>{Math.round((gen.probability_manual || 0) * 100)}%</div>
                </div>
                <div>
                  <div style={{ fontSize: "9px", color: "#333344", marginBottom: "2px" }}>CONFIDENCE</div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: originColor }}>{gen.confidence}</div>
                </div>
              </div>
            </div>
            {gen.generative_tool && (
              <div style={{ fontSize: "11px", color: "#555566", marginBottom: "0.75rem" }}>
                <span style={{ color: originColor }}>◈</span> Strumento probabile: <span style={{ color: "#ccccdd" }}>{gen.generative_tool}</span>
              </div>
            )}
            {gen.key_reasons?.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {gen.key_reasons.map((r: string, i: number) => (
                  <div key={i} style={{ display: "flex", gap: "8px", fontSize: "11px", color: "#555566" }}>
                    <span style={{ color: originColor, flexShrink: 0 }}>→</span> {r}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── 2 COLUMNS: LAYERS + BLOCKCHAIN ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem", animation: "fadeIn 0.5s ease 0.2s both" }}>

          {/* Layer scores */}
          <div style={{ border: "1px solid #ffffff08", padding: "1.5rem", background: "#07070d" }}>
            <div style={{ fontSize: "10px", color: "#333344", letterSpacing: "0.12em", marginBottom: "1.25rem" }}>9 LAYER SCORES</div>
            {layers.map((l, i) => (
              <div key={l.label} style={{ marginBottom: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", marginBottom: "4px" }}>
                  <span style={{ color: "#888899" }}>{l.label}</span>
                  <span style={{ color: l.color }}>{Math.round(l.score * 100)}%</span>
                </div>
                <div style={{ height: "2px", background: "#ffffff06" }}>
                  <div style={{ height: "100%", width: bars ? `${l.score * 100}%` : "0%", background: l.color, transition: `width ${0.6 + i * 0.08}s ease-out`, boxShadow: `0 0 6px ${l.color}60` }} />
                </div>
              </div>
            ))}
          </div>

          {/* Blockchain + C2PA */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {/* Blockchain */}
            <div style={{ border: `1px solid ${PURPLE}33`, padding: "1.25rem", background: "#07070d", flex: 1 }}>
              <div style={{ fontSize: "10px", color: PURPLE, letterSpacing: "0.12em", marginBottom: "0.75rem" }}>⛓ BLOCKCHAIN NOTARIZATION</div>
              {bc.tx_hash ? (
                <>
                  <div style={{ fontSize: "10px", color: "#555566", marginBottom: "4px" }}>TX Hash</div>
                  <div style={{ fontSize: "10px", color: "#aaaacc", marginBottom: "8px", wordBreak: "break-all" }}>0x{bc.tx_hash?.slice(0, 20)}...</div>
                  <div style={{ fontSize: "10px", color: "#555566", marginBottom: "4px" }}>Block · Network</div>
                  <div style={{ fontSize: "10px", color: "#aaaacc", marginBottom: "8px" }}>{bc.block} · Polygon Amoy</div>
                  <a href={`https://amoy.polygonscan.com/tx/0x${bc.tx_hash}`} target="_blank" rel="noopener noreferrer" style={{ fontSize: "10px", color: PURPLE, textDecoration: "none" }}>Verifica su Polygonscan ↗</a>
                </>
              ) : (
                <div style={{ fontSize: "10px", color: "#333344" }}>Non disponibile</div>
              )}
            </div>

            {/* C2PA */}
            <div style={{ border: `1px solid #2233aa33`, padding: "1.25rem", background: "#07070d", flex: 1 }}>
              <div style={{ fontSize: "10px", color: "#4466ff", letterSpacing: "0.12em", marginBottom: "0.75rem" }}>◉ C2PA — EU AI ACT ART. 50</div>
              {c2pa.has_manifest ? (
                <div style={{ fontSize: "10px", color: GREEN }}>✓ Manifest C2PA valido rilevato</div>
              ) : (
                <>
                  <div style={{ fontSize: "10px", color: "#ff8844", marginBottom: "4px" }}>⚠ NO_C2PA_MANIFEST</div>
                  <div style={{ fontSize: "10px", color: "#444455", lineHeight: 1.6 }}>Provenance non verificabile — flag EU AI Act Art. 50</div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* ── AI NARRATIVE ── */}
        {narrative && (
          <div style={{ border: "1px solid #ffffff08", padding: "1.5rem", marginBottom: "1.5rem", background: "#07070d", animation: "fadeIn 0.5s ease 0.3s both" }}>
            <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.12em", marginBottom: "1rem" }}>◉ ANALISI AI — LLAMA 3.3-70B (GROQ)</div>
            <p style={{ fontSize: "12px", color: "#888899", lineHeight: 1.8 }}>{narrative}</p>
            <div style={{ marginTop: "0.75rem", fontSize: "10px", color: "#333344", fontStyle: "italic" }}>⚠ Narrativa generata da AI — verificare con perito umano certificato</div>
          </div>
        )}

        {/* ── FLAGS ── */}
        {result.metadata_flags?.length > 0 && (
          <div style={{ border: "1px solid #ffffff08", padding: "1.5rem", marginBottom: "1.5rem", background: "#07070d", animation: "fadeIn 0.5s ease 0.35s both" }}>
            <div style={{ fontSize: "10px", color: "#333344", letterSpacing: "0.12em", marginBottom: "1rem" }}>DETECTION FLAGS</div>
            {result.metadata_flags.map((flag: any, i: number) => {
              const sc = flag.severity === "HIGH" ? RED : flag.severity === "MEDIUM" ? "#ff7322" : "#444455";
              return (
                <div key={i} style={{ display: "flex", gap: "10px", marginBottom: "10px", fontSize: "11px" }}>
                  <span style={{ flexShrink: 0, padding: "2px 8px", border: `1px solid ${sc}40`, color: sc, background: `${sc}10`, fontSize: "9px", letterSpacing: "0.08em", height: "fit-content" }}>{flag.severity}</span>
                  <div>
                    <div style={{ color: "#e8e8f0", marginBottom: "2px" }}>{flag.type?.replace(/_/g, " ")}</div>
                    <div style={{ color: "#444455", lineHeight: 1.5 }}>{flag.detail}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── ACTIONS ── */}
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", animation: "fadeIn 0.5s ease 0.4s both" }}>
          <a
            href={`/api/backend${result.report_url}`}
            download={`AURA_${result.job_id}.pdf`}
            className="btn"
            style={{ fontFamily: "inherit", fontSize: "12px", padding: "12px 24px", border: `1px solid ${CYAN}`, color: CYAN, background: "transparent", textDecoration: "none", cursor: "pointer", letterSpacing: "0.08em", transition: "opacity 0.2s" }}
          >
            ↓ DOWNLOAD PDF REPORT
          </a>
          <button
            onClick={() => router.push("/analyze")}
            className="btn"
            style={{ fontFamily: "inherit", fontSize: "12px", padding: "12px 24px", border: "1px solid #ffffff08", color: "#444455", background: "transparent", cursor: "pointer", letterSpacing: "0.08em", transition: "opacity 0.2s" }}
          >
            ← NUOVA ANALISI
          </button>
          {result.verify_url && (
            <a
              href={`/api/backend${result.verify_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn"
              style={{ fontFamily: "inherit", fontSize: "12px", padding: "12px 24px", border: `1px solid ${PURPLE}55`, color: PURPLE, background: "transparent", textDecoration: "none", cursor: "pointer", letterSpacing: "0.08em", transition: "opacity 0.2s" }}
            >
              ⛓ VERIFICA ON-CHAIN
            </a>
          )}
        </div>

        <div style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid #ffffff06", fontSize: "10px", color: "#222233", lineHeight: 1.8 }}>
          AURA fornisce analisi probabilistica. I risultati devono essere validati da professionisti forensi qualificati prima dell'uso in procedimenti legali.<br />
          Report ID: {result.job_id}
        </div>
      </main>
    </div>
  );
}
