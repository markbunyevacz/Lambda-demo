# Docker Compose Troubleshooting Log

Ez a dokumentum a `docker-compose` alapú fejlesztői környezetben felmerült hibák és azok megoldásának lépéseit rögzíti.

## Probléma: Celery és Backend Szolgáltatások Folyamatosan Újraindulnak

A `docker-compose ps` parancs kimenete alapján a `celery_worker`, `celery_beat`, `celery_flower` és `backend` konténerek instabilak voltak és folyamatosan újraindultak.

### Lépés 1: Hiba Azonosítása a Celery Logokban

A `docker-compose logs celery_worker` parancs megmutatta az elsődleges hibát:

```
ImportError: cannot import name 'get_db' from 'app.database'
```

Ez a hiba jelezte, hogy a Celery feladatok által használt `database_integration.py` modul nem találta a `get_db` adatbázis-kapcsolatot biztosító függvényt.

**Megoldás:** A `backend/app/database.py` fájlban létrehoztuk a hiányzó `get_db` függvényt, ami egy FastAPI-ban és Celery-ben is használható, "dependency injection" mintát követő session generátor.

### Lépés 2: Import Hiba a Scraper Modulban

A `get_db` hiba javítása után egy újabb import hiba jelent meg:

```
ImportError: cannot import name 'ScrapingConfig' from 'app.scraper'
```

A `scraping_tasks.py` sikertelenül próbálta importálni a `ScrapingConfig` osztályt a scraper modulból. A vizsgálat kimutatta, hogy a `ScrapingConfig` a `rockwool_scraper.py`-ban volt definiálva, de nem volt exportálva a `scraper` csomag `__init__.py` fájljában.

**Megoldás:** A `backend/app/scraper/__init__.py` fájlban importáltuk és hozzáadtuk a `ScrapingConfig` osztályt az `__all__` listához, így elérhetővé téve más modulok számára.

### Lépés 3: Hiányzó `requests` Csomag a Backendben

A Celery szolgáltatások stabilizálása után a `backend` konténer továbbra is leállt. A `docker-compose logs backend` parancs kimutatta a következő hibát:

```
ModuleNotFoundError: No module named 'requests'
```

Annak ellenére, hogy a `requests` csomag szerepelt a `requirements.txt`-ben, a Docker image nem tartalmazta. Ez arra utalt, hogy az image elavult volt, és nem a legfrissebb függőségekkel lett felépítve.

**Megoldás:** A `docker-compose build backend` paranccsal újraépítettük a backend Docker image-et, ami frissen telepítette az összes függőséget.

### Lépés 4: Adatbázis Típus Eltérési Hiba (SQLite vs. PostgreSQL)

Az image újraépítése után a backend egy újabb hibával állt le:

```
sqlalchemy.exc.CompileError: ... can't render element of type JSONB
```

Ez a hiba abból adódott, hogy az SQLAlchemy modellek PostgreSQL-specifikus `JSONB` típust használtak, de az alkalmazás egy `.env` fájl hiányában az alapértelmezett SQLite adatbázishoz próbált csatlakozni, ami nem támogatja ezt a típust.

**Megoldás:**
1.  Létrehoztunk egy `.env` fájlt a megfelelő `DATABASE_URL`-lel és egyéb környezeti változókkal.
2.  Mivel a PostgreSQL konténer már inicializálódott a `.env` fájl nélkül (így nem jött létre a `lambda_db` adatbázis), leállítottuk a `db` szolgáltatást (`docker-compose down db`).
3.  Töröltük a régi, hibásan inicializált volume-ot (`docker volume rm lambda_postgres_data`).
4.  Újraindítottuk a `db` és `backend` szolgáltatásokat, amelyek már a `.env` fájlban definiált PostgreSQL adatbázissal indultak el.

Ezen lépések után az összes szolgáltatás stabilan és hibamentesen futott. 