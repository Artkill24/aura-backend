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
  const [cameraMode, setCameraMode] = useState(false);
  const [recording, setRecording] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const router = useRouter();

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith("video/") && !f.type.startsWith("image/")) {
      setError("Solo file video (MP4, MOV, AVI)"); return;
    }
    setError(""); setFile(f);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if (f) handleFile(f);
  }, [handleFile]);

  // ── Camera: open ──────────────────────────────────────────────────────────
  const openCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });
      streamRef.current = stream;
      setCameraMode(true);
      setCameraReady(false);
      // Aspetta che il video element sia montato
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => setCameraReady(true);
        }
      }, 100);
    } catch (err: any) {
      setError("Camera non disponibile: " + (err.message || "permesso negato"));
    }
  };

  // ── Camera: start recording ───────────────────────────────────────────────
  const startRecording = () => {
    if (!streamRef.current) return;
    chunksRef.current = [];
    const mimeType = MediaRecorder.isTypeSupported("video/mp4")
      ? "video/mp4"
      : MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : "video/webm";
    const recorder = new MediaRecorder(streamRef.current, { mimeType });
    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType });
      const ext = mimeType.includes("mp4") ? "mp4" : "webm";
      const f = new File([blob], `aura_capture_${Date.now()}.${ext}`, { type: mimeType });
      setFile(f);
      closeCamera();
    };
    recorder.start();
    recorderRef.current = recorder;
    setRecording(true);
  };

  // ── Camera: stop recording ────────────────────────────────────────────────
  const stopRecording = () => {
    recorderRef.current?.stop();
    setRecording(false);
  };

  // ── Camera: close ─────────────────────────────────────────────────────────
  const closeCamera = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setCameraMode(false);
    setCameraReady(false);
    setRecording(false);
  };

  const analyze = async () => {
    if (!file) return;
    setUploading(true); setProgress(0); setError("");
    const msgs = ["Initializing pipeline...","Extracting metadata...","Visual frame analysis...","Audio sync check...","Signal physics...","PRNU sensor fingerprint...","Generating report..."];
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

  const cornerStyle = (v: string, h: string, color: string) => ({
    position: 'absolute' as const,
    [v]: 8, [h]: 8, width: 16, height: 16,
    borderTop: v === 'top' ? `2px solid ${color}` : 'none',
    borderBottom: v === 'bottom' ? `2px solid ${color}` : 'none',
    borderLeft: h === 'left' ? `2px solid ${color}` : 'none',
    borderRight: h === 'right' ? `2px solid ${color}` : 'none',
  });

  return (
    <div style={{minHeight:'100vh',display:'flex',flexDirection:'column',background:'#080b0f',color:'#c8d4dc',fontFamily:'monospace'}}>
      <header style={{borderBottom:'1px solid #1e2830',padding:'20px 32px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
        <div style={{display:'flex',alignItems:'center',gap:'12px'}}>
          <div style={{width:32,height:32,border:'1px solid rgba(0,180,255,0.4)',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <div style={{width:12,height:12,background:'#00b4ff',boxShadow:'0 0 10px #00b4ff'}} />
          </div>
          <span style={{fontSize:13,fontWeight:500,color:'#e8f0f5',letterSpacing:'0.15em'}}>AURA</span>
          <span style={{fontSize:11,color:'#3a4a56',letterSpacing:'0.1em'}}>v0.5 — FORENSIC ENGINE</span>
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
          <h1 style={{fontSize:36,fontWeight:300,color:'#e8f0f5',lineHeight:1.3,margin:'0 0 16px'}}>
            Detect AI-Generated<br/>
            <span style={{fontWeight:600,color:'#00b4ff'}}>Video Evidence</span>
          </h1>
          <p style={{fontSize:12,color:'#3a4a56',lineHeight:1.8,margin:'16px 0 0'}}>
            6-layer forensic analysis · metadata · visual · audio · signal physics · moire · PRNU<br/>
            For insurance adjusters, legal teams, and digital forensics professionals.
          </p>
        </div>

        {/* ── Camera Modal ─────────────────────────────────────────────────── */}
        {cameraMode && (
          <div style={{position:'fixed',inset:0,background:'rgba(8,11,15,0.96)',zIndex:100,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:24}}>
            <div style={{fontSize:11,color:'rgba(0,180,255,0.7)',letterSpacing:'0.2em',textTransform:'uppercase'}}>
              {recording ? '● REC — CAPTURING' : cameraReady ? 'CAMERA READY' : 'INITIALIZING CAMERA...'}
            </div>

            {/* Viewfinder */}
            <div style={{position:'relative',border:`2px solid ${recording?'#ff2d4e':cameraReady?'rgba(0,180,255,0.5)':'#1e2830'}`,maxWidth:560,width:'100%'}}>
              {['top left','top right','bottom left','bottom right'].map(pos => {
                const [v,h] = pos.split(' ');
                const c = recording ? '#ff2d4e' : '#00b4ff';
                return <div key={pos} style={cornerStyle(v,h,c)} />;
              })}
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                style={{width:'100%',display:'block',maxHeight:360,objectFit:'cover',background:'#000'}}
              />
              {recording && (
                <div style={{position:'absolute',top:16,left:16,display:'flex',alignItems:'center',gap:8}}>
                  <div style={{width:8,height:8,borderRadius:'50%',background:'#ff2d4e',animation:'pulse 1s infinite'}} />
                  <span style={{fontSize:11,color:'#ff2d4e',letterSpacing:'0.1em'}}>REC</span>
                </div>
              )}
            </div>

            {/* Camera controls */}
            <div style={{display:'flex',gap:12}}>
              {!recording ? (
                <button
                  onClick={startRecording}
                  disabled={!cameraReady}
                  style={{fontFamily:'monospace',fontSize:13,fontWeight:500,padding:'12px 32px',background:cameraReady?'#ff2d4e':'#1e2830',color:cameraReady?'#fff':'#3a4a56',border:`1px solid ${cameraReady?'#ff2d4e':'#1e2830'}`,cursor:cameraReady?'pointer':'not-allowed',letterSpacing:'0.1em'}}
                >
                  ● START REC
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  style={{fontFamily:'monospace',fontSize:13,fontWeight:500,padding:'12px 32px',background:'#ff2d4e',color:'#fff',border:'1px solid #ff2d4e',cursor:'pointer',letterSpacing:'0.1em',animation:'pulse 1s infinite'}}
                >
                  ■ STOP & ANALYZE
                </button>
              )}
              <button
                onClick={closeCamera}
                style={{fontFamily:'monospace',fontSize:11,padding:'12px 16px',background:'transparent',color:'#3a4a56',border:'1px solid #1e2830',cursor:'pointer'}}
              >
                CANCEL
              </button>
            </div>

            <div style={{fontSize:11,color:'#3a4a56',textAlign:'center'}}>
              {recording ? 'Press STOP when done — video will be analyzed automatically' : 'Point camera at subject · Press START REC to capture'}
            </div>
          </div>
        )}

        {!uploading ? (
          <div style={{width:'100%',maxWidth:480}}>
            {/* Drop zone */}
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
                return <div key={pos} style={cornerStyle(v,h,c)} />;
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

            {/* Camera button */}
            {!file && (
              <button
                onClick={openCamera}
                style={{
                  width:'100%',marginTop:12,fontFamily:'monospace',fontSize:12,
                  padding:'10px 24px',background:'transparent',color:'rgba(0,180,255,0.7)',
                  border:'1px solid rgba(0,180,255,0.25)',cursor:'pointer',
                  letterSpacing:'0.1em',transition:'all 0.2s',display:'flex',
                  alignItems:'center',justifyContent:'center',gap:8,
                }}
                onMouseEnter={e=>{(e.currentTarget).style.borderColor='rgba(0,180,255,0.6)';(e.currentTarget).style.background='rgba(0,180,255,0.05)';}}
                onMouseLeave={e=>{(e.currentTarget).style.borderColor='rgba(0,180,255,0.25)';(e.currentTarget).style.background='transparent';}}
              >
                <span style={{fontSize:16}}>◉</span>
                CAPTURE FROM CAMERA
              </button>
            )}

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
        <span style={{fontSize:11,color:'#3a4a56'}}>6-LAYER DETECTION PIPELINE</span>
      </footer>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
