"""
Rockwool State Manager - Állapot mentés és kezelés
--------------------------------------------------

Ez a modul kezeli a Rockwool scraper állapotainak mentését,
helyreállítását és különböző formátumokba való exportálását.

Funkciók:
- JSON/CSV/Database mentés
- Verziókezelés
- Állapot snapshots
- Adatbázis integráció
"""
import asyncio
import logging
import json
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[5]
STATE_STORAGE_DIR = PROJECT_ROOT / "src" / "backend" / "src" / "rockwool_states"
EXPORTS_DIR = STATE_STORAGE_DIR / "exports"
SNAPSHOTS_DIR = STATE_STORAGE_DIR / "snapshots"

# Ensure directories exist
STATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RockwoolProduct:
    """Rockwool termék adatstruktúra"""
    name: str
    category: str
    pdf_url: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    scraped_at: str = None
    is_duplicate: bool = False
    hash_id: Optional[str] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
        if self.hash_id is None:
            self.hash_id = self.generate_hash()
    
    def generate_hash(self) -> str:
        """Egyedi hash generálás a termék azonosításához"""
        content = f"{self.name}_{self.pdf_url}_{self.category}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class RockwoolScrapingState:
    """Teljes scraping állapot"""
    state_id: str
    timestamp: str
    scraper_version: str
    products: List[RockwoolProduct]
    statistics: Dict[str, Any]
    config: Dict[str, Any]
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.state_id is None:
            self.state_id = f"rockwool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class RockwoolStateManager:
    """
    Rockwool állapotkezelő osztály
    """
    
    def __init__(self):
        self.current_state: Optional[RockwoolScrapingState] = None
        self.state_history: List[RockwoolScrapingState] = []
        
    async def create_state_from_scraped_data(
        self, 
        scraped_products: List[Dict], 
        statistics: Dict = None,
        config: Dict = None
    ) -> RockwoolScrapingState:
        """
        Új állapot létrehozása scraped adatokból
        """
        timestamp = datetime.now().isoformat()
        state_id = f"rockwool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Convert to RockwoolProduct objects
        products = []
        for item in scraped_products:
            product = RockwoolProduct(
                name=item.get('name', 'Unknown'),
                category=item.get('category', 'Uncategorized'),
                pdf_url=item.get('pdf_url', ''),
                file_path=item.get('file_path'),
                file_size_bytes=item.get('file_size_bytes'),
                scraped_at=timestamp,
                is_duplicate=item.get('is_duplicate', False)
            )
            products.append(product)
        
        # Default statistics if not provided
        if statistics is None:
            statistics = {
                'total_products': len(products),
                'unique_products': len([p for p in products if not p.is_duplicate]),
                'duplicates': len([p for p in products if p.is_duplicate]),
                'total_downloads': len([p for p in products if p.file_path]),
                'scraping_date': timestamp
            }
        
        # Default config if not provided
        if config is None:
            config = {
                'scraper_type': 'live_data',
                'data_source': 'rockwool.com',
                'language': 'hu',
                'fallback_used': False
            }
        
        state = RockwoolScrapingState(
            state_id=state_id,
            timestamp=timestamp,
            scraper_version="2.0_live_only",
            products=products,
            statistics=statistics,
            config=config
        )
        
        self.current_state = state
        self.state_history.append(state)
        
        logger.info(f"✅ Új állapot létrehozva: {state_id}")
        logger.info(f"📊 Termékek: {len(products)} (ebből {statistics['duplicates']} duplikátum)")
        
        return state
    
    async def save_state_to_json(self, state: RockwoolScrapingState) -> Path:
        """Állapot mentése JSON formátumban"""
        filename = f"{state.state_id}_complete.json"
        filepath = STATE_STORAGE_DIR / filename
        
        state_dict = {
            'state_id': state.state_id,
            'timestamp': state.timestamp,
            'scraper_version': state.scraper_version,
            'products': [asdict(p) for p in state.products],
            'statistics': state.statistics,
            'config': state.config
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 JSON mentve: {filepath}")
        return filepath
    
    async def save_state_to_csv(self, state: RockwoolScrapingState) -> Path:
        """Termékek mentése CSV formátumban"""
        filename = f"{state.state_id}_products.csv"
        filepath = EXPORTS_DIR / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Hash ID', 'Name', 'Category', 'PDF URL', 
                'File Path', 'File Size (bytes)', 'Is Duplicate', 'Scraped At'
            ])
            
            for product in state.products:
                writer.writerow([
                    product.hash_id, product.name, product.category,
                    product.pdf_url, product.file_path or '', 
                    product.file_size_bytes or 0, product.is_duplicate, 
                    product.scraped_at
                ])
        
        logger.info(f"📊 CSV mentve: {filepath}")
        return filepath
    
    async def save_state_to_sqlite(self, state: RockwoolScrapingState) -> Path:
        """Állapot mentése SQLite adatbázisba"""
        db_filename = f"rockwool_states.db"
        db_filepath = STATE_STORAGE_DIR / db_filename
        
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_states (
                state_id TEXT PRIMARY KEY,
                timestamp TEXT,
                scraper_version TEXT,
                statistics TEXT,
                config TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                hash_id TEXT PRIMARY KEY,
                state_id TEXT,
                name TEXT,
                category TEXT,
                pdf_url TEXT,
                file_path TEXT,
                file_size_bytes INTEGER,
                is_duplicate BOOLEAN,
                scraped_at TEXT,
                FOREIGN KEY (state_id) REFERENCES scraping_states (state_id)
            )
        ''')
        
        # Insert data
        cursor.execute('''
            INSERT OR REPLACE INTO scraping_states 
            (state_id, timestamp, scraper_version, statistics, config)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            state.state_id, state.timestamp, state.scraper_version,
            json.dumps(state.statistics), json.dumps(state.config)
        ))
        
        for product in state.products:
            cursor.execute('''
                INSERT OR REPLACE INTO products 
                (hash_id, state_id, name, category, pdf_url, file_path, 
                 file_size_bytes, is_duplicate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.hash_id, state.state_id, product.name, 
                product.category, product.pdf_url, product.file_path,
                product.file_size_bytes, product.is_duplicate, 
                product.scraped_at
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🗃️  SQLite mentve: {db_filepath}")
        return db_filepath
    
    async def create_snapshot(self, name: str = None) -> Path:
        """
        Pillanatkép létrehozása a jelenlegi állapotról
        """
        if self.current_state is None:
            raise ValueError("Nincs jelenlegi állapot a snapshot-hoz!")
        
        if name is None:
            name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot_file = SNAPSHOTS_DIR / f"{name}.json"
        
        await self.save_state_to_json(self.current_state)
        
        # Copy to snapshots directory
        import shutil
        json_file = STATE_STORAGE_DIR / f"{self.current_state.state_id}_complete.json"
        shutil.copy2(json_file, snapshot_file)
        
        logger.info(f"📸 Snapshot létrehozva: {snapshot_file}")
        return snapshot_file
    
    async def save_all_formats(self, state: RockwoolScrapingState = None) -> Dict[str, Path]:
        """
        Állapot mentése minden formátumban
        """
        if state is None:
            state = self.current_state
        
        results = {}
        
        try:
            results['json'] = await self.save_state_to_json(state)
            results['csv'] = await self.save_state_to_csv(state)
            results['sqlite'] = await self.save_state_to_sqlite(state)
            
            logger.info("✅ Állapot minden formátumban elmentve!")
            
        except Exception as e:
            logger.error(f"❌ Mentési hiba: {e}")
            raise
        
        return results
    
    def get_statistics_summary(self, state: RockwoolScrapingState = None) -> Dict:
        """
        Részletes statisztikák összefoglalója
        """
        if state is None:
            state = self.current_state
        
        if state is None:
            return {}
        
        products = state.products
        
        # Category breakdown
        categories = {}
        for product in products:
            cat = product.category
            if cat not in categories:
                categories[cat] = {'total': 0, 'unique': 0, 'duplicates': 0}
            categories[cat]['total'] += 1
            if product.is_duplicate:
                categories[cat]['duplicates'] += 1
            else:
                categories[cat]['unique'] += 1
        
        # File size analysis
        total_size = sum(p.file_size_bytes or 0 for p in products if p.file_path)
        avg_size = total_size / len([p for p in products if p.file_path]) if products else 0
        
        return {
            'state_info': {
                'state_id': state.state_id,
                'timestamp': state.timestamp,
                'scraper_version': state.scraper_version
            },
            'product_counts': {
                'total_products': len(products),
                'unique_products': len([p for p in products if not p.is_duplicate]),
                'duplicates': len([p for p in products if p.is_duplicate]),
                'downloaded_files': len([p for p in products if p.file_path])
            },
            'categories': categories,
            'file_info': {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024*1024), 2),
                'average_size_bytes': round(avg_size),
                'largest_file': max((p.file_size_bytes or 0 for p in products), default=0)
            },
            'config': state.config,
            'storage_locations': {
                'json_files': str(STATE_STORAGE_DIR),
                'csv_exports': str(EXPORTS_DIR),
                'snapshots': str(SNAPSHOTS_DIR)
            }
        }


# Convenience functions
async def save_current_rockwool_state(products_data: List[Dict], **kwargs) -> Dict[str, Path]:
    """Gyors mentés funkció scraped adatokhoz"""
    manager = RockwoolStateManager()
    state = await manager.create_state_from_scraped_data(products_data, **kwargs)
    return await manager.save_all_formats(state)


async def load_latest_rockwool_state() -> Optional[RockwoolScrapingState]:
    """
    Legfrissebb állapot betöltése
    """
    json_files = list(STATE_STORAGE_DIR.glob("*_complete.json"))
    if not json_files:
        return None
    
    # Sort by modification time
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    
    manager = RockwoolStateManager()
    return await manager.load_state_from_json(latest_file) 