# Archív - Régi Verziók

## FEJLESZTÉSI_ELVEK_original.mdc
- **Dátum**: 2025-06-29 18:52
- **Méret**: 14,974 bytes
- **Leírás**: Az eredeti, átstrukturálás előtti verzió
- **Tartalom**: 
  - Duplikációkkal és átfedésekkel
  - Nem strukturált felépítés
  - AI Agent specifikációk teljes részletességgel
  - Vegyes sorrendű fejezetek

## FEJLESZTÉSI_BACKLOG_original.mdc
- **Dátum**: 2025-06-29 19:02
- **Méret**: 9,467 bytes
- **Leírás**: Az eredeti backlog, átstrukturálás előtti verzió
- **Tartalom**:
  - Fázisok kronológiai sorrendben
  - Részletes evidence és tested információk minden modulnál
  - Summary status a végén
  - Kevésbé strukturált navigáció

## Miért kerültek archívba?
- **2025-06-29**: Teljes átstrukturálás és logikai átrendezés mindkét fájlnál
- **Cél**: 
  - **ELVEK**: Duplikációk megszüntetése, logikus sorrend, szabályok vs implementációk szétválasztása
  - **BACKLOG**: Tartalomjegyzék, státusz kategóriák, jobb csoportosítás
- **Eredmény**: 
  - **ELVEK**: 8 fő fejezet, szabályok és elvek fókusz
  - **BACKLOG**: 6 fő fejezet, implementációs tervek és TODO-k fókusz

## Visszaállítás
Ha szükség lenne a régi verziókra:
```bash
# Fejlesztési elvek visszaállítása
cp .cursorrules_archiv/FEJLESZTÉSI_ELVEK_original.mdc .cursorrules/FEJLESZTÉSI_ELVEK.mdc

# Fejlesztési backlog visszaállítása  
cp .cursorrules_archiv/FEJLESZTÉSI_BACKLOG_original.mdc .cursorrules/FEJLESZTÉSI_BACKLOG.mdc
```

## Fájl Méretek Összehasonlítás
| Fájl | Eredeti | Új | Változás |
|------|---------|----|---------| 
| FEJLESZTÉSI_ELVEK.mdc | 14,974 bytes | ~9,200 bytes | -38% (kompaktabb) |
| FEJLESZTÉSI_BACKLOG.mdc | 9,467 bytes | ~11,500 bytes | +22% (bővebb agent backlog) |

---
*Archív frissítve: 2025-06-29 19:02* 