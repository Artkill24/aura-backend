"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../lib/supabase";

const PLAN_LIMITS: Record<string, number> = { free: 10, pro: 999, enterprise: 9999 };
const PLAN_COLORS: Record<string, string> = { free: "#666677", pro: "#00e5ff", enterprise: "#8247E5" };

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser]           = useState<any>(null);
  const [userData, setUserData]   = useState<any>(null);
  const [analyses, setAnalyses]   = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);
  const CYAN = "#00e5ff";

  useEffect(() => {
    const init = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { router.push("/login"); return; }
      setUser(session.user);

      const email = session.user.email!;

      // Upsert utente
      const { data: existing } = await supabase
        .from("aura_users")
        .select("*")
        .eq("email", email)
        .single();

      if (!existing) {
        const { data: newUser } = await supabase
          .from("aura_users")
          .insert({ email, plan: "free" })
          .select()
          .single();
        setUserData(newUser);
      } else {
        await supabase.from("aura_users").update({ last_seen: new Date().toISOString() }).eq("email", email);
        setUserData(existing);
      }

      // Carica analisi
      const { data: analysesList } = await supabase
        .from("aura_analyses")
        .select("*")
        .eq("user_email", email)
        .order("created_at", { ascending: false })
        .limit(50);

      setAnalyses(analysesList || []);
      setLoading(false);
    };
    init();
  }, [router]);

  const logout = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  if (loading) return (
    <div style={{ minHeight: "100vh", background: "#050508", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Mono', monospace", color: "#333344", fontSize: "12px", letterSpacing: "0.1em" }}>
      CARICAMENTO...
    </div>
  );

  const plan        = userData?.plan || "free";
  const used        = userData?.analyses_this_month || 0;
  const limit       = PLAN_LIMITS[plan];
  const planColor   = PLAN_COLORS[plan];
  const usedPct     = Math.min(100, (used / limit) * 100);

  return (
    <div style={{ minHeight: "100vh", background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 3px; } ::-webkit-scrollbar-thumb { background: #00e5ff22; }
        @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        .row:hover { background: #0a0a14 !important; }
        .btn:hover { opacity: 0.8; }
      `}</style>
      <div style={{ position: "fixed", inset: 0, backgroundImage: `linear-gradient(#00e5ff04 1px, transparent 1px), linear-gradient(90deg, #00e5ff04 1px, transparent 1px)`, backgroundSize: "48px 48px", pointerEvents: "none", zIndex: 0 }} />

      {/* NAV */}
      <nav style={{ position: "sticky", top: 0, zIndex: 100, borderBottom: "1px solid #ffffff06", padding: "0 2rem", height: "56px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(5,5,8,0.95)", backdropFilter: "blur(12px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }} onClick={() => router.push("/")}>
          <div style={{ width: "24px", height: "24px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em" }}>AURA</span>
          <span style={{ color: "#ffffff18", fontSize: "10px" }}>/ DASHBOARD</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          <div style={{ fontSize: "10px", color: "#333344" }}>{user?.email}</div>
          <div style={{ padding: "3px 10px", border: `1px solid ${planColor}44`, color: planColor, fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em" }}>{plan.toUpperCase()}</div>
          <button onClick={logout} className="btn" style={{ fontFamily: "inherit", fontSize: "10px", padding: "5px 12px", background: "transparent", color: "#333344", border: "1px solid #ffffff06", cursor: "pointer" }}>ESCI</button>
        </div>
      </nav>

      <main style={{ maxWidth: "1000px", margin: "0 auto", padding: "2.5rem 1.5rem", position: "relative", zIndex: 1 }}>

        {/* ── STATS ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "2rem", animation: "fadeIn 0.4s ease both" }}>
          {/* Quota */}
          <div style={{ border: `1px solid ${planColor}33`, padding: "1.5rem", background: "#07070d" }}>
            <div style={{ fontSize: "10px", color: planColor, letterSpacing: "0.12em", marginBottom: "0.75rem" }}>QUOTA MENSILE</div>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: planColor, marginBottom: "0.5rem" }}>
              {plan === "pro" || plan === "enterprise" ? "∞" : `${used}/${limit}`}
            </div>
            {plan === "free" && (
              <div style={{ height: "3px", background: "#ffffff06", marginBottom: "0.5rem" }}>
                <div style={{ height: "100%", width: `${usedPct}%`, background: usedPct > 80 ? "#ff2d55" : CYAN, transition: "width 0.8s ease" }} />
              </div>
            )}
            <div style={{ fontSize: "10px", color: "#333344" }}>
              {plan === "free" ? `${Math.max(0, limit - used)} rimanenti` : "Illimitato"}
            </div>
          </div>

          {/* Totale analisi */}
          <div style={{ border: "1px solid #ffffff08", padding: "1.5rem", background: "#07070d" }}>
            <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.12em", marginBottom: "0.75rem" }}>ANALISI TOTALI</div>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#e8e8f0", marginBottom: "0.5rem" }}>{userData?.analyses_total || analyses.length}</div>
            <div style={{ fontSize: "10px", color: "#333344" }}>Dalla registrazione</div>
          </div>

          {/* Piano */}
          <div style={{ border: "1px solid #ffffff08", padding: "1.5rem", background: "#07070d" }}>
            <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.12em", marginBottom: "0.75rem" }}>PIANO ATTIVO</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: planColor, marginBottom: "0.75rem" }}>{plan.toUpperCase()}</div>
            {plan === "free" && (
              <a href="/analyze" style={{ fontSize: "10px", color: CYAN, textDecoration: "none", border: `1px solid ${CYAN}33`, padding: "4px 10px", display: "inline-block", letterSpacing: "0.08em" }}>
                Upgrade a Pro →
              </a>
            )}
          </div>

          {/* Azioni rapide */}
          <div style={{ border: "1px solid #ffffff08", padding: "1.5rem", background: "#07070d" }}>
            <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.12em", marginBottom: "0.75rem" }}>AZIONI RAPIDE</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <a href="/analyze" style={{ fontSize: "11px", color: CYAN, textDecoration: "none", display: "flex", alignItems: "center", gap: "6px" }}>→ Nuova analisi</a>
              <a href="/analyze" style={{ fontSize: "11px", color: "#444455", textDecoration: "none", display: "flex", alignItems: "center", gap: "6px" }}>→ Analizza link</a>
            </div>
          </div>
        </div>

        {/* ── STORICO ANALISI ── */}
        <div style={{ border: "1px solid #ffffff08", background: "#07070d", animation: "fadeIn 0.4s ease 0.1s both" }}>
          <div style={{ padding: "1.25rem 1.5rem", borderBottom: "1px solid #ffffff06", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.12em" }}>STORICO ANALISI ({analyses.length})</div>
            <a href="/analyze" style={{ fontSize: "10px", color: CYAN, textDecoration: "none", letterSpacing: "0.08em" }}>+ NUOVA →</a>
          </div>

          {analyses.length === 0 ? (
            <div style={{ padding: "3rem", textAlign: "center", fontSize: "12px", color: "#333344" }}>
              Nessuna analisi ancora.<br />
              <a href="/analyze" style={{ color: CYAN, textDecoration: "none" }}>Inizia la prima analisi →</a>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #ffffff06" }}>
                    {["Data", "File / URL", "Verdetto", "Score", "Origin", "PDF"].map(h => (
                      <th key={h} style={{ padding: "10px 16px", textAlign: "left", color: "#333344", fontWeight: 400, letterSpacing: "0.08em", fontSize: "9px" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {analyses.map((a: any) => {
                    const colorMap: Record<string, string> = { "LIKELY MANIPULATED": "#ff2d55", "PROBABLY AUTHENTIC": "#00e87a", "SUSPICIOUS": "#ffb700", "HIGHLY LIKELY SYNTHETIC": "#ff2d55", "AUTHENTIC": "#00e87a", "SYNTHETIC / DEEPFAKE": "#ff2d55" };
                    const vc = colorMap[a.verdict_label] || "#666677";
                    const date = new Date(a.created_at).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
                    const filename = (a.filename || "").length > 30 ? (a.filename || "").slice(0, 30) + "..." : (a.filename || "—");
                    return (
                      <tr key={a.id} className="row" style={{ borderBottom: "1px solid #ffffff04", transition: "background 0.15s" }}>
                        <td style={{ padding: "10px 16px", color: "#444455" }}>{date}</td>
                        <td style={{ padding: "10px 16px", color: "#888899", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{filename}</td>
                        <td style={{ padding: "10px 16px" }}>
                          <span style={{ color: vc, fontSize: "10px", fontWeight: 700 }}>{a.verdict_label || "—"}</span>
                        </td>
                        <td style={{ padding: "10px 16px", color: vc }}>{a.composite_score ? `${Math.round(a.composite_score * 100)}%` : "—"}</td>
                        <td style={{ padding: "10px 16px", color: a.origin_verdict === "AI-PRODUCED" ? "#ff2d55" : "#00e87a", fontSize: "10px" }}>{a.origin_verdict || "—"}</td>
                        <td style={{ padding: "10px 16px" }}>
                          {a.pdf_url ? (
                            <a href={a.pdf_url} target="_blank" rel="noopener noreferrer" style={{ color: CYAN, textDecoration: "none", fontSize: "10px" }}>↓ PDF</a>
                          ) : <span style={{ color: "#333344" }}>—</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div style={{ marginTop: "2rem", fontSize: "10px", color: "#222233", lineHeight: 1.8 }}>
          Le tue analisi sono private e crittografate. AURA non condivide i tuoi dati con terze parti.
        </div>
      </main>
    </div>
  );
}
