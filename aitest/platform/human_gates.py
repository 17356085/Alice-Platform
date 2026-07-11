"""Persistent, process-local coordination for Workflow human gates."""
from __future__ import annotations
import json, sqlite3, threading, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from aitest.platform.paths import get_workstudy

_path = get_workstudy() / "governance" / ".data" / "human_gates.db"
_lock = threading.RLock()
_waiters: dict[str, threading.Event] = {}

def _conn():
    _path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(_path, check_same_thread=False); c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS human_gates (
      id TEXT PRIMARY KEY, run_id TEXT NOT NULL, node_id TEXT NOT NULL, status TEXT NOT NULL,
      prompt TEXT NOT NULL, context_json TEXT NOT NULL, actions_json TEXT NOT NULL,
      resolution_json TEXT, created_at TEXT NOT NULL, resolved_at TEXT,
      UNIQUE(run_id,node_id))""")
    return c

def create_gate(run_id: str, node_id: str, prompt: str, context: dict[str, Any], actions: list[str]) -> dict:
    now=datetime.now(timezone.utc).isoformat()
    with _lock, _conn() as c:
        row=c.execute("SELECT * FROM human_gates WHERE run_id=? AND node_id=?",(run_id,node_id)).fetchone()
        if not row:
            gid=f"gate_{uuid.uuid4().hex}"; c.execute("INSERT INTO human_gates VALUES (?,?,?,?,?,?,?,?,?,?)",(gid,run_id,node_id,"pending",prompt,json.dumps(context),json.dumps(actions),None,now,None)); row=c.execute("SELECT * FROM human_gates WHERE id=?",(gid,)).fetchone()
        _waiters.setdefault(row['id'],threading.Event())
    return _to_dict(row)

def list_gates(run_id: str) -> list[dict]:
    with _conn() as c: return [_to_dict(r) for r in c.execute("SELECT * FROM human_gates WHERE run_id=? ORDER BY created_at",(run_id,))]

def resolve_gate(run_id: str, gate_id: str, action: str, comment: str="", fields: dict|None=None, approver: str="local") -> dict:
    with _lock, _conn() as c:
        row=c.execute("SELECT * FROM human_gates WHERE id=? AND run_id=?",(gate_id,run_id)).fetchone()
        if not row: raise KeyError(gate_id)
        if row['status']!='pending': return _to_dict(row)
        if action not in json.loads(row['actions_json']): raise ValueError("unsupported action")
        status={"approve":"approved","reject":"rejected","request_changes":"changes_requested"}.get(action,action)
        value=json.dumps({"action":status,"comment":comment,"fields":fields or {},"approver":approver})
        now=datetime.now(timezone.utc).isoformat(); c.execute("UPDATE human_gates SET status=?,resolution_json=?,resolved_at=? WHERE id=? AND status='pending'",(status,value,now,gate_id)); row=c.execute("SELECT * FROM human_gates WHERE id=?",(gate_id,)).fetchone(); _waiters.setdefault(gate_id,threading.Event()).set()
    return _to_dict(row)

def wait_for_gate(gate_id: str, timeout: int, fallback: str) -> dict:
    event=_waiters.setdefault(gate_id,threading.Event()); event.wait(max(1,timeout))
    with _conn() as c: row=c.execute("SELECT * FROM human_gates WHERE id=?",(gate_id,)).fetchone()
    gate=_to_dict(row)
    if gate['status']=='pending': return {"success":False,"action":fallback,"comment":"Human gate timed out","gate_id":gate_id,"timed_out":True}
    return {"success":gate['status']=='approved',"action":gate['status'],"comment":gate.get('resolution',{}).get('comment',''),"gate_id":gate_id}

def _to_dict(row):
    data=dict(row); data['context']=json.loads(data.pop('context_json')); data['actions']=json.loads(data.pop('actions_json')); data['resolution']=json.loads(data.pop('resolution_json') or '{}'); return data
