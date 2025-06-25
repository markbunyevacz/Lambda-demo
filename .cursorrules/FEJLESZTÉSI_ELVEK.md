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

## Memory Management és Tanulás
- **Tapasztalatok rögzítése**: Minden jelentős problémamegoldás után memory létrehozása a jövőbeli referenciára.
- **Ismétlődő hibák elkerülése**: Memory ellenőrzés minden hasonló feladat előtt.
- **Folyamatos fejlődés**: Rendszeres visszatekintés és módszertan finomítás.