"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

export default function ResultPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();
  const [result, setResult] = useState<any>(null);
  const [bars, setBars] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem(`aura_result_${jobId}`);
    if (stored) { setResult(JSON.parse(stored)); setTimeout(()=>setBars(true),200); }
    else router.push("/");
  }, [jobId, router]);

  if (!result) return <div style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',background:'#080b0f',color:'#3a4a56',fontFamily:'monospace',fontSize:12}}>Loading...</div>;

  const colorMap: Record<string,string> = {green:'#00e87a',yellow:'#ffb700',orange:'#ff7322',red:'#ff2d4e'};
  const vc = colorMap[result.verdict.risk_color] || '#00e87a';
  const score = result.verdict.composite_score;
  const bd = result.verdict.breakdown;

  const layers = [
    {label:'Metadata',     score: result.metadata_flags?.filter((f:any)=>f.severity!=='INFO').length>0?0.3:0.03, color:'#7c8cf0'},
    {label:'Visual',       score: result.visual_score||0,              color:'#a855f7'},
    {label:'Audio Sync',   score: result.audio_score||0,               color:'#06b6d4'},
    {label:'Signal Physics',score:result.signal_score||0,              color:'#00b4ff'},
    {label:'Screen Detect',score: result.screen_recording_score||0,    color:'#f59e0b'},
  ];

  return (
    <div style={{minHeight:'100vh',background:'#080b0f',color:'#c8d4dc',fontFamily:'monospace'}}>
      <header style={{borderBottom:'1px solid #1e2830',padding:'20px 32px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
        <div style={{display:'flex',alignItems:'center',gap:12,cursor:'pointer'}} onClick={()=>router.push('/')}>
          <div style={{width:32,height:32,border:'1px solid rgba(0,180,255,0.4)',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <div style={{width:12,height:12,background:'#00b4ff',boxShadow:'0 0 10px #00b4ff'}} />
          </div>
          <span style={{fontSize:13,color:'#e8f0f5',letterSpacing:'0.15em'}}>AURA</span>
          <span style={{fontSize:11,color:'#3a4a56'}}>/ FORENSIC REPORT</span>
        </div>
        <span style={{fontSize:11,color:'#3a4a56'}}>JOB {result.job_id?.split('-')[0].toUpperCase()}</span>
      </header>

      <main style={{maxWidth:800,margin:'0 auto',padding:'48px 24px'}}>
        {/* Verdict */}
        <div style={{border:`1px solid ${vc}`,background:`${vc}0f`,padding:32,marginBottom:32,position:'relative'}}>
          {['top left','top right','bottom left','bottom right'].map(pos=>{
            const [v,h]=pos.split(' ');
            return <div key={pos} style={{position:'absolute',[v]:8,[h]:8,width:20,height:20,
              borderTop:v==='top'?`2px solid ${vc}`:'none',borderBottom:v==='bottom'?`2px solid ${vc}`:'none',
              borderLeft:h==='left'?`2px solid ${vc}`:'none',borderRight:h==='right'?`2px solid ${vc}`:'none'}} />;
          })}
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:24}}>
            <div>
              <div style={{fontSize:11,color:vc,letterSpacing:'0.15em',textTransform:'uppercase',marginBottom:8}}>Forensic Verdict</div>
              <div style={{fontSize:28,fontWeight:600,color:vc,marginBottom:8}}>{result.verdict.label}</div>
              <div style={{fontSize:11,color:'#3a4a56'}}>{result.filename}</div>
            </div>
            <div style={{textAlign:'right'}}>
              <div style={{fontSize:48,fontWeight:300,color:vc,lineHeight:1}}>{Math.round(score*100)}</div>
              <div style={{fontSize:11,color:'#3a4a56'}}>RISK / 100</div>
              <div style={{fontSize:11,color:vc,marginTop:4}}>{result.verdict.confidence} CONFIDENCE</div>
            </div>
          </div>
          <div style={{marginTop:24,height:4,background:'#1e2830'}}>
            <div style={{height:'100%',width:bars?`${score*100}%`:'0%',background:vc,transition:'width 1s ease-out',boxShadow:`0 0 12px ${vc}`}} />
          </div>
          <div style={{marginTop:20,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:16,paddingTop:20,borderTop:`1px solid ${vc}30`}}>
            {[['ANALYSIS TIME',`${result.analysis_time_seconds}s`],['FLAGS RAISED',result.metadata_flags?.length||0],['LAYERS',`5 / 5`]].map(([k,v])=>(
              <div key={k}><div style={{fontSize:10,color:'#3a4a56',marginBottom:4}}>{k}</div><div style={{fontSize:13,color:'#e8f0f5'}}>{v}</div></div>
            ))}
          </div>
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:24,marginBottom:24}}>
          {/* Layer scores */}
          <div style={{border:'1px solid #1e2830',padding:24}}>
            <div style={{fontSize:11,color:'#3a4a56',textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:20}}>Layer Scores</div>
            {layers.map((l,i)=>(
              <div key={l.label} style={{marginBottom:16}}>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:11,marginBottom:6}}>
                  <span style={{color:'#c8d4dc'}}>{l.label}</span>
                  <span style={{color:l.color}}>{Math.round(l.score*100)}%</span>
                </div>
                <div style={{height:2,background:'#1e2830'}}>
                  <div style={{height:'100%',width:bars?`${l.score*100}%`:'0%',background:l.color,transition:`width ${0.7+i*0.1}s ease-out`,boxShadow:`0 0 6px ${l.color}60`}} />
                </div>
              </div>
            ))}
          </div>

          {/* Breakdown */}
          <div style={{border:'1px solid #1e2830',padding:24}}>
            <div style={{fontSize:11,color:'#3a4a56',textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:20}}>Score Contribution</div>
            {Object.entries(bd).map(([key,val]:any)=>(
              <div key={key} style={{display:'flex',alignItems:'center',gap:12,marginBottom:10}}>
                <span style={{fontSize:10,color:'#3a4a56',width:80,flexShrink:0,textTransform:'capitalize'}}>{key.replace('_contribution','').replace(/_/g,' ')}</span>
                <div style={{flex:1,height:1,background:'#1e2830'}}>
                  <div style={{height:'100%',width:bars?`${(val/score)*100}%`:'0%',background:'#00b4ff',transition:'width 0.7s ease-out'}} />
                </div>
                <span style={{fontSize:10,color:'#00b4ff',width:36,textAlign:'right'}}>{(val*100).toFixed(1)}%</span>
              </div>
            ))}
            <div style={{marginTop:16,paddingTop:16,borderTop:'1px solid #1e2830',display:'flex',justifyContent:'space-between',fontSize:11}}>
              <span style={{color:'#3a4a56'}}>COMPOSITE</span>
              <span style={{color:vc}}>{(score*100).toFixed(1)} / 100</span>
            </div>
          </div>
        </div>

        {/* Flags */}
        {result.metadata_flags?.length>0 && (
          <div style={{border:'1px solid #1e2830',padding:24,marginBottom:24}}>
            <div style={{fontSize:11,color:'#3a4a56',textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:16}}>Detection Flags</div>
            {result.metadata_flags.map((flag:any,i:number)=>{
              const sc = flag.severity==='HIGH'?'#ff2d4e':flag.severity==='MEDIUM'?'#ff7322':'#3a4a56';
              return (
                <div key={i} style={{display:'flex',gap:12,marginBottom:12,fontSize:11}}>
                  <span style={{flexShrink:0,padding:'2px 8px',border:`1px solid ${sc}40`,color:sc,background:`${sc}10`,fontSize:10,textTransform:'uppercase'}}>{flag.severity}</span>
                  <div>
                    <div style={{color:'#e8f0f5',marginBottom:2}}>{flag.type.replace(/_/g,' ')}</div>
                    <div style={{color:'#3a4a56',lineHeight:1.5}}>{flag.detail}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Actions */}
        <div style={{display:'flex',gap:12}}>
          <a href={`/api/backend${result.report_url}`} download={`AURA_${result.job_id}.pdf`}
            style={{fontFamily:'monospace',fontSize:12,padding:'12px 24px',border:'1px solid #00b4ff',color:'#00b4ff',background:'transparent',textDecoration:'none',cursor:'pointer',display:'inline-block'}}
            onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.background='#00b4ff';(e.currentTarget as HTMLElement).style.color='#080b0f';}}
            onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.background='transparent';(e.currentTarget as HTMLElement).style.color='#00b4ff';}}>
            ↓ DOWNLOAD PDF REPORT
          </a>
          <button onClick={()=>router.push('/')} style={{fontFamily:'monospace',fontSize:12,padding:'12px 24px',border:'1px solid #1e2830',color:'#3a4a56',background:'transparent',cursor:'pointer'}}>
            ← NEW ANALYSIS
          </button>
        </div>

        <div style={{marginTop:40,paddingTop:24,borderTop:'1px solid #1e2830',fontSize:10,color:'#3a4a56',lineHeight:1.8}}>
          AURA provides probabilistic analysis. Results should be validated by qualified forensic professionals.<br/>
          Report ID: {result.job_id}
        </div>
      </main>
    </div>
  );
}
