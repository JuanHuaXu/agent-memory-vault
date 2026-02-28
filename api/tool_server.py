import os
import sys
import uuid
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Path for core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import insert_l0_record, get_db_connection
from core.models import MemoryRecord, Provenance
from core.context_compiler import ContextCompiler
from utils.secret_utility import get_secret
from scripts.dream_l3 import consolidate_l3
from scripts.dream_l2 import dream_l2_summary

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic
    compiler.close()

app = FastAPI(title="Agent Memory Vault Tool Server", lifespan=lifespan)

# --- Security ---
api_key_header = APIKeyHeader(name="X-Vault-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_key = get_secret("VAULT_API_KEY")
    if not expected_key:
        expected_key = "dev-key-123" # Fallback if not injected yet
    
    if api_key == expected_key:
        return api_key
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key")

# --- Models for Request/Response ---
class IngestRequest(BaseModel):
    scope_id: str
    record_type: str
    payload: Dict[str, Any]
    tool_name: str = "LLM_Tool"
    version: str = "1.0"
    confidence: float = 1.0

class QueryRequest(BaseModel):
    query: str
    scope_ids: List[str]
    token_budget: Optional[int] = 4000

class HotSymbolUpdate(BaseModel):
    scope_id: str
    symbols: Dict[str, str]

class CorrectionRequest(BaseModel):
    scope_id: str
    target_record_id: str
    correction_payload: Dict[str, Any]
    confidence: float = 1.0

class WorkspaceCreate(BaseModel):
    owner_id: str
    scope_type: str = "workspace"

class DreamTrigger(BaseModel):
    sync: bool = False

# Global Context Compiler instance
# In production, this would be pooled or handled per request.
compiler = ContextCompiler()

@app.post("/ingest", tags=["Write"], dependencies=[Depends(get_api_key)])
def ingest_memory(req: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingests official agent observations into the vault.
    Spawns a background 'dream cycle' to promote it to the semantic index.
    """
    prov = Provenance(tool=req.tool_name, version=req.version, source="llm_agent")
    record = MemoryRecord(
        record_id=str(uuid.uuid4()),
        scope_id=req.scope_id,
        record_type=req.record_type,
        payload=req.payload,
        provenance=prov,
        confidence=req.confidence
    )
    
    success = insert_l0_record(record)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to ingest record into L0")
    
    # Trigger semantic dreaming in background
    background_tasks.add_task(consolidate_l3)
    background_tasks.add_task(dream_l2_summary)
    
    return {"status": "success", "record_id": record.record_id, "dream_triggered": True}

@app.post("/context", tags=["Read"], dependencies=[Depends(get_api_key)])
def get_perfect_context(req: QueryRequest):
    """
    Returns a grounded, multiscale context block (L1+L2+L3).
    Use this to 'prime' the next agent iteration with authoritative truth.
    """
    compiler.token_budget = req.token_budget
    context = compiler.compile_multiscale_context(req.query, req.scope_ids)
    return {"context_block": context}

@app.post("/hot_symbols", tags=["State"], dependencies=[Depends(get_api_key)])
def update_hot_symbols(req: HotSymbolUpdate):
    """
    Updates the L1 (Hot) ephemeral state in Redis.
    This informs the immediate session focus in future context windows.
    """
    try:
        # We only update the delta overlay here. Base snapshot is for compactions.
        delta_key = f"hot_symbols:{req.scope_id}:delta"
        compiler.redis.hset(delta_key, mapping=req.symbols)
        return {"status": "updated", "symbols_set": list(req.symbols.keys()), "scope_id": req.scope_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/correction", tags=["Write"], dependencies=[Depends(get_api_key)])
def record_correction(req: CorrectionRequest):
    """Records a user correction or refutation that supersedes a previous claim."""
    prov = Provenance(tool="human_correction", version="1.0", source="user")
    record = MemoryRecord(
        record_id=str(uuid.uuid4()),
        scope_id=req.scope_id,
        record_type="correction",
        payload=req.correction_payload,
        provenance=prov,
        confidence=req.confidence
    )
    # Internally DB logic should wire up the 'supersedes' property, or we embed in payload.
    # For now, store it as a new authoritative l0 memory.
    record.payload["supersedes_target"] = req.target_record_id
    success = insert_l0_record(record)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to ingest correction")
    return {"status": "success", "record_id": record.record_id}

@app.post("/admin/scopes", tags=["Admin"], dependencies=[Depends(get_api_key)])
def create_workspace(req: WorkspaceCreate):
    """Admin function: Create a new secure workspace scope."""
    # Fast runtime optimization: perform minimal logic and immediate DB commit.
    if req.scope_type not in ["private", "workspace", "public"]:
        raise HTTPException(status_code=400, detail="Invalid scope type")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scopes (scope_type, owner_id) VALUES (%s, %s) RETURNING scope_id",
                (req.scope_type, req.owner_id)
            )
            scope_id = cur.fetchone()[0]
            conn.commit()
            return {"status": "success", "scope_id": str(scope_id)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/dream", tags=["Workers"], dependencies=[Depends(get_api_key)])
def trigger_dream(req: DreamTrigger, background_tasks: BackgroundTasks):
    """Trigger the dream consolidation pipeline (sync or background)."""
    if req.sync:
        consolidate_l3()
        dream_l2_summary()
        return {"status": "success", "sync": True}
    else:
        background_tasks.add_task(consolidate_l3)
        background_tasks.add_task(dream_l2_summary)
        return {"status": "success", "sync": False}

@app.get("/health")
async def health_check():
    return {"status": "online", "engine": "pgvector + redis + postgres"}

if __name__ == "__main__":
    import uvicorn
    import socket

    def find_free_port(start_port: int, end_port: int) -> int:
        for port in range(start_port, end_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        return -1

    assigned_port = find_free_port(8000, 8080)
    if assigned_port == -1:
        print("Error: Could not find a free port in range 8000-8080.")
        sys.exit(1)

    print(f"Starting server on detected free port: {assigned_port}...")
    uvicorn.run("api.tool_server:app", host="127.0.0.1", port=assigned_port, reload=True)
