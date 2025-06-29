"""
Lambda.hu AI Agents Modul

Ez a modul tartalmazza a különböző AI agenteket a demo számára:
- BrightDataMCPAgent: Fejlett web scraping BrightData MCP-vel
- ScrapingCoordinator: Multi-strategy scraping koordináció
- DataCollectionAgent: Adatgyűjtési koordináció
- DataProcessingAgent: Adatfeldolgozás és normalizálás
- RecommendationAgent: RAG-alapú termék ajánlások
- PriceMonitoringAgent: Árfigyelés és trend analízis
- CompatibilityAgent: Termék kompatibilitás ellenőrzés
"""

from .brightdata_agent import BrightDataMCPAgent
from .scraping_coordinator import ScrapingCoordinator
from .data_collection_agent import DataCollectionAgent
from .data_processing_agent import DataProcessingAgent
from .recommendation_agent import RecommendationAgent
from .price_monitoring_agent import PriceMonitoringAgent
from .compatibility_agent import CompatibilityAgent

__all__ = [
    'BrightDataMCPAgent',
    'ScrapingCoordinator',
    'DataCollectionAgent', 
    'DataProcessingAgent',
    'RecommendationAgent',
    'PriceMonitoringAgent',
    'CompatibilityAgent'
] 