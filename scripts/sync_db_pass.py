import subprocess
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def reset_db_password():
    sudo_pass = get_secret("SUDO_PASSWORD")
    db_user = get_secret("VAULT_DB_USER")
    db_pass = get_secret("VAULT_DB_PASS")
    
    if not all([sudo_pass, db_user, db_pass]):
        print("Missing secrets.")
        return

    # Use psql as postgres user to alter user
    alter_sql = f"ALTER USER {db_user} WITH PASSWORD '{db_pass}';"
    p = subprocess.Popen(["sudo", "-u", "postgres", "psql", "-c", alter_sql], 
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate()
    print(f"Outcome: {stdout if stdout else stderr}")

if __name__ == "__main__":
    reset_db_password()
