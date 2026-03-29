"use client";
import { useState } from "react";

const IT = {
  nav: { product: "Prodotto", pricing: "Prezzi", docs: "Docs", quick: "Quick Scan", dashboard: "Dashboard" },
  hero: { tag: "ADVANCED UNIVERSAL REALITY AUTHENTICATION", title1: "Analisi Forense", title2: "Video", sub: "12 layer · rPPG · C2PA EU AI Act · Blockchain Polygon · Gemini AI · Semantic AI" },
  cta: { primary: "Inizia Analisi Forense", secondary: "Quick Scan Gratuito →" },
  stats: [
    { v: "12", l: "Layer Forensi" },
    { v: "99.1%", l: "Accuratezza" },
    { v: "<3min", l: "Tempo Medio" },
    { v: "EU", l: "AI Act Conforme" },
  ],
  compliance: {
    tag: "COMPLIANCE & STANDARDS 2026",
    title: "Forense. Legale. Immutabile.",
    items: [
      { icon: "⛓", title: "Blockchain Polygon", desc: "Notarizzazione immutabile su Polygon Amoy. Hash SHA-256 + chain-of-custody verificabile da tribunali." },
      { icon: "◈", title: "C2PA EU AI Act Art. 50", desc: "Verifica Content Credentials secondo lo standard Coalition for Content Provenance. Conforme EU AI Act." },
      { icon: "◉", title: "AI Narrative Legale", desc: "Report in linguaggio legale italiano generato da Llama 3.3-70B. Pronto per atti processuali." },
      { icon: "⬡", title: "Gemini 2.0 Observer", desc: "Layer 12 esclusivo: analisi audio-video cross-check con Gemini 2.0 Flash. Lip sync, laringe, glitch." },
      { icon: "▣", title: "QR Verificabile", desc: "QR code nel PDF collega a endpoint di verifica live. Chiunque può verificare l'integrità del report." },
      { icon: "⊕", title: "rPPG Cardiac Signal", desc: "Rilevazione battito cardiaco biologico da segnale video. I deepfake non replicano la fisiologia umana." },
    ]
  },
  extension: {
    tag: "CHROME EXTENSION",
    title: "AURA ovunque navighi",
    desc: "Installa l'estensione Chrome e verifica qualsiasi video su YouTube, TikTok o X con un clic destro. Risultato immediato nel popup.",
    features: ["Clic destro → analisi istantanea", "Popup con verdict + score", "Integrazione YouTube / TikTok / X", "Manifest V3 · Open source"],
    cta: "Installa Estensione",
  },
  pricing: {
    tag: "PRICING",
    title: "Scegli il piano",
    plans: [
      { name: "Free", price: "€0", period: "/mese", color: "#666677", features: ["10 analisi/mese", "Quick Scan illimitato", "PDF report base", "4 layer forensi", "Supporto community"], cta: "Inizia Gratis", href: "/login" },
      { name: "Pro", price: "€24", period: "/mese", color: "#00e5ff", badge: "POPOLARE", features: ["Analisi illimitate", "12 layer forensi completi", "Blockchain notarization", "PDF forense + QR", "Analisi link YouTube/TikTok", "Gemini Layer 12", "Supporto prioritario"], cta: "Inizia Pro", href: "/login" },
      { name: "Enterprise", price: "Su richiesta", period: "", color: "#8247E5", features: ["Tutto Pro incluso", "API privata + Webhooks", "SLA garantito", "Custom prompt refinement", "Account multi-utente team", "Onboarding dedicato", "Fatturazione aziendale"], cta: "Contattaci", href: "mailto:kaicarsaad455@gmail.com" },
    ]
  },
  layers: {
    tag: "12 LAYER FORENSI",
    title: "La pipeline più avanzata del 2026",
    items: [
      { n: "01", name: "Metadata Analysis", w: "7%" },
      { n: "02", name: "Visual AI (HF API)", w: "5%" },
      { n: "03", name: "Audio Sync", w: "7%" },
      { n: "04", name: "Signal Physics", w: "22%" },
      { n: "05", name: "Moiré Screen", w: "7%" },
      { n: "06", name: "PRNU Sensor", w: "12%" },
      { n: "07", name: "Virtual Cam", w: "11%" },
      { n: "08", name: "rPPG Cardiac", w: "16%" },
      { n: "09", name: "C2PA EU AI Act", w: "8%" },
      { n: "10", name: "Generative Origin (Groq)", w: "bonus" },
      { n: "11", name: "Temporal Coherence", w: "5%" },
      { n: "12", name: "Gemini 2.0 Observer", w: "bg" },
    ]
  },
  footer: "AURA fornisce analisi probabilistica. I risultati devono essere validati da professionisti forensi qualificati prima dell'uso in procedimenti legali.",
};

