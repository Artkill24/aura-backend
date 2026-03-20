"use client";
import { useState } from "react";
import { supabase } from "../../lib/supabase";

export default function LoginPage() {
  const [email, setEmail]     = useState("");
  const [sent, setSent]       = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const CYAN = "#00e5ff";

  const sendMagicLink = async () => {
    if (!email) return;
    setLoading(true); setError("");
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/dashboard` }
    });
    if (error) setError(error.message);
    else setSent(true);
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#050508", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Mono', monospace", color: "#e8e8f0" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap'); * { box-sizing: border-box; margin: 0; padding: 0; }`}</style>
      <div style={{ position: "fixed", inset: 0, backgroundImage: `linear-gradient(#00e5ff05 1px, transparent 1px), linear-gradient(90deg, #00e5ff05 1px, transparent 1px)`, backgroundSize: "48px 48px", pointerEvents: "none" }} />

      <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: "420px", padding: "2rem" }}>
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "10px", marginBottom: "1.5rem" }}>
            <div style={{ width: "32px", height: "32px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px", color: CYAN, fontWeight: 700 }}>A</div>
            <span style={{ fontWeight: 700, fontSize: "16px", letterSpacing: "0.15em" }}>AURA</span>
          </div>
          <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "0.75rem" }}>ACCESSO PIATTAFORMA</div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Accedi a AURA</h1>
          <p style={{ fontSize: "12px", color: "#444455", marginTop: "0.5rem" }}>Magic link — nessuna password richiesta</p>
        </div>

        {!sent ? (
          <div style={{ border: "1px solid #ffffff08", padding: "2rem", background: "#07070d" }}>
            <div style={{ fontSize: "10px", color: "#444455", marginBottom: "0.75rem", letterSpacing: "0.1em" }}>EMAIL</div>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMagicLink()}
              placeholder="tua@email.com"
              style={{ width: "100%", padding: "12px", background: "#050508", border: "1px solid #ffffff0a", color: "#e8e8f0", fontFamily: "inherit", fontSize: "13px", marginBottom: "1rem", outline: "none" }}
            />
            {error && <div style={{ fontSize: "11px", color: "#ff2d55", marginBottom: "1rem" }}>⚠ {error}</div>}
            <button onClick={sendMagicLink} disabled={loading || !email}
              style={{ width: "100%", padding: "13px", background: email ? CYAN : "#0a0a14", color: email ? "#050508" : "#333344", border: "none", fontFamily: "inherit", fontSize: "13px", fontWeight: 700, cursor: email ? "pointer" : "not-allowed", letterSpacing: "0.08em" }}>
              {loading ? "Invio..." : "Invia Magic Link →"}
            </button>
            <div style={{ fontSize: "10px", color: "#333344", marginTop: "1rem", textAlign: "center" }}>
              Riceverai un link per accedere istantaneamente. Nessuna password.
            </div>
          </div>
        ) : (
          <div style={{ border: `1px solid ${CYAN}33`, padding: "2rem", background: "#07070d", textAlign: "center" }}>
            <div style={{ fontSize: "28px", marginBottom: "1rem" }}>✉</div>
            <div style={{ fontSize: "14px", color: CYAN, fontWeight: 700, marginBottom: "0.75rem" }}>Magic link inviato!</div>
            <div style={{ fontSize: "12px", color: "#555566", lineHeight: 1.7 }}>
              Controlla la tua email <span style={{ color: "#e8e8f0" }}>{email}</span><br />e clicca il link per accedere.
            </div>
          </div>
        )}

        <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
          <a href="/" style={{ fontSize: "11px", color: "#333344", textDecoration: "none" }}>← Torna alla landing</a>
        </div>
      </div>
    </div>
  );
}
