import asyncio, json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Any
from aitest.platform.human_gates import list_gates, resolve_gate

human_gates_router=APIRouter(prefix="/api/v1/runs",tags=["human-gates"])
class GateResolution(BaseModel):
    action:str; comment:str=""; fields:dict[str,Any]={}; approver:str="local"
@human_gates_router.get("/{run_id}/human-gates")
async def get_human_gates(run_id:str): return {"gates":list_gates(run_id)}
@human_gates_router.post("/{run_id}/human-gates/{gate_id}/resolve")
async def resolve_human_gate(run_id:str,gate_id:str,body:GateResolution):
    try: return resolve_gate(run_id,gate_id,body.action,body.comment,body.fields,body.approver)
    except KeyError: raise HTTPException(404,"human gate not found")
    except ValueError as exc: raise HTTPException(422,str(exc))
@human_gates_router.websocket("/{run_id}/human-gates/ws")
async def human_gate_stream(ws: WebSocket, run_id: str):
    await ws.accept(); previous = ""
    try:
        while True:
            gates = list_gates(run_id); payload = json.dumps({"type":"human_gates","gates":gates}, default=str)
            if payload != previous: await ws.send_text(payload); previous = payload
            await asyncio.sleep(1)
    except WebSocketDisconnect: pass
