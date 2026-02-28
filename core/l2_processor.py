import os
import sys
import json
from datetime import datetime

# Path for core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db_connection
from core.vector_store import MockEncoder

class L2Processor:
    def __init__(self):
        self.encoder = MockEncoder()

    def create_digest(self, scope_id, text, lod_level="session", parent_id=None, version=1):
        """Creates a new high-level digest in the L2 pyramid."""
        conn = get_db_connection()
        try:
            embedding = self.encoder.encode(text).tolist()
            emb_str = "[" + ",".join(map(str, embedding)) + "]"
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO l2_digests (scope_id, lod_level, parent_id, text, embedding, version)
                    VALUES (%s, %s, %s, %s, %s::vector, %s)
                    RETURNING digest_id
                """, (scope_id, lod_level, parent_id, text, emb_str, version))
                digest_id = cur.fetchone()[0]
                conn.commit()
                return digest_id
        except Exception as e:
            print(f"L2 Processing Error: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_digests(self, scope_ids, lod_level=None):
        """Retrieves digests for context compilation."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT digest_id, text, lod_level, version FROM l2_digests WHERE scope_id = ANY(%s::uuid[])"
                params = [scope_ids]
                if lod_level:
                    query += " AND lod_level = %s"
                    params.append(lod_level)
                
                cur.execute(query, tuple(params))
                return cur.fetchall()
        finally:
            conn.close()

if __name__ == "__main__":
    # Smoke test
    proc = L2Processor()
    print("L2 Processor Initialized.")
