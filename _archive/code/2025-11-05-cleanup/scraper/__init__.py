"""
Lambda.hu Rockwool Scraper Modul

Ez a modul tartalmazza a Rockwool weboldal automatizált adatgyűjtési funkcióit.
Az MCP stratégia szerint először csak a Rockwool scrapert implementáljuk.

Főbb komponensek:
- RockwoolScraper: Fő scraper osztály (API-alapú)
- BrightDataMCPAgent: AI-vezérelt scraper BrightData MCP-vel
- ScrapingCoordinator: Scraper koordinátor és fallback logika
- ProductParser: Termékadatok feldolgozása 
- CategoryMapper: Kategóriák normalizálása
- DataValidator: Scraped adatok validálása
- DatabaseIntegration: Adatbázis integráció
"""

# Hagyományos scraper komponensek
# from .rockwool_scraper import RockwoolApiScraper as RockwoolScraper
from .product_parser import ProductParser
from .category_mapper import CategoryMapper
from .data_validator import DataValidator
from .database_integration import DatabaseIntegration

# AI Agent komponensek (opcionális - dependency-alapú)
try:
    from ..agents import BrightDataMCPAgent, ScrapingCoordinator
    from ..agents.scraping_coordinator import ScrapingStrategy
    
    # AI-enhanced exports
    __all__ = [
        'RockwoolScraper',
        'ProductParser', 
        'CategoryMapper',
        'DataValidator',
        'DatabaseIntegration',
        'BrightDataMCPAgent',
        'ScrapingCoordinator',
        'ScrapingStrategy'
    ]
    
except ImportError:
    # Fallback - csak hagyományos komponensek
    __all__ = [
        'RockwoolScraper',
        'ProductParser', 
        'CategoryMapper',
        'DataValidator',
        'DatabaseIntegration'
    ] 