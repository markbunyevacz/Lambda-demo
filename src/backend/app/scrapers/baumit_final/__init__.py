"""
BAUMIT Scrapers Package
----------------------

This package contains all BAUMIT-specific scrapers following the
manufacturer isolation architecture pattern.

Modules:
- baumit_product_catalog_scraper: High Priority A-Z catalog scraper
- baumit_color_system_scraper: Medium Priority color system scraper
- baumit_category_mapper: BAUMIT-specific category mapping
- run_baumit_scraper: Runner script for all BAUMIT scrapers

Priority Implementation:
🔴 High: Product A-Z catalog and technical specs
🟡 Medium: Color systems and application guides  
🟢 Low: Professional training materials (future)
"""

from .baumit_category_mapper import get_baumit_category_mapper
from .baumit_product_catalog_scraper import BaumitProductCatalogScraper
from .baumit_color_system_scraper import BaumitColorSystemScraper

__all__ = [
    'get_baumit_category_mapper',
    'BaumitProductCatalogScraper', 
    'BaumitColorSystemScraper'
] 