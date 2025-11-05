# Scrapers Overview

This directory contains web scrapers for different building materials manufacturers.

## Production Scrapers

### Rockwool (`rockwool/`)
**Status**: ✅ Production-ready, actively used

The Rockwool scraper is the primary production scraper, used by:
- `app/agents/scraping_coordinator.py` - Scraping coordination
- `app/agents/data_collection_agent.py` - Data collection

**Files**:
- `brochure_and_pricelist_scraper.py` (274 lines) - Main scraper for brochures and pricelists
- `rockwool_product_scraper.py` (335 lines) - Product data scraper
- `rockwool_state_manager.py` (380 lines) - State management for scraping sessions

**Usage**:
```python
from app.scrapers.rockwool.brochure_and_pricelist_scraper import RockwoolBrochureScraper
scraper = RockwoolBrochureScraper()
products = await scraper.scrape_all_product_datasheets()
```

## Experimental Scrapers

### Leier (`leier/`)
**Status**: 🧪 Experimental, not used in production

Comprehensive implementation for Leier product scraping with multiple strategies.

**Files** (12 Python files, ~5,000 lines total):
- `leier_product_scraper.py` (491 lines) - Main product scraper
- `leier_product_tree_mapper.py` (587 lines) - Product tree mapping
- `leier_calculator_scraper.py` (631 lines) - Calculator scraper
- `leier_documents_scraper.py` (552 lines) - Document scraper
- `leier_documents_scraper_root_version.py` (453 lines) - Alternative document scraper
- `leier_dynamic_scraper.py` (366 lines) - Dynamic scraping
- `leier_specific_urls_scraper.py` (510 lines) - Specific URL scraper
- `leier_recursive_scraper.py` (224 lines) - Recursive scraper
- `leier_download_manager_scraper.py` (234 lines) - Download manager
- `run_leier_scrapers.py` (234 lines) - Runner script
- `run_leier_master_scraper.py` (123 lines) - Master runner
- `demo_specific_urls.py` (183 lines) - Demo URLs

**Documentation**:
- `README_LEIER_IMPLEMENTATION.md` - Implementation details
- `README_LEIER_DYNAMIC_PLAN.md` - Dynamic scraping plan
- `README_leier_strategy.md` - Strategy overview

**Note**: Contains a 6MB PDF file (`Akciós termékkínálat.pdf`) that should be moved to data directory.

### Baumit (`baumit_final/`)
**Status**: 🧪 Experimental, not used in production

Implementation for Baumit product catalog and color system scraping.

**Files** (5 Python files, ~1,500 lines total):
- `baumit_product_catalog_scraper.py` (481 lines) - Product catalog scraper
- `baumit_enhanced_scraper.py` (401 lines) - Enhanced scraper
- `baumit_category_mapper.py` (225 lines) - Category mapping
- `baumit_color_system_scraper.py` (95 lines) - Color system scraper
- `run_baumit_scraper.py` (75 lines) - Runner script

**Documentation**:
- `IMPLEMENTATION_REPORT.md` - Implementation report
- `README_baumit_strategy.md` - Strategy overview

## Integration

To add a new scraper to production:

1. Implement the scraper following the Rockwool pattern
2. Add import to `scraping_coordinator.py`
3. Update `ScrapingCoordinator.__init__()` to initialize the scraper
4. Add scraping methods for the new manufacturer
5. Update tests and documentation

## Notes

- All scrapers follow async/await patterns
- Scrapers use the shared database session from `app.database`
- Error handling and logging are standardized
- State management is important for resumable scraping sessions
