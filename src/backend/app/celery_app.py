"""
Celery alkalmazás konfiguráció - Lambda.hu Backend

Ez a modul tartalmazza a Celery worker és scheduler konfigurációját
a Lambda.hu építőanyag AI rendszerhez.

Főbb funkciók:
- Aszinkron scraping feladatok
- Ütemezett adatgyűjtés
- Email értesítések
- Adatbázis karbantartási feladatok
"""

import os
from celery import Celery
from kombu import Exchange, Queue

# Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

# Get Redis URL from environment variable, default to a standard local setup if not found
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery alkalmazás létrehozása
celery_app = Celery(
    'lambda_hu_backend',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'app.celery_tasks.scraping_tasks',
        'app.celery_tasks.database_tasks',
        'app.celery_tasks.notification_tasks'
    ]
)

# Celery konfiguráció
celery_app.conf.update(
    # Időzóna beállítása
    timezone='Europe/Budapest',
    enable_utc=True,
    
    # Feladatok TTL és eredmények
    result_expires=3600,  # 1 óra
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Worker beállítások
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Routing és queue-k
    task_routes={
        'app.celery_tasks.scraping_tasks.*': {'queue': 'scraping'},
        'app.celery_tasks.database_tasks.*': {'queue': 'database'},
        'app.celery_tasks.notification_tasks.*': {'queue': 'notifications'},
    },
    
    # Queue-k definiálása
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('scraping', Exchange('scraping'), routing_key='scraping'),
        Queue('database', Exchange('database'), routing_key='database'),
        Queue('notifications', Exchange('notifications'), routing_key='notifications'),
    ),
    
    # Beat scheduler beállítások
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler' if os.getenv('USE_DJANGO_BEAT') else 'celery.beat:PersistentScheduler',
    
    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Retry beállítások
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
)

# A `beat_schedule` és a `setup_periodic_tasks` funkciók eltávolítva,
# mivel az időzített feladatok logikája elavult. A Celery mostantól
# csak az API-n keresztül manuálisan indított taskokat hajtja végre.

if __name__ == '__main__':
    celery_app.start() 