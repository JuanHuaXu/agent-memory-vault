import psycopg2
from psycopg2.extras import Json
import os
import sys
import uuid

# Path for secure utility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def get_db_connection():
    db_user = get_secret("VAULT_DB_USER")
    db_pass = get_secret("VAULT_DB_PASS")
    db_name = get_secret("VAULT_DB_NAME")
    
    # Using TCP/IP to force password-based MD5 authentication
    return psycopg2.connect(
        host="127.0.0.1",
        database=db_name,
        user=db_user,
        password=db_pass
    )

def sanitize_payload(d):
    """Recursively replaces NULL bytes (\x00) with a safe string."""
    if isinstance(d, str):
        return d.replace("\x00", "<NULL_BYTE>")
    if isinstance(d, dict):
        return {k: sanitize_payload(v) for k, v in d.items()}
    if isinstance(d, list):
        return [sanitize_payload(x) for x in d]
    return d

def insert_l0_record(record):
    """Inserts a MemoryRecord object into the L0 table and logs an event."""
    # Sanitize payload before database insertion
    sanitized_payload = sanitize_payload(record.payload)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Determine scope_type
            cur.execute("SELECT scope_type FROM scopes WHERE scope_id = %s", (record.scope_id,))
            row = cur.fetchone()
            scope_type = row[0] if row else 'workspace'
            
            # Extract source from provenance
            source = record.provenance.source if record.provenance else 'unknown'
            
            # 1. Insert Ingest record
            cur.execute("""
                INSERT INTO records_l0 (
                    record_id, scope_type, scope_id, record_type, source, path, start_line, end_line, 
                    payload, confidence_hint, provenance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record.record_id, scope_type, record.scope_id, record.record_type, source, record.path, 
                record.start_line, record.end_line, Json(sanitized_payload), 
                record.confidence, Json(record.provenance.__dict__)
            ))
            
            # 2. Add to event log for dreaming
            # We assume version 1 for initial ingest entries
            cur.execute("""
                INSERT INTO event_log (record_id, action, version)
                VALUES (%s, 'upsert', 1)
            """, (record.record_id,))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Database error during ingest: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    from core.models import MemoryRecord, Provenance
    
    # Test record
    prov = Provenance(tool="CLI", version="1.0", source="test")
    rec = MemoryRecord(
        record_type="test_data",
        scope_id=str(uuid.uuid4()) if 'uuid' in dir() else "mock-scope", # Placeholder
        payload={"msg": "Integration Test"},
        provenance=prov
    )
    # Manual scope creation needed for FK
    print("Testing record insertion logic...")
