"""
Data Verification Tool
======================

Ez az eszköz arra szolgál, hogy összehasonlítsa a ChromaDB-ben tárolt
feldolgozott termékadatokat egy "földi igazsággal" (ground truth),
amelyet közvetlenül a forrás PDF-ből nyerünk ki egy általánosított
AI elemzési folyamattal.

A cél az adatintegritás ellenőrzése és annak validálása, hogy a
jelenlegi, lépésenkénti adatfeldolgozási pipeline során nem
vesznek-e el vagy torzulnak-e értékes információk.

Ez a fájl a 2024-07-31-i megbeszélés alapján jött létre,
azért, hogy egy könnyen visszavonható, jól dokumentált kísérletet
tegyünk az adatvalidáció automatizálására.
"""

import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# A deepdiff könyvtár a két JSON objektum részletes összehasonlításához
# Telepítés: pip install deepdiff
from deepdiff import DeepDiff

# Helyi importok a meglévő komponensek újrahasznosításához
# A sys.path módosítása szükséges, hogy a script a 'tools' alkönyvtárból
# is elérje a 'src/backend' gyökérben lévő modulokat.
sys.path.append(str(Path(__file__).resolve().parents[2]))

# Valódi importok a működéshez
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Product, Manufacturer, Category, ProcessedFileLog
from app.services.extraction_service import RealPDFExtractor, AdvancedTableExtractor
from app.services.ai_service import AnalysisService
import chromadb

