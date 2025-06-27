# BrightData MCP Integration - Setup & Használat

## Áttekintés

A Lambda demo BrightData MCP integrációja fejlett AI-vezérelt web scraping képességeket ad hozzá a meglévő Rockwool scraper rendszerhez. Ez az integráció lehetővé teszi:

- **18 BrightData scraping tool** használatát
- **AI-vezérelt adatgyűjtést** Claude-dal
- **Captcha megoldást** automatikusan
- **Fejlett anti-detection** funkciókat
- **Fallback logikát** a tradicionális API scraper és AI scraper között

## Előfeltételek

### 1. Szoftver Követelmények
- Node.js 20.x+ (MCP szerver)
- Python 3.8+ (AI agent)
- Docker (Lambda demo környezet)

### 2. API Kulcsok Beszerzése

#### BrightData Fiók
1. Regisztrálj a [BrightData oldalon](https://brdta.com/techwithtim_mcp) (ingyenes kreditek)
2. Menj a **User Dashboard → Proxies and Scraping → Add**
3. Hozz létre **Web Unlocker API**-t:
   - Név: `web_unlocker` (aláhúzással!)
   - Captcha solver: Engedélyezve
   - Másolj ki az API tokent
4. Hozz létre **Browser API**-t (opcionális):
   - Név: `scraping_browser` (aláhúzással!)
   - Másold ki a connection stringet

#### Anthropic API
1. Menj a [console.anthropic.com](https://console.anthropic.com) oldalra
2. Hozz létre API kulcsot
3. Másold ki az API kulcsot

## Telepítés

### 1. Python Dependencies
```bash
cd backend
pip install langchain langchain-anthropic langchain-mcp-adapters langgraph mcp httpx-sse
```

### 2. Node.js MCP Szerver
```bash
# BrightData MCP szerver telepítése (automatikus NPX-el)
npx -y @brightdata/mcp
```

### 3. Környezeti Változók Konfigurálás

Hozd létre vagy frissítsd a `.env` fájlt:

```bash
# Meglévő Lambda konfiguráció
DATABASE_URL=postgresql://admin:admin123@postgres:5432/lambda_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
DEBUG=False
ENVIRONMENT=production

# BrightData MCP Konfiguráció
BRIGHTDATA_API_TOKEN=your-token-here
BRIGHTDATA_WEB_UNLOCKER_ZONE=web_unlocker
BRIGHTDATA_BROWSER_AUTH=your-browser-connection-string-here

# Anthropic API (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-REAL-KEY-HERE

# MCP Konfiguráció
MCP_SERVER_TIMEOUT=60
MCP_MAX_RETRIES=3
```

## Használat

### 1. Celery Task-okkal

#### BrightData MCP Kapcsolat Teszt
```python
from app.celery_tasks.brightdata_tasks import test_brightdata_mcp_connection

# Celery task indítása
result = test_brightdata_mcp_connection.delay()
print(result.get())
```

#### AI-vezérelt Scraping
```python
from app.celery_tasks.brightdata_tasks import ai_powered_rockwool_scraping

# Konkrét URL-ek scraping-je
target_urls = [
    "https://www.rockwool.hu/termekek/",
    "https://www.rockwool.hu/rockton/"
]

result = ai_powered_rockwool_scraping.delay(
    target_urls=target_urls,
    max_products=10,
    save_to_database=True
)

scraping_result = result.get()
print(f"Scraped products: {scraping_result['scraped_products']}")
```

#### Koordinált Scraping (Fallback logikával)
```python
from app.celery_tasks.brightdata_tasks import coordinated_scraping_with_fallback

# API-first stratégia MCP fallback-kel
result = coordinated_scraping_with_fallback.delay(
    strategy="api_fallback_mcp",
    max_products=15
)

coord_result = result.get()
print(f"Strategy used: {coord_result['strategy_used']}")
print(f"Total products: {coord_result['total_products']}")
```

### 2. Közvetlen Agent Használat

```python
import asyncio
from app.agents import BrightDataMCPAgent, ScrapingCoordinator

async def demo_usage():
    # BrightData MCP Agent
    agent = BrightDataMCPAgent()
    
    # Kapcsolat teszt
    connection = await agent.test_mcp_connection()
    print(f"MCP Available: {connection['success']}")
    
    # AI scraping
    urls = ["https://www.rockwool.hu/termekek/"]
    products = await agent.scrape_rockwool_with_ai(urls)
    print(f"AI scraped: {len(products)} products")
    
    # Koordinált scraping
    coordinator = ScrapingCoordinator()
    test_results = await coordinator.test_all_scrapers()
    print(f"Recommended strategy: {test_results['coordination']['recommended_strategy']}")

# Futtatás
asyncio.run(demo_usage())
```

### 3. Demo Script-el

```bash
cd backend
python run_demo_scrape.py
```

A demo script automatikusan futtatja:
- Hagyományos API scraping demo
- BrightData MCP demo (ha elérhető)
- Koordinált scraping demo

## Scraping Stratégiák

### 1. API_ONLY
- Csak hagyományos Rockwool API scraping
- Gyors, megbízható PDF adatlapok
- Korlátozott adatfajták

### 2. MCP_ONLY
- Csak BrightData MCP AI scraping
- Fejlett web navigálás
- Captcha megoldás
- Nagyobb adatgazdagság

### 3. API_FALLBACK_MCP (Alapértelmezett)
- Elsődlegesen API scraping
- Ha sikertelen vagy kevés adat → MCP fallback
- Optimális megbízhatóság

### 4. MCP_FALLBACK_API
- Elsődlegesen MCP scraping
- Ha sikertelen → API fallback
- Maximális adatgazdagság

### 5. PARALLEL
- Mindkét módszer párhuzamosan
- Eredmények kombinálása
- Leggyorsabb, legtöbb adat

## Hibaelhárítás

### Gyakori Problémák

#### 1. "MCP dependencies hiányoznak"
```bash
pip install langchain langchain-anthropic langchain-mcp-adapters langgraph mcp
```

#### 2. "BrightData MCP agent nem elérhető"
- Ellenőrizd a környezeti változókat
- Bizonyosodj meg, hogy Node.js telepítve van
- Teszteld az API kulcsokat

#### 3. "Claude modell inicializálás sikertelen"
- Ellenőrizd az `ANTHROPIC_API_KEY` értékét
- Bizonyosodj meg, hogy van kreditegyenleg

#### 4. "npx command not found"
- Telepítsd a Node.js-t
- Windows-on: `winget install OpenJS.NodeJS`
- Vagy töltsd le: https://nodejs.org

### Debug Módok

#### 1. Kapcsolat Teszt
```python
from app.celery_tasks.brightdata_tasks import test_brightdata_mcp_connection
result = test_brightdata_mcp_connection.delay().get()
print(result)
```

#### 2. Scraper Elérhetőség
```python
from app.celery_tasks.brightdata_tasks import test_all_scraping_methods
result = test_all_scraping_methods.delay().get()
print(result['summary'])
```

#### 3. Verbose Logging
```python
import logging
logging.getLogger('app.agents').setLevel(logging.DEBUG)
```

## Performance Összehasonlítás

| Módszer | Sebesség | Adatgazdagság | Megbízhatóság | Captcha |
|---------|----------|---------------|---------------|---------|
| API Only | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| MCP Only | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ |
| API→MCP | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ |
| Parallel | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ |

## Költségek

- **BrightData**: Ingyenes kreditek regisztrációnál
- **Anthropic**: Claude API használat alapján
- **Lambda Demo**: Ingyenes (saját infrastruktúra)

## Biztonsági Megjegyzések

- API kulcsokat sosem commitold
- Használj environment változókat
- BrightData tokeneket rotáld rendszeresen
- Monitor API használatot

## További Információk

- [BrightData MCP Documentation](https://docs.brightdata.com/mcp)
- [Claude API Limits](https://docs.anthropic.com/claude/docs/rate-limits)
- [Lambda Demo Repository](../../README.md)

# Setup API keys in .env:
BRIGHTDATA_API_TOKEN=your-token-here
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-REAL-KEY-HERE

# Test AI scraping
docker-compose exec backend python -c "
import asyncio
from app.agents import BrightDataMCPAgent
async def test(): 
    agent = BrightDataMCPAgent()
    result = await agent.test_mcp_connection()
    print(f'MCP Status: {result}')
asyncio.run(test())
" 