from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

@dataclass
class Provenance:
    tool: str
    version: str
    dependencies: Dict[str, str] = field(default_factory=dict)
    execution_log: str = ""
    exit_code: int = 0
    source: str = "conversation" # 'conversation', 'git', 'terminal'

@dataclass
class MemoryRecord:
    record_type: str # 'code', 'decision', 'command_success', 'user_wish'
    scope_id: str
    payload: Dict[str, Any]
    provenance: Provenance
    path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0

    def to_json(self):
        return {
            "record_id": self.record_id,
            "scope_id": self.scope_id,
            "record_type": self.record_type,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "payload": self.payload,
            "provenance": {
                "tool": self.provenance.tool,
                "version": self.provenance.version,
                "dependencies": self.provenance.dependencies,
                "execution_log": self.provenance.execution_log,
                "exit_code": self.provenance.exit_code,
                "source": self.provenance.source
            },
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }
