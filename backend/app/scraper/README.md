# Rockwool Scraper Dokumentáció

## Áttekintés

A Rockwool Scraper egy teljes körű automatizálási rendszer a Rockwool.hu weboldal termékadatainak összegyűjtésére. Ez a dokumentáció részletesen bemutatja a scraper használatát, konfigurációját és az automatizálási lehetőségeket.

## 🏗️ Architektúra

A scraper moduláris felépítésű, négy fő komponenssel:

### 1. **RockwoolScraper** - Fő scraper osztály
- Weboldal struktúra feltérképezése
- Termékek automatikus felderítése  
- Rate limiting és hibakezelés
- Újrapróbálkozási logika

### 2. **ProductParser** - HTML elemzés és adatkinyerés
- Terméknevek és leírások feldolgozása
- Műszaki specifikációk táblázatokból
- Képek és dokumentumok URL-jeinek gyűjtése
- Rockwool specifikus tisztítási szabályok

### 3. **CategoryMapper** - Kategóriák normalizálása
- URL alapú kategória meghatározás
- Egységes kategória struktúra
- Terméknevek alapú automatikus kategorizálás

### 4. **DataValidator** - Adatminőség biztosítás
- Kötelező mezők ellenőrzése
- Adatformátum validálás
- Konzisztencia vizsgálat

## 🚀 Gyors indítás

### 1. Függőségek telepítése

```bash
# Backend könyvtárban
pip install -r requirements.txt
```

### 2. Egyszerű scraping teszt

```python
from app.scraper import RockwoolScraper

# Scraper inicializálása
scraper = RockwoolScraper()

# Weboldal struktúra feltérképezése
structure = scraper.discover_website_structure()
print(f"Talált kategóriák: {len(structure['categories'])}")

# Egyetlen termék scraping-je
product = scraper._scrape_single_product(
    "https://www.rockwool.hu/termekek/.../frontrock-max-e/"
)
if product:
    print(f"Scraped: {product.name}")
```

### 3. REST API használat

```bash
# Scraper állapot ellenőrzése
curl http://localhost:8000/api/scraper/status

# Weboldal struktúra feltérképezése
curl http://localhost:8000/api/scraper/website-structure

# Egyetlen termék scraping-je
curl -X POST "http://localhost:8000/api/scraper/scrape/single-product" \
     -H "Content-Type: application/json" \
     -d '{"product_url": "https://www.rockwool.hu/..."}'
```

## ⚙️ Konfiguráció

### ScrapingConfig osztály

```python
from app.scraper import ScrapingConfig

config = ScrapingConfig(
    base_url="https://www.rockwool.hu",
    max_requests_per_minute=30,    # Rate limiting
    request_delay=2.0,             # Késleltetés kérések között (másodperc)
    timeout=30,                    # HTTP timeout
    max_retries=3,                 # Újrapróbálkozások száma
    user_agent="Mozilla/5.0..."    # User-Agent string
)

scraper = RockwoolScraper(config)
```

### Ajánlott beállítások

**Gyors scraping (fejlesztés/teszt):**
```python
config = ScrapingConfig(
    request_delay=1.0,
    max_requests_per_minute=60
)
```

**Óvatos scraping (éles használat):**
```python
config = ScrapingConfig(
    request_delay=3.0,
    max_requests_per_minute=20,
    max_retries=5
)
```

## 📋 API Végpontok

### GET `/api/scraper/status`
Scraper állapot lekérdezése
```json
{
  "is_running": false,
  "scraped_urls": 42,
  "failed_urls": 3,
  "last_activity": "2024-01-15T10:30:00"
}
```

### GET `/api/scraper/website-structure`
Rockwool weboldal struktúrájának feltérképezése
```json
{
  "success": true,
  "structure": {
    "categories": ["https://www.rockwool.hu/homlokzat/...", ...],
    "product_pages": ["https://www.rockwool.hu/termekek/...", ...]
  },
  "discovered_at": "2024-01-15T10:30:00"
}
```

