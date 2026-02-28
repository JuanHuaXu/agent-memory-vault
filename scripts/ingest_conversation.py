import os
import sys
import uuid
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import MemoryRecord, Provenance
from core.db import get_db_connection, insert_l0_record

def sanitize(d):
    if isinstance(d, str):
        return d.replace("\x00", "<NULL_BYTE>")
    if isinstance(d, dict):
        return {k: sanitize(v) for k, v in d.items()}
    if isinstance(d, list):
        return [sanitize(x) for x in d]
    return d

def ingest_recent_session():
    # 1. Get the workspace scope
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT scope_id FROM scopes WHERE owner_id = 'wxu' LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("No scope found. Run init_scope.py first.")
            return
        scope_id = row[0]
    conn.close()

    print(f"Ingesting memory into scope: {scope_id}")

    tool_ver = {
        "python": sys.version.split()[0],
        "postgres": "16.x"
    }

    # Record A: User's wish
    wish_payload = sanitize({
        "directive": "Success is only truthful when you specify versions and dependencies.",
        "enforcement": "Hardened L0 Provenance"
    })
    
    wish_record = MemoryRecord(
        record_type="user_wish",
        scope_id=scope_id,
        payload=wish_payload,
        provenance=Provenance(
            tool="ConversationIngester",
            version="1.0.0",
            dependencies=tool_ver,
            source="conversation",
            execution_log="Captured from Step 1364"
        ),
        confidence=1.0
    )

    # Record B: Redis fix
    success_payload = sanitize({
        "issue": "Redis Protocol Error \x00 (Port 6379 occupied by gcs_server)",
        "resolution": "Manual kill of gcs_server followed by systemd restart",
        "validation": "redis-cli ping -> PONG"
    })

    success_record = MemoryRecord(
        record_type="command_success",
        scope_id=scope_id,
        payload=success_payload,
        provenance=Provenance(
            tool="FullCleanup",
            version="1.1.0",
            dependencies=tool_ver,
            source="terminal",
            execution_log="Resolved port conflict in Step 1642",
            exit_code=0
        ),
        confidence=0.9
    )

    if insert_l0_record(wish_record):
        print(f"Ingested Record: user_wish - '{wish_record.record_id}'")
    
    if insert_l0_record(success_record):
        print(f"Ingested Record: command_success - '{success_record.record_id}'")

if __name__ == "__main__":
    ingest_recent_session()
