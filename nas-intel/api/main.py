from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, List
import asyncpg, os, logging
from celery import Celery

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('fastapi')

app = FastAPI(title='NAS Intelligence API', version='1.0.0')

DATABASE_URL = os.environ['DATABASE_URL']
REDIS_URL    = os.environ['REDIS_URL']

celery_app = Celery('nas_tasks', broker=REDIS_URL, backend=REDIS_URL)

# ── DB Pool ──────────────────────────────────────────────────────
pool = None
@app.on_event('startup')
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    log.info('Database pool created')

@app.on_event('shutdown')
async def shutdown():
    await pool.close()

# ── Models ───────────────────────────────────────────────────────
class FileEvent(BaseModel):
    user_id:   str
    file_path: str
    action:    str
    file_size: Optional[int] = None
    ip_address: Optional[str] = None

class SecurityAlert(BaseModel):
    type:       str
    ip:         Optional[str] = None
    reason:     str
    timestamp:  Optional[str] = None

# ── Endpoints ────────────────────────────────────────────────────
@app.get('/health')
async def health():
    return {'status': 'ok', 'service': 'nas-intelligence'}

@app.post('/api/v1/event')
async def receive_event(alert: SecurityAlert):
    async with pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO security_alerts(alert_type, ip_address, reason) VALUES($1,$2,$3)',
            alert.type, alert.ip, alert.reason
        )
    log.info(f'Alert received: {alert.type} from {alert.ip}')
    return {'status': 'recorded'}

@app.post('/api/v1/file')
async def file_event(event: FileEvent, bg: BackgroundTasks):
    async with pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO file_events(user_id, file_path, action, file_size, ip_address) VALUES($1,$2,$3,$4,$5)',
            event.user_id, event.file_path, event.action, event.file_size, event.ip_address
        )
    # Queue ML classification if it's an upload
    if event.action == 'upload':
        bg.add_task(queue_classification, event.file_path, event.user_id)
    return {'status': 'recorded', 'queued_ml': event.action == 'upload'}

def queue_classification(file_path: str, user_id: str):
    celery_app.send_task('workers.tasks.classify_file',
                         args=[file_path, user_id])
    log.info(f'Queued ML classification for {file_path}')

@app.get('/api/v1/analytics/summary')
async def analytics_summary():
    async with pool.acquire() as conn:
        uploads  = await conn.fetchval("SELECT COUNT(*) FROM file_events WHERE action='upload'")
        alerts   = await conn.fetchval("SELECT COUNT(*) FROM security_alerts WHERE resolved=false")
        users    = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM file_events")
        return {'total_uploads': uploads, 'open_alerts': alerts, 'active_users': users}

@app.get('/api/v1/alerts')
async def get_alerts(limit: int = 50):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT * FROM security_alerts ORDER BY alert_time DESC LIMIT $1', limit
        )
        return [dict(r) for r in rows]

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
