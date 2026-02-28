import sys
import os
import json
from core.models import MemoryRecord, Provenance

class ConversationIngester:
    def __init__(self, scope_id: str):
        self.scope_id = scope_id

    def extract_records(self, log_content: str):
        """
        Parses raw chat logs into MemoryRecord objects.
        Captures specific environment metadata for L0 truth.
        """
        # In a real implementation, this would use a regex or LLM-based parser
        # to separate User/Assistant turns and extract executed commands.
        
        # Example metadata collection via shell commands
        tool_versions = self._get_tool_versions()
        
        # Mock parsing: Treat the whole block as a 'decision' record for now
        prov = Provenance(
            tool="Antigravity-Ingester",
            version="1.0.0",
            dependencies=tool_versions,
            source="conversation",
            execution_log=f"Extracted from log of length {len(log_content)}"
        )
        
        record = MemoryRecord(
            record_type="decision",
            scope_id=self.scope_id,
            payload={"content": log_content},
            provenance=prov
        )
        return [record]

    def _get_tool_versions(self):
        """Captures the exact binary versions of tools used in this environment."""
        versions = {}
        try:
            versions["python"] = sys.version.split()[0]
            # Try to get git version as a baseline dependency
            import subprocess
            git_ver = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
            versions["git"] = git_ver.split()[-1]
        except Exception:
            pass
        return versions

if __name__ == "__main__":
    # Test ingester with mock log
    ingester = ConversationIngester("mock-workspace-id")
    records = ingester.extract_records("User requested the L0 records to be extracted from conversation logs.")
    for r in records:
        print(json.dumps(r.to_json(), indent=2))
