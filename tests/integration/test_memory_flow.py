import pytest
import uuid
from core.db import get_db_connection, insert_l0_record
from core.models import MemoryRecord, Provenance
from core.vector_store import VectorStore, MockEncoder

@pytest.fixture
def test_scope():
    """Ensures a clean test scope exists in the database."""
    conn = get_db_connection()
    scope_id = str(uuid.uuid4())
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO scopes (scope_id, scope_type, owner_id) VALUES (%s, 'workspace', 'test-user')", (scope_id,))
            conn.commit()
            yield scope_id
            # Cleanup
            cur.execute("DELETE FROM l3_snippets WHERE scope_id = %s", (scope_id,))
            cur.execute("DELETE FROM event_log WHERE record_id IN (SELECT record_id FROM records_l0 WHERE scope_id = %s)", (scope_id,))
            cur.execute("DELETE FROM records_l0 WHERE scope_id = %s", (scope_id,))
            cur.execute("DELETE FROM scopes WHERE scope_id = %s", (scope_id,))
            conn.commit()
    finally:
        conn.close()

def test_l0_to_l3_ingest_flow(test_scope):
    scope_id = test_scope
    prov = Provenance(tool="pytest", version="1.0.0", source="integration")
    record = MemoryRecord(
        record_id=str(uuid.uuid4()),
        scope_id=scope_id,
        record_type="integration_test",
        payload={"msg": "Full Flow Test <NULL_BYTE>"}, # Test sanitization too
        provenance=prov,
        confidence=1.0
    )

    # 1. Ingest into L0
    assert insert_l0_record(record) is True

    # 2. Manual Dream (Synthesizing L3 from L0)
    # We'll use the core logic directly to avoid script overhead
    from scripts.dream_l3 import consolidate_l3
    # This might process other events, but we care that ours is done.
    consolidate_l3()

    # 3. Search L3 for our record
    vs = VectorStore()
    encoder = MockEncoder()
    query_vec = encoder.encode("Full Flow Test").tolist()
    
    results = vs.search_l3([scope_id], query_vec, limit=1)
    
    assert len(results) > 0
    match = results[0]
    # match is (snippet_id, record_id, text, metadata, sim)
    assert match[1] == record.record_id
    assert "Full Flow Test <NULL_BYTE>" in match[2]
    vs.close()
