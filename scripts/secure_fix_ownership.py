import subprocess
import os
import sys

# Add the project root to sys.path so we can import our utility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def restore_ownership():
    sudo_pass = get_secret("SUDO_PASSWORD")
    if not sudo_pass:
        print("Failed to retrieve sudo password from vault.")
        return

    files = [
        "/home/wxu/.gemini/antigravity/playground/crystal-pioneer/.keystore.data",
        "/home/wxu/.gemini/antigravity/playground/crystal-pioneer/.keystore.env",
        "/home/wxu/.gemini/antigravity/playground/crystal-pioneer/.keystore.salt"
    ]
    
    for f in files:
        # Use stdin to avoid the password appearing in 'ps' output
        process = subprocess.Popen(
            ["sudo", "-S", "chown", "wxu:wxu", f],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.communicate(input=sudo_pass + "\n")
    
    print("Ownership restored to user 'wxu' for all keystore files.")

if __name__ == "__main__":
    restore_ownership()
