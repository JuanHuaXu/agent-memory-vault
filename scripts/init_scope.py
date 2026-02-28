import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db_connection

def init_first_scope():
    """Initializes the default workspace scope for this project."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if scope already exists
            cur.execute("SELECT scope_id FROM scopes WHERE owner_id = 'wxu' AND scope_type = 'workspace';")
            row = cur.fetchone()
            if row:
                print(f"Workspace scope already exists: {row[0]}")
                return row[0]
            
            # Create a new scope
            scope_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO scopes (scope_id, scope_type, owner_id)
                VALUES (%s, 'workspace', 'wxu')
            """, (scope_id,))
            conn.commit()
            print(f"New workspace scope created: {scope_id}")
            return scope_id
    finally:
        conn.close()

if __name__ == "__main__":
    init_first_scope()
