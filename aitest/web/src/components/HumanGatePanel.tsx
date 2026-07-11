import { useEffect, useState } from 'react'
import { api } from '@/api/client'

type Gate={id:string;status:string;prompt:string;actions:string[];resolution?:{comment?:string}}
export default function HumanGatePanel({runId}:{runId:string}) {
  const [gates,setGates]=useState<Gate[]>([]); const [comment,setComment]=useState('')
  useEffect(()=>{ let alive=true; const load=()=>api.get<{gates:Gate[]}>(`/api/v1/runs/${runId}/human-gates`).then(x=>alive&&setGates(x.gates)).catch(()=>{}); load(); const t=setInterval(load,1500); return()=>{alive=false;clearInterval(t)} },[runId])
  const resolve=(gate:Gate,action:string)=>api.post(`/api/v1/runs/${runId}/human-gates/${gate.id}/resolve`,{action,comment}).then(()=>setComment(''))
  if(!gates.length)return null
  return <section className="mt-4 border border-border rounded-md p-3" aria-label="人工审核">
    <h3 className="m-0 text-sm font-semibold">人工审核</h3>
    {gates.map(g=><div key={g.id} className="mt-2 text-sm"><p className="m-0">{g.prompt}</p>{g.status==='pending'?<><input className="mt-2 w-full rounded border border-input bg-background p-2 text-sm" value={comment} onChange={e=>setComment(e.target.value)} placeholder="审核意见（拒绝或要求修改时必填）"/><div className="mt-2 flex gap-2"><button onClick={()=>resolve(g,'approve')}>批准</button><button onClick={()=>resolve(g,'request_changes')}>要求修改</button><button onClick={()=>resolve(g,'reject')}>拒绝</button></div></>:<p className="mt-1 text-muted-foreground">{g.status} {g.resolution?.comment}</p>}</div>)}
  </section>
}
