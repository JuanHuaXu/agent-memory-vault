import subprocess
import os
import sys

# Add the project root to sys.path so we can import our utility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def run_sudo_command(cmd_list, password, user=None):
    """Executes a command with sudo, providing password via stdin."""
    base_cmd = ["sudo", "-S"]
    if user:
        base_cmd.extend(["-u", user])
    base_cmd.extend(cmd_list)
    
    process = subprocess.Popen(
        base_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=password + "\n")
    return process.returncode, stdout, stderr

def setup_postgres():
    # 1. Get secrets
    sudo_pass = get_secret("SUDO_PASSWORD")
    db_user = get_secret("VAULT_DB_USER")
    db_pass = get_secret("VAULT_DB_PASS")
    db_name = get_secret("VAULT_DB_NAME")
    
    if not all([sudo_pass, db_user, db_pass, db_name]):
        print("Required secrets missing from vault.")
        return

    print("--- Initializing Postgres ---")

    # 2. Create DB User
    create_user_sql = f"CREATE USER {db_user} WITH PASSWORD '{db_pass}';"
    ret, out, err = run_sudo_command(["psql", "-c", create_user_sql], sudo_pass, user="postgres")
    if ret == 0:
        print(f"User '{db_user}' created or already exists.")
    else:
        print(f"Notice: {err.strip()}")

    # 3. Create Database
    create_db_sql = f"CREATE DATABASE {db_name} OWNER {db_user};"
    ret, out, err = run_sudo_command(["psql", "-c", create_db_sql], sudo_pass, user="postgres")
    if ret == 0:
        print(f"Database '{db_name}' created.")
    else:
        print(f"Notice: {err.strip()}")

    # 4. Enable pgvector extension
    vector_sql = "CREATE EXTENSION IF NOT EXISTS vector;"
    ret, out, err = run_sudo_command(["psql", "-d", db_name, "-c", vector_sql], sudo_pass, user="postgres")
    if ret == 0:
        print("pgvector extension enabled.")
    else:
        print(f"Error enabling pgvector: {err}")
        return

    # 5. Create Schema
    schema_sql = """
    CREATE TABLE IF NOT EXISTS scopes (
        scope_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        scope_type VARCHAR(20) CHECK (scope_type IN ('private', 'workspace', 'public')),
        owner_id VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS records_l0 (
        record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        scope_type VARCHAR(20) CHECK (scope_type IN ('private', 'workspace', 'public')),
        scope_id UUID REFERENCES scopes(scope_id),
        record_type VARCHAR(50) NOT NULL,
        source VARCHAR(100),
        branch VARCHAR(100),
        path TEXT,
        start_line INT,
        end_line INT,
        payload JSONB NOT NULL,
        confidence_hint FLOAT DEFAULT 1.0, 
        supersedes UUID REFERENCES records_l0(record_id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        provenance JSONB
    );
    
    CREATE TABLE IF NOT EXISTS event_log (
        event_id BIGSERIAL PRIMARY KEY,
        record_id UUID REFERENCES records_l0(record_id),
        action VARCHAR(20),
        version BIGINT NOT NULL,
        processed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS l2_digests (
        digest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        scope_id UUID REFERENCES scopes(scope_id),
        lod_level VARCHAR(20),
        parent_id UUID REFERENCES l2_digests(digest_id),
        text TEXT NOT NULL,
        embedding VECTOR(1536),
        version BIGINT NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS l3_snippets (
        snippet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        record_id UUID REFERENCES records_l0(record_id),
        scope_id UUID REFERENCES scopes(scope_id),
        text TEXT NOT NULL,
        metadata JSONB,
        embedding VECTOR(1536),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_records_scope_path ON records_l0(scope_id, path);
    CREATE INDEX IF NOT EXISTS idx_records_scope_type ON records_l0(scope_type);
    CREATE INDEX IF NOT EXISTS idx_records_source ON records_l0(source);
    CREATE INDEX IF NOT EXISTS idx_l2_scope_lod ON l2_digests(scope_id, lod_level);
    """
    
    ret, out, err = run_sudo_command(["psql", "-d", db_name, "-c", schema_sql], sudo_pass, user="postgres")
    if ret == 0:
        print("Database schema successfully applied.")
    else:
        print(f"Error applying schema: {err}")

if __name__ == "__main__":
    setup_postgres()
