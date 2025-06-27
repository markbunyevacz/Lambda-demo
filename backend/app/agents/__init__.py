"""
Lambda.hu AI Agents Modul

Ez a modul tartalmazza a különböző AI agenteket a demo számára:
- BrightDataMCPAgent: Fejlett web scraping BrightData MCP-vel
- ScrapingAgent: Hagyományos scraping agent
- DataAnalysisAgent: Adatelemző agent
"""

from .brightdata_agent import BrightDataMCPAgent
from .scraping_coordinator import ScrapingCoordinator

__all__ = [
    'BrightDataMCPAgent',
    'ScrapingCoordinator'
] 