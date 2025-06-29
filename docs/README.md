# Lambda.hu Építőanyag AI Rendszer

## Projekt Áttekintés

A Lambda.hu egy AI-alapú építőanyag keresési és ajánlási rendszer, amely modern technológiákat használ a felhasználói élmény optimalizálásához.

## Technológiai Stack

### Backend
- **FastAPI** - Modern, gyors Python web framework
- **PostgreSQL** - Relációs adatbázis termék- és kategóriaadatok tárolására
- **Redis** - Cache layer a gyors adateléréshez
- **SQLAlchemy** - ORM az adatbázis műveletekhez

### Frontend  
- **Next.js 14.2.18** - React-alapú frontend framework
- **TypeScript** - Típusbiztos JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React 18** - UI komponens library

### DevOps
- **Docker & Docker Compose** - Konténerizáció és orchestration
- **Node.js 18 Alpine** - Könnyű production environment
- **uv** - Python csomagkezelő

## Projekt Struktúra

```
Lambda/
├── src/                           # Forráskód (backend, frontend)
│   ├── backend/                   # FastAPI alkalmazás
│   └── frontend/                  # Next.js alkalmazás
├── scripts/                       # Segédscriptek (pl. elemzők, tesztelők)
│   ├── archive/                   # Régi, már nem használt scriptek
│   └── ...
├── docs/                          # Projekt dokumentáció
│   ├── README.md                  # Ez a fájl
│   └── ...
├── tools/                         # Külső, fejlesztést segítő eszközök
├── .cursorrules/                  # Cursor AI szabályok
├── .env.example                   # Környezeti változók sablonja
├── docker-compose.yml             # Docker szolgáltatások definíciója
├── pyproject.toml                 # Python projekt és függőségek (uv)
└── uv.lock                        # Rögzített függőségi fa
```

## Telepítés és Futtatás

### Előfeltételek
- Docker & Docker Compose telepítve
- Git telepítve

### Lépések

1. **Projekt klónozása**
```bash
git clone <repository-url>
cd Lambda
```

2. **`.env` fájl létrehozása**
A projekt gyökerében hozz létre egy `.env` fájlt a `.env.example` sablon alapján, és töltsd ki a szükséges értékekkel (API kulcsok, jelszavak).

3. **Docker szolgáltatások indítása**
```bash
docker-compose up --build
```

4. **Szolgáltatások elérése**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API dokumentáció: http://localhost:8000/docs

## Docker Szolgáltatások

### Backend (Port: 8000)
```yaml
backend:
  build: ./src/backend
  ports: ["8000:8000"]
  depends_on: [db, cache]
```

### Frontend (Port: 3000)  
```yaml
frontend:
  build: ./src/frontend
  ports: ["3000:3000"]
```

### PostgreSQL Adatbázis (Port: 5432)
```yaml
db:
  image: postgres:15
  environment:
    POSTGRES_DB: lambda_db
    POSTGRES_USER: lambda_user
    POSTGRES_PASSWORD: your_db_password_here # .env fájlban beállítandó
```

### Redis Cache (Port: 6379)
```yaml
cache:
  image: redis:latest
```

## API Endpoints

### Kategóriák
- `GET /categories` - Összes kategória listázása
- `POST /categories` - Új kategória létrehozása

### Gyártók
- `GET /manufacturers` - Összes gyártó listázása  
- `POST /manufacturers` - Új gyártó létrehozása

### Termékek
- `GET /products` - Termékek listázása
- `POST /products` - Új termék hozzáadása

## Adatbázis Modellek

### Category
- Hierarchikus kategória struktúra
- Self-referencing foreign key a parent_id-val
- Név és leírás mezők

### Manufacturer  
- Gyártó információk
- Kapcsolat termékekkel (one-to-many)
- Elérhetőségi adatok

### Product
- Termék részletek  
- Foreign key kapcsolatok kategóriával és gyártóval
- JSONB technical_specs a rugalmas specifikációkhoz

## Fejlesztési Tapasztalatok

### Problémák és Megoldások

**Frontend Docker Issues:**
- **Probléma**: "next: not found" hiba Next.js 15-tel
- **Megoldás**: Visszatérés Next.js 14.2.18-ra, npx használata
- **Tanulság**: Verzió kompatibilitás kritikus fontosságú

