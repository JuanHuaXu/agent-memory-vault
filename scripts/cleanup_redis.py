import subprocess
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def run_cmd(cmd, sudo=False):
    if sudo:
        sudo_pass = get_secret("SUDO_PASSWORD")
        full_cmd = ["sudo", "-S"] + cmd
        p = subprocess.Popen(full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = p.communicate(input=sudo_pass + "\n" if sudo_pass else "")
        return p.returncode, stdout, stderr
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr

def full_cleanup_redis():
    print("--- FULL CLEANUP START ---")
    
    # Check all listening ports
    ret, out, err = run_cmd(["netstat", "-tlnp"], sudo=True)
    print(f"Listening Ports:\n{out}")

    # Kill anything on 6379
    ret, out, err = run_cmd(["sh", "-c", "lsof -t -i:6379 | xargs -r kill -9"], sudo=True)
    print("Killed processes on 6379 if any.")

    # Try starting the service properly
    ret, out, err = run_cmd(["systemctl", "restart", "redis-server"], sudo=True)
    print(f"Service restart return code: {ret}")
    if err:
        print(f"Service restart error: {err}")

    # Wait 2 seconds
    import time
    time.sleep(2)

    # Check status
    ret, out, err = run_cmd(["redis-cli", "ping"])
    print(f"Final Ping: {out.strip() if out else 'ERROR'}")
    if err:
        print(f"Final Ping Error: {err.strip()}")

    print("--- FULL CLEANUP COMPLETE ---")

if __name__ == "__main__":
    full_cleanup_redis()
