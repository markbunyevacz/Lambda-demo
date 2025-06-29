# Rockwool Client Implementation Plan

## 🎯 **Current Status**
- ✅ **Working Solution**: 34 PDFs successfully scraped from termékadatlapok
- ✅ **Data Source**: `debug_termekadatlapok.html` with O74DocumentationList component
- ✅ **Storage**: `downloads/final_test/` directory
- ✅ **Brochures**: Separate brochure scraper working

## 🚀 **Phase 1: Extract & Modularize (2-3 hours)**

### Step 1.1: Create Client Directory Structure
```bash
mkdir -p clients/rockwool/{config,scrapers,parsers,models,utils,api,tests,docs}
mkdir -p shared/{base,mcp,storage,utils}
mkdir -p factory
```

### Step 1.2: Move Current Working Code
```bash
# Move main scraper
mv rockwool_scraper_final.py clients/rockwool/scrapers/termekadatlapok.py

# Move brochure scraper  
mv backend/app/scrapers/rockwool_final/brochure_scraper.py clients/rockwool/scrapers/brochures.py

# Copy debug files to fixtures
cp debug_termekadatlapok.html clients/rockwool/tests/fixtures/
```

### Step 1.3: Extract Configuration
```python
# clients/rockwool/config/endpoints.py
class RockwoolEndpoints:
    BASE_URL = "https://www.rockwool.com"
    TERMEKADATLAPOK = "/hu/muszaki-informaciok/termekadatlapok/"
    ARLISTAK = "/hu/muszaki-informaciok/arlistak-es-prospektusok/"

# clients/rockwool/config/selectors.py  
class RockwoolSelectors:
    O74_COMPONENT = '[data-component-name="O74DocumentationList"]'
    COOKIE_DIALOG = '#CybotCookiebotDialog'
```

### Step 1.4: Create Base Classes
```python
# shared/base/scraper.py
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, **kwargs):
        pass
    
    @abstractmethod  
    async def parse_content(self, html_content: str):
        pass
```

## 🔧 **Phase 2: Implement Factory Pattern (1-2 hours)**

### Step 2.1: Create Client Factory
```python
# factory/client_factory.py
class ClientFactory:
    _scrapers = {
        "rockwool": {
            "termekadatlapok": "clients.rockwool.scrapers.termekadatlapok.RockwoolTermekadatlapokScraper",
            "brochures": "clients.rockwool.scrapers.brochures.RockwoolBrochuresScraper"
        }
    }
    
    @classmethod
    def create_scraper(cls, client: str, scraper_type: str):
        # Dynamic import and instantiation
        pass
```

### Step 2.2: Update Main Scraper Class
```python
# clients/rockwool/scrapers/termekadatlapok.py
from shared.base.scraper import BaseScraper
from ..config.endpoints import RockwoolEndpoints

class RockwoolTermekadatlapokScraper(BaseScraper):
    def __init__(self):
        self.endpoints = RockwoolEndpoints()
        self.storage_dir = Path("downloads/final_test")
    
    async def scrape(self, **kwargs):
        # Use existing working logic
        return await self._scrape_from_debug_file()
```

## 🔌 **Phase 3: Create API Interface (1 hour)**

### Step 3.1: Client-Specific API
```python
# clients/rockwool/api/endpoints.py
from fastapi import APIRouter
from factory.client_factory import ClientFactory

router = APIRouter(prefix="/api/clients/rockwool")

@router.post("/scrape/termekadatlapok")
async def scrape_termekadatlapok():
    scraper = ClientFactory.create_scraper("rockwool", "termekadatlapok")
    result = await scraper.scrape()
    return {"status": "success", "products": len(result)}
```

### Step 3.2: Main API Registration
```python
# main.py
from clients.rockwool.api.endpoints import router as rockwool_router

app.include_router(rockwool_router, tags=["Rockwool"])
```

## 🧪 **Phase 4: Add Testing (1 hour)**

### Step 4.1: Unit Tests
```python
# clients/rockwool/tests/test_termekadatlapok.py
import pytest
from ..scrapers.termekadatlapok import RockwoolTermekadatlapokScraper

class TestRockwoolTermekadatlapok:
    @pytest.mark.asyncio
    async def test_scrape_success(self):
        scraper = RockwoolTermekadatlapokScraper()
        result = await scraper.scrape()
        
        assert result.products_found == 34  # Our known working result
        assert result.downloads_successful > 0
```

### Step 4.2: Integration Tests
```python
# Test API endpoints
async def test_api_scrape_termekadatlapok():
    response = client.post("/api/clients/rockwool/scrape/termekadatlapok")
    assert response.status_code == 200
    assert response.json()["products"] > 0
```

## 📚 **Phase 5: Documentation (30 minutes)**

### Step 5.1: Client Documentation
```markdown
# clients/rockwool/README.md
# Rockwool Client Scraper

## Quick Start
```python
from factory.client_factory import ClientFactory

scraper = ClientFactory.create_scraper("rockwool", "termekadatlapok")
result = await scraper.scrape()
```

## API Endpoints
- POST /api/clients/rockwool/scrape/termekadatlapok
- POST /api/clients/rockwool/scrape/brochures
```

### Step 5.2: Technical Documentation
```markdown
# clients/rockwool/docs/technical_details.md
## Data Flow
1. Load debug_termekadatlapok.html
2. Parse O74DocumentationList component  
3. Extract product data (45 products)
4. Download PDFs (34 successful)
5. Store in downloads/final_test/
```

## ⚡ **Phase 6: Optimize & Extend (Optional)**

### Step 6.1: Add Árlisták Scraper
```python
# clients/rockwool/scrapers/arlistak.py
class RockwoolArlistakScraper(BaseScraper):
    async def scrape(self, **kwargs):
        # Implement pricelists scraping
        pass
```

### Step 6.2: Add Monitoring
```python
# shared/utils/monitoring.py
class ScrapingMetrics:
    def track_scraping_success(client: str, scraper_type: str, count: int):
        # Track metrics for monitoring
        pass
```

## 🎯 **Expected Outcomes**

After implementation:

1. **Clean Architecture**: 
   - `ClientFactory.create_scraper("rockwool", "termekadatlapok")`
   - Separated concerns and reusable components

2. **Easy Extension**:
   - Add new clients: `clients/new_client/`
   - Add new scrapers: Register in factory

3. **Robust API**:
   - `POST /api/clients/rockwool/scrape/termekadatlapok`
   - Consistent interface across all clients

4. **Maintainable Code**:
   - Clear separation of client-specific logic
   - Shared utilities for common functionality
   - Comprehensive testing coverage

## 🚨 **Migration Safety**

- Keep `rockwool_scraper_final.py` as backup until migration complete
- Test each phase independently
- Maintain backward compatibility during transition
- Use feature flags for gradual rollout

## ⏰ **Total Time Estimate: 5-7 hours**

This plan transforms the current working solution into a **production-ready, client-specific architecture** while preserving the successful scraping functionality. 