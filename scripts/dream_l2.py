import os
import sys
import json

# Path for core logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db_connection
from core.l2_processor import L2Processor

def dream_l2_summary():
    """Builds the first L2 Session Digest (The 'Bird's Eye View')."""
    print("--- DREAM CYCLE: L2 PYRAMID BUILD ---")
    
    conn = get_db_connection()
    l2 = L2Processor()
    
    try:
        with conn.cursor() as cur:
            # 1. Fetch available scope
            cur.execute("SELECT scope_id FROM scopes WHERE owner_id = 'wxu' LIMIT 1")
            row = cur.fetchone()
            if not row:
                print("No scope found.")
                return
            scope_id = row[0]
            
            # 2. Check if a session digest for today exists
            cur.execute("SELECT digest_id FROM l2_digests WHERE scope_id = %s AND lod_level = 'session' LIMIT 1", (scope_id,))
            if cur.fetchone():
                print("Session digest already exists for this scope. Skipping manual ingest.")
                return

            # 3. Create Session Summary (The 'Bird's Eye View')
            # In a full system, this would be an LLM-synthesized summary of L0 records.
            summary_text = (
                "Infrastructure Convergence: Corrected local Redis port conflict with gcs_server "
                "and integrated vaulted PQC credentials for secure multi-tenant memory retrieval. "
                "Enforced L0 verifiability with explicit tool and dependency provenance for "
                "authoritative grounding."
            )
            
            digest_id = l2.create_digest(
                scope_id=scope_id,
                text=summary_text,
                lod_level="session",
                version=1
            )
            
            if digest_id:
                print(f"L2 Session Digest Created: {digest_id}")
            else:
                print("Failed to create L2 Digest.")

    except Exception as e:
        print(f"L2 Dream Failure: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    dream_l2_summary()
