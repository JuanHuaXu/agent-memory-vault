import os
import sys
import json
import redis
from datetime import datetime

# Path for core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db_connection
from core.vector_store import VectorStore, MockEncoder
from core.l2_processor import L2Processor

class ContextCompiler:
    def __init__(self, token_budget=6000):
        self.token_budget = token_budget 
        self.vs = VectorStore()
        self.l2 = L2Processor()
        self.encoder = MockEncoder()
        # Connect to Redis for L1 Hot Symbols
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def compile_multiscale_context(self, query: str, scope_ids: list):
        """Compiles a grounded context block using L1 (Hot), L2 (Digest), and L3 (Snippet) memory."""
        print(f"--- COMPILING MULTISCALE CONTEXT: '{query}' ---")
        
        context_blocks = []

        # 1. Level 1: Hot Symbols (Redis Ephemeral)
        try:
            aggregated_symbols = {}
            for scope_id in scope_ids:
                base_symbols = self.redis.hgetall(f"hot_symbols:{scope_id}:base")
                delta_symbols = self.redis.hgetall(f"hot_symbols:{scope_id}:delta")
                
                merged = {}
                if base_symbols:
                    merged.update(base_symbols)
                if delta_symbols:
                    for k, v in delta_symbols.items():
                        if v == "__DELETE__":
                            merged.pop(k, None)
                        else:
                            merged[k] = v
                            
                if merged:
                    aggregated_symbols.update(merged)
                    
            if aggregated_symbols:
                context_blocks.append("## [L1] EPHEMERAL SESSION FOCUS")
                for k, v in aggregated_symbols.items():
                    context_blocks.append(f"- {k}: {v}")
        except Exception as e:
            print(f"Redis L1 Fetch Error: {e}")

        # 2. Level 2: Bird's Eye View (L2 Digests)
        try:
            digests = self.l2.get_digests(scope_ids, lod_level='session')
            if digests:
                context_blocks.append("## [L2] ARCHITECTURAL BIRD'S EYE VIEW")
                for did, text, level, ver in digests:
                    context_blocks.append(f"### DIGEST (v{ver}): {text}")
        except Exception as e:
            print(f"L2 Digest Fetch Error: {e}")

        # 3. Level 3: Semantic Retrieval (L3 Vector Index)
        try:
            query_vec = self.encoder.encode(query).tolist()
            l3_matches = self.vs.search_l3(scope_ids, query_vec, limit=3)
            
            if l3_matches:
                context_blocks.append("## [L3] SEMANTIC MEMORY ANCHORS")
                for sid, rid, text, metadata, sim in l3_matches:
                    provenance = self._get_l0_provenance(rid)
                    block = f"### RECORD: {rid}\n"
                    block += f"Evidence: {text}\n"
                    block += f"Grounding: Semantic match (score: {sim:.4f})\n"
                    block += f"L0 Provenance: {json.dumps(provenance)}\n"
                    context_blocks.append(block)
        except Exception as e:
            print(f"Postgres L3 Fetch Error: {e}")

        # 4. Action Guardrails (Safety)
        guardrails_block = (
            "## [AGENT ACTION GUARDRAILS]\n"
            "- MAXIMUM_FILES_MODIFIED: 3\n"
            "- MAXIMUM_LOC_ADDED: 200\n"
            "- FORBIDDEN_PATHS: ['.git/', 'venv/', '.keystore.*']\n"
            "- REQUIRED_TESTS: Any new logic MUST include a corresponding unit or integration test.\n"
            "- EVIDENCE_REQUIREMENT: Any proposed code change MUST cite at least one authoritative anchor (record ID) from the [L3] Semantic Memory Anchors section if available."
        )
        context_blocks.append(guardrails_block)

        # 5. Assembly & Truncation
        full_context = "\n\n".join(context_blocks)
        if len(full_context) > self.token_budget:
            full_context = full_context[:self.token_budget] + "\n... [CONTEXT TRUNCATED]"
            
        return full_context

    def _get_l0_provenance(self, record_id):
        """Retrieves authoritative L0 provenance metadata."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT provenance FROM records_l0 WHERE record_id = %s", (record_id,))
                row = cur.fetchone()
                return row[0] if row else {"error": "Provenance missing"}
        finally:
            conn.close()

    def close(self):
        self.vs.close()

if __name__ == "__main__":
    compiler = ContextCompiler()
    # Use the scope from Step 1744
    scope_id = "6c573960-c516-4c12-be3b-91cd84a7f2b6"
    
    # Mock some L1 base data in Redis
    compiler.redis.hset(f"hot_symbols:{scope_id}:base", mapping={
        "focus": "multiscale context compilation",
        "last_resolved_bug": "pgvector param bug"
    })
    # Mock some L1 delta data in Redis
    compiler.redis.hset(f"hot_symbols:{scope_id}:delta", mapping={
        "last_resolved_bug": "pgvector uuid cast error",
        "next_step": "L2 pyramid verification"
    })
    
    context = compiler.compile_multiscale_context("infrastructure and redis setup", [scope_id])
    
    print("\n" + "="*50)
    print("FINAL CONTEXT COMPILER OUTPUT (MULTISCALEGrounding)")
    print("="*50)
    print(context)
    compiler.close()
