import subprocess
import os
import sys

# Add the project root to sys.path so we can import our utility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def test_sudo_securely():
    """Tests sudo access by piping the secret from the vault directly into the process."""
    print("--- SECURE SUDO TEST START ---")
    
    # 1. Retrieve the password from the PQC Vault (Memory-only)
    sudo_pass = get_secret("SUDO_PASSWORD")
    if not sudo_pass:
        print("[FAIL] Could not retrieve password from vault.")
        return

    # 2. Execute 'sudo id' using stdin piping (Process isolation)
    # The password never appears in the command arguments or shell history.
    try:
        process = subprocess.Popen(
            ["sudo", "-S", "id"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Handoff secret to the kernel pipe
        stdout, stderr = process.communicate(input=sudo_pass + "\n")
        
        if process.returncode == 0:
            print(f"[PASS] Sudo command executed successfully.")
            print(f"Resulting Identity: {stdout.strip()}")
        else:
            print(f"[FAIL] Sudo failed. Error: {stderr.strip()}")
            
    except Exception as e:
        print(f"[ERROR] Exception during sudo execution: {e}")

    print("--- SECURE SUDO TEST COMPLETE ---")

if __name__ == "__main__":
    test_sudo_securely()
