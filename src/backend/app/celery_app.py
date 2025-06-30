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
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.celery_tasks.scraping_tasks']
)

# Celery konfiguráció
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  
    result_serializer='json',
    timezone='Europe/Budapest',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

# A `beat_schedule` és a `setup_periodic_tasks` funkciók eltávolítva,
# mivel az időzített feladatok logikája elavult. A Celery mostantól
# csak az API-n keresztül manuálisan indított taskokat hajtja végre.

if __name__ == '__main__':
    celery_app.start() 