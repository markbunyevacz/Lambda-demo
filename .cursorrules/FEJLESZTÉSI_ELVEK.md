FEJLESZTÉSI_ELVEK.md (Project Rules for Cursor)

# Lambda.hu Építőanyag AI Projekt - Fejlesztési Szabályok

## Általános Elvek
- Minden kódgenerálásnál és módosításnál vedd figyelembe a projekt teljes kontextusát (`@workspace`).
- A generált kód legyen tiszta, karbantartható és kövesse a "production-ready" elveket. Nincsenek placeholder-ek vagy dummy adatok.
- A "Teljes Rendszerterv" és az "Implementációs Útmutató" dokumentumokban lefektetett technológiai stacket (FastAPI, SQLAlchemy, Scrapy, React/Next.js, LangChain, Celery, PostgreSQL) használd.

## Kódolási Stílus
- **Python (Backend):**
    - Formázó: `black`
    - Típusellenőrzés (Type Hinting): Kötelező minden függvénydefiníciónál és változónál.
    - API-k: Minden API végponthoz Pydantic séma szükséges a validációhoz.
- **TypeScript (Frontend):**
    - Mód: `Strict mode`
    - Típusok: Explicit `return type`-ok kötelezőek. Minden komponensnek saját `props` interface-szel kell rendelkeznie.
    - Stílus: `Tailwind CSS`-t használj a megadott design tokenekkel.

## Fájl- és Elnevezési Konvenciók
- API route-ok: `/backend/app/api/[resource].py`
- Adatbázis modellek: `/backend/app/models/[model].py`
- Service-ek: `/backend/app/services/[service_name]_service.py`
- React komponensek: `/frontend/src/components/[Feature]/[Component].tsx` (PascalCase)
- React hook-ok: `/frontend/src/hooks/use[HookName].ts` (camelCase)

## Specifikus Projekt Követelmények
- **Nyelv:** Minden felhasználó felé irányuló szöveg, kommentár, log üzenet és hibaüzenet legyen magyar nyelvű.
- **Web Scraping:** Minden scraper az `async/await` patternt kövesse. A hibakezelés és az udvarias késleltetés (`asyncio.sleep`) kötelező.
- **AI Válaszok:** Az AI asszisztens válaszainak formátuma és nyelvezete mindig feleljen meg a `Teljes Rendszerterv`-ben definiált "építészeti szakértői" stílusnak.
- **Adatformátumok:**
    - Az árakat `HUF` pénznemben, `m2`, `db` stb. egységekkel add meg, ahogy a Rendszertervben szerepel.
    - A műszaki paramétereket a normalizált JSONB struktúrában tárold.