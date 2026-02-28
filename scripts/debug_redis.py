import subprocess
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret

def run_cmd(cmd, sudo=False, input_data=None):
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

def debug_redis():
    print("--- REDIS DEBUG START ---")
    
    # Check if process is running
    ret, out, err = run_cmd(["pgrep", "-af", "redis"])
    print(f"Redis Processes:\n{out if out else 'None'}\n")

    # Check network listening
    ret, out, err = run_cmd(["netstat", "-tlnp"], sudo=True)
    for line in out.splitlines():
        if ":6379" in line:
            print(f"6379 Listener: {line}")

    # Check logs
    ret, out, err = run_cmd(["tail", "-n", "20", "/var/log/redis/redis-server.log"], sudo=True)
    print(f"Recent Redis Logs:\n{out if out else 'Log empty or inaccessible'}")
    if err:
        print(f"Log Error: {err}")

    # Try a simple ping
    ret, out, err = run_cmd(["redis-cli", "ping"])
    print(f"Ping Return Code: {ret}")
    print(f"Ping Output: {out.strip()}")
    if err:
        print(f"Ping Error: {err.strip()}")

    print("--- REDIS DEBUG COMPLETE ---")

if __name__ == "__main__":
    debug_redis()
