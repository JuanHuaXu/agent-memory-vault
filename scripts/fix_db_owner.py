import subprocess
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def fix_table_ownership():
    sudo_pass = get_secret("SUDO_PASSWORD")
    db_user = get_secret("VAULT_DB_USER")
    db_name = get_secret("VAULT_DB_NAME")
    
    tables = ["scopes", "records_l0", "event_log", "l2_digests", "l3_snippets"]
    
    for table in tables:
        chown_sql = f"ALTER TABLE {table} OWNER TO {db_user};"
        p = subprocess.Popen(["sudo", "-u", "postgres", "psql", "-d", db_name, "-c", chown_sql],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = p.communicate()
        print(f"Ownership fix for {table}: {stdout if stdout else stderr}")

if __name__ == "__main__":
    fix_table_ownership()
