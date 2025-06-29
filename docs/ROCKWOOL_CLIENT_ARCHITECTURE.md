# Rockwool Client-Specific Scraping Architecture

## 🎯 **Executive Summary**

This document defines the **modular, client-specific architecture** for the Rockwool scraping solution within the Lambda.hu platform. The architecture ensures **separation of concerns**, **reusability**, and **technical scalability** for handling multiple clients.

## 🏗️ **Architecture Overview**

```
clients/
├── rockwool/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── endpoints.py          # Rockwool-specific URLs
│   │   ├── selectors.py          # CSS/XPath selectors
│   │   ├── parsing_rules.py      # HTML parsing logic
│   │   └── product_schemas.py    # Data validation schemas
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract base scraper
│   │   ├── termekadatlapok.py    # Product datasheets scraper
│   │   ├── arlistak.py           # Pricelists scraper
│   │   └── brochures.py          # Brochures scraper
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── product_parser.py     # O74DocumentationList parser
│   │   ├── category_mapper.py    # Category normalization
│   │   └── data_validator.py     # Rockwool-specific validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py            # Rockwool product data model
│   │   ├── category.py           # Category data model
│   │   └── download_result.py    # Download result model
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_manager.py       # PDF download & storage
│   │   ├── cookie_handler.py     # Cookie consent bypass
│   │   └── url_builder.py        # URL construction utilities
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py             # Rockwool API client
│   │   └── endpoints.py          # REST API endpoints
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_scrapers.py
│   │   ├── test_parsers.py
│   │   └── fixtures/
│   ├── docs/
│   │   ├── api_reference.md
│   │   ├── data_flow.md
│   │   └── troubleshooting.md
│   └── README.md
├── shared/
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   ├── scraper.py            # Abstract scraper interface
│   │   ├── parser.py             # Abstract parser interface
│   │   └── client.py             # Abstract client interface
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── brightdata_client.py  # BrightData MCP wrapper
│   │   └── session_manager.py    # MCP session management
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── file_storage.py       # File system storage
│   │   └── database_storage.py   # Database storage
│   └── utils/
│       ├── __init__.py
│       ├── logging.py            # Centralized logging
│       ├── config.py             # Configuration management
│       └── exceptions.py         # Custom exception classes
└── factory/
    ├── __init__.py
    ├── client_factory.py         # Client factory pattern
    └── scraper_registry.py       # Scraper registration
```

## 🔧 **Core Components**

### 1. **Client-Specific Configuration**

```python
# clients/rockwool/config/endpoints.py
from dataclasses import dataclass

@dataclass
class RockwoolEndpoints:
    """Rockwool-specific URL endpoints"""
    BASE_URL: str = "https://www.rockwool.com"
    TERMEKADATLAPOK: str = "/hu/muszaki-informaciok/termekadatlapok/"
    ARLISTAK: str = "/hu/muszaki-informaciok/arlistak-es-prospektusok/"
    
    @property
    def full_termekadatlapok_url(self) -> str:
        return f"{self.BASE_URL}{self.TERMEKADATLAPOK}"
```

### 2. **Abstract Base Classes**

```python
# shared/base/scraper.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseScraper(ABC):
    """Abstract base class for all client scrapers"""
    
    def __init__(self, client_name: str, config: Dict[str, Any]):
        self.client_name = client_name
        self.config = config
        self.session = None
    
    @abstractmethod
    async def scrape(self, url: str, **kwargs):
        """Main scraping method - must be implemented by clients"""
        pass
```

This architecture ensures **separation of concerns**, **reusability**, and **technical scalability** for the Rockwool client while being easily extensible for future clients. 