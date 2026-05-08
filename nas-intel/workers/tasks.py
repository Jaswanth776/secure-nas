from celery import Celery
import magic, os, logging, psycopg2
from datetime import datetime

log = logging.getLogger('celery_worker')

REDIS_URL    = os.environ['REDIS_URL']
DATABASE_URL = os.environ['DATABASE_URL']

app = Celery('nas_tasks', broker=REDIS_URL, backend=REDIS_URL)

# File category mapping by MIME type prefix
CATEGORY_MAP = {
    'image':       'image',
    'video':       'video',
    'audio':       'audio',
    'text':        'document',
    'application/pdf':          'document',
    'application/zip':          'archive',
    'application/x-tar':        'archive',
    'application/x-gzip':       'archive',
    'application/msword':       'document',
    'application/vnd.openxml':  'document',
    'application/x-python':     'code',
    'application/javascript':   'code',
}

def get_category(mime: str) -> str:
    for prefix, cat in CATEGORY_MAP.items():
        if mime.startswith(prefix):
            return cat
    return 'other'

def get_tags(mime: str, category: str) -> list:
    tags = [category]
    if 'pdf' in mime:   tags.append('pdf')
    if 'image' in mime: tags.append('visual-media')
    if 'video' in mime: tags.append('video-media')
    if 'zip'   in mime or 'tar' in mime: tags.append('compressed')
    if 'python' in mime or 'javascript' in mime: tags.append('source-code')
    return list(set(tags))

@app.task(name='workers.tasks.classify_file')
def classify_file(file_path: str, user_id: str):
    log.info(f'Classifying {file_path} for user {user_id}')
    try:
        host_path = f'/nas-data/{user_id}/files/{file_path.lstrip("/")}'
        if not os.path.exists(host_path):
            log.warning(f'File not found: {host_path}')
            return

        mime = magic.from_file(host_path, mime=True)
        category = get_category(mime)
        tags     = get_tags(mime, category)
        size     = os.path.getsize(host_path)

        conn = psycopg2.connect(DATABASE_URL)
        cur  = conn.cursor()
        cur.execute(
            '''INSERT INTO file_classifications
               (file_path, mime_type, category, tags, confidence)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (file_path) DO UPDATE
               SET mime_type=%s, category=%s, tags=%s, confidence=%s, classified_at=NOW()''',
            (file_path, mime, category, tags, 0.90,
             mime, category, tags, 0.90)
        )
        conn.commit()
        cur.close()
        conn.close()
        log.info(f'Classified {file_path}: {category} [{mime}] tags={tags}')
    except Exception as e:
        log.error(f'Classification error for {file_path}: {e}')
