"use client";
import { useState, useEffect, useRef } from "react";

const copy = {
  it: {
    nav: { product: "Prodotto", pricing: "Prezzi", docs: "Docs", cta: "Prova ora" },
    hero: {
      badge: "v0.9 — 8 Layer + AI Legale",
      title: ["Il Perito Forense", "Digitale contro", "Deepfake e AI"],
      sub: "Analisi multilivello con segnali cardiaci rPPG, heatmap ELA e conclusione legale generata da Llama 3.3-70B. Report PDF con QR verificabile e chain-of-custody SHA-256.",
      cta1: "Inizia gratis",
      cta2: "Demo Enterprise",
      trust: ["Nessuna carta richiesta", "Report in <3 min", "Deploy EU-compliant"],
    },
    layers: {
      title: "8 Layer di Analisi Forense",
      sub: "Ogni video viene scomposto in segnali indipendenti. La convergenza tra layer determina il verdetto.",
      items: [
        { icon: "◈", name: "Metadata", desc: "Encoder tag, GPS, device fingerprint, timestamp discrepancy" },
        { icon: "◉", name: "Visual AI", desc: "Dual-model deepfake detection: dima806 + umm-maybe" },
        { icon: "◈", name: "Audio Sync", desc: "A/V drift, TTS voice signatures, spettro 50/60Hz" },
        { icon: "◉", name: "Signal Physics", desc: "Block uniformity + edge sharpness calibrati su FF++" },
        { icon: "◈", name: "Moiré Screen", desc: "Rileva registrazioni fisiche di schermo LCD" },
        { icon: "◉", name: "PRNU Sensor", desc: "Impronta digitale del sensore camera fisico" },
        { icon: "◈", name: "Virtual Cam", desc: "Injection OBS/Deep-Live-Cam via sensor noise analysis" },
        { icon: "◉", name: "rPPG Cardiaco", desc: "Segnale cardiaco biologico dal canale verde (FFT)" },
      ],
    },
    features: {
      title: "Non un detector. Un'infrastruttura forense.",
      items: [
        {
          tag: "EXPLAINABILITY",
          title: "Heatmap ELA + Signal Map",
          desc: "Visualizza esattamente dove il video è stato manipolato. Le zone a compressione anomala appaiono in rosso. Prova visiva per il tribunale.",
        },
        {
          tag: "AI LEGALE",
          title: "Narrativa Llama 3.3-70B",
          desc: "La conclusione forense non è un numero. È un paragrafo in italiano giuridico firmato dall'AI: vettore d'attacco, layer coinvolti, raccomandazione operativa.",
        },
        {
          tag: "CHAIN OF CUSTODY",
          title: "QR verificabile + SHA-256",
          desc: "Ogni report ha un hash SHA-256 e un QR che punta all'endpoint /verify live. Se il PDF viene modificato, la verifica fallisce.",
        },
        {
          tag: "CROSS-LAYER",
          title: "Motore di Inferenza Forense",
          desc: "AURA non analizza layer isolati. Se Virtual Cam + rPPG convergono, il vettore diventa VIRTUAL_CAM_DEEPFAKE. 8 pattern di attacco mappati.",
        },
      ],
    },
    pricing: {
      title: "Prezzi",
      sub: "Inizia gratis. Scala quando hai clienti.",
      plans: [
        {
          name: "Free",
          price: "€0",
          period: "/mese",
          desc: "Per provare AURA",
          features: ["10 analisi/mese", "PDF con watermark AURA", "Verdetto base 8 layer", "Chain-of-custody SHA-256"],
          cta: "Inizia gratis",
          highlight: false,
        },
        {
          name: "Pro",
          price: "€24",
          period: "/mese",
          desc: "Per professionisti",
          features: ["Analisi illimitate", "PDF clean + QR verificabile", "Narrativa AI in italiano/inglese", "Heatmap ELA full-res", "Priorità elaborazione"],
          cta: "Inizia Pro",
          highlight: true,
          badge: "Più popolare",
        },
        {
          name: "Enterprise",
          price: "Su richiesta",
          period: "",
          desc: "Per studi e assicurazioni",
          features: ["API privata dedicata", "Fine-tune custom per settore", "SLA garantito", "Onboarding dedicato", "Compliance EU AI Act + DORA", "White-label report"],
          cta: "Contattaci",
          highlight: false,
        },
      ],
    },
    usecases: {
      title: "Chi usa AURA",
      items: [
        { icon: "⚖", title: "Studi Legali", desc: "Perizie video per processi civili e penali. Report ammissibile con chain-of-custody." },
        { icon: "🛡", title: "Assicurazioni", desc: "Verifica sinistri da video. Rileva frodi da screen recording o deepfake." },
        { icon: "🔍", title: "Investigatori Privati", desc: "Analisi forensi su materiale video contestato. Output direttamente allegabile." },
        { icon: "🏢", title: "Corporate Security", desc: "Verifica identità in videochiamate critiche. Anti-impersonation per C-level." },
      ],
    },
    footer: {
      desc: "AURA Reality Firewall — Analisi forense video di nuova generazione.",
      links: ["GitHub", "Docs", "API", "Privacy"],
      copy: "© 2026 AURA. Tutti i diritti riservati.",
    },
  },
  en: {
    nav: { product: "Product", pricing: "Pricing", docs: "Docs", cta: "Try now" },
    hero: {
      badge: "v0.9 — 8 Layers + Legal AI",
      title: ["The Digital Forensic", "Expert against", "Deepfakes & AI"],
      sub: "Multi-layer analysis with rPPG cardiac signals, ELA heatmaps and legal conclusion generated by Llama 3.3-70B. PDF report with verifiable QR code and SHA-256 chain-of-custody.",
      cta1: "Start free",
      cta2: "Enterprise Demo",
      trust: ["No credit card required", "Report in <3 min", "EU-compliant deploy"],
    },
    layers: {
      title: "8 Forensic Analysis Layers",
      sub: "Every video is decomposed into independent signals. Convergence between layers determines the verdict.",
      items: [
        { icon: "◈", name: "Metadata", desc: "Encoder tags, GPS, device fingerprint, timestamp discrepancy" },
        { icon: "◉", name: "Visual AI", desc: "Dual-model deepfake detection: dima806 + umm-maybe" },
        { icon: "◈", name: "Audio Sync", desc: "A/V drift, TTS voice signatures, 50/60Hz spectrum" },
        { icon: "◉", name: "Signal Physics", desc: "Block uniformity + edge sharpness calibrated on FF++" },
        { icon: "◈", name: "Moiré Screen", desc: "Detects physical screen recordings from LCD displays" },
        { icon: "◉", name: "PRNU Sensor", desc: "Physical camera sensor digital fingerprint" },
        { icon: "◈", name: "Virtual Cam", desc: "OBS/Deep-Live-Cam injection via sensor noise analysis" },
        { icon: "◉", name: "rPPG Cardiac", desc: "Biological cardiac signal from green channel (FFT)" },
      ],
    },
    features: {
      title: "Not a detector. A forensic infrastructure.",
      items: [
        {
          tag: "EXPLAINABILITY",
          title: "ELA Heatmap + Signal Map",
          desc: "Visualize exactly where the video was manipulated. Areas with anomalous compression appear in red. Visual evidence for court.",
        },
        {
          tag: "LEGAL AI",
          title: "Llama 3.3-70B Narrative",
          desc: "The forensic conclusion is not a number. It's a paragraph in legal language: attack vector, involved layers, operational recommendation.",
        },
        {
          tag: "CHAIN OF CUSTODY",
          title: "Verifiable QR + SHA-256",
          desc: "Every report has a SHA-256 hash and a QR pointing to the live /verify endpoint. If the PDF is modified, verification fails.",
        },
        {
          tag: "CROSS-LAYER",
          title: "Forensic Inference Engine",
          desc: "AURA doesn't analyze isolated layers. If Virtual Cam + rPPG converge, the vector becomes VIRTUAL_CAM_DEEPFAKE. 8 attack patterns mapped.",
        },
      ],
    },
    pricing: {
      title: "Pricing",
      sub: "Start free. Scale when you have clients.",
      plans: [
        {
          name: "Free",
          price: "€0",
          period: "/month",
          desc: "Try AURA",
          features: ["10 analyses/month", "PDF with AURA watermark", "Base 8-layer verdict", "SHA-256 chain-of-custody"],
          cta: "Start free",
          highlight: false,
        },
        {
          name: "Pro",
          price: "€24",
          period: "/month",
          desc: "For professionals",
          features: ["Unlimited analyses", "Clean PDF + verifiable QR", "AI narrative IT/EN", "Full-res ELA heatmap", "Priority processing"],
          cta: "Start Pro",
          highlight: true,
          badge: "Most popular",
        },
        {
          name: "Enterprise",
          price: "On request",
          period: "",
          desc: "For firms & insurers",
          features: ["Dedicated private API", "Custom fine-tuning", "Guaranteed SLA", "Dedicated onboarding", "EU AI Act + DORA compliance", "White-label reports"],
          cta: "Contact us",
          highlight: false,
        },
      ],
    },
    usecases: {
      title: "Who uses AURA",
      items: [
        { icon: "⚖", title: "Law Firms", desc: "Video forensics for civil and criminal proceedings. Admissible report with chain-of-custody." },
        { icon: "🛡", title: "Insurance", desc: "Claims video verification. Detect fraud from screen recordings or deepfakes." },
        { icon: "🔍", title: "Investigators", desc: "Forensic analysis on contested video material. Output directly attachable to reports." },
        { icon: "🏢", title: "Corporate Security", desc: "Identity verification in critical video calls. Anti-impersonation for C-level." },
      ],
    },
    footer: {
      desc: "AURA Reality Firewall — Next-generation video forensic analysis.",
      links: ["GitHub", "Docs", "API", "Privacy"],
      copy: "© 2026 AURA. All rights reserved.",
    },
  },
};

