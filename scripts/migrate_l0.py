import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.secret_utility import get_secret

def migrate():
    conn = psycopg2.connect(
        host="127.0.0.1",
        database=get_secret("VAULT_DB_NAME"),
        user=get_secret("VAULT_DB_USER"),
        password=get_secret("VAULT_DB_PASS")
    )
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE records_l0 ADD COLUMN IF NOT EXISTS scope_type VARCHAR(20) CHECK (scope_type IN ('private', 'workspace', 'public'))")
        cur.execute("ALTER TABLE records_l0 ADD COLUMN IF NOT EXISTS source VARCHAR(100)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_scope_type ON records_l0(scope_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_source ON records_l0(source)")
    conn.commit()
    conn.close()
    print("MIGRATION_SUCCESS")

if __name__ == "__main__":
    migrate()
