#!/bin/bash
# Securely push to GitHub without writing private keys to disk.
# Bridges to the sister 'crystal-pioneer' project for secure PQC secret retrieval.

PROJECT_ROOT=$(pwd)
KEYSTORE_DIR="/home/wxu/.gemini/antigravity/playground/crystal-pioneer"

# Check if the keystore script exists
if [ ! -f "$KEYSTORE_DIR/secrets.sh" ]; then
    echo "Error: Could not find secure keystore at $KEYSTORE_DIR/secrets.sh"
    exit 1
fi

# Load the keystore password from the env if present, or help user interactively
# (In this session, we've already set KEYSTORE_PASSWORD)
if [ -z "$KEYSTORE_PASSWORD" ]; then
    # Usually this is handled by the user or session init, but we'll try to get it from .keystore.env
    PASSWORD=$(grep "^PASSWORD=" "$KEYSTORE_DIR/.keystore.env" | cut -d'=' -f2)
    export KEYSTORE_PASSWORD=$PASSWORD
fi

# 1. Start a temporary ssh-agent
eval "$(ssh-agent -s)"

# 2. Securely add the SSH key directly to RAM-resident agent from the PQC Vault
# Using the keystore.py from the sister project
python3 "$KEYSTORE_DIR/keystore.py" get "SSH_PRIVATE_KEY" | ssh-add -

# 3. Push to origin main
echo "Pushing code to JuanHuaXu/agent-memory-vault/main securely..."
git push origin main

# 4. Cleanup the agent
ssh-agent -k