**Függőség Konfliktusok:**
- **Probléma**: lucide-react kompatibilitási problémák  
- **Megoldás**: Emoji ikonok használata egyszerű megoldásként
- **Tanulság**: Külső függőségek minimalizálása ajánlott

## Fejlesztési Alapelvek

1. **Docker First**: Minden szolgáltatás konténerben fut
2. **API First**: RESTful API design FastAPI-val
3. **Type Safety**: TypeScript használata a frontenden
4. **Modern CSS**: Tailwind utility-first megközelítés
5. **Documentation**: Minden változtatás dokumentálása

## Következő Lépések

- [ ] AI chatbot integráció
- [ ] Termék keresési funkciók
- [ ] Felhasználói autentikáció
- [ ] Fejlett szűrési lehetőségek
- [ ] Performance optimalizáció
- [ ] Testing coverage növelése
- [ ] **Celery taskok újraírása** az új scraper architektúrára.

## Hibakeresési Tippek

### Container problémák
```bash
# Logok megtekintése
docker-compose logs [service-name]

# Container újraépítése
docker-compose build --no-cache [service-name]

# Teljes újraindítás
docker-compose down && docker-compose up --build
```

### Frontend hibák
- Next.js verzió ellenőrzése
- Node_modules tisztítása
- Függőség konfliktusok vizsgálata

## 🚀 Új! BrightData MCP Integration

A Lambda demo most már tartalmazza a **BrightData MCP (Model Context Protocol)** integrációt, amely fejlett AI-vezérelt web scraping képességeket biztosít:

### ✨ Új Funkciók

- **🤖 AI-vezérelt scraping** Claude Sonnet 4-gyel
- **🛠️ 18 BrightData tool** (HTML/Markdown scraping, browser automation, stb.)
- **🔒 Captcha megoldás** automatikusan
- **🛡️ Fejlett anti-detection** funkciók
- **🔄 Multi-strategy koordináció** fallback logikával
- **📊 Performance monitoring** és metrics

### 🎯 Scraping Stratégiák

1. **API_ONLY** - Hagyományos Rockwool API (gyors, megbízható)
2. **MCP_ONLY** - Csak BrightData AI scraping (fejlett, gazdag adatok)
3. **API_FALLBACK_MCP** - API először, MCP backup (ajánlott)
4. **MCP_FALLBACK_API** - MCP először, API backup
5. **PARALLEL** - Mindkettő párhuzamosan (leggyorsabb)

### 🔧 Gyors Setup

1. **API kulcsok beszerzése:**
   - [BrightData fiók](https://brdta.com/techwithtim_mcp) (ingyenes kreditek)
   - [Anthropic API kulcs](https://console.anthropic.com)

2. **Környezeti változók (.env):**
   ```bash
   # Hozd létre a .env fájlt az .env.example alapján!
   BRIGHTDATA_API_TOKEN=your-brightdata-token
   ANTHROPIC_API_KEY=your-anthropic-key
   # ...
   ```

3. **Dependencies telepítése:**
   A függőségeket a `uv` automatikusan telepíti a `pyproject.toml` alapján a Docker image építésekor. Manuális telepítésre nincs szükség.

4. **Tesztelés:**
   ```bash
   docker-compose exec backend python -c "from src.backend.app.agents import BrightDataMCPAgent; print('✅ MCP Ready!')"
   ```

### 📚 Részletes Dokumentáció

- [BrightData MCP Setup Guide](docs/BRIGHTDATA_MCP_SETUP_DOCUMENTATION.md)
- [AI Agent Specification](.cursorrules/FEJLESZTÉSI_ELVEK.mdc)
- [Scraper API Documentation](src/backend/app/scraper/README.md)

### 🎮 Demo Használat

```python
from src.backend.app.agents import BrightDataMCPAgent, ScrapingCoordinator

# AI scraping
agent = BrightDataMCPAgent()
products = await agent.scrape_rockwool_with_ai(["https://www.rockwool.hu"])

# Koordinált scraping
coordinator = ScrapingCoordinator(strategy="api_fallback_mcp")
results = await coordinator.scrape_products(max_products=10)
```

## Eredeti Demo Funkciók

---

**Verzió**: 1.0.0  
**Utolsó frissítés**: 2025-01-25  
**Fejlesztő**: Lambda.hu AI Team 