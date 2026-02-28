#!/bin/bash
# Startup Script for Agent Memory Vault Tool Server
# Automatically bridges vaulted credentials and starts the FastAPI gateway.

export PROJECT_ROOT=$(pwd)
source venv/bin/activate

echo "--- STARTING AGENT MEMORY VAULT ---"

# Step 1: Ensure Postgres is in 'trust' or accessible mode for 'wxu'
# Verification of L0/L1 state
echo "Checking Redis (L1)..."
redis-cli ping || (echo "Redis not running. Attempting restart..." && sudo systemctl restart redis-server)

echo "Checking Postgres (L3)..."
source venv/bin/activate && python3 scripts/test_db_conn.py || (echo "Postgres unreachable. Check pg_hba.conf trust settings.")

# Step 2: Start the FastAPI Tool Server
echo "Starting FastAPI gateway (auto-detecting free port in 8000-8080 range)..."
python3 api/tool_server.py
