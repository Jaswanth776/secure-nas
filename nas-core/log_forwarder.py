#!/usr/bin/env python3
import time, urllib.request, json, os, re

LOG_FILE = "/opt/nas/nginx/logs/access.log"
INTEL_URL = "http://172.21.30.100:8000/api/v1/file"

# Nginx log pattern: IP - user [date] "METHOD /path HTTP" status ...
PATTERN = re.compile(r'(\S+) - (\S+) \[.*?\] "PUT (/remote\.php/dav/files/\S+) HTTP')

def send_event(payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(INTEL_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3)
        print(f"[forwarder] Sent: {payload['file_path']} by {payload['user_id']}")
    except Exception as e:
        print(f"[forwarder] send failed: {e}")

def tail_log():
    print(f"[forwarder] Watching {LOG_FILE}")
    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            m = PATTERN.search(line)
            if m:
                ip, user, path = m.group(1), m.group(2), m.group(3)
                parts = path.split("/remote.php/dav/files/")[-1].split("/", 1)
                nc_user = parts[0]
                file_path = "/" + parts[1] if len(parts) > 1 else "/"
                payload = {
                    "user_id": nc_user,
                    "file_path": file_path,
                    "file_size": 0,
                    "action": "upload",
                    "ip_address": ip
                }
                send_event(payload)

if __name__ == "__main__":
    while not os.path.exists(LOG_FILE):
        print(f"[forwarder] Waiting for {LOG_FILE}...")
        time.sleep(5)
    tail_log()
