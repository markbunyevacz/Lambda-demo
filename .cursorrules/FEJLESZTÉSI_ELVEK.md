FEJLESZTÉSI_ELVEK.md (Project Rules for Cursor)

# Lambda.hu Építőanyag AI Projekt - Fejlesztési Szabályok

## Általános Elvek
- Minden kódgenerálásnál és módosításnál vedd figyelembe a projekt teljes kontextusát (`@workspace`).
- A generált kód legyen tiszta, karbantartható és kövesse a "production-ready" elveket. Nincsenek placeholder-ek vagy dummy adatok.
- A "Teljes Rendszerterv" és az "Implementációs Útmutató" dokumentumokban lefektetett technológiai stacket (FastAPI, SQLAlchemy, Scrapy, React/Next.js, LangChain, Celery, PostgreSQL) használd.

## Fejlesztési Metodológia (Tapasztalatok Alapján)
- **Strukturált problémamegoldás**: Minden hibánál vagy feladatnál előbb elemezd a problémát, tervezd meg a megoldást, CSAK AZTÁN kezdj el kódolni.
- **Dokumentálás közben**: Minden jelentős változtatásnál azonnal írd meg a dokumentációt és kommenteket - ez segít átgondolni a megoldást.
- **Verzió kompatibilitás ellenőrzés**: Docker környezetben MINDIG ellenőrizd a függőség verziókat mielőtt implementálnál.
- **Minimális külső függőségek**: Kerüld a felesleges npm/pip csomagokat - egyszerű megoldások előnyben.
- **Tesztelés minden lépésnél**: Ne várj a teljes implementáció végére - tesztelj építés közben.

## Docker és DevOps Elvek (Kritikus Tanulságok)
- **Next.js Docker**: MINDIG `npx next dev` használat a CMD-ben "next: not found" hibák elkerülésére.
- **Függőség konfliktusok**: TypeScript és React verziók harmóniája kritikus - Next.js 14.2.18 + React 18 kombinációt használj.
- **Container építés**: `--no-cache` flag használata problémák esetén, ne csak újraindítsd a service-t.
- **Hibakeresés prioritás**: 
  1. Container logok (`docker-compose logs [service]`)
  2. Függőség verzió ellenőrzés
  3. Dockerfile optimalizálás
  4. Újabb megközelítés keresése
- **Build estratégia**: Egyszerű single-stage Dockerfile fejlesztéshez, multi-stage csak production-ra.

## Kódolási Stílus
- **Python (Backend):**
    - Formázó: `black`
    - Típusellenőrzés (Type Hinting): Kötelező minden függvénydefiníciónál és változónál.
    - API-k: Minden API végponthoz Pydantic séma szükséges a validációhoz.
    - **Dokumentáció**: Minden funkciónál részletes docstring python konvenciókkal.
- **TypeScript (Frontend):**
    - Mód: `Strict mode`
    - Típusok: Explicit `return type`-ok kötelezőek. Minden komponensnek saját `props` interface-szel kell rendelkeznie.
    - Stílus: `Tailwind CSS`-t használj a megadott design tokenekkel.
    - **Komponens dokumentáció**: Minden React komponens tetején komment a funkcióról.

## Fájl- és Elnevezési Konvenciók
- API route-ok: `/backend/app/api/[resource].py`
- Adatbázis modellek: `/backend/app/models/[model].py`
- Service-ek: `/backend/app/services/[service_name]_service.py`
- React komponensek: `/frontend/src/components/[Feature]/[Component].tsx` (PascalCase)
- React hook-ok: `/frontend/src/hooks/use[HookName].ts` (camelCase)

## Hibakezelési Protokoll (Új)
- **Első lépés**: Probléma pontos elemzése és dokumentálása
- **Második lépés**: Lehetséges megoldások brainstormelése
- **Harmadik lépés**: Legegyszerűbb megoldás implementálása
- **Negyedik lépés**: Tesztelés és validálás
- **Ötödik lépés**: Tapasztalatok dokumentálása a jövőre nézve
- **TILTOTT**: Random próbálgatás és többszöri ugyanolyan megközelítés

## Specifikus Projekt Követelmények
- **Nyelv:** Minden felhasználó felé irányuló szöveg, kommentár, log üzenet és hibaüzenet legyen magyar nyelvű.
- **Web Scraping:** Minden scraper az `async/await` patternt kövesse. A hibakezelés és az udvarias késleltetés (`asyncio.sleep`) kötelező.
- **AI Válaszok:** Az AI asszisztens válaszainak formátuma és nyelvezete mindig feleljen meg a `Teljes Rendszerterv`-ben definiált "építészeti szakértői" stílusnak.
- **Adatformátumok:**
    - Az árakat `HUF` pénznemben, `m2`, `db` stb. egységekkel add meg, ahogy a Rendszertervben szerepel.
    - A műszaki paramétereket a normalizált JSONB struktúrában tárold.

## Lambda AI Agent Specification Template

### Általános Agent Architektúra
Minden Lambda.hu AI agent követi az alábbi alapelveket:
- **Autonómia**: Az agent képes önállóan döntést hozni a saját hatókörében
- **Reaktivitás**: Gyorsan reagál a környezet változásaira és eseményekre
- **Proaktivitás**: Nem csak reagál, hanem kezdeményez és tervez előre
- **Szociális képesség**: Kommunikál más agentekkel és szolgáltatásokkal
- **Perzisztencia**: Állapotot tart fenn és tanul a tapasztalatokból

### Agent Típusok és Felelősségek

