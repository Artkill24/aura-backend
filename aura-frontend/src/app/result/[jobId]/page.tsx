"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type Verdict = {
  label: string;
  composite_score: number;
  risk_color: string;
  confidence: string;
  breakdown: Record<string, number>;
};

type Result = {
  job_id: string;
  filename: string;
  analysis_time_seconds: number;
  verdict: Verdict;
  metadata_flags: { type: string; detail: string; severity: string }[];
  visual_score: number;
  audio_score: number;
  signal_score: number;
  screen_recording_score?: number;
  report_url: string;
};

const VERDICT_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  green:  { color: "#00e87a", bg: "rgba(0,232,122,0.06)",  label: "AUTHENTIC" },
  yellow: { color: "#ffb700", bg: "rgba(255,183,0,0.06)",  label: "SUSPICIOUS" },
  orange: { color: "#ff7322", bg: "rgba(255,115,34,0.06)", label: "LIKELY MANIPULATED" },
  red:    { color: "#ff2d4e", bg: "rgba(255,45,78,0.06)",  label: "SYNTHETIC / DEEPFAKE" },
};

function ScoreBar({ label, score, color, delay = 0 }: { label: string; score: number; color: string; delay?: number }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(score * 100), delay);
    return () => clearTimeout(t);
  }, [score, delay]);

  return (
    <div className="mb-4">
      <div className="flex justify-between font-mono text-xs mb-2">
        <span style={{ color: 'var(--text)' }}>{label}</span>
        <span style={{ color }}>{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1 w-full" style={{ background: 'var(--border)' }}>
        <div
          className="h-full transition-all duration-700 ease-out"
          style={{ width: `${width}%`, background: color, boxShadow: `0 0 8px ${color}40` }}
        />
      </div>
    </div>
  );
}

function ContribBar({ label, value, total }: { label: string; value: number; total: number }) {
  const [width, setWidth] = useState(0);
  const pct = total > 0 ? (value / total) * 100 : 0;
  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 200);
    return () => clearTimeout(t);
  }, [pct]);

  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="font-mono text-xs w-28 shrink-0" style={{ color: 'var(--muted)' }}>{label}</span>
      <div className="flex-1 h-px" style={{ background: 'var(--border)' }}>
        <div
          className="h-px transition-all duration-700 ease-out"
          style={{ width: `${width}%`, background: 'var(--blue)' }}
        />
      </div>
      <span className="font-mono text-xs w-12 text-right" style={{ color: 'var(--blue)' }}>
        {(value * 100).toFixed(1)}%
      </span>
    </div>
  );
}

