import os
import sys
import uuid
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Path for core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import insert_l0_record
from core.models import MemoryRecord, Provenance
from core.context_compiler import ContextCompiler
from scripts.dream_l3 import consolidate_l3
from scripts.dream_l2 import dream_l2_summary

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic
    compiler.close()

app = FastAPI(title="Agent Memory Vault Tool Server", lifespan=lifespan)

# Models for Request/Response
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

# Global Context Compiler instance
# In production, this would be pooled or handled per request.
compiler = ContextCompiler()

@app.post("/ingest", tags=["Write"])
async def ingest_memory(req: IngestRequest, background_tasks: BackgroundTasks):
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

@app.post("/context", tags=["Read"])
async def get_perfect_context(req: QueryRequest):
    """
    Returns a grounded, multiscale context block (L1+L2+L3).
    Use this to 'prime' the next agent iteration with authoritative truth.
    """
    compiler.token_budget = req.token_budget
    context = compiler.compile_multiscale_context(req.query, req.scope_ids)
    return {"context_block": context}

@app.post("/hot_symbols", tags=["State"])
async def update_hot_symbols(req: HotSymbolUpdate):
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

@app.get("/health")
async def health_check():
    return {"status": "online", "engine": "pgvector + redis + postgres"}

if __name__ == "__main__":
    import uvicorn
    # In local dev we'll run it manually, or use the startup script
    uvicorn.run(app, host="127.0.0.1", port=8000)