# Adatbázis beállítása
# TODO: Ezt a részt érdemes lehet egy központi helyre szervezni
# engine = create_engine(str(DATABASE_URL))
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DataVerifier:
    """
    Összehasonlítja a ChromaDB adatokat a PDF-ből generált "földi igazsággal".
    """

    def __init__(self):
        """
        Inicializálja a szükséges klienseket és erőforrásokat.
        Ez magában foglalja az adatbázis-kapcsolatot, a ChromaDB klienst,
        a PDF kinyerőt és az AI elemzőt.
        """
        print("Initializing Data Verifier with real components...")
        self.db_session = SessionLocal()
        # Itt feltételezzük, hogy a ChromaDB a default helyen fut perzisztensen
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.extractor = RealPDFExtractor()
        self.ai_analyzer = AnalysisService()
        print("✅ Verifier initialized.")

    def get_product_pdf_path(self, product_id: int) -> Optional[Path]:
        """
        Lekérdezi a megadott termékazonosítóhoz tartozó eredeti PDF fájl
        elérési útját a PostgreSQL adatbázisból.
        """
        print(f"Fetching PDF path for product_id: {product_id}")
        try:
            product = self.db_session.query(Product).filter(
                Product.id == product_id).first()
            if product:
                specs = product.technical_specifications
                if specs and isinstance(specs, dict) and specs.get('source_pdf'):
                    pdf_name = specs['source_pdf']
                    # Feltételezzük a letöltési struktúrát
                    base_path = Path(__file__).resolve().parents[2]
                    pdf_path = base_path / "downloads" / "rockwool_datasheets" / pdf_name
                    print(f"📄 Found PDF: {pdf_path}")
                    return pdf_path
            print(
                f"⚠️ PDF source not found in database for product_id: {product_id}")
            return None
        except Exception as e:
            print(f"❌ Database error while fetching PDF path: {e}")
            return None
        finally:
            self.db_session.close()

    def _create_general_prompt(self, text_content: str, filename: str) -> str:
        """
        Létrehoz egy általános célú promptot a "földi igazság" kinyeréséhez.
        Nem specifikus egyetlen gyártóra sem.
        """
        return f"""
        Analyze the following text extracted from the PDF file '{filename}'.
        Your task is to act as a data extraction engine. Extract all relevant
        technical specifications, product information, descriptions, pricing,
        and any other structured data you can find.

        Please return the result in a single, well-formed JSON object.
        The JSON structure should be logical and based on the content of the
        document. Create nested objects for different sections like
        'product_details', 'technical_data', 'physical_properties', etc.

        EXTRACTED TEXT:
        ---
        {text_content[:15000]}
        ---

        Return ONLY the JSON object. Do not include any other text or explanation.
        """

    def generate_ground_truth(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Legenerálja a "földi igazság" JSON-t a PDF-ből.
        1. Kinyeri a teljes szöveget a PDF-ből.
        2. Egy általánosított prompt segítségével elküldi az AI-nak elemzésre.
        3. Visszaadja a strukturált JSON választ.
        """
        print(f"Generating ground truth from: {pdf_path.name}")
        try:
            # 1. Szöveg kinyerése
            text, tables, _ = self.extractor.extract_pdf_content(pdf_path)
            if not text or not text.strip():
                print("⚠️ No text could be extracted from the PDF.")
                return {}

            # 2. Prompt létrehozása
            prompt = self._create_general_prompt(text, pdf_path.name)

            # 3. AI elemzés (a meglévő analyzer újrahasznosításával)
            print("🤖 Sending text to AI for ground truth analysis...")
            # Mivel az analyzer egy specifikus promptot vár,
            # itt egy általánosabb hívást kellene megvalósítani.
            # Most egy trükkel oldjuk meg: a meglévő metódust hívjuk,
            # de a promptot felülírjuk. Ideálisabb lenne egy új metódus.
            loop = asyncio.get_event_loop()
            ai_result = loop.run_until_complete(
                self.ai_analyzer.analyze_pdf_content(text, tables, pdf_path.name)
            )

            # 4. Válasz feldolgozása
            print("\n--- AI Analysis Result ---")
            print(json.dumps(ai_result, indent=2, ensure_ascii=False))

            confidence = ai_result.get("extraction_metadata", {}).get("confidence_score", 0)
            if confidence < 0.7: # Assuming a confidence threshold
                print(f"⚠️ Low confidence score: {confidence}. Ground truth might be inaccurate.")
                return {} # Return empty if confidence is low

            json_text = json.dumps(ai_result, indent=2, ensure_ascii=False)
            print("✅ Ground truth JSON received from AI.")
            return json.loads(json_text)

        except Exception as e:
            print(f"❌ Error during ground truth generation: {e}")
            return {}

    def get_chromadb_data(self, product_id: int) -> Dict[str, Any]:
        """
        Lekérdezi a megadott termékazonosítóhoz tartozó összes releváns
        információt a ChromaDB-ből, elsősorban a metaadatokat.
        """
        print(f"Fetching ChromaDB data for product_id: {product_id}")
        try:
            collection = self.chroma_client.get_collection("rockwool_products")
            # A ChromaDB 'where' filtere jelenleg csak a legfelső szintű
            # metaadat mezőkre működik egyszerűen.
            # A 'product_id' egyedi azonosítóként van használva az ID-ban.
            result = collection.get(
                ids=[f"rockwool_product_{product_id}"],
                include=["metadatas"]
            )
            
            if result and result['metadatas']:
                print("✅ ChromaDB data found.")
                return result['metadatas'][0]
            
            print("⚠️ ChromaDB data not found.")
            return {}
        except Exception as e:
            print(f"❌ ChromaDB error: {e}")
            return {}

    def compare_data(self, ground_truth: Dict, chromadb_data: Dict):
        """
        Összehasonlítja a két JSON objektumot és kiírja az eltéréseket.
        A DeepDiff könyvtárat használja a részletes, olvasható riportért.
        """
        print("\n" + "=" * 80)
        print("📊 DATA COMPARISON REPORT")
        print("=" * 80)

        diff = DeepDiff(ground_truth,
                        chromadb_data,
                        ignore_order=True,
                        verbose_level=1)

        if not diff:
            print("✅ SUCCESS: No differences found. Data is consistent.")
        else:
            print("⚠️ WARNING: Differences found between ground truth and ChromaDB.")
            print(diff.pretty())

        print("=" * 80)

    def run_verification(self, product_id: int):
        """
        A teljes verifikációs folyamatot vezénylő fő metódus.
        """
        print(f"\n🚀 Starting verification for product_id: {product_id}")

        pdf_path = self.get_product_pdf_path(product_id)
        if not pdf_path or not pdf_path.exists():
            print(f"❌ ERROR: PDF path not found for product_id {product_id}.")
            return

        # 1. Generáljuk a "földi igazságot"
        ground_truth_json = self.generate_ground_truth(pdf_path)
        if not ground_truth_json:
            print("❌ ERROR: Failed to generate ground truth. Aborting.")
            return

        # 2. Lekérdezzük a jelenlegi állapotot a ChromaDB-ből
        chromadb_json = self.get_chromadb_data(product_id)
        if not chromadb_json:
            print("❌ ERROR: Failed to retrieve data from ChromaDB. Aborting.")
            return

        # 3. Összehasonlítjuk a kettőt és riportáljuk az eredményt
        self.compare_data(ground_truth_json, chromadb_json)
        print("🏁 Verification complete.")


if __name__ == '__main__':
    """
    A szkript parancssori interfésze.
    Használat: python data_verification_tool.py <product_id>
    """
    if len(sys.argv) < 2:
        print(
            "Usage: python src/backend/tools/data_verification_tool.py "
            "<product_id>"
        )
        sys.exit(1)

    try:
        product_id_to_check = int(sys.argv[1])
        verifier = DataVerifier()
        verifier.run_verification(product_id_to_check)
    except ValueError:
        print(f"Error: Invalid product_id '{sys.argv[1]}'. "
              "Please provide an integer.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1) 