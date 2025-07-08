import shutil
import hashlib
from pathlib import Path
import logging


# --- Konfiguráció ---
# A szkript gyökeréhez képesti relatív útvonalak
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "src" / "backend" / "src" / "downloads"
TARGET_DIR_NAME = "leier_final_pdfs"
TARGET_DIR = DOWNLOADS_DIR / TARGET_DIR_NAME
LOG_FILE = BASE_DIR / "leier_consolidation_log.txt"

# --- Logger beállítása ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def get_file_hash(path: Path) -> str:
    """Egy fájl tartalmának SHA256 hash-ét adja vissza."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            # Olvasás darabokban, hogy nagy fájlokkal is működjön
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    """
    Összegyűjti a Leier PDF-eket egy könyvtárba, és eltávolítja a duplikátumokat.
    """
    logging.info(
        "--- Leier PDF konszolidáció és duplikátum szűrés elindult ---"
    )

    if not DOWNLOADS_DIR.exists() or not DOWNLOADS_DIR.is_dir():
        logging.error(f"A forrás könyvtár nem található: {DOWNLOADS_DIR}")
        return

    # Célkönyvtár létrehozása, ha nem létezik
    TARGET_DIR.mkdir(exist_ok=True)
    logging.info(f"Célkönyvtár: {TARGET_DIR}")

    # Leier könyvtárak megkeresése
    leier_dirs = [
        d for d in DOWNLOADS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("leier")
        and d.name != TARGET_DIR_NAME
    ]

    if not leier_dirs:
        logging.warning(
            "Nem található 'leier' kezdetű könyvtár a feldolgozáshoz."
        )
        logging.info("--- Folyamat befejezve ---")
        return

    dir_names = [str(d.relative_to(BASE_DIR)) for d in leier_dirs]
    logging.info(f"Feldolgozásra váró Leier könyvtárak: {dir_names}")

    processed_hashes = set()
    total_files_found = 0
    copied_files_count = 0
    duplicate_files_count = 0

    for leier_dir in leier_dirs:
        logging.info(f"--- Feldolgozás alatt: {leier_dir.name} ---")
        pdf_files = list(leier_dir.rglob("*.pdf"))

        if not pdf_files:
            logging.info("Nem található PDF fájl ebben a könyvtárban.")
            continue

        for pdf_path in pdf_files:
            total_files_found += 1
            try:
                file_hash = get_file_hash(pdf_path)

                if file_hash in processed_hashes:
                    msg = (
                        f"DUPLIKÁTUM: '{pdf_path.name}' a(z) "
                        f"'{leier_dir.name}' könyvtárból már "
                        f"feldolgozásra került. Kihagyva."
                    )
                    logging.warning(msg)
                    duplicate_files_count += 1
                else:
                    processed_hashes.add(file_hash)
                    destination_path = TARGET_DIR / pdf_path.name

                    # Névütközés kezelése
                    counter = 1
                    while destination_path.exists():
                        new_name = f"{pdf_path.stem}_{counter}{pdf_path.suffix}"
                        destination_path = TARGET_DIR / new_name
                        logging.warning(
                            f"NÉVÜTKÖZÉS: '{pdf_path.name}' már létezik. "
                            f"Új név: '{destination_path.name}'"
                        )
                        counter += 1

                    shutil.copy2(pdf_path, destination_path)
                    copied_files_count += 1
                    dest_rel_path = destination_path.relative_to(BASE_DIR)
                    logging.info(
                        f"ÁTMÁSOLVA: '{pdf_path.name}' -> '{dest_rel_path}'"
                    )

            except Exception as e:
                logging.error(
                    f"Hiba a(z) '{pdf_path}' fájl feldolgozása közben: {e}"
                )

    logging.info("\n--- ÖSSZEGZÉS ---")
    logging.info(f"Összesen talált PDF fájl: {total_files_found}")
    logging.info(f"Egyedi fájlok átmásolva: {copied_files_count}")
    logging.info(f"Kiszűrt duplikátumok: {duplicate_files_count}")
    target_rel_path = TARGET_DIR.relative_to(BASE_DIR)
    logging.info(
        f"Az egyedi fájlok a '{target_rel_path}' könyvtárban "
        f"találhatóak."
    )
    logging.info(
        "\nJavaslat: Ellenőrizd a célkönyvtárat, majd manuálisan töröld "
        "a következő könyvtárakat, ha már nincs rájuk szükség:"
    )
    for d in leier_dirs:
        logging.info(f" - {d.relative_to(BASE_DIR)}")

    logging.info("--- Folyamat sikeresen befejezve ---")


if __name__ == "__main__":
    main() 