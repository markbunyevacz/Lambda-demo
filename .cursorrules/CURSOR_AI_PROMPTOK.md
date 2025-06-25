# Lambda.hu AI Rendszer - Cursor AI Promptok

### Fázis 1: Alapozás és Infrastruktúra

**Task 1.1: Projektstruktúra és Docker-compose**
@workspace
Hozd létre a projekt alapvető Docker környezetét.
Követelmények:
Hozz létre egy docker-compose.yml fájlt.
Definiálj benne három service-t: backend (FastAPI), db (PostgreSQL 15), és cache (Redis).
A backend service a helyi backend mappából épüljön, a Dockerfile alapján.
A db service-hez hozz létre egy volume-ot (postgres_data) a perzisztens tároláshoz. Konfiguráld a szükséges környezeti változókat (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) egy .env fájl alapján.
Tedd közzé a backend service 8000-es portját a host 8000-es portjára, és a db 5432-es portját.
Hozz létre egy backend/Dockerfile-t, ami Python 3.11-re épül, telepíti a requirements.txt-ben lévő függőségeket, és uvicorn-nal indítja az alkalmazást.
Hozz létre egy alap backend/requirements.txt-t a következő csomagokkal: fastapi, uvicorn, sqlalchemy, psycopg2-binary, redis.


**Task 1.2: Adatbázis Modellek (SQLAlchemy)**
@workspace
Hozd létre a SQLAlchemy adatbázis modelleket a Teljes Rendszerterv.pdf dokumentumban található SQL CREATE TABLE definíciók alapján.
Hely: backend/app/models/
Követelmények:
Hozz létre egy manufacturer.py fájlt a manufacturers táblához.
Hozz létre egy category.py fájlt a categories táblához. Implementáld a self-referential kapcsolatot (parent_id) a rekurzív kategóriákhoz.
Hozz létre egy product.py fájlt a products táblához.
Minden modellben használd a SQLAlchemy 2.0 szintaktikát és a declarative_base-t.
Definiáld a táblák közötti kapcsolatokat (relationship) a back_populates argumentummal. (Pl. Manufacturer -> Products).
A JSONB típusú oszlopokhoz használd a sqlalchemy.dialects.postgresql.JSONB típust.
Implementálj minden modellhez egy to_dict() metódust, ami a modell adatait egy szótárrá alakítja, és a kapcsolódó objektumokat (pl. gyártó, kategória) beágyazza.


### Fázis 2: Adat-pipeline és Web Scraping

**Task 2.1: Rockwool Scraper**
@workspace
Implementáld a Rockwool scrapert a Teljes Rendszerterv.pdf 9. oldalán található Scrapy kód alapján. Azonban ne Scrapy-t, hanem aiohttp-t és BeautifulSoup-t használj egy async/await alapú, önálló szkriptben.
Hely: backend/scrapers/rockwool_scraper.py
Követelmények:
A scraper legyen egy osztály, ami követi a PDF-ben lévő logikát: kategória oldalak feltérképezése, majd termék oldalak linkjeinek kinyerése, végül a termék részleteinek "scrape-elése".
A kinyert adatok (név, leírás, műszaki adatok, képek, dokumentumok) egy dataclass vagy Pydantic modellbe kerüljenek.
Implementálj egy robusztus extract_technical_specs metódust, ami képes a táblázatokból és a kulcs-érték listákból is kinyerni az adatokat.
Normalizáld a műszaki adatok kulcsait (pl. "Hővezetési tényező" -> "thermal_conductivity").
Az értékekből (pl. "0.035 W/mK") nyerd ki a numerikus értéket és a mértékegységet külön.
A szkript legyen futtatható és mentsa az eredményt egy rockwool_products.json fájlba.


### Fázis 3: AI Modul - RAG Pipeline

**Task 3.1: RAG Service Implementáció**
@workspace
Hozz létre egy BuildingMaterialsAI service-t a RAG (Retrieval-Augmented Generation) logika implementálásához LangChain segítségével.
Hely: backend/app/services/ai_service.py
Követelmények:
Az osztály inicializálásakor töltse be az OpenAI LLM-et és az embedding modellt az API kulcsokkal .env fájlból.
Hozzon létre egy Chroma vektor store-t. Legyen egy metódus, ami a scraped JSON adatfájlokból beolvassa, feldarabolja (RecursiveCharacterTextSplitter), és vektorizálva elmenti a termékinformációkat a Chroma DB-be.
Hozzon létre egy RetrievalQA láncot a "Teljes Rendszerterv" 12. oldalán lévő magyar nyelvű, építészeti szakértői prompt sablonnal.
Legyen egy get_product_recommendations(user_query: str) metódus, ami lefuttatja a Q&A láncot, és visszaadja az AI által generált szöveges választ, valamint a releváns, adatbázisból kinyert termékek listáját.


### Fázis 4: Backend API és Frontend Integráció

**Task 4.1: AI Chat API Végpont**
@workspace
Hozz létre egy FastAPI végpontot az AI asszisztens számára.
Hely: backend/app/api/ai_assistant.py
Követelmények:
Endpoint: POST /api/v1/ai/chat
Használj egy Pydantic modellt a bemeneti adatok validálásához (pl. { "message": str, "context": List[Dict] }).
Hívja meg a korábban létrehozott BuildingMaterialsAI service get_product_recommendations metódusát.
A válasz legyen egy Pydantic modell, ami tartalmazza az AI szöveges válaszát és az ajánlott termékek listáját.
Implementálj alapvető hibakezelést.
Az új routert regisztráld be a fő main.py fájlban.


**Task 4.2: Frontend AI Chat Komponens**

@workspace
Hozz létre egy React komponenst egy AI chat ablakhoz, a "Teljes Rendszerterv" 13. oldalán található AIAssistant JSX kód alapján.
Hely: frontend/src/components/AIAssistant/AIAssistant.tsx
Követelmények:
A komponens legyen egy lebegő ablak a jobb alsó sarokban.
Használd a useState hookot az üzenetek listájának és a "gépel" állapotnak a kezelésére.
Hozz létre egy useChat nevű egyéni hookot, ami @tanstack/react-query (useMutation) segítségével kezeli az API hívást a /api/v1/ai/chat végpontra.
Az üzeneteket jelenítsd meg egy listában, eltérő stílussal a felhasználói és az AI üzeneteknek.
Amíg az API válaszra vársz, jeleníts meg egy "gépel..." indikátort.
Az AI válaszában kapott termékajánlásokat jelenítsd meg kattintható kártyákként a chat üzenet alatt.


### Fázis 6: Finalizálás és Deployment

**Task 6.1: Teszt az API Végponthoz**
@workspace
Írj egy pytest tesztet a /api/v1/ai/chat végponthoz.
Hely: backend/tests/test_ai_api.py
Követelmények:
Használd a pytest.mark.asyncio-t az aszinkron tesztekhez.
Használd a httpx.AsyncClient-et a FastAPI alkalmazás teszteléséhez.
Küldj egy valószerű POST kérést egy építőipari kérdéssel (pl. "Milyen vastag szigetelés kell homlokzatra?").
Ellenőrizd, hogy a válasz HTTP státuszkódja 200.
Ellenőrizd, hogy a JSON válasz tartalmazza az ai_response és a recommended_products kulcsokat.
Ellenőrizd, hogy az ai_response nem üres string.