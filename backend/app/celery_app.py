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

# Redis URL konfigurálása
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

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

# Beat schedule - ütemezett feladatok
celery_app.conf.beat_schedule = {
    # Napi Rockwool scraping
    'daily-rockwool-scraping': {
        'task': 'app.celery_tasks.scraping_tasks.scheduled_rockwool_scraping',
        'schedule': 60.0 * 60.0 * 24.0,  # 24 óránként (másodpercekben)
        'options': {
            'queue': 'scraping',
            'expires': 60 * 60 * 2  # 2 óra alatt le kell futnia
        }
    },
    
    # Heti teljes scraping
    'weekly-full-scraping': {
        'task': 'app.celery_tasks.scraping_tasks.weekly_full_scraping',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # Hetente
        'options': {
            'queue': 'scraping',
            'expires': 60 * 60 * 6  # 6 óra alatt
        }
    },
    
    # Adatbázis karbantartás
    'database-maintenance': {
        'task': 'app.celery_tasks.database_tasks.database_maintenance',
        'schedule': 60.0 * 60.0 * 24.0,  # Naponta
        'options': {
            'queue': 'database'
        }
    },
    
    # Scraping statisztikák riport
    'daily-scraping-report': {
        'task': 'app.celery_tasks.notification_tasks.send_daily_scraping_report',
        'schedule': 60.0 * 60.0 * 24.0,  # Naponta
        'options': {
            'queue': 'notifications'
        }
    }
}


# Celery signals
@celery_app.task(bind=True)
def debug_task(self):
    """Debug feladat a Celery tesztelésére"""
    print(f'Request: {self.request!r}')
    return 'Celery működik!'


# Worker startup hook
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Worker indítás után futó setup"""
    from app.celery_tasks.scraping_tasks import test_scraper_connection
    
    # Tesztelő feladat 30 másodperc múlva
    sender.add_periodic_task(
        30.0, 
        test_scraper_connection.s(), 
        name='Scraper kapcsolat teszt'
    )


# Worker ready hook
@celery_app.on_after_finalize.connect
def setup_periodic_tasks_finalize(sender, **kwargs):
    """Worker teljes indítás után"""
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Celery worker inicializálva és ready")
    logger.info(f"Broker: {celery_app.conf.broker_url}")
    logger.info(f"Backend: {celery_app.conf.result_backend}")
    logger.info(f"Ütemezett feladatok: {len(celery_app.conf.beat_schedule)}")


if __name__ == '__main__':
    celery_app.start() 