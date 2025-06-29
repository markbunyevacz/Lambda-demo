# Projekt Átszervezési és Tisztítási Napló (2025-06-29)

Ez a dokumentum rögzíti a projektben végrehajtott nagyszabású strukturális és logikai átszervezés lépéseit, céljait és eredményeit.

## 1. Kiinduló Helyzet: Problémák

A refaktorálás előtti projekt több, a karbantarthatóságot és átláthatóságot nehezítő problémával küzdött:

-   **Strukturális Kétértelműség:** A forráskód (`backend`, `frontend`), a segédscriptek, a dokumentáció és a külső eszközök a gyökérkönyvtárban keveredtek.
-   **Duplikált Belépési Pont:** Két `main.py` fájl létezett, ami megnehezítette a valódi alkalmazás-belépési pont azonosítását.
-   **Elavult és Redundáns Scriptek:** Több, hasonló nevű scraper-fájl létezett párhuzamosan, melyek egy része már elavult volt.
-   **Felesleges Fájlok:** A repository tele volt ideiglenes debug-fájlokkal (`.html`), eredményfájlokkal (`.json`) és duplikált képernyőképekkel.
-   **Rejtett Hibák:** A Celery időzített feladatai egy már nem létező, régi scraper-architektúrára épültek, ami csak az átszervezés során derült ki.

## 2. A Refaktorálás Célja

-   Egy tiszta, iparági sztenderdeknek megfelelő (`src-layout`) mappaszerkezet kialakítása.
-   A felelősségi körök egyértelmű szétválasztása (forráskód, scriptek, dokumentáció).
-   A technikai adósság csökkentése a felesleges és elavult kódok eltávolításával.
-   A projekt karbantarthatóságának és az új fejlesztők bevonásának megkönnyítése.
-   A rejtett architekturális hibák feltárása és javítása.

## 3. Végrehajtott Lépések

A folyamat szigorúan kontrollált, lépésenkénti jóváhagyással történt.

1.  **Feltérképezés:** Egyedi elemző script (`project_cleanup_analyzer.py`) futtatásával azonosítottuk a problémás területeket.
2.  **Tisztítás:**
    -   Töröltük a felesleges `main.py`-t.
    -   Eltávolítottuk az összes ideiglenes és duplikált fájlt.
    -   Frissítettük a `.gitignore` fájlt a jövőbeli szennyeződések elkerülése érdekében.
3.  **Scraper-ek Racionalizálása:**
    -   Teszteléssel beazonosítottuk a két aktív, működő scraper-t (termékadatlap és prospektus).
    -   A két scriptet egy közös mappába (`src/backend/app/scrapers/rockwool_final/`) helyeztük, leíró neveket (`datasheet_scraper.py`, `brochure_and_pricelist_scraper.py`) és magyarázó kommenteket kaptak.
    -   Az összes többi, elavult scraper-verziót töröltük.
4.  **Strukturális Átszervezés:**
    -   Létrehoztuk a `src/`, `scripts/`, `docs/`, `tools/` mappákat.
    -   A `backend` és `frontend` a `src/`-be került.
    -   Minden segédscript a `scripts/`-be került.
    -   Minden `.md` dokumentáció a `docs/`-ba került.
    -   A külső `AI-Cursor-Scraping-Assistant` a `tools/`-ba került.
5.  **Konfigurációk Javítása:**
    -   A `docker-compose.yml`, `pyproject.toml` és `.gitignore` fájlokat frissítettük, hogy az új mappaszerkezetnek megfeleljenek.
6.  **Hibaelhárítás:**
    -   A Docker indításakor felmerülő Celery `ImportError` hibát analizáltuk.
    -   A hibát okozó, elavult Celery task-okat eltávolítottuk a `scraping_tasks.py`-ból.
7.  **Végső Teszt:** A `docker-compose up --build` paranccsal ellenőriztük, hogy az átszervezett és javított rendszer minden szolgáltatása stabilan elindul-e.

## 4. Eredmény

Az átszervezés eredményeképpen a projekt egy **stabil, tiszta és logikus struktúrával** rendelkezik, ami a jövőbeli fejlesztések szilárd alapját képezi. A rejtett hibák javításra kerültek, a technikai adósság pedig jelentősen csökkent. 

# .env.example
# Ez egy minta .env fájl. Másold át .env névre és töltsd ki a saját értékeiddel.
# SOHA ne tedd a .env fájlt a Git repository-ba!

# PostgreSQL Adatbázis Beállítások
# Ezeket a változókat a docker-compose.yml használja a 'db' service indításakor.
POSTGRES_USER=lambda_user
POSTGRES_PASSWORD=
POSTGRES_DB=lambda_db
DATABASE_URL=postgresql://lambda_user:your_password_here@db:5432/lambda_db

# Redis Beállítások (Celery üzenetküldő és cache)
REDIS_URL=redis://cache:6379/0

# Adatgyűjtési (Scraping) API Kulcsok
# Ezek szükségesek a BrightData és Anthropic (Claude) szolgáltatások használatához.
BRIGHTDATA_API_TOKEN=
ANTHROPIC_API_KEY=

# BrightData - Speciális beállítások (opcionális)
BRIGHTDATA_BROWSER_AUTH=
BRIGHTDATA_WEB_UNLOCKER_ZONE=

# Celery Opcionális Beállítások
# Állítsd 'True'-ra, ha a django-celery-beat adatbázis-alapú ütemezőt szeretnéd használni.
USE_DJANGO_BEAT=False 