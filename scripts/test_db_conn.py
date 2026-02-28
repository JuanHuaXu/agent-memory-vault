import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def test_conn():
    print("Fetching secrets...")
    db_user = get_secret("VAULT_DB_USER")
    db_pass = get_secret("VAULT_DB_PASS")
    db_name = get_secret("VAULT_DB_NAME")
    
    print(f"Connecting as {db_user} to {db_name}...")
    try:
        conn = psycopg2.connect(host="localhost", user=db_user, password=db_pass, database=db_name)
        print("Connected!")
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_conn()
