"""
Celery Tasks modul - Lambda.hu Backend

Ez a modul tartalmazza az összes aszinkron feladatot a Lambda.hu rendszerhez:
- Scraping feladatok
- Adatbázis karbantartás
- Email értesítések
"""

# Celery tasks modulok importálása
from . import scraping_tasks
from . import database_tasks
from . import notification_tasks

__all__ = [
    'scraping_tasks',
    'database_tasks', 
    'notification_tasks'
] 