# LLM Tool Definitions: Agent Memory Vault

The following tool definitions should be provided to the AI agent to enable multi-scale memory retrieval and authoritative grounding.

## 1. `ingest_observation`
**Goal**: Store a new fact, success, or environmental focus in the long-term vault. Use this to permanently record "lessons learned" or critical terminal successes.

**Parameters**:
- `scope_id` (str): Unique UUID for the workspace/tenant.
- `record_type` (str): e.g., 'command_success', 'bug_resolution', 'user_wish'.
- `payload` (dict): JSON body containing the observation data. 
- `confidence` (float): Your 0-1 estimate of data reliability.

---

## 2. `retrieve_grounded_context`
**Goal**: Query the vault for multiscale context (L1+L2+L3). Use this AT THE START of any high-stakes task to ensure you aren't repeating work or ignoring previous architectural decisions.

**Parameters**:
- `query` (str): Semantic search string (e.g., 'redis port conflict').
- `scope_ids` (list[str]): List of UUIDs authorized for retrieval.
- `token_budget` (int): Max characters for the context block (default: 4000).

---

## 3. `focus_hot_symbols`
**Goal**: Update the ephemeral (L1) Redis cache with your CURRENT focus. This ensures that the next iteration of the agent knows exactly where you left off.

**Parameters**:
- `symbols` (dict): Key-value pairs of active symbols (e.g., `{"active_file": "core/db.py", "current_bug": "ConnectionTimeout"}`).

---

### Implementation Implementation Details
The server is running on `http://127.0.0.1:8000`. 
Every 'ingest' call automatically triggers a **'Dream' background task** to update the semantic `pgvector` index and hierarchical L2 digests.
