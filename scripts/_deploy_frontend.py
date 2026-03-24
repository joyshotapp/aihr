"""Trigger frontend Docker build+deploy on the remote server via SSH."""
import subprocess, sys, time

SSH_HOST = "root@172.233.67.81"
REMOTE_CMD = (
    "cd /opt/aihr && "
    "nohup bash -c '"
    "docker compose -f docker-compose.prod.yml --env-file .env.production build frontend web "
    "> /tmp/build_frontend.log 2>&1 "
    "; docker compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps frontend web "
    ">> /tmp/build_frontend.log 2>&1 "
    "; echo BUILD_DONE >> /tmp/build_frontend.log"
    "' </dev/null >/dev/null 2>&1 & echo TRIGGERED"
)

print("Triggering remote build...")
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST, REMOTE_CMD],
    capture_output=True, text=True, timeout=20
)
print("stdout:", repr(r.stdout))
print("stderr:", repr(r.stderr))
print("returncode:", r.returncode)

if r.returncode != 0:
    sys.exit(1)
print("Build triggered. Waiting 120s before checking log...")
time.sleep(120)

# Check log
r2 = subprocess.run(
    ["ssh", SSH_HOST, "cat /tmp/build_frontend.log | tail -30"],
    capture_output=True, text=True, timeout=15
)
print("=== BUILD LOG (last 30 lines) ===")
print(r2.stdout or "(no output)")
print(r2.stderr or "")
