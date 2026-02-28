import os
import subprocess

# Absolute path to the keystore's wrapper script and directory
KEYSTORE_DIR = "/home/wxu/.gemini/antigravity/playground/crystal-pioneer"
KEYSTORE_SH = os.path.join(KEYSTORE_DIR, "secrets.sh")

def get_secret(key):
    """Securely fetches a secret from the crystal-pioneer keystore."""
    try:
        # Run from the keystore directory to ensure .keystore.env is found
        result = subprocess.run(
            [KEYSTORE_SH, "get", key],
            capture_output=True,
            text=True,
            check=True,
            cwd=KEYSTORE_DIR
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching secret '{key}': {e.stderr}")
        return None

if __name__ == "__main__":
    # Smoke test for vault secret retrieval
    user = get_secret("VAULT_DB_USER")
    if user:
        print(f"Successfully retrieved VAULT_DB_USER from keystore.")
    else:
        print("Failed to retrieve secret.")