#### 1. Data Collection Agent (Scraper Agent)
- **Felelősség**: Multi-forrású termékadatok autonóm gyűjtése
- **Technológia**: `async/await`, `aiohttp`, `BeautifulSoup`, `Celery`
- **Helye**: `backend/app/scraper/`
- **API**: `POST /api/scraper/`, `GET /api/scraper/status`
- **Metrikák**: sikeres scraping %, frissítési gyakoriság, adatminőség pontszám

#### 2. Data Processing Agent (Normalization Agent)  
- **Felelősség**: Nyers adatok tisztítása, kategorizálása, normalizálása
- **Technológia**: `pandas`, `fuzzy matching`, `regex`, `LangChain`
- **Helye**: `backend/app/services/data_processing_service.py`
- **API**: `POST /api/data/normalize`, `GET /api/data/validation-report`
- **Metrikák**: feldolgozási sebesség, hibaarány, kategóriazálási pontosság

#### 3. Recommendation Agent (RAG Agent)
- **Felelősség**: Természetes nyelvű kérdések értelmezése és termékajánlások
- **Technológia**: `LangChain`, `ChromaDB`, `OpenAI Embeddings`, `HuggingFace`
- **Helye**: `backend/app/services/ai_service.py`
- **API**: `POST /api/ai/query`, `GET /api/ai/recommendations`
- **Metrikák**: válaszidő, relevancia pontszám, felhasználói elégedettség

#### 4. Price Monitoring Agent
- **Felelősség**: Árváltozások követése, trend elemzés, ajánlatok figyelése
- **Technológia**: `asyncio`, `statistical analysis`, `alerting`
- **Helye**: `backend/app/services/price_monitoring_service.py`
- **API**: `GET /api/prices/trends`, `POST /api/prices/alerts`
- **Metrikák**: árváltozás detektálási pontosság, előrejelzési precizitás

#### 5. Compatibility Agent
- **Felelősség**: Termékkompatibilitás ellenőrzése, rendszerintegritás biztosítása
- **Technológia**: `rule engine`, `graph algorithms`, `constraint solving`
- **Helye**: `backend/app/services/compatibility_service.py`
- **API**: `POST /api/compatibility/check`, `GET /api/compatibility/systems`
- **Metrikák**: kompatibilitási ellenőrzések száma, hibás ajánlások aránya

### Agent Kommunikációs Protokoll

#### Inter-Agent Messaging
```python
# Standard agent üzenet formátum
class AgentMessage:
    source_agent: str          # küldő agent azonosítója
    target_agent: str          # címzett agent(ek)
    message_type: str          # 'request', 'response', 'notification', 'error'
    payload: Dict[str, Any]    # üzenet tartalma
    priority: int              # 1-5 (5 = kritikus)
    correlation_id: str        # kérés-válasz összekapcsolás
    timestamp: datetime
```

#### Event-Driven Communication
- **Redis Pub/Sub**: Valós idejű event streaming agenteknek
- **Celery Queues**: Aszinkron task ütemezés priority queue-kkal
- **WebSocket**: Frontend real-time notifications
- **Database Events**: PostgreSQL triggers agent aktiválására

#### Agent Lifecycle Management
```python
# Agent állapot management
class AgentState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle" 
    WORKING = "working"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"
```

### Agent Teljesítmény Metrikák

#### Core KPI-k minden agenthez:
- **Válaszidő**: átlagos/95. percentilis response time
- **Throughput**: feldolgozott kérések száma/óra
- **Sikerességi arány**: sikeres műveletek / összes művelet
- **Erőforrás-használat**: CPU, memória, network utilizáció
- **Hibaarány**: critical/warning/info szintű hibák száma

#### Specialized Metrics:
- **Scraper Agent**: frissített termékek száma, duplikáció arány, data freshness
- **RAG Agent**: embedding generation speed, similarity search accuracy, hallucination rate
- **Price Agent**: trend prediction accuracy, alert false positive rate

#### Monitoring és Alerting:
```python
# Prometheus metrics exportálás
# Grafana dashboardok minden agenthez
# Slack/email alerts critical küszöbök esetén
# Weekly agent performance reports
```

### Agent Development Guidelines

#### Agent Template Struktúra:
```python
# /backend/app/agents/base_agent.py
class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.agent_id = config.agent_id
        self.state = AgentState.INITIALIZING
        self.metrics_collector = MetricsCollector()
        
    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResult:
        """Főlogika implementálása"""
        pass
        
    async def health_check(self) -> HealthStatus:
        """Agent állapot ellenőrzés"""
        pass
```

#### Agent Tesztelési Protokoll:
- **Unit Tests**: Minden agent core logikájához 90%+ coverage
- **Integration Tests**: Agent kommunikáció és külső szolgáltatások
- **Load Tests**: Teljesítmény tesztelés realistic workload mellett
- **Chaos Engineering**: Resilience testing failure scenarios alatt

#### Agent Deployment:
- **Docker Containers**: Minden agent külön konténerben
- **Health Checks**: Kubernetes/Docker Compose health endpoints
- **Rolling Updates**: Zero-downtime deployment strategy
- **Circuit Breaker**: Failure handling external dependencies felé


## Memory Management és Tanulás
- **Tapasztalatok rögzítése**: Minden jelentős problémamegoldás után memory létrehozása a jövőbeli referenciára.
- **Ismétlődő hibák elkerülése**: Memory ellenőrzés minden hasonló feladat előtt.
- **Folyamatos fejlődés**: Rendszeres visszatekintés és módszertan finomítás.