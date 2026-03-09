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
    if (!f.type.startsWith("video/")) { setError("Solo file video (MP4, MOV, AVI)"); return; }
    setError(""); setFile(f);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if (f) handleFile(f);
  }, [handleFile]);

  const analyze = async () => {
    if (!file) return;
    setUploading(true); setProgress(0); setError("");
    const msgs = ["Initializing pipeline...","Extracting metadata...","Visual frame analysis...","Audio sync check...","Signal physics...","Generating report..."];
    let mi = 0; setStatusMsg(msgs[0]);
    const mi_int = setInterval(() => { mi = Math.min(mi+1, msgs.length-1); setStatusMsg(msgs[mi]); }, 8000);
    const pr_int = setInterval(() => setProgress(p => p < 88 ? p + Math.random()*3 : p), 500);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch("/api/backend/analyze", { method: "POST", body: fd, signal: AbortSignal.timeout(300000) });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      clearInterval(mi_int); clearInterval(pr_int);
      setProgress(100); setStatusMsg("Analysis complete.");
      sessionStorage.setItem(`aura_result_${data.job_id}`, JSON.stringify(data));
      setTimeout(() => router.push(`/result/${data.job_id}`), 600);
    } catch (err: any) {
      clearInterval(mi_int); clearInterval(pr_int);
      setUploading(false); setProgress(0);
      setError(err.message || "Analysis failed. Make sure backend is running on port 8000.");
    }
  };

  return (
    <div style={{minHeight:'100vh',display:'flex',flexDirection:'column',background:'#080b0f',color:'#c8d4dc',fontFamily:'monospace'}}>
      <header style={{borderBottom:'1px solid #1e2830',padding:'20px 32px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
        <div style={{display:'flex',alignItems:'center',gap:'12px'}}>
          <div style={{width:32,height:32,border:'1px solid rgba(0,180,255,0.4)',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <div style={{width:12,height:12,background:'#00b4ff',boxShadow:'0 0 10px #00b4ff'}} />
          </div>
          <span style={{fontSize:13,fontWeight:500,color:'#e8f0f5',letterSpacing:'0.15em'}}>AURA</span>
          <span style={{fontSize:11,color:'#3a4a56',letterSpacing:'0.1em'}}>v0.3 — FORENSIC ENGINE</span>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:8}}>
          <div style={{width:8,height:8,borderRadius:'50%',background:'#00e87a',boxShadow:'0 0 8px #00e87a'}} />
          <span style={{fontSize:11,color:'#3a4a56'}}>SYSTEM ONLINE</span>
        </div>
      </header>

      <main style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:'64px 24px'}}>
        <div style={{textAlign:'center',marginBottom:64,maxWidth:560}}>
          <div style={{fontSize:11,color:'rgba(0,180,255,0.7)',letterSpacing:'0.2em',textTransform:'uppercase',marginBottom:16}}>
            Advanced Universal Reality Authentication
          </div>
          <h1 style={{fontSize:36,fontWeight:300,color:'#e8f0f5',marginBottom:16,lineHeight:1.3,margin:'0 0 16px'}}>
            Detect AI-Generated<br/>
            <span style={{fontWeight:600,color:'#00b4ff'}}>Video Evidence</span>
          </h1>
          <p style={{fontSize:12,color:'#3a4a56',lineHeight:1.8,margin:'16px 0 0'}}>
            5-layer forensic analysis · metadata · visual · audio · signal physics · screen detection<br/>
            For insurance adjusters, legal teams, and digital forensics professionals.
          </p>
        </div>

        {!uploading ? (
          <div style={{width:'100%',maxWidth:480}}>
            <div
              onClick={() => !file && inputRef.current?.click()}
              onDrop={onDrop}
              onDragOver={e=>{e.preventDefault();setDragging(true);}}
              onDragLeave={()=>setDragging(false)}
              style={{
                position:'relative',border:`2px solid ${dragging?'#00b4ff':file?'rgba(0,232,122,0.5)':'#1e2830'}`,
                padding:'48px 32px',cursor:file?'default':'pointer',
                background:dragging?'rgba(0,180,255,0.04)':file?'rgba(0,232,122,0.04)':'transparent',
                transition:'all 0.3s',textAlign:'center'
              }}
            >
              {['top left','top right','bottom left','bottom right'].map(pos => {
                const [v,h] = pos.split(' ');
                const c = dragging?'#00b4ff':file?'#00e87a':'#3a4a56';
                return <div key={pos} style={{position:'absolute',[v]:8,[h]:8,width:16,height:16,
                  borderTop:v==='top'?`2px solid ${c}`:'none',borderBottom:v==='bottom'?`2px solid ${c}`:'none',
                  borderLeft:h==='left'?`2px solid ${c}`:'none',borderRight:h==='right'?`2px solid ${c}`:'none'}} />;
              })}
              {file ? (
                <>
                  <div style={{fontSize:11,color:'#3a4a56',marginBottom:8,textTransform:'uppercase',letterSpacing:'0.1em'}}>File loaded</div>
                  <div style={{fontSize:13,color:'#e8f0f5',marginBottom:4}}>{file.name}</div>
                  <div style={{fontSize:11,color:'#3a4a56'}}>{(file.size/1024/1024).toFixed(1)} MB</div>
                </>
              ) : (
                <>
                  <div style={{fontSize:32,marginBottom:12,opacity:0.3}}>▶</div>
                  <div style={{fontSize:13,color:'#c8d4dc',marginBottom:4}}>{dragging?'Release to load':'Drop video file here'}</div>
                  <div style={{fontSize:11,color:'#3a4a56'}}>or click to browse · MP4, MOV, AVI, MKV</div>
                </>
              )}
            </div>

            <input ref={inputRef} type="file" accept="video/*" style={{display:'none'}}
              onChange={e=>e.target.files?.[0]&&handleFile(e.target.files[0])} />

            {error && <div style={{marginTop:12,fontSize:11,color:'#ff2d4e',border:'1px solid rgba(255,45,78,0.2)',padding:'8px 12px',background:'rgba(255,45,78,0.05)'}}>⚠ {error}</div>}

            {file && (
              <div style={{marginTop:16,display:'flex',gap:12}}>
                <button onClick={analyze} style={{flex:1,fontFamily:'monospace',fontSize:13,fontWeight:500,padding:'12px 24px',background:'#00b4ff',color:'#080b0f',border:'1px solid #00b4ff',cursor:'pointer',transition:'all 0.2s'}}
                  onMouseEnter={e=>{(e.target as HTMLElement).style.background='transparent';(e.target as HTMLElement).style.color='#00b4ff';}}
                  onMouseLeave={e=>{(e.target as HTMLElement).style.background='#00b4ff';(e.target as HTMLElement).style.color='#080b0f';}}>
                  INITIATE ANALYSIS →
                </button>
                <button onClick={()=>{setFile(null);setError('');}} style={{fontFamily:'monospace',fontSize:11,padding:'12px 16px',background:'transparent',color:'#3a4a56',border:'1px solid #1e2830',cursor:'pointer'}}>
                  CLEAR
                </button>
              </div>
            )}
          </div>
        ) : (
          <div style={{width:'100%',maxWidth:480,border:'1px solid #1e2830',padding:32}}>
            <div style={{fontSize:11,color:'#3a4a56',textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:24}}>Analysis in progress</div>
            <div style={{marginBottom:24}}>
              <div style={{display:'flex',justifyContent:'space-between',fontSize:11,color:'#3a4a56',marginBottom:8}}>
                <span>{statusMsg}</span><span>{Math.round(progress)}%</span>
              </div>
              <div style={{height:2,background:'#1e2830',width:'100%'}}>
                <div style={{height:'100%',width:`${progress}%`,background:'linear-gradient(90deg,#00b4ff,#00e87a)',transition:'width 0.5s',boxShadow:'0 0 10px #00b4ff'}} />
              </div>
            </div>
            <div style={{fontSize:11,color:'#3a4a56'}}>{file?.name} · {((file?.size||0)/1024/1024).toFixed(1)} MB</div>
            <div style={{marginTop:12,fontSize:11,color:'#3a4a56'}}>█ Do not close this window</div>
          </div>
        )}
      </main>

      <footer style={{borderTop:'1px solid #1e2830',padding:'16px 32px',display:'flex',justifyContent:'space-between'}}>
        <span style={{fontSize:11,color:'#3a4a56'}}>AURA FORENSIC ENGINE — NOT FOR CONSUMER USE</span>
        <span style={{fontSize:11,color:'#3a4a56'}}>5-LAYER DETECTION PIPELINE</span>
      </footer>
    </div>
  );
}