const EN = {
  nav: { product: "Product", pricing: "Pricing", docs: "Docs", quick: "Quick Scan", dashboard: "Dashboard" },
  hero: { tag: "ADVANCED UNIVERSAL REALITY AUTHENTICATION", title1: "Forensic Video", title2: "Analysis", sub: "12 layers · rPPG · C2PA EU AI Act · Polygon Blockchain · Gemini AI · Semantic AI" },
  cta: { primary: "Start Forensic Analysis", secondary: "Free Quick Scan →" },
  stats: [
    { v: "12", l: "Forensic Layers" },
    { v: "99.1%", l: "Accuracy" },
    { v: "<3min", l: "Avg Time" },
    { v: "EU", l: "AI Act Compliant" },
  ],
  compliance: {
    tag: "COMPLIANCE & STANDARDS 2026",
    title: "Forensic. Legal. Immutable.",
    items: [
      { icon: "⛓", title: "Polygon Blockchain", desc: "Immutable notarization on Polygon Amoy. SHA-256 hash + chain-of-custody verifiable by courts." },
      { icon: "◈", title: "C2PA EU AI Act Art. 50", desc: "Content Credentials verification per Coalition for Content Provenance standard. EU AI Act compliant." },
      { icon: "◉", title: "Legal AI Narrative", desc: "Italian legal-language report generated by Llama 3.3-70B. Ready for legal proceedings." },
      { icon: "⬡", title: "Gemini 2.0 Observer", desc: "Exclusive Layer 12: audio-video cross-check with Gemini 2.0 Flash. Lip sync, larynx, glitches." },
      { icon: "▣", title: "Verifiable QR", desc: "QR code in PDF links to live verification endpoint. Anyone can verify report integrity." },
      { icon: "⊕", title: "rPPG Cardiac Signal", desc: "Biological heartbeat detection from video signal. Deepfakes cannot replicate human physiology." },
    ]
  },
  extension: {
    tag: "CHROME EXTENSION",
    title: "AURA wherever you browse",
    desc: "Install the Chrome extension and verify any video on YouTube, TikTok or X with a right-click. Instant result in the popup.",
    features: ["Right-click → instant analysis", "Popup with verdict + score", "YouTube / TikTok / X integration", "Manifest V3 · Open source"],
    cta: "Install Extension",
  },
  pricing: {
    tag: "PRICING",
    title: "Choose your plan",
    plans: [
      { name: "Free", price: "€0", period: "/month", color: "#666677", features: ["10 analyses/month", "Unlimited Quick Scan", "Basic PDF report", "4 forensic layers", "Community support"], cta: "Start Free", href: "/login" },
      { name: "Pro", price: "€24", period: "/month", color: "#00e5ff", badge: "POPULAR", features: ["Unlimited analyses", "Full 12 forensic layers", "Blockchain notarization", "Forensic PDF + QR", "YouTube/TikTok link analysis", "Gemini Layer 12", "Priority support"], cta: "Start Pro", href: "/login" },
      { name: "Enterprise", price: "On request", period: "", color: "#8247E5", features: ["Everything in Pro", "Private API + Webhooks", "Guaranteed SLA", "Custom prompt refinement", "Multi-user team accounts", "Dedicated onboarding", "Business billing"], cta: "Contact Us", href: "mailto:kaicarsaad455@gmail.com" },
    ]
  },
  layers: {
    tag: "12 FORENSIC LAYERS",
    title: "The most advanced pipeline of 2026",
    items: IT.layers.items,
  },
  footer: "AURA provides probabilistic analysis. Results must be validated by qualified forensic professionals before use in legal proceedings.",
};

