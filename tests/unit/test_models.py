import pytest
import uuid
from core.models import MemoryRecord, Provenance

def test_memory_record_creation():
    prov = Provenance(tool="pytest", version="1.0.0", source="unit_test")
    scope_id = str(uuid.uuid4())
    record = MemoryRecord(
        record_id=str(uuid.uuid4()),
        scope_id=scope_id,
        record_type="test",
        payload={"msg": "hello"},
        provenance=prov,
        confidence=0.9
    )
    assert record.record_type == "test"
    assert record.payload["msg"] == "hello"
    assert record.provenance.tool == "pytest"

def test_provenance_serialization():
    prov = Provenance(tool="pytest", version="1.0.0", source="unit_test", dependencies={"pytest": "7.x"})
    prov_dict = prov.__dict__
    assert prov_dict["tool"] == "pytest"
    assert prov_dict["dependencies"]["pytest"] == "7.x"