### POST `/api/scraper/scrape/single-product`
Egyetlen termék scraping-je
```json
{
  "product_url": "https://www.rockwool.hu/termekek/.../frontrock-max-e/"
}
```

### POST `/api/scraper/scrape/start`
Teljes scraping indítása háttérben
```json
{
  "max_products_per_category": 10,
  "max_categories": 5,
  "test_mode": false,
  "specific_urls": null
}
```

### GET `/api/scraper/health`
Scraper egészségügyi ellenőrzés

## 🔍 Weboldal térképezés

A scraper automatikusan feltérképezi a Rockwool weboldal struktúráját:

### 1. Navigációs menü elemzése
- Főmenü linkek azonosítása
- Termék kategóriák feltérképezése
- Hierarchikus menü struktúra

### 2. Kategória felderítés
A scraper the következő kategóriákat azonosítja:
- **Tetőszigetelés** (roofrock, deltarock)
- **Homlokzati hőszigetelés** (frontrock, multirock)
- **Padlószigetelés** (steprock)
- **Válaszfal szigetelés** (airrock)
- **Gépészeti szigetelés** (wired mat)
- **Tűzvédelem** (hardrock, firesafe)
- **Hangszigetelés** (rocksilence)

### 3. Termékoldal azonosítás
- URL pattern alapú felismerés
- Terméknevek alapján
- Breadcrumb navigáció elemzése

## 📊 Adatkinyerés részletei

### Termékadatok struktúra

```python
@dataclass
class ScrapedProduct:
    name: str                    # Termék neve (tisztítva)
    url: str                     # Termék URL-je
    category: str                # Normalizált kategória
    description: str             # Termék leírása
    technical_specs: Dict        # Műszaki specifikációk
    images: List[str]            # Kép URL-ek
    documents: List[str]         # Dokumentum URL-ek
    price: Optional[float]       # Ár (ha elérhető)
    availability: bool           # Elérhetőség
    scraped_at: datetime         # Scraping időpontja
```

### Műszaki specifikációk kinyerése

A scraper különböző helyekről gyűjti a műszaki adatokat:

1. **HTML táblázatok** (`<table>`)
   - Műszaki adatok táblázatok
   - Paraméter-érték párok
   - Egységek kezelése

2. **Definíciós listák** (`<dl>`, `<dt>`, `<dd>`)
   - Strukturált adatok
   - Címke-érték párok

3. **Szöveges feldolgozás**
   - Reguláris kifejezések
   - Mértékegységek normalizálása

### Képek és dokumentumok

**Képek gyűjtése:**
- Termékfotók azonosítása
- Galéria képek
- Műszaki rajzok
- Logo és dekoratív képek kiszűrése

**Dokumentumok:**
- PDF termékadatlapok
- Műszaki útmutatók
- Tanúsítványok
- CAD fájlok

## 🛡️ Adatvalidálás

### Validálási szabályok

1. **Kötelező mezők**
   - Termék név (min 3 karakter)
   - URL (érvényes formátum)
   - Kategória (előre definiált listából)

2. **Adatminőség ellenőrzés**
   - Leírás hossza (min 10 karakter)
   - Gyanús tartalmak kiszűrése
   - URL formátum validálás

3. **Konzisztencia vizsgálat**
   - Kategória-termék megfelelés
   - Műszaki adatok típusok
   - Dátum validálás

### Validálási jelentés

```python
validator = DataValidator()
report = validator.get_validation_report(products)

print(f"Érvényes termékek: {report['summary']['valid']}")
print(f"Sikeres arány: {report['summary']['success_rate']:.1f}%")
print(f"Hiányzó leírások: {report['issues']['missing_descriptions']}")
```

## 🔄 Automatizálás

### 1. Cron job beállítás

```bash
# Naponta egyszer, hajnali 2-kor
0 2 * * * /usr/bin/python3 /path/to/scraper_daily.py

# Hetente egyszer, vasárnap este
0 22 * * 0 /usr/bin/python3 /path/to/scraper_weekly.py
```