export default function ResultPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();
  const [result, setResult] = useState<Result | null>(null);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem(`aura_result_${jobId}`);
    if (stored) {
      setResult(JSON.parse(stored));
      setTimeout(() => setRevealed(true), 100);
    } else {
      router.push("/");
    }
  }, [jobId, router]);

  if (!result) return (
    <div className="min-h-screen flex items-center justify-center font-mono text-muted text-sm">
      Loading...
    </div>
  );

  const vs = VERDICT_STYLES[result.verdict.risk_color] || VERDICT_STYLES.green;
  const score = result.verdict.composite_score;
  const bd = result.verdict.breakdown;
  const totalContrib = Object.values(bd).reduce((a, b) => a + b, 0);

  const layerScores = [
    { label: "Metadata",          score: result.metadata_flags.filter(f => f.severity !== "INFO").length > 0 ? 0.3 : 0.03, color: "#7c8cf0" },
    { label: "Visual / Frames",   score: result.visual_score,              color: "#a855f7" },
    { label: "Audio Sync",        score: result.audio_score,               color: "#06b6d4" },
    { label: "Signal Physics",    score: result.signal_score,              color: "var(--blue)" },
    { label: "Screen Detection",  score: result.screen_recording_score ?? 0, color: "#f59e0b" },
  ];

  return (
    <div className="min-h-screen flex flex-col">

      {/* Header */}
      <header className="border-b border-border px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/")} className="flex items-center gap-2 group">
            <div className="w-8 h-8 border border-blue/40 flex items-center justify-center">
              <div className="w-3 h-3 bg-blue rounded-sm" style={{ boxShadow: '0 0 10px var(--blue)' }} />
            </div>
            <span className="font-mono text-sm font-medium text-bright tracking-widest uppercase group-hover:text-blue transition-colors">AURA</span>
          </button>
          <span className="font-mono text-xs text-muted">/ FORENSIC REPORT</span>
        </div>
        <div className="font-mono text-xs text-muted">JOB {result.job_id.split("-")[0].toUpperCase()}</div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-12">

        {/* Verdict Hero */}
        <div
          className="border p-8 mb-8 relative overflow-hidden"
          style={{
            borderColor: vs.color,
            background: vs.bg,
            opacity: revealed ? 1 : 0,
            transform: revealed ? 'none' : 'translateY(8px)',
            transition: 'opacity 0.5s, transform 0.5s',
          }}
        >
          {/* Corner decorators */}
          {['top-2 left-2 border-t-2 border-l-2', 'top-2 right-2 border-t-2 border-r-2',
            'bottom-2 left-2 border-b-2 border-l-2', 'bottom-2 right-2 border-b-2 border-r-2'].map(c => (
            <div key={c} className={`absolute w-5 h-5 ${c}`} style={{ borderColor: vs.color }} />
          ))}

          <div className="flex items-start justify-between gap-6">
            <div>
              <div className="font-mono text-xs mb-3 uppercase tracking-widest" style={{ color: vs.color }}>
                Forensic Verdict
              </div>
              <div className="text-3xl font-mono font-semibold mb-2" style={{ color: vs.color }}>
                {vs.label}
              </div>
              <div className="font-mono text-xs text-muted truncate max-w-xs">
                {result.filename}
              </div>
            </div>

            {/* Big score */}
            <div className="text-right shrink-0">
              <div className="font-mono text-5xl font-light" style={{ color: vs.color }}>
                {(score * 100).toFixed(0)}
              </div>
              <div className="font-mono text-xs text-muted">RISK SCORE / 100</div>
              <div className="font-mono text-xs mt-1" style={{ color: vs.color }}>
                {result.verdict.confidence} CONFIDENCE
              </div>
            </div>
          </div>

          {/* Wide score bar */}
          <div className="mt-6">
            <div className="h-2 w-full rounded-sm overflow-hidden" style={{ background: 'var(--border)' }}>
              <div
                className="h-full rounded-sm transition-all duration-1000 ease-out"
                style={{
                  width: revealed ? `${score * 100}%` : '0%',
                  background: `linear-gradient(90deg, ${vs.color}88, ${vs.color})`,
                  boxShadow: `0 0 12px ${vs.color}`,
                }}
              />
            </div>
          </div>

          {/* Stats row */}
          <div className="mt-5 grid grid-cols-3 gap-4 pt-5 border-t" style={{ borderColor: `${vs.color}30` }}>
            <div>
              <div className="font-mono text-xs text-muted mb-1">ANALYSIS TIME</div>
              <div className="font-mono text-sm text-bright">{result.analysis_time_seconds}s</div>
            </div>
            <div>
              <div className="font-mono text-xs text-muted mb-1">FLAGS RAISED</div>
              <div className="font-mono text-sm text-bright">{result.metadata_flags.length}</div>
            </div>
            <div>
              <div className="font-mono text-xs text-muted mb-1">LAYERS ANALYZED</div>
              <div className="font-mono text-sm text-bright">5 / 5</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">

          {/* Layer Scores */}
          <div className="border border-border p-6">
            <div className="font-mono text-xs text-muted uppercase tracking-widest mb-5">Layer Scores</div>
            {layerScores.map((l, i) => (
              <ScoreBar key={l.label} {...l} delay={i * 100} />
            ))}
          </div>

          {/* Composite Breakdown */}
          <div className="border border-border p-6">
            <div className="font-mono text-xs text-muted uppercase tracking-widest mb-5">Score Contribution</div>
            {Object.entries(bd).map(([key, val]) => (
              <ContribBar
                key={key}
                label={key.replace("_contribution", "").replace(/_/g, " ")}
                value={val}
                total={totalContrib}
              />
            ))}
            <div className="mt-4 pt-4 border-t border-border flex justify-between font-mono text-xs">
              <span className="text-muted">COMPOSITE SCORE</span>
              <span style={{ color: vs.color }}>{(score * 100).toFixed(1)} / 100</span>
            </div>
          </div>
        </div>

        {/* Flags */}
        {result.metadata_flags.length > 0 && (
          <div className="border border-border p-6 mb-6">
            <div className="font-mono text-xs text-muted uppercase tracking-widest mb-4">Detection Flags</div>
            <div className="space-y-3">
              {result.metadata_flags.map((flag, i) => {
                const severityColor = flag.severity === "HIGH" ? "var(--red)" : flag.severity === "MEDIUM" ? "var(--orange)" : "var(--muted)";
                return (
                  <div key={i} className="flex items-start gap-3 font-mono text-xs">
                    <span className="shrink-0 px-2 py-0.5 border text-xs uppercase"
                      style={{ borderColor: `${severityColor}40`, color: severityColor, background: `${severityColor}10` }}>
                      {flag.severity}
                    </span>
                    <div>
                      <div className="text-bright mb-0.5">{flag.type.replace(/_/g, " ")}</div>
                      <div className="text-muted leading-relaxed">{flag.detail}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <a
            href={`/api/backend${result.report_url}`}
            download={`AURA_Report_${result.job_id}.pdf`}
            className="font-mono text-sm py-3 px-6 border transition-all duration-200 flex items-center gap-2"
            style={{ borderColor: 'var(--blue)', color: 'var(--blue)' }}
            onMouseEnter={e => {
              const el = e.currentTarget as HTMLElement;
              el.style.background = 'var(--blue)';
              el.style.color = 'var(--bg)';
            }}
            onMouseLeave={e => {
              const el = e.currentTarget as HTMLElement;
              el.style.background = 'transparent';
              el.style.color = 'var(--blue)';
            }}
          >
            ↓ DOWNLOAD PDF REPORT
          </a>
          <button
            onClick={() => router.push("/")}
            className="font-mono text-sm py-3 px-6 border border-border text-muted hover:border-muted hover:text-text transition-colors"
          >
            ← NEW ANALYSIS
          </button>
        </div>

        {/* Disclaimer */}
        <div className="mt-10 font-mono text-xs text-muted border-t border-border pt-6 leading-relaxed">
          AURA provides probabilistic analysis based on multi-layer signal detection. Results should be interpreted by
          qualified forensic professionals and do not constitute definitive legal evidence without expert validation.
          Report ID: {result.job_id}
        </div>
      </main>
    </div>
  );
}