export default function LandingPage() {
  const [lang, setLang] = useState<"IT" | "EN">("IT");
  const t = lang === "IT" ? IT : EN;
  const CYAN = "#00e5ff";

  return (
    <div style={{ minHeight: "100vh", background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        ::-webkit-scrollbar { width: 3px; } ::-webkit-scrollbar-thumb { background: #00e5ff22; }
        @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes scan { 0%{transform:translateY(-100%)} 100%{transform:translateY(400%)} }
        .nav-link { color: #555566; text-decoration: none; font-size: 12px; letter-spacing: 0.08em; transition: color 0.2s; }
        .nav-link:hover { color: #e8e8f0; }
        .compliance-card:hover { border-color: #ffffff14 !important; background: #0a0a14 !important; }
        .plan-card:hover { transform: translateY(-2px); }
        .layer-row:hover { background: #0a0a14 !important; }
        .btn-primary:hover { background: #00c4d9 !important; }
        .btn-outline:hover { background: #00e5ff11 !important; }
      `}</style>

      {/* Grid BG */}
      <div style={{ position: "fixed", inset: 0, backgroundImage: `linear-gradient(#00e5ff04 1px, transparent 1px), linear-gradient(90deg, #00e5ff04 1px, transparent 1px)`, backgroundSize: "48px 48px", pointerEvents: "none", zIndex: 0 }} />

      {/* NAV */}
      <nav style={{ position: "sticky", top: 0, zIndex: 100, borderBottom: "1px solid #ffffff06", padding: "0 2rem", height: "56px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(5,5,8,0.95)", backdropFilter: "blur(12px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ width: "28px", height: "28px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "14px", letterSpacing: "0.15em" }}>AURA</span>
          <span style={{ fontSize: "9px", color: "#333344", letterSpacing: "0.1em" }}>v1.6</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          {[t.nav.product, t.nav.pricing, t.nav.docs].map(l => <a key={l} href="#" className="nav-link">{l}</a>)}
          <a href="/quick" className="nav-link" style={{ color: "#00e87a" }}>⚡ {t.nav.quick}</a>
          <a href="/dashboard" className="nav-link">{t.nav.dashboard}</a>
          <div style={{ display: "flex", gap: "2px", background: "#ffffff08", padding: "2px", borderRadius: "2px" }}>
            {(["IT", "EN"] as const).map(l => (
              <button key={l} onClick={() => setLang(l)}
                style={{ fontFamily: "inherit", padding: "3px 10px", fontSize: "10px", background: lang === l ? CYAN : "transparent", color: lang === l ? "#050508" : "#555566", border: "none", cursor: "pointer", fontWeight: lang === l ? 700 : 400, transition: "all 0.2s", letterSpacing: "0.05em" }}>
                {l}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main style={{ position: "relative", zIndex: 1 }}>

        {/* HERO */}
        <section style={{ maxWidth: "900px", margin: "0 auto", padding: "6rem 2rem 4rem", textAlign: "center", animation: "fadeIn 0.6s ease" }}>
          <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.2em", marginBottom: "1.5rem", opacity: 0.8 }}>{t.hero.tag}</div>
          <h1 style={{ fontSize: "clamp(2.5rem, 6vw, 4.5rem)", fontWeight: 700, lineHeight: 1.1, marginBottom: "1.5rem" }}>
            {t.hero.title1} <span style={{ color: CYAN }}>{t.hero.title2}</span>
          </h1>
          <p style={{ fontSize: "13px", color: "#555566", letterSpacing: "0.05em", marginBottom: "2.5rem", lineHeight: 1.8 }}>{t.hero.sub}</p>

          <div style={{ display: "flex", gap: "12px", justifyContent: "center", flexWrap: "wrap", marginBottom: "4rem" }}>
            <a href="/login" className="btn-primary" style={{ padding: "14px 32px", background: CYAN, color: "#050508", textDecoration: "none", fontSize: "13px", fontWeight: 700, letterSpacing: "0.1em", transition: "all 0.2s" }}>{t.cta.primary}</a>
            <a href="/quick" className="btn-outline" style={{ padding: "14px 32px", background: "transparent", color: "#00e87a", textDecoration: "none", fontSize: "13px", fontWeight: 700, letterSpacing: "0.1em", border: "1px solid #00e87a44", transition: "all 0.2s" }}>{t.cta.secondary}</a>
          </div>

          {/* Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1px", background: "#ffffff06", border: "1px solid #ffffff06" }}>
            {t.stats.map(s => (
              <div key={s.l} style={{ padding: "1.5rem", background: "#050508", textAlign: "center" }}>
                <div style={{ fontSize: "1.75rem", fontWeight: 700, color: CYAN, marginBottom: "4px" }}>{s.v}</div>
                <div style={{ fontSize: "10px", color: "#444455", letterSpacing: "0.1em" }}>{s.l}</div>
              </div>
            ))}
          </div>
        </section>

        {/* COMPLIANCE 2026 */}
        <section style={{ maxWidth: "1000px", margin: "0 auto", padding: "4rem 2rem" }}>
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <div style={{ fontSize: "10px", color: "#8247E5", letterSpacing: "0.15em", marginBottom: "0.75rem" }}>◈ {t.compliance.tag}</div>
            <h2 style={{ fontSize: "2rem", fontWeight: 700 }}>{t.compliance.title}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1px", background: "#ffffff06" }}>
            {t.compliance.items.map((item, i) => (
              <div key={i} className="compliance-card" style={{ padding: "1.75rem", background: "#07070d", border: "1px solid transparent", transition: "all 0.2s" }}>
                <div style={{ fontSize: "20px", marginBottom: "0.75rem", color: "#8247E5" }}>{item.icon}</div>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "#e8e8f0", marginBottom: "0.5rem", letterSpacing: "0.05em" }}>{item.title}</div>
                <div style={{ fontSize: "11px", color: "#555566", lineHeight: 1.7 }}>{item.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* 12 LAYERS */}
        <section style={{ maxWidth: "800px", margin: "0 auto", padding: "4rem 2rem" }}>
          <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
            <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "0.75rem" }}>◈ {t.layers.tag}</div>
            <h2 style={{ fontSize: "2rem", fontWeight: 700 }}>{t.layers.title}</h2>
          </div>
          <div style={{ border: "1px solid #ffffff06", background: "#07070d" }}>
            {t.layers.items.map((layer, i) => (
              <div key={i} className="layer-row" style={{ display: "flex", alignItems: "center", padding: "0.875rem 1.25rem", borderBottom: i < 11 ? "1px solid #ffffff04" : "none", gap: "1rem", transition: "background 0.15s" }}>
                <span style={{ fontSize: "10px", color: "#333344", minWidth: "24px" }}>{layer.n}</span>
                <span style={{ fontSize: "12px", color: "#e8e8f0", flex: 1 }}>{layer.name}</span>
                <span style={{ fontSize: "10px", color: layer.w === "bonus" ? "#ffb700" : layer.w === "bg" ? "#8247E5" : CYAN, letterSpacing: "0.05em" }}>
                  {layer.w === "bonus" ? "BONUS" : layer.w === "bg" ? "BACKGROUND" : layer.w}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* CHROME EXTENSION */}
        <section style={{ maxWidth: "900px", margin: "0 auto", padding: "4rem 2rem" }}>
          <div style={{ border: "1px solid #ffffff08", padding: "3rem", background: "#07070d", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "3rem", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "0.75rem" }}>◈ {t.extension.tag}</div>
              <h2 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "1rem", lineHeight: 1.3 }}>{t.extension.title}</h2>
              <p style={{ fontSize: "12px", color: "#666677", lineHeight: 1.8, marginBottom: "1.5rem" }}>{t.extension.desc}</p>
              <a href="#" style={{ display: "inline-block", padding: "12px 24px", background: CYAN, color: "#050508", textDecoration: "none", fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em" }}>{t.extension.cta}</a>
            </div>
            <div>
              {t.extension.features.map((f, i) => (
                <div key={i} style={{ display: "flex", gap: "10px", padding: "10px 0", borderBottom: i < 3 ? "1px solid #ffffff06" : "none", fontSize: "12px", color: "#888899" }}>
                  <span style={{ color: CYAN }}>→</span> {f}
                </div>
              ))}
              {/* Mini popup preview */}
              <div style={{ marginTop: "1.5rem", border: "1px solid #ffffff0a", background: "#050508", padding: "12px", fontSize: "10px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                  <div style={{ width: "14px", height: "14px", border: `1px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "8px", color: CYAN }}>A</div>
                  <span style={{ fontWeight: 700, letterSpacing: "0.1em" }}>AURA</span>
                  <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "4px" }}>
                    <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#00e87a" }} />
                    <span style={{ color: "#333344" }}>ONLINE</span>
                  </span>
                </div>
                <div style={{ padding: "6px 8px", background: "#07070d", color: "#ff2d55", fontWeight: 700, marginBottom: "4px", fontSize: "11px" }}>LIKELY MANIPULATED</div>
                <div style={{ color: "#444455" }}>Score: 60/100 · AI-PRODUCED</div>
              </div>
            </div>
          </div>
        </section>

        {/* PRICING */}
        <section style={{ maxWidth: "1000px", margin: "0 auto", padding: "4rem 2rem" }}>
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "0.75rem" }}>◈ {t.pricing.tag}</div>
            <h2 style={{ fontSize: "2rem", fontWeight: 700 }}>{t.pricing.title}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1px", background: "#ffffff06" }}>
            {t.pricing.plans.map((plan, i) => (
              <div key={i} className="plan-card" style={{ padding: "2rem", background: "#07070d", border: `1px solid ${plan.color}${i === 1 ? "44" : "11"}`, position: "relative", transition: "transform 0.2s" }}>
                {plan.badge && <div style={{ position: "absolute", top: "-1px", left: "50%", transform: "translateX(-50%)", background: plan.color, color: "#050508", fontSize: "9px", fontWeight: 700, padding: "2px 10px", letterSpacing: "0.1em" }}>{plan.badge}</div>}
                <div style={{ fontSize: "10px", color: plan.color, letterSpacing: "0.15em", marginBottom: "1rem" }}>{plan.name.toUpperCase()}</div>
                <div style={{ fontSize: "2rem", fontWeight: 700, color: plan.color, marginBottom: "0.25rem" }}>{plan.price}</div>
                <div style={{ fontSize: "11px", color: "#444455", marginBottom: "1.5rem" }}>{plan.period}</div>
                <div style={{ marginBottom: "1.5rem" }}>
                  {plan.features.map((f, j) => (
                    <div key={j} style={{ display: "flex", gap: "8px", fontSize: "11px", color: "#888899", padding: "5px 0", borderBottom: "1px solid #ffffff04" }}>
                      <span style={{ color: plan.color }}>✓</span> {f}
                    </div>
                  ))}
                </div>
                <a href={plan.href} style={{ display: "block", padding: "12px", textAlign: "center", background: i === 1 ? plan.color : "transparent", color: i === 1 ? "#050508" : plan.color, textDecoration: "none", fontSize: "12px", fontWeight: 700, border: `1px solid ${plan.color}`, letterSpacing: "0.08em", transition: "all 0.2s" }}>{plan.cta}</a>
              </div>
            ))}
          </div>
        </section>

      </main>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid #ffffff06", padding: "2rem", textAlign: "center", position: "relative", zIndex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: "1000px", margin: "0 auto", flexWrap: "wrap", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ width: "20px", height: "20px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "9px", color: CYAN, fontWeight: 700 }}>A</div>
            <span style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.1em" }}>AURA</span>
            <span style={{ fontSize: "9px", color: "#333344" }}>v1.6 — NOT FOR CONSUMER USE</span>
          </div>
          <div style={{ fontSize: "10px", color: "#222233", maxWidth: "500px", textAlign: "right", lineHeight: 1.6 }}>{t.footer}</div>
          <a href="/landing" style={{ fontSize: "10px", color: "#333344", textDecoration: "none" }}>→ Landing</a>
        </div>
      </footer>
    </div>
  );
}
