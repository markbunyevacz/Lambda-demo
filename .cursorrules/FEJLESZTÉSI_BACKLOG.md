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

### Fázis 2: Adat-pipeline és Web Scraping (Hét 2-4)
- [ ] Rockwool scraper implementációja a Rendszerterv alapján
- [ ] Leier scraper implementációja
- [ ] Baumit scraper implementációja
- [ ] Scraped adatok validálása és normalizálása
- [ ] Adatbázisba mentési logika implementálása
- [ ] Celery és Celery Beat beállítása az automatikus, időzített frissítéshez

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