import os
import sys
import json
from datetime import datetime

# Path for secure utility and core logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db_connection
from core.vector_store import VectorStore, MockEncoder

def consolidate_l3():
    """Incremental Dream Consolidation: Promotes L0 Events into L3 Vector Snippets."""
    print("--- DREAM CYCLE: L3 CONSOLIDATION ---")
    
    conn = get_db_connection()
    vs = VectorStore()
    encoder = MockEncoder() # Default 1536 dim for pgvector
    
    try:
        with conn.cursor() as cur:
            # 1. Fetch pending L0 events
            cur.execute("""
                SELECT e.event_id, r.record_id, r.scope_id, r.record_type, r.payload, r.path, r.source, r.scope_type, r.branch
                FROM event_log e
                JOIN records_l0 r ON e.record_id = r.record_id
                WHERE e.processed_at IS NULL
                ORDER BY e.event_id ASC
                LIMIT 100
            """)
            events = cur.fetchall()
            
            if not events:
                print("No pending events for consolidation.")
                return

            print(f"Found {len(events)} pending events. Dream processing...")

            for eid, rid, sid, rtype, payload, path, source, scope_type, branch in events:
                # 2. Extract Text Snippet for L3
                # For code, it's the raw content; for wishes/decisions, it's the JSON summary.
                snippet_text = ""
                if rtype == 'user_wish':
                    snippet_text = f"User Wish/Directive: {payload.get('directive', '')}"
                elif rtype == 'command_success':
                    snippet_text = f"Command Success: {payload.get('resolution', '')} - {payload.get('issue', '')}"
                else:
                    snippet_text = json.dumps(payload)

                # 3. Generate Embedding (L3 Semantic Anchor)
                embedding = encoder.encode(snippet_text).tolist()

                # 4. Insert into L3 Index
                metadata = {
                    "path": path, 
                    "artifact_type": rtype, 
                    "source": source,
                    "scope_type": scope_type,
                    "branch": branch,
                    "repo_id": "agent-memory-vault"
                }
                vs.add_snippet(rid, sid, snippet_text, json.dumps(metadata), embedding)
                
                # 5. Mark Event as Processed (Atomic promotion)
                cur.execute("UPDATE event_log SET processed_at = %s WHERE event_id = %s", (datetime.now(), eid))
            
            conn.commit()
            print(f"Successfully dreamt {len(events)} L3 snippets.")

    except Exception as e:
        print(f"Dream Failure: {e}")
        conn.rollback()
    finally:
        vs.close()
        conn.close()

if __name__ == "__main__":
    consolidate_l3()
