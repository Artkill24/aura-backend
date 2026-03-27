"use client";
import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { supabase } from "../../lib/supabase";

function LoginContent() {
  const [mode, setMode]       = useState<"login" | "register">("login");
  const [email, setEmail]     = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [success, setSuccess] = useState("");
  const searchParams = useSearchParams();
  const redirect     = searchParams.get("redirect") || "/dashboard";
  const router       = useRouter();
  const CYAN = "#00e5ff";

  // Ascolta cambio stato auth e reindirizza
  useState(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session && (event === "SIGNED_IN" || event === "TOKEN_REFRESHED")) {
        router.push(redirect);
      }
    });
    return () => subscription.unsubscribe();
  });

  const handleGoogle = async () => {
    setLoading(true); setError("");
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}${redirect}` }
    });
    if (error) { setError(error.message); setLoading(false); }
  };

  const handleSubmit = async () => {
    if (!email || !password) { setError("Inserisci email e password"); return; }
    setLoading(true); setError(""); setSuccess("");

    if (mode === "register") {
      const { error } = await supabase.auth.signUp({
        email, password,
        options: { emailRedirectTo: `${window.location.origin}${redirect}` }
      });
      if (error) setError(error.message);
      else setSuccess("✓ Controlla la tua email per confermare la registrazione.");
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) setError(error.message);
      else router.push(redirect);
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#050508", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Mono', monospace", color: "#e8e8f0", padding: "1rem" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input { transition: border-color 0.2s; }
        input:focus { outline: none; border-color: #00e5ff44 !important; }
        .btn-google:hover { background: #1a1a2e !important; border-color: #ffffff22 !important; }
        .btn-submit:hover { background: #00c4d9 !important; }
        .tab:hover { color: #e8e8f0 !important; }
      `}</style>

      <div style={{ position: "fixed", inset: 0, backgroundImage: `linear-gradient(#00e5ff05 1px, transparent 1px), linear-gradient(90deg, #00e5ff05 1px, transparent 1px)`, backgroundSize: "48px 48px", pointerEvents: "none" }} />

      <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: "400px" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "10px", marginBottom: "1.25rem" }}>
            <div style={{ width: "32px", height: "32px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px", color: CYAN, fontWeight: 700 }}>A</div>
            <span style={{ fontWeight: 700, fontSize: "16px", letterSpacing: "0.15em" }}>AURA</span>
          </div>
          <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "0.5rem" }}>ACCESSO PIATTAFORMA</div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            {mode === "login" ? "Accedi a AURA" : "Crea account"}
          </h1>
        </div>

        {/* Tab */}
        <div style={{ display: "flex", border: "1px solid #ffffff08", marginBottom: "1.5rem", background: "#07070d" }}>
          {[["login", "Accedi"], ["register", "Registrati"]].map(([m, label]) => (
            <button key={m} className="tab" onClick={() => { setMode(m as any); setError(""); setSuccess(""); }}
              style={{ flex: 1, padding: "10px", fontFamily: "inherit", fontSize: "12px", fontWeight: mode === m ? 700 : 400, background: mode === m ? "#0a141a" : "transparent", color: mode === m ? CYAN : "#444455", border: "none", cursor: "pointer", letterSpacing: "0.08em", borderBottom: mode === m ? `2px solid ${CYAN}` : "2px solid transparent", transition: "all 0.2s" }}>
              {label}
            </button>
          ))}
        </div>

        <div style={{ border: "1px solid #ffffff08", padding: "1.75rem", background: "#07070d" }}>
          {/* Google */}
          <button onClick={handleGoogle} disabled={loading} className="btn-google"
            style={{ width: "100%", padding: "12px", background: "#0a0a14", color: "#e8e8f0", border: "1px solid #ffffff0a", fontFamily: "inherit", fontSize: "12px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", marginBottom: "1.25rem", letterSpacing: "0.05em", transition: "all 0.2s" }}>
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continua con Google
          </button>

          {/* Divider */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "1.25rem" }}>
            <div style={{ flex: 1, height: "1px", background: "#ffffff08" }} />
            <span style={{ fontSize: "10px", color: "#333344", letterSpacing: "0.1em" }}>OPPURE</span>
            <div style={{ flex: 1, height: "1px", background: "#ffffff08" }} />
          </div>

          {/* Email */}
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", color: "#444455", letterSpacing: "0.1em", marginBottom: "6px" }}>EMAIL</div>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="tua@email.com"
              style={{ width: "100%", padding: "10px 12px", background: "#050508", border: "1px solid #ffffff0a", color: "#e8e8f0", fontFamily: "inherit", fontSize: "12px" }} />
          </div>

          {/* Password */}
          <div style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "9px", color: "#444455", letterSpacing: "0.1em", marginBottom: "6px" }}>PASSWORD</div>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••" onKeyDown={e => e.key === "Enter" && handleSubmit()}
              style={{ width: "100%", padding: "10px 12px", background: "#050508", border: "1px solid #ffffff0a", color: "#e8e8f0", fontFamily: "inherit", fontSize: "12px" }} />
          </div>

          {/* Error / Success */}
          {error && <div style={{ fontSize: "11px", color: "#ff2d55", marginBottom: "12px", border: "1px solid #ff2d5522", padding: "8px 10px", background: "#ff2d5506" }}>⚠ {error}</div>}
          {success && <div style={{ fontSize: "11px", color: "#00e87a", marginBottom: "12px", border: "1px solid #00e87a22", padding: "8px 10px", background: "#00e87a06" }}>{success}</div>}

          {/* Submit */}
          <button onClick={handleSubmit} disabled={loading} className="btn-submit"
            style={{ width: "100%", padding: "12px", background: CYAN, color: "#050508", border: "none", fontFamily: "inherit", fontSize: "13px", fontWeight: 700, cursor: loading ? "wait" : "pointer", letterSpacing: "0.08em", transition: "all 0.2s" }}>
            {loading ? "..." : mode === "login" ? "Accedi →" : "Crea account →"}
          </button>
        </div>

        <div style={{ marginTop: "1.25rem", textAlign: "center" }}>
          <a href="/" style={{ fontSize: "11px", color: "#333344", textDecoration: "none" }}>← Torna alla landing</a>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return <Suspense fallback={null}><LoginContent /></Suspense>;
}
