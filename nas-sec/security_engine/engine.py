import json, time, re, subprocess, logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('security_engine')

LOG_FILE  = '/var/log/nextcloud/nextcloud.log'
INTEL_URL = 'http://172.21.30.100:8000/api/v1/event'

# Rule config
BRUTE_FORCE_THRESHOLD = 5   # failed logins
BRUTE_FORCE_WINDOW    = 300  # seconds (5 min)
MASS_DOWNLOAD_THRESHOLD = 50 # files in window
MASS_DOWNLOAD_WINDOW    = 120 # seconds

# Track state
login_failures  = defaultdict(lambda: deque())
file_downloads  = defaultdict(lambda: deque())
blocked_ips     = set()

def block_ip(ip: str, reason: str):
    if ip in blocked_ips or ip.startswith('172.21.30'):  # never block LAN
        return
    log.warning(f'BLOCKING IP {ip}: {reason}')
    try:
        subprocess.run(['fail2ban-client', 'set', 'nextcloud', 'banip', ip],
                       capture_output=True, timeout=5)
        blocked_ips.add(ip)
        send_alert(ip, reason)
    except Exception as e:
        log.error(f'Failed to block {ip}: {e}')

def send_alert(ip: str, reason: str):
    try:
        payload = {'type': 'security_alert', 'ip': ip, 'reason': reason,
                   'timestamp': datetime.now(timezone.utc).isoformat()}
        requests.post(INTEL_URL, json=payload, timeout=3)
    except Exception:
        pass  # non-critical

def process_line(line: str):
    try:
        entry = json.loads(line.strip())
    except json.JSONDecodeError:
        return

    msg    = entry.get('message', '')
    ip     = entry.get('remoteAddr', '')
    user   = entry.get('user', '')
    now    = time.time()

    # --- Rule 1: Brute Force Detection ---
    if ('Login failed' in msg or 'maximum failed attempts' in msg or 'TooManyRequests' in msg) and ip:
        q = login_failures[ip]
        q.append(now)
        while q and q[0] < now - BRUTE_FORCE_WINDOW:
            q.popleft()
        if len(q) >= BRUTE_FORCE_THRESHOLD:
            block_ip(ip, f'Brute force: {len(q)} failed logins in {BRUTE_FORCE_WINDOW}s')

    # --- Rule 2: Mass Download Detection ---
    if 'download' in msg.lower() and ip:
        q = file_downloads[ip]
        q.append(now)
        while q and q[0] < now - MASS_DOWNLOAD_WINDOW:
            q.popleft()
        if len(q) >= MASS_DOWNLOAD_THRESHOLD:
            send_alert(ip, f'Mass download: {len(q)} files in {MASS_DOWNLOAD_WINDOW}s')
            log.warning(f'Mass download from {ip} by {user}')


class LogHandler(FileSystemEventHandler):
    def __init__(self):
        self._file = open(LOG_FILE, 'r')
        self._file.seek(0, 2)  # Seek to end

    def on_modified(self, event):
        if event.src_path == LOG_FILE:
            for line in self._file:
                if line.strip():
                    process_line(line)


def main():
    log.info(f'Security Engine starting. Watching: {LOG_FILE}')
    log_path = Path(LOG_FILE)

    while not log_path.exists():
        print(f"[WAIT] Log file not found: {LOG_FILE}")
        time.sleep(2)

    print(f"[OK] Monitoring log file: {LOG_FILE}")
    handler  = LogHandler()
    observer = Observer()
    observer.schedule(handler, path=str(Path(LOG_FILE).parent), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
