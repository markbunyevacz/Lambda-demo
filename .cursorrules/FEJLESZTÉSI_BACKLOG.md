# Lambda.hu Építőanyag AI Rendszer - Fejlesztési Backlog

## Minimum Credible Product (MCP) Célja
**Cél:** Bemutatni a rendszer alapvető képességét: egy felhasználó természetes nyelven kereshet építőanyagot, a rendszer pedig a naprakész, "scraped" adatok alapján releváns termékeket és AI-alapú szakértői választ ad.
- **Gyártók:** Csak 1 gyártó (Rockwool) adatainak teljes feldolgozása.
- **Funkciók:**
    - Automatizált adatgyűjtés és feldolgozás (Rockwool).
    - Strukturált adatbázis (PostgreSQL) és vektor adatbázis (Chroma).
    - Természetes nyelvű keresés (RAG pipeline) és egyszerű, szűrő nélküli terméklista.
    - Egyszerűsített UI: egy keresőmező, egy AI chat ablak és egy terméklista megjelenítő.
- **Nem része az MCP-nek:** Több gyártó, ajánlatkészítő modul, komplex szűrők, felhasználói fiókok.

---

## Teljes Projekt Fázisok és Feladatok

### Fázis 1: Alapozás és Infrastruktúra (Hét 1-2) ✅ KÉSZ
- [x] Projektstruktúra felállítása (Backend, Docker)
- [x] Docker-compose konfiguráció (FastAPI, PostgreSQL, Redis)
- [x] Adatbázis sémák és SQLAlchemy modellek létrehozása (`manufacturers`, `categories`, `products`)
- [x] Alapvető FastAPI alkalmazás létrehozása, CORS és DB kapcsolattal
- [x] Alapvető Next.js/React frontend váz létrehozása Tailwind CSS-szel (vizuális váz kész)

### Fázis 2: Adat-pipeline és Web Scraping (Hét 2-4) ✅ KÉSZ
- [x] **Rockwool scraper implementációja a Rendszerterv alapján** ✅ KÉSZ
  - [x] Weboldal struktúra elemzése és térképezése
  - [x] Termék adatok automatikus kinyerése (név, leírás, műszaki paraméterek)
  - [x] Képek és dokumentumok letöltése
  - [x] Rate limiting és hibakezelés implementálása
  - [x] Moduláris scraper architektúra (RockwoolScraper, ProductParser, CategoryMapper, DataValidator)
  - [x] REST API végpontok scraper kezelésére
  - [x] Komprehenzív dokumentáció és tesztelési eszközök
- [ ] Leier scraper implementációja (MCP után)
- [ ] Baumit scraper implementációja (MCP után)
- [x] **Scraped adatok validálása és normalizálása + Adatbázisba mentési logika** ✅ KÉSZ *(A pont)*
  - [x] **DatabaseIntegration szolgáltatás:** ScrapedProduct → Product modell mappelés teljes automatizálással
  - [x] **Gyártók és kategóriák:** automatikus létrehozása (`ensure_manufacturer`, `ensure_category`) cache-eléssel
  - [x] **SKU generálás:** ROCK-{kategória}-{URL_hash} formátum duplikátum kezeléssel
  - [x] **Bulk mentési műveletek:** hibatűrő logikával és source_url alapú felülírással
  - [x] **Műszaki specifikációk normalizálása:** raw + processed adatok strukturálása
  - [x] **API integráció:** `POST /api/scraper/scrape/single-product` és `/save-to-database` végpontok
  - [x] **DataValidator:** teljes adatminőség biztosítás és konzisztencia vizsgálat
- [x] **Celery és Celery Beat automatikus, időzített frissítés** ✅ KÉSZ *(B pont)*
  - [x] **Celery alkalmazás konfiguráció:** Redis broker 4 specializált queue-val (scraping, database, notifications, default)
  - [x] **Ütemezett feladatok:** beat scheduler napi/heti automatizmussal
  - [x] **scraping_tasks.py:** `scheduled_rockwool_scraping()` (napi 20 termék/kategória), `weekly_full_scraping()`, `scrape_specific_urls()`
  - [x] **database_tasks.py:** `database_maintenance()` (cleanup, deduplikáció, VACUUM), `backup_database_statistics()`, `check_database_health()`
  - [x] **notification_tasks.py:** `send_daily_scraping_report()`, `send_scraping_error_alert()`, `monitor_scraper_health()`
  - [x] **Docker integráció:** `celery_worker`, `celery_beat`, `celery_flower` (monitoring UI localhost:5555)
  - [x] **Worker beállítások:** optimalizált prefetch, retry logika, részletes logging
- [x] **Integrációs tesztelés éles Rockwool adatokon** ✅ KÉSZ *(C pont)*
  - [x] **test_integration.py:** komprehenzív teszt framework 5 fő területtel
  - [x] **Adatbázis kapcsolat:** connection, table counts, health check ellenőrzése
  - [x] **Scraper alapvető működés:** weboldal struktúra feltérképezés, kategória bejárás, termék scraping
  - [x] **Adatbázis integráció:** egyedi + bulk mentések validálása Product/Manufacturer/Category objektumokkal
  - [x] **API végpontok:** health check, website-structure, scraping végpontok tesztelése
  - [x] **Celery feladatok:** worker kapcsolat, debug task, queue monitoring ellenőrzése
  - [x] **Hibakezelés és retry:** rate limiting, timeout, exponential backoff teljes lefedettséggel

### Fázis 3: AI Modul - RAG Pipeline (Hét 4-6)
- [ ] Chroma vektor adatbázis inicializálása és perzisztálása
- [ ] LangChain integráció és `BuildingMaterialsAI` service létrehozása
- [ ] Termékadatok automatikus vektorizálása és indexelése
- [ ] Q&A lánc létrehozása a magyar nyelvű, építészeti szakértői prompt-tal
- [ ] Kompatibilitás-ellenőrző logika alapjainak implementálása (`check_system_compatibility`)

### Fázis 4: Backend API és Frontend Integráció (Hét 6-9)
- [ ] Termékkereső API végpont létrehozása (szöveges keresés + szűrés)
- [ ] AI Chat API végpont létrehozása (`get_product_recommendations`)
- [ ] Kompatibilitás-ellenőrző API végpont létrehozása
- [ ] Frontend: Termékkereső interface (keresőmező, szűrők, termékrács) fejlesztése
- [ ] Frontend: AI Chat komponens fejlesztése és bekötése
- [ ] Frontend: Termék adatlap és összehasonlító komponens fejlesztése

### Fázis 5: Ajánlatkészítő Modul (Hét 9-11)
- [ ] `quotes` adatbázis tábla és SQLAlchemy modell
- [ ] `QuoteCalculator` service implementálása (árkalkuláció, veszteségszámítás)
- [ ] Ajánlatkészítő API végpontok (létrehozás, lekérdezés)
- [ ] PDF generáló modul integrálása (ReportLab)
- [ ] Email küldő szolgáltatás integrációja
- [ ] Frontend: Ajánlatkészítő UI (kosár, véglegesítés)

### Fázis 6: Finalizálás és Deployment (Hét 12)
- [ ] Teljes körű API és frontend tesztelés (pytest, Jest/Playwright)
- [ ] `Dockerfile`-ok finomhangolása éles környezetre
- [ ] CI/CD pipeline alapjainak létrehozása (pl. GitHub Actions)
- [ ] Részletes dokumentáció (API Swagger, README)
- [ ] Felhasználói tesztelés és visszajelzések feldolgozása