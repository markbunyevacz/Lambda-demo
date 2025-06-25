"""
Database Integration - Scraped adatok mentése adatbázisba

Ez a modul kezeli a ScrapedProduct adatok mentését a Lambda.hu
adatbázis struktúrájába a megfelelő mappelésekkel és validálásokkal.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models.product import Product
from ..models.manufacturer import Manufacturer
from ..models.category import Category
from .rockwool_scraper import ScrapedProduct
from .category_mapper import CategoryMapper

logger = logging.getLogger(__name__)


class DatabaseIntegration:
    """
    Scraped adatok adatbázis integrációja
    
    Funkcionalitás:
    - ScrapedProduct → Product modell mappelés
    - Gyártók és kategóriák automatikus kezelése
    - Duplikátumok elkerülése
    - Bulk mentési műveletek
    - Hibaellenálló adatmentés
    """
    
    def __init__(self, db_session: Session = None):
        self.db = db_session
        self.category_mapper = CategoryMapper()
        
        # Cache a gyakran használt objektumokhoz
        self._manufacturer_cache: Dict[str, Manufacturer] = {}
        self._category_cache: Dict[str, Category] = {}
        
        # Statisztikák
        self.stats = {
            'products_created': 0,
            'products_updated': 0,
            'products_skipped': 0,
            'errors': 0
        }
    
    def get_db_session(self) -> Session:
        """Adatbázis session lekérése"""
        if self.db is None:
            self.db = next(get_db())
        return self.db
    
    def ensure_manufacturer(self, manufacturer_name: str) -> Manufacturer:
        """
        Gyártó biztosítása az adatbázisban
        
        Args:
            manufacturer_name: Gyártó neve
            
        Returns:
            Manufacturer objektum
        """
        # Cache ellenőrzés
        if manufacturer_name in self._manufacturer_cache:
            return self._manufacturer_cache[manufacturer_name]
        
        db = self.get_db_session()
        
        # Keresés az adatbázisban
        manufacturer = db.query(Manufacturer).filter(
            Manufacturer.name == manufacturer_name
        ).first()
        
        if not manufacturer:
            # Új gyártó létrehozása
            manufacturer_data = self._get_manufacturer_data(manufacturer_name)
            manufacturer = Manufacturer(
                name=manufacturer_name,
                description=manufacturer_data.get('description'),
                website=manufacturer_data.get('website'),
                country=manufacturer_data.get('country'),
                logo_url=manufacturer_data.get('logo_url')
            )
            
            try:
                db.add(manufacturer)
                db.commit()
                db.refresh(manufacturer)
                logger.info(f"Új gyártó létrehozva: {manufacturer_name}")
            except IntegrityError:
                db.rollback()
                # Újra keresés, ha közben más thread létrehozta
                manufacturer = db.query(Manufacturer).filter(
                    Manufacturer.name == manufacturer_name
                ).first()
        
        # Cache-be mentés
        self._manufacturer_cache[manufacturer_name] = manufacturer
        return manufacturer
    
    def ensure_category(self, category_name: str) -> Category:
        """
        Kategória biztosítása az adatbázisban
        
        Args:
            category_name: Kategória neve
            
        Returns:
            Category objektum
        """
        # Cache ellenőrzés
        if category_name in self._category_cache:
            return self._category_cache[category_name]
        
        db = self.get_db_session()
        
        # Keresés az adatbázisban
        category = db.query(Category).filter(
            Category.name == category_name
        ).first()
        
        if not category:
            # Új kategória létrehozása
            category_data = self._get_category_data(category_name)
            category = Category(
                name=category_name,
                description=category_data.get('description'),
                parent_id=category_data.get('parent_id'),
                level=category_data.get('level', 0),
                sort_order=category_data.get('sort_order', 0),
                is_active=1
            )
            
            try:
                db.add(category)
                db.commit()
                db.refresh(category)
                logger.info(f"Új kategória létrehozva: {category_name}")
            except IntegrityError:
                db.rollback()
                # Újra keresés
                category = db.query(Category).filter(
                    Category.name == category_name
                ).first()
        
        # Cache-be mentés
        self._category_cache[category_name] = category
        return category
    
    def generate_sku(self, scraped_product: ScrapedProduct) -> str:
        """
        SKU generálása a scraped termékhez
        
        Args:
            scraped_product: ScrapedProduct objektum
            
        Returns:
            Egyedi SKU string
        """
        # URL alapú hash generálás (konzisztens SKU)
        url_hash = hashlib.md5(scraped_product.url.encode()).hexdigest()[:8]
        
        # Gyártó prefix
        manufacturer_prefix = "ROCK"  # Rockwool
        
        # Kategória alapú prefix
        category_prefixes = {
            'Tetőszigetelés': 'TR',
            'Homlokzati hőszigetelés': 'HH',
            'Padlószigetelés': 'PS',
            'Válaszfal szigetelés': 'VS',
            'Gépészeti szigetelés': 'GS',
            'Tűzvédelem': 'TV',
            'Hangszigetelés': 'HS',
            'Általános szigetelés': 'AS'
        }
        
        category_prefix = category_prefixes.get(scraped_product.category, 'XX')
        
        return f"{manufacturer_prefix}-{category_prefix}-{url_hash.upper()}"
    
    def map_scraped_to_product(self, scraped_product: ScrapedProduct) -> Dict:
        """
        ScrapedProduct mappelése Product modell adataira
        
        Args:
            scraped_product: ScrapedProduct objektum
            
        Returns:
            Dict a Product modell adataival
        """
        # Gyártó és kategória objektumok
        manufacturer = self.ensure_manufacturer("ROCKWOOL")
        category = self.ensure_category(scraped_product.category)
        
        # SKU generálás
        sku = self.generate_sku(scraped_product)
        
        # Műszaki specifikációk normalizálása
        normalized_specs, raw_specs = self._normalize_technical_specs(
            scraped_product.technical_specs
        )
        
        return {
            'name': scraped_product.name,
            'description': scraped_product.description,
            'sku': sku,
            'manufacturer_id': manufacturer.id,
            'category_id': category.id,
            'price': scraped_product.price,
            'currency': 'HUF',
            'unit': self._extract_unit_from_specs(normalized_specs),
            'technical_specs': normalized_specs,
            'raw_specs': raw_specs,
            'images': scraped_product.images,
            'documents': scraped_product.documents,
            'source_url': scraped_product.url,
            'scraped_at': scraped_product.scraped_at,
            'is_active': True,
            'in_stock': scraped_product.availability
        }
    
    def save_scraped_product(self, scraped_product: ScrapedProduct) -> Tuple[Product, bool]:
        """
        Egyetlen scraped termék mentése adatbázisba
        
        Args:
            scraped_product: ScrapedProduct objektum
            
        Returns:
            Tuple[Product, bool]: (Product objektum, új termék volt-e)
        """
        db = self.get_db_session()
        
        try:
            # Termék keresése URL alapján (duplikátum ellenőrzés)
            existing_product = db.query(Product).filter(
                Product.source_url == scraped_product.url
            ).first()
            
            # Product adatok mappelése
            product_data = self.map_scraped_to_product(scraped_product)
            
            if existing_product:
                # Meglévő termék frissítése
                for key, value in product_data.items():
                    if key not in ['sku']:  # SKU-t ne írjuk felül
                        setattr(existing_product, key, value)
                
                existing_product.updated_at = datetime.now()
                
                db.commit()
                db.refresh(existing_product)
                
                self.stats['products_updated'] += 1
                logger.debug(f"Termék frissítve: {existing_product.name}")
                return existing_product, False
            
            else:
                # Új termék létrehozása
                new_product = Product(**product_data)
                
                db.add(new_product)
                db.commit()
                db.refresh(new_product)
                
                self.stats['products_created'] += 1
                logger.debug(f"Új termék létrehozva: {new_product.name}")
                return new_product, True
                
        except Exception as e:
            db.rollback()
            self.stats['errors'] += 1
            logger.error(f"Hiba a termék mentésénél {scraped_product.url}: {e}")
            raise
    
    def save_scraped_products_bulk(self, scraped_products: List[ScrapedProduct]) -> Dict[str, int]:
        """
        Termékek tömeges mentése adatbázisba
        
        Args:
            scraped_products: ScrapedProduct objektumok listája
            
        Returns:
            Dict a mentési statisztikákkal
        """
        logger.info(f"Bulk mentés indítása: {len(scraped_products)} termék")
        
        # Statisztikák nullázása
        self.stats = {
            'products_created': 0,
            'products_updated': 0,
            'products_skipped': 0,
            'errors': 0
        }
        
        for i, scraped_product in enumerate(scraped_products, 1):
            try:
                self.save_scraped_product(scraped_product)
                
                # Progress log minden 10. terméknél
                if i % 10 == 0:
                    logger.info(f"Feldolgozva: {i}/{len(scraped_products)} termék")
                    
            except Exception as e:
                logger.error(f"Termék kihagyva ({i}/{len(scraped_products)}): {e}")
                self.stats['products_skipped'] += 1
                continue
        
        logger.info(f"Bulk mentés befejezve: {self.stats}")
        return self.stats
    
    def _get_manufacturer_data(self, manufacturer_name: str) -> Dict:
        """Gyártó kiegészítő adatainak lekérése"""
        # Rockwool specifikus adatok
        if manufacturer_name.upper() == "ROCKWOOL":
            return {
                'description': 'ROCKWOOL Group dán anyacég magyar leányvállalata, kőzetgyapot alapú szigetelőanyagok gyártója.',
                'website': 'https://www.rockwool.hu',
                'country': 'Dánia',
                'logo_url': 'https://www.rockwool.hu/siteassets/rw-global/global/footer-images/logo_rockwool_black.png'
            }
        
        return {
            'description': None,
            'website': None,
            'country': None,
            'logo_url': None
        }
    
    def _get_category_data(self, category_name: str) -> Dict:
        """Kategória kiegészítő adatainak meghatározása"""
        category_data = {
            'Tetőszigetelés': {
                'description': 'Tetők hő- és hangszigetelésére szolgáló termékek',
                'level': 1,
                'sort_order': 10
            },
            'Homlokzati hőszigetelés': {
                'description': 'Épülethomlokzatok külső hőszigetelésére alkalmas termékek',
                'level': 1,
                'sort_order': 20
            },
            'Padlószigetelés': {
                'description': 'Padlószerkezetek hő- és hangszigetelő anyagai',
                'level': 1,
                'sort_order': 30
            },
            'Válaszfal szigetelés': {
                'description': 'Belső válaszfalak szigetelésére szolgáló termékek',
                'level': 1,
                'sort_order': 40
            },
            'Gépészeti szigetelés': {
                'description': 'Gépészeti rendszerek, csővezetékek szigetelése',
                'level': 1,
                'sort_order': 50
            },
            'Tűzvédelem': {
                'description': 'Tűzálló és tűzgátló építőanyagok',
                'level': 1,
                'sort_order': 60
            },
            'Hangszigetelés': {
                'description': 'Akusztikai hangszigetelő megoldások',
                'level': 1,
                'sort_order': 70
            },
            'Általános szigetelés': {
                'description': 'Egyéb és általános célú szigetelőanyagok',
                'level': 1,
                'sort_order': 80
            }
        }
        
        return category_data.get(category_name, {
            'description': None,
            'level': 1,
            'sort_order': 99
        })
    
    def _normalize_technical_specs(self, raw_specs: Dict) -> Tuple[Dict, Dict]:
        """
        Műszaki specifikációk normalizálása
        
        Args:
            raw_specs: Nyers műszaki adatok
            
        Returns:
            Tuple[Dict, Dict]: (normalizált_specs, eredeti_specs)
        """
        if not raw_specs:
            return {}, {}
        
        normalized = {}
        
        # Egységes kulcsnevek mapping
        key_mappings = {
            'hővezetési tényező': 'thermal_conductivity',
            'lambda': 'thermal_conductivity',
            'λ': 'thermal_conductivity',
            'sűrűség': 'density',
            'density': 'density',
            'vastagság': 'thickness',
            'thickness': 'thickness',
            'tűzállóság': 'fire_resistance',
            'fire class': 'fire_resistance',
            'reakció tűzre': 'fire_reaction',
            'hangszigetelés': 'sound_insulation',
            'acoustic': 'sound_insulation'
        }
        
        # Értékek normalizálása
        for key, value in raw_specs.items():
            normalized_key = key_mappings.get(key.lower(), key.lower().replace(' ', '_'))
            
            # Numerikus értékek kinyerése
            normalized_value = self._extract_numeric_value(value)
            if normalized_value is None:
                normalized_value = value
            
            normalized[normalized_key] = normalized_value
        
        return normalized, raw_specs
    
    def _extract_numeric_value(self, value: str) -> Optional[float]:
        """Numerikus érték kinyerése szövegből"""
        if not isinstance(value, str):
            return None
        
        import re
        
        # Szám keresése (tizedesjeggyel vagy anélkül)
        match = re.search(r'(\d+(?:[.,]\d+)?)', value.replace(' ', ''))
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except ValueError:
                pass
        
        return None
    
    def _extract_unit_from_specs(self, normalized_specs: Dict) -> Optional[str]:
        """Mértékegység meghatározása a műszaki adatokból"""
        # Gyakori egységek építőanyagoknál
        common_units = {
            'thickness': 'm2',  # Vastagság alapján általában m2-ben árulják
            'thermal_conductivity': 'm2',
            'density': 'm3'
        }
        
        for spec_key in normalized_specs.keys():
            if spec_key in common_units:
                return common_units[spec_key]
        
        # Alapértelmezett
        return 'm2'
    
    def get_statistics(self) -> Dict[str, int]:
        """Mentési statisztikák lekérése"""
        return self.stats.copy()
    
    def clear_cache(self):
        """Cache-ek törlése"""
        self._manufacturer_cache.clear()
        self._category_cache.clear()
        logger.debug("Database integration cache törölve")


def save_product_for_demo(db: Session, scraped_product: ScrapedProduct, manufacturer_name: str):
    """
    Egyszerűsített adatbázis mentési logika a DEMO számára.
    Frissíti a meglévő terméket az URL alapján, vagy újat hoz létre.
    """
    
    # 1. Gyártó biztosítása (egyszerűsített)
    manufacturer = db.query(Manufacturer).filter(Manufacturer.name == manufacturer_name).first()
    if not manufacturer:
        manufacturer = Manufacturer(name=manufacturer_name, country="HU") # Egyszerűsített adat
        db.add(manufacturer)
        db.commit()
        db.refresh(manufacturer)
        logger.info(f"DEMO: Új gyártó létrehozva: {manufacturer_name}")

    # Alapértelmezett kategória (a DEMO-ban nem fókusz)
    default_category = db.query(Category).filter(Category.name == "Általános").first()
    if not default_category:
        default_category = Category(name="Általános", is_active=True, level=0)
        db.add(default_category)
        db.commit()
        db.refresh(default_category)

    # 2. Létező termék keresése URL alapján
    existing_product = db.query(Product).filter(Product.source_url == scraped_product.url).first()
    
    if existing_product:
        # 3. Frissítés
        logger.info(f"DEMO: Termék frissítése: {scraped_product.name}")
        existing_product.name = scraped_product.name
        existing_product.full_text_content = scraped_product.full_text_content
        existing_product.scraped_at = datetime.now()
        existing_product.manufacturer_id = manufacturer.id
        existing_product.category_id = default_category.id
    else:
        # 4. Új termék létrehozása
        logger.info(f"DEMO: Új termék mentése: {scraped_product.name}")
        new_product = Product(
            name=scraped_product.name,
            source_url=scraped_product.url,
            full_text_content=scraped_product.full_text_content,
            scraped_at=datetime.now(),
            manufacturer_id=manufacturer.id,
            category_id=default_category.id,
            is_active=True,
            in_stock=True,
            currency="HUF"
        )
        db.add(new_product)

    try:
        db.commit()
    except Exception as e:
        logger.error(f"DEMO: Hiba a mentés során a '{scraped_product.name}' terméknél: {e}")
        db.rollback() 