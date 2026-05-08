#!/usr/bin/env python3
# Called by Nextcloud workflow on file events
# Env vars: NC_USER, NC_FILE, NC_FILESIZE, NC_ACTION, NC_REMOTE_ADDRESS
import os, sys, json, urllib.request, urllib.error

INTEL_URL = 'http://172.21.30.100:8000/api/v1/file'

payload = {
    'user_id':    os.environ.get('NC_USER', 'unknown'),
    'file_path':  os.environ.get('NC_FILE', ''),
    'file_size':  int(os.environ.get('NC_FILESIZE', 0) or 0),
    'action':     os.environ.get('NC_ACTION', 'unknown'),
    'ip_address': os.environ.get('NC_REMOTE_ADDRESS', ''),
}

try:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(INTEL_URL, data=data,
                                  headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=3)
except Exception as e:
    # Non-fatal — never block Nextcloud operations
    sys.stderr.write(f'Hook failed: {e}\n')