### 2. Celery feladatok (fejlesztés alatt)

```python
@celery_app.task
def scheduled_rockwool_scraping():
    scraper = RockwoolScraper()
    products = scraper.scrape_all_products()
    # Adatbázisba mentés...
    return len(products)
```

### 3. Docker környezetben

```yaml
# docker-compose.yml kiegészítés
scraper:
  build: ./backend
  command: python -m app.scraper.scheduled_runner
  environment:
    - SCRAPING_SCHEDULE=daily
  depends_on:
    - db
    - redis
```

## 🧪 Tesztelés

### Automata tesztek futtatása

```bash
# Backend könyvtárban
python -m app.scraper.test_scraper
```

### Tesztelési móddok

1. **Weboldal struktúra teszt**
   - Navigáció feltérképezése
   - Kategóriák azonosítása
   - Termék linkek felderítése

2. **Egyetlen termék teszt**
   - Minta termék scraping-je
   - Adatok validálása
   - Eredmény mentése

3. **Kategória teszt**
   - Korlátozott termékszám
   - Validálási statisztikák
   - Performance mérés

4. **Teljes scraping teszt**
   - Minden kategória (korlátozott)
   - Bulk validálás
   - Eredmények jelentése

## 📈 Performance és optimalizálás

### Rate Limiting stratégia

1. **Alapvető védelem**
   - 2-3 másodperc késleltetés kérések között
   - Maximum 20-30 kérés percenként
   - Exponenciális backoff hibák esetén

2. **Rockwool specifikus**
   - Kategóriák között 1 másodperc várakozás
   - Termékek között 0.5 másodperc
   - IP alapú blokkolás elkerülése

### Memory management

```python
# Nagy adatmennyiség esetén
products = []
for product_url in urls:
    product = scraper._scrape_single_product(product_url)
    if product:
        products.append(product)
    
    # Rendszeres tisztítás
    if len(products) % 100 == 0:
        # Adatbázisba mentés
        save_products_to_db(products)
        products.clear()
```

## 🚨 Hibakezelés

### Gyakori hibák és megoldások

1. **Connection timeout**
   ```python
   # Timeout növelése
   config.timeout = 60
   config.max_retries = 5
   ```

2. **Rate limiting (429 hiba)**
   ```python
   # Lassabb scraping
   config.request_delay = 5.0
   config.max_requests_per_minute = 10
   ```

3. **HTML struktúra változás**
   - ProductParser szelektorok frissítése
   - Új HTML elemek hozzáadása
   - Tesztek újrafuttatása

### Logging és monitoring

```python
import logging

# Részletes logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
```

## 🔮 Jövőbeli fejlesztések

### Rövid távú (1-2 hét)
- [ ] Adatbázis integráció (ScrapedProduct -> Product model)
- [ ] Celery alapú ütemezett feladatok
- [ ] Részletes hibakezelés és retry logika
- [ ] API authentikáció és rate limiting

### Középtávú (1 hónap)
- [ ] Incremental scraping (csak változások)
- [ ] Multi-threading/async scraping
- [ ] Real-time monitoring dashboard
- [ ] Email riasztások hibák esetén

### Hosszú távú (3+ hónap)
- [ ] További gyártók scraped (Isover, Knauf)
- [ ] Machine learning alapú kategorizálás
- [ ] Proxy rotation és IP váltás
- [ ] Distributed scraping (több szerver)

## 📞 Támogatás

### Fejlesztői kapcsolat
- **Projekt:** Lambda.hu Építőanyag AI
- **Fázis:** 2 - Adat-pipeline és Web Scraping
- **Státusz:** Rockwool scraper implementációja kész

### Hibabejelentés
1. Reprodukálható hiba leírása
2. Scraper konfiguráció
3. Log fájlok csatolása
4. Várt vs. tényleges eredmény

### Új funkció kérések
- GitHub issues használata
- Részletes use case leírás
- Priority és timeline megjelölése 