# Agent Memory Vault

The Agent Memory Vault is a standalone, secure memory aggregation and RAG (Retrieval-Augmented Generation) microservice designed for autonomous AI agents. It leverages PostgreSQL (with `pgvector`) for L3 semantic matching, Redis for L1 hot symbol tracking, and a Python worker layer to distill context dynamically into multi-scale "Memory Blocks" for the agent.

## Features
- **L1 Hot Symbols**: Micro-scale intent tracking via isolated Redis caches (`base` and `delta` overlay merges).
- **L2 Bird's Eye Digests**: Background routines summarize groups of interactions into higher-level architectural perspectives.
- **L3 Semantic Grounding**: Vector index matching (pgvector) to fetch relevant code snippets and past reasoning based on natural language search.
- **Context Compiler**: Yields strictly bounded prompts (with auto-appended Action Guardrails and size limits) ready for immediate LLM injection.
- **Strong Isolation & Provenance**: L0 base schema guarantees tenant isolation via `scope_id` down to the DB transaction level. No cross-tenant leaks.
- **Zero-Disk Crypto Integration**: Native integration with the Crystal Pioneer PQC keystore using RAM-resident SSH and password handling. Database and API keys run fully secured.

## System Prerequisites

To run the Agent Memory Vault locally, you must have the following system dependencies installed on Ubuntu/Linux:

- **PostgreSQL 14+**
- **pgvector Extension for Postgres** 
- **Redis Server**
- **Python 3.10+** (using `venv`)
- **[Antigravity Keystore (Crystal Pioneer)](../crystal-pioneer)** running locally in a sibling directory (or path-updated) for master secrets (`VAULT_DB_USER`, `VAULT_DB_PASS`, `VAULT_API_KEY`, `SUDO_PASSWORD`).

### Installing System Dependencies (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server python3.12-venv
```

To install `pgvector`:
```bash
sudo apt install build-essential postgresql-server-dev-all
cd /tmp
git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git
cd pgvector
sudo make
sudo make install
```

## Setup & Compilation Documentation

Follow these steps faithfully to reproduce the exact secure vault environment.

### 1. Configure the Secrets Keystore
Ensure the `crystal-pioneer` keystore exists and has been initialized before launching the vault.
You must insert the following keys using `python3 keystore.py set <KEY> <VALUE>`:
- `VAULT_DB_USER` (e.g. `vault_admin`)
- `VAULT_DB_PASS` (Strong DB Password)
- `VAULT_DB_NAME` (e.g. `memory_vault`)
- `VAULT_API_KEY` (Strong API Gateway Password)
- `SUDO_PASSWORD` (User's sudo password to dynamically initialize Postgres extensions)

### 2. Python Environment Setup
Install the necessary python dependencies. This project uses `psycopg2`, `fastapi`, `pydantic`, `redis`, and `numpy`.

```bash
cd agent-memory-vault
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# If requirements.txt is missing:
# pip install fastapi uvicorn pydantic psycopg2-binary redis numpy pytest pytest-cov
```

### 3. Initialize the Database Migration
When the Postgres service is active, execute the vault initialization script. This interacts with the system via `sudo` securely to create roles, generate the `vector` extension, and spin up the complete L0 tracking schemas and L3 vectors.

```bash
# Verify redis and postgres daemon statuses:
sudo systemctl status redis-server
sudo systemctl status postgresql

# Run the master init schema config
source venv/bin/activate
python3 scripts/init_db.py
```
*Note: If permissions fail, verify `test_db_conn.py` to ensure local `pg_hba.conf` supports strict md5/scram-sha-256 TCP configurations via `127.0.0.1`.*

## Running the API Gateway

Use the secure startup shell to engage the API layer. The shell verifies L1/L3 database connectivity automatically before bootstrapping FastAPI on an available port in the `8000-8080` range.

```bash
source venv/bin/activate
bash scripts/start_vault.sh
```

### Endpoints
The Tool Server enforces `X-Vault-API-Key` headers on all endpoints. Key routes include:
- `GET /health` : Verify system connectivity.
- `POST /ingest` : L0 raw memory insert and async dispatch for L2/L3 dream processing.
- `POST /correction` : Emits a superseding correction to a previous memory.
- `POST /hot_symbols` : Push L1 Delta overlay frames (short-term agent focus).
- `POST /context` : Run the `ContextCompiler` for a specific query and scopes to generate the next LLM grounding prompt + Action Guardrails.
- `POST /admin/scopes` : Bootstraps a new tenant workspace boundary.
- `POST /dream` : Manually engage L2/L3 rolling compaction loops (sync or async).

## Testing

A comprehensive unit and mock-integrated test suite resides in `/tests`.

```bash
source venv/bin/activate
pytest tests/ -v
```

This ensures `MemoryRecord` logic, provenance metadata parsing, and L0 to L3 simulated event promotion logic does not drift or break.