export default function AuraLanding() {
  const [lang, setLang] = useState<"it" | "en">("it");
  const [scrolled, setScrolled] = useState(false);
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  const t = copy[lang];
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setVisibleSections((s) => { const n = new Set(Array.from(s)); n.add(e.target.id); return n; });
        });
      },
      { threshold: 0.1 }
    );
    document.querySelectorAll("[data-observe]").forEach((el) => observerRef.current?.observe(el));
    return () => observerRef.current?.disconnect();
  }, [lang]);

  const CYAN = "#00e5ff";
  const RED = "#ff2d55";

  return (
    <div style={{ background: "#050508", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace", minHeight: "100vh", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::selection { background: #00e5ff33; color: #00e5ff; }
        ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #050508; } ::-webkit-scrollbar-thumb { background: #00e5ff44; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(32px); } to { opacity:1; transform:translateY(0); } }
        @keyframes scanline { from { transform: translateY(-100%); } to { transform: translateY(100vh); } }
        @keyframes pulse { 0%,100% { opacity:0.4; } 50% { opacity:1; } }
        @keyframes glitch { 0%,100% { clip-path:inset(0 0 95% 0); transform:translateX(0); } 20% { clip-path:inset(10% 0 70% 0); transform:translateX(-4px); } 40% { clip-path:inset(50% 0 30% 0); transform:translateX(4px); } 60% { clip-path:inset(80% 0 5% 0); transform:translateX(-2px); } }
        .fade-up { opacity:0; transform:translateY(32px); transition: opacity 0.7s ease, transform 0.7s ease; }
        .fade-up.visible { opacity:1; transform:translateY(0); }
        .layer-card:hover { border-color: #00e5ff66 !important; background: #0a0a14 !important; transform: translateY(-2px); }
        .feature-card:hover { border-color: #00e5ff44 !important; }
        .plan-card:hover { transform: translateY(-4px); }
        .usecase-card:hover { border-color: #00e5ff44 !important; background: #0a0a14 !important; }
        .nav-link:hover { color: #00e5ff; }
        .btn-primary:hover { background: #00c4d9; box-shadow: 0 0 24px #00e5ff44; }
        .btn-outline:hover { border-color: #00e5ff; color: #00e5ff; background: #00e5ff0a; }
        .lang-btn:hover { color: #00e5ff; }
        * { transition: border-color 0.2s, color 0.2s, background 0.2s, transform 0.2s, box-shadow 0.2s; }
      `}</style>

      {/* Scanline effect */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden", opacity: 0.03 }}>
        <div style={{ position: "absolute", width: "100%", height: "2px", background: `linear-gradient(transparent, ${CYAN}, transparent)`, animation: "scanline 8s linear infinite" }} />
      </div>

      {/* Grid background */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, backgroundImage: `linear-gradient(#00e5ff08 1px, transparent 1px), linear-gradient(90deg, #00e5ff08 1px, transparent 1px)`, backgroundSize: "64px 64px" }} />

      {/* NAV */}
      <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, padding: "0 2rem", height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", background: scrolled ? "rgba(5,5,8,0.95)" : "transparent", borderBottom: scrolled ? "1px solid #ffffff0a" : "1px solid transparent", backdropFilter: scrolled ? "blur(12px)" : "none" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ width: "28px", height: "28px", border: `2px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", color: CYAN, fontWeight: 700 }}>A</div>
          <span style={{ fontWeight: 700, fontSize: "14px", letterSpacing: "0.15em" }}>AURA</span>
          <span style={{ color: "#ffffff33", fontSize: "11px", marginLeft: "4px" }}>v0.9</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
          {[t.nav.product, t.nav.pricing, t.nav.docs].map((l) => (
            <a key={l} href="#" className="nav-link" style={{ fontSize: "12px", color: "#aaaacc", textDecoration: "none", letterSpacing: "0.08em" }}>{l}</a>
          ))}
          <div style={{ display: "flex", gap: "4px", background: "#ffffff0a", border: "1px solid #ffffff14", padding: "2px" }}>
            {(["it", "en"] as ("it" | "en")[]).map((l) => (
              <button key={l} className="lang-btn" onClick={() => setLang(l)} style={{ padding: "3px 10px", fontSize: "11px", background: lang === l ? CYAN : "transparent", color: lang === l ? "#050508" : "#666688", border: "none", cursor: "pointer", fontFamily: "inherit", fontWeight: lang === l ? 700 : 400, letterSpacing: "0.05em" }}>{l.toUpperCase()}</button>
            ))}
          </div>
          <a href="/analyze" className="btn-primary" style={{ padding: "8px 20px", background: CYAN, color: "#050508", border: "none", fontSize: "12px", fontFamily: "inherit", fontWeight: 700, cursor: "pointer", letterSpacing: "0.08em", textDecoration: "none" }}>{t.nav.cta}</a>
        </div>
      </nav>

      {/* HERO */}
      <section style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "8rem 2rem 4rem", position: "relative", textAlign: "center" }}>
        {/* Glow */}
        <div style={{ position: "absolute", top: "30%", left: "50%", transform: "translate(-50%,-50%)", width: "600px", height: "600px", background: `radial-gradient(circle, ${CYAN}0a 0%, transparent 70%)`, pointerEvents: "none" }} />

        <div style={{ animation: "fadeUp 0.6s ease 0.1s both" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", border: `1px solid ${CYAN}44`, padding: "6px 16px", marginBottom: "2rem", fontSize: "11px", color: CYAN, letterSpacing: "0.12em" }}>
            <span style={{ width: "6px", height: "6px", background: CYAN, borderRadius: "50%", animation: "pulse 2s infinite" }} />
            {t.hero.badge}
          </div>
        </div>

        <h1 style={{ fontSize: "clamp(3rem, 8vw, 7rem)", fontWeight: 700, lineHeight: 1.0, marginBottom: "2rem", letterSpacing: "-0.02em", animation: "fadeUp 0.6s ease 0.2s both" }}>
          {t.hero.title.map((line, i) => (
            <div key={i} style={{ display: "block", color: i === 2 ? CYAN : "#e8e8f0" }}>{line}</div>
          ))}
        </h1>

        <p style={{ maxWidth: "600px", color: "#888899", fontSize: "15px", lineHeight: 1.7, marginBottom: "2.5rem", animation: "fadeUp 0.6s ease 0.3s both" }}>{t.hero.sub}</p>

        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center", animation: "fadeUp 0.6s ease 0.4s both" }}>
          <a href="/analyze" className="btn-primary" style={{ padding: "14px 32px", background: CYAN, color: "#050508", border: "none", fontSize: "13px", fontFamily: "inherit", fontWeight: 700, cursor: "pointer", letterSpacing: "0.08em", textDecoration: "none" }}>{t.hero.cta1}</a>
          <a href="mailto:kaicarsaad455@gmail.com" className="btn-outline" style={{ padding: "14px 32px", background: "transparent", color: "#ccccdd", border: "1px solid #ffffff22", fontSize: "13px", fontFamily: "inherit", cursor: "pointer", letterSpacing: "0.08em", textDecoration: "none" }}>{t.hero.cta2}</a>
        </div>

        <div style={{ display: "flex", gap: "2rem", marginTop: "3rem", animation: "fadeUp 0.6s ease 0.5s both" }}>
          {t.hero.trust.map((item) => (
            <div key={item} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#555566" }}>
              <span style={{ color: CYAN }}>✓</span> {item}
            </div>
          ))}
        </div>

        {/* Verdict mockup */}
        <div style={{ marginTop: "5rem", border: "1px solid #00e5ff22", background: "#0a0a14", padding: "1.5rem 2rem", maxWidth: "480px", textAlign: "left", animation: "fadeUp 0.6s ease 0.6s both" }}>
          <div style={{ fontSize: "10px", color: "#555566", letterSpacing: "0.1em", marginBottom: "0.75rem" }}>AURA VERDICT OUTPUT</div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "1rem" }}>
            <div style={{ padding: "4px 12px", background: "#ff2d5522", border: `1px solid ${RED}`, color: RED, fontSize: "13px", fontWeight: 700, letterSpacing: "0.1em" }}>LIKELY MANIPULATED</div>
            <div style={{ fontSize: "12px", color: "#888899" }}>Score: 51% · HIGH confidence</div>
          </div>
          <div style={{ fontSize: "11px", color: "#555566", fontStyle: "italic", lineHeight: 1.6 }}>
            "Vettore: POST_PRODUCTION_DEEPFAKE · rPPG: ABSENT · BPM: 53.3 (anomalo) · PRNU: 72% · Signal: 72%"
          </div>
        </div>
      </section>

      {/* LAYERS */}
      <section id="layers" data-observe style={{ padding: "6rem 2rem", maxWidth: "1100px", margin: "0 auto" }}>
        <div className={`fade-up ${visibleSections.has("layers") ? "visible" : ""}`}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ fontSize: "11px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1rem" }}>ARCHITETTURA</div>
            <h2 style={{ fontSize: "clamp(1.8rem, 4vw, 3rem)", fontWeight: 700, marginBottom: "1rem" }}>{t.layers.title}</h2>
            <p style={{ color: "#666677", maxWidth: "560px", margin: "0 auto", lineHeight: 1.6, fontSize: "14px" }}>{t.layers.sub}</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1px", background: "#ffffff0a" }}>
            {t.layers.items.map((item, i) => (
              <div key={i} className="layer-card" style={{ background: "#050508", border: "1px solid #ffffff08", padding: "1.5rem", cursor: "default" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "0.75rem" }}>
                  <span style={{ color: i % 2 === 0 ? CYAN : "#ffffff44", fontSize: "16px" }}>{item.icon}</span>
                  <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.1em", color: "#ccccdd" }}>LAYER {i + 1}</div>
                </div>
                <div style={{ fontWeight: 700, fontSize: "15px", marginBottom: "0.5rem", color: "#e8e8f0" }}>{item.name}</div>
                <div style={{ fontSize: "12px", color: "#555566", lineHeight: 1.6 }}>{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" data-observe style={{ padding: "6rem 2rem", background: "#07070d" }}>
        <div className={`fade-up ${visibleSections.has("features") ? "visible" : ""}`} style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ fontSize: "11px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1rem" }}>DIFFERENZIAZIONE</div>
            <h2 style={{ fontSize: "clamp(1.8rem, 4vw, 3rem)", fontWeight: 700 }}>{t.features.title}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
            {t.features.items.map((item, i) => (
              <div key={i} className="feature-card" style={{ border: "1px solid #ffffff0a", padding: "2rem", background: "#050508" }}>
                <div style={{ fontSize: "10px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1rem", fontWeight: 700 }}>{item.tag}</div>
                <h3 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "0.75rem", color: "#e8e8f0" }}>{item.title}</h3>
                <p style={{ fontSize: "13px", color: "#555566", lineHeight: 1.7 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* USE CASES */}
      <section id="usecases" data-observe style={{ padding: "6rem 2rem", maxWidth: "1100px", margin: "0 auto" }}>
        <div className={`fade-up ${visibleSections.has("usecases") ? "visible" : ""}`}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ fontSize: "11px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1rem" }}>TARGET B2B</div>
            <h2 style={{ fontSize: "clamp(1.8rem, 4vw, 3rem)", fontWeight: 700 }}>{t.usecases.title}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1.5rem" }}>
            {t.usecases.items.map((item, i) => (
              <div key={i} className="usecase-card" style={{ border: "1px solid #ffffff0a", padding: "2rem", background: "#050508" }}>
                <div style={{ fontSize: "28px", marginBottom: "1rem" }}>{item.icon}</div>
                <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "0.5rem" }}>{item.title}</h3>
                <p style={{ fontSize: "13px", color: "#555566", lineHeight: 1.6 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" data-observe style={{ padding: "6rem 2rem", background: "#07070d" }}>
        <div className={`fade-up ${visibleSections.has("pricing") ? "visible" : ""}`} style={{ maxWidth: "1000px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ fontSize: "11px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1rem" }}>PRICING</div>
            <h2 style={{ fontSize: "clamp(1.8rem, 4vw, 3rem)", fontWeight: 700, marginBottom: "0.75rem" }}>{t.pricing.title}</h2>
            <p style={{ color: "#666677", fontSize: "14px" }}>{t.pricing.sub}</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem", alignItems: "start" }}>
            {t.pricing.plans.map((plan, i) => (
              <div key={i} className="plan-card" style={{ border: plan.highlight ? `1px solid ${CYAN}66` : "1px solid #ffffff0a", padding: "2rem", background: plan.highlight ? "#0a141a" : "#050508", position: "relative" }}>
                {plan.badge && (
                  <div style={{ position: "absolute", top: "-1px", left: "50%", transform: "translateX(-50%)", background: CYAN, color: "#050508", fontSize: "10px", fontWeight: 700, padding: "3px 12px", letterSpacing: "0.1em" }}>{plan.badge}</div>
                )}
                <div style={{ fontSize: "11px", color: "#666677", marginBottom: "0.5rem", letterSpacing: "0.1em" }}>{plan.desc.toUpperCase()}</div>
                <div style={{ fontWeight: 700, fontSize: "28px", marginBottom: "0.25rem", color: plan.highlight ? CYAN : "#e8e8f0" }}>
                  {plan.name}
                </div>
                <div style={{ fontSize: "32px", fontWeight: 700, color: "#e8e8f0", marginBottom: "1.5rem" }}>
                  {plan.price}<span style={{ fontSize: "14px", color: "#555566", fontWeight: 400 }}>{plan.period}</span>
                </div>
                <div style={{ borderTop: "1px solid #ffffff0a", paddingTop: "1.5rem", marginBottom: "1.5rem" }}>
                  {plan.features.map((f) => (
                    <div key={f} style={{ display: "flex", gap: "8px", fontSize: "13px", color: "#888899", marginBottom: "0.6rem", lineHeight: 1.5 }}>
                      <span style={{ color: CYAN, flexShrink: 0 }}>→</span> {f}
                    </div>
                  ))}
                </div>
                <a href={i === 2 ? "mailto:kaicarsaad455@gmail.com" : "/analyze"} style={{ display: "block", padding: "12px", textAlign: "center", background: plan.highlight ? CYAN : "transparent", color: plan.highlight ? "#050508" : "#ccccdd", border: plan.highlight ? "none" : "1px solid #ffffff22", fontSize: "13px", fontFamily: "inherit", fontWeight: 700, cursor: "pointer", letterSpacing: "0.08em", textDecoration: "none" }}>{plan.cta}</a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section style={{ padding: "6rem 2rem", textAlign: "center", position: "relative" }}>
        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: "500px", height: "300px", background: `radial-gradient(ellipse, ${CYAN}08 0%, transparent 70%)`, pointerEvents: "none" }} />
        <div style={{ fontSize: "11px", color: CYAN, letterSpacing: "0.15em", marginBottom: "1.5rem" }}>OPEN SOURCE + ENTERPRISE</div>
        <h2 style={{ fontSize: "clamp(1.5rem, 4vw, 2.5rem)", fontWeight: 700, marginBottom: "1rem" }}>
          {lang === "it" ? "Pronto a difenderti dai deepfake?" : "Ready to fight deepfakes?"}
        </h2>
        <p style={{ color: "#555566", fontSize: "14px", marginBottom: "2.5rem", maxWidth: "400px", margin: "0 auto 2.5rem" }}>
          {lang === "it" ? "Backend open-source su GitHub. Deploy su Hugging Face Spaces." : "Open-source backend on GitHub. Deployed on Hugging Face Spaces."}
        </p>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
          <a href="/analyze" className="btn-primary" style={{ padding: "14px 32px", background: CYAN, color: "#050508", fontSize: "13px", fontFamily: "inherit", fontWeight: 700, cursor: "pointer", letterSpacing: "0.08em", textDecoration: "none" }}>
            {lang === "it" ? "Inizia ora →" : "Start now →"}
          </a>
          <a href="https://github.com/Artkill24/aura-backend" className="btn-outline" style={{ padding: "14px 32px", background: "transparent", color: "#ccccdd", border: "1px solid #ffffff22", fontSize: "13px", fontFamily: "inherit", cursor: "pointer", letterSpacing: "0.08em", textDecoration: "none" }}>GitHub ↗</a>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid #ffffff08", padding: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ width: "20px", height: "20px", border: `1px solid ${CYAN}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", color: CYAN }}>A</div>
          <span style={{ fontSize: "11px", color: "#444455" }}>{t.footer.desc}</span>
        </div>
        <div style={{ display: "flex", gap: "1.5rem" }}>
          {t.footer.links.map((l) => (
            <a key={l} href="#" style={{ fontSize: "11px", color: "#444455", textDecoration: "none" }}>{l}</a>
          ))}
        </div>
        <div style={{ fontSize: "11px", color: "#333344" }}>{t.footer.copy}</div>
      </footer>
    </div>
  );
}
