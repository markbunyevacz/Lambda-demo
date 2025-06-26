"""
Lambda.hu Rockwool Scraper Modul

Ez a modul tartalmazza a Rockwool weboldal automatizált adatgyűjtési funkcióit.
Az MCP stratégia szerint először csak a Rockwool scrapert implementáljuk.

Főbb komponensek:
- RockwoolScraper: Fő scraper osztály
- ScrapingConfig: Scraper konfigurációs osztály
- ProductParser: Termékadatok feldolgozása 
- CategoryMapper: Kategóriák normalizálása
- DataValidator: Scraped adatok validálása
"""

from .rockwool_scraper import RockwoolApiScraper as RockwoolScraper
from .product_parser import ProductParser
from .category_mapper import CategoryMapper
from .data_validator import DataValidator
from .database_integration import DatabaseIntegration

__all__ = [
    'RockwoolScraper',
    'ProductParser', 
    'CategoryMapper',
    'DataValidator',
    'DatabaseIntegration'
] 