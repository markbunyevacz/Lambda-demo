"""
BrightData MCP Agent - Fejlett scraping képességek AI-val

Ez a modul integrálja a BrightData MCP szervert a Lambda demo-ba,
lehetővé téve fejlett web scraping funkciókat AI irányítással.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# MCP imports
from mcp import stdio
from mcp.client.session import ClientSession

# LangChain imports
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters import load_mcp_tools
from langgraph.prebuilts import chat_agent_executor

# Local imports
from ..models.product import Product
from .data_validator import DataValidator

logger = logging.getLogger(__name__)


class BrightDataMCPAgent:
    """
    BrightData MCP Agent osztály
    
    Funkcionalitás:
    - MCP szerver kapcsolat kezelése
    - AI-vezérelt scraping Claude-dal
    - 18 BrightData tool elérése
    - Adatok validálása és normalizálása
    """
    
    def __init__(self, timeout: int = 60, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.validator = DataValidator()
        
        # Environment változók ellenőrzése
        self._validate_environment()
        
        # Claude modell inicializálása
        self.model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # MCP szerver paraméterek
        self.server_params = stdio.StdioServerParameters(
            command="npx",
            env={
                "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
                "BROWSER_AUTH": os.getenv("BRIGHTDATA_BROWSER_AUTH"),
                "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_WEB_UNLOCKER_ZONE")
            },
            args=["-y", "@brightdata/mcp"]
        )
        
        self.scraping_stats = {
            'requests_made': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'total_time': 0,
            'tools_used': []
        }
        
    def _validate_environment(self):
        """Ellenőrzi a szükséges környezeti változókat"""
        required_vars = [
            'BRIGHTDATA_API_TOKEN',
            'BRIGHTDATA_WEB_UNLOCKER_ZONE', 
            'ANTHROPIC_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var) == f'your-{var.lower().replace("_", "-")}-here':
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Hiányzó környezeti változók: {missing_vars}")
            logger.warning("A .env.sample fájlban találsz útmutatást a konfigurációhoz")
    
    async def create_agent_executor(self):
        """MCP Agent executor létrehozása"""
        try:
            async with stdio.stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # MCP tools betöltése
                    tools = await load_mcp_tools(session)
                    logger.info(f"BrightData MCP tools betöltve: {len(tools)} tool elérhető")
                    
                    # Agent executor létrehozása
                    agent = chat_agent_executor.create_tool_calling_executor(
                        self.model, 
                        tools
                    )
                    
                    return agent, session
                    
        except Exception as e:
            logger.error(f"MCP Agent executor létrehozása sikertelen: {e}")
            raise
    
    async def scrape_rockwool_with_ai(self, target_urls: List[str], 
                                     task_description: str = None) -> List[Dict]:
        """
        AI-vezérelt Rockwool scraping BrightData eszközökkel
        
        Args:
            target_urls: Scraping-elni kívánt URL-ek
            task_description: AI számára szóló feladat leírás
            
        Returns:
            Lista a scraped termék adatokkal
        """
        start_time = datetime.now()
        logger.info(f"AI-vezérelt scraping indítása: {len(target_urls)} URL")
        
        if not task_description:
            task_description = """
            Rockwool építőipari szigetelőanyag adatokat kell összegyűjteni.
            Minden termékhez gyűjts össze:
            - Termék név és leírás
            - Műszaki paraméterek (λ érték, tűzállóság, méret)
            - Alkalmazási területek
            - Kategória
            - Esetleges ár információ
            
            Használj markdown formátumot a strukturált adatok visszaadásához.
            """
        
        scraped_products = []
        
        try:
            agent, session = await self.create_agent_executor()
            
            for i, url in enumerate(target_urls):
                try:
                    self.scraping_stats['requests_made'] += 1
                    
                    logger.info(f"URL feldolgozása ({i+1}/{len(target_urls)}): {url}")
                    
                    # AI prompt összeállítása
                    messages = [
                        {
                            "role": "system", 
                            "content": f"""
                            Te egy szakértő web scraper vagy, aki Rockwool építőipari termékeket elemez.
                            
                            Feladat: {task_description}
                            
                            Használd a rendelkezésre álló BrightData tools-okat az alábbi URL elemzéséhez.
                            Kezdd HTML vagy Markdown scraping-gel, majd elemezd az adatokat.
                            
                            URL: {url}
                            
                            A válaszodat strukturáld JSON formátumban az alábbi séma szerint:
                            {{
                                "name": "termék név",
                                "description": "termék leírás", 
                                "category": "kategória",
                                "technical_specs": {{"param": "érték"}},
                                "applications": ["alkalmazás1", "alkalmazás2"],
                                "source_url": "{url}"
                            }}
                            """
                        },
                        {
                            "role": "user",
                            "content": f"Elemezd ezt a Rockwool terméket: {url}"
                        }
                    ]
                    
                    # AI scraping végrehajtása
                    response = await agent.ainvoke({"messages": messages})
                    
                    # Válasz feldolgozása
                    ai_response = response['messages'][-1].content
                    product_data = self._parse_ai_response(ai_response, url)
                    
                    if product_data and self.validator.validate_product(product_data):
                        scraped_products.append(product_data)
                        self.scraping_stats['successful_scrapes'] += 1
                        logger.info(f"Sikeres scraping: {product_data.get('name', 'Névtelen termék')}")
                    else:
                        logger.warning(f"Érvénytelen adat vagy parsing hiba: {url}")
                        self.scraping_stats['failed_scrapes'] += 1
                        
                except Exception as e:
                    logger.error(f"URL scraping hiba {url}: {e}")
                    self.scraping_stats['failed_scrapes'] += 1
                    continue
                    
                # Delay a scraping-ek között
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"AI scraping általános hiba: {e}")
            raise
        
        # Statisztikák frissítése
        total_time = (datetime.now() - start_time).total_seconds()
        self.scraping_stats['total_time'] += total_time
        
        logger.info(f"AI scraping befejezve: {len(scraped_products)} termék összegyűjtve")
        return scraped_products
    
    def _parse_ai_response(self, ai_response: str, source_url: str) -> Optional[Dict]:
        """AI válasz parsing és normalizálás"""
        try:
            # JSON kinyerése az AI válaszból
            import json
            import re
            
            # JSON blokk keresése
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Alternatív: JSON objektum keresése
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.warning("Nem találtam JSON-t az AI válaszban")
                    return None
            
            # JSON parsing
            product_data = json.loads(json_str)
            
            # Kötelező mezők ellenőrzése és alapértelmezések
            product_data['source_url'] = source_url
            product_data['scraped_at'] = datetime.now().isoformat()
            product_data['scraper_type'] = 'brightdata_ai'
            
            # Adatok normalizálása
            if 'name' not in product_data or not product_data['name']:
                product_data['name'] = 'Rockwool termék'
                
            if 'category' not in product_data:
                product_data['category'] = 'Szigetelőanyag'
                
            return product_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing hiba: {e}")
            logger.debug(f"AI válasz: {ai_response}")
            return None
        except Exception as e:
            logger.error(f"AI válasz feldolgozási hiba: {e}")
            return None
    
    async def search_rockwool_products(self, search_query: str) -> List[Dict]:
        """
        Rockwool termékek keresése AI-val és search engine tools-szal
        
        Args:
            search_query: Keresési kifejezés
            
        Returns:
            Lista a találat termékekkel
        """
        logger.info(f"Rockwool termék keresése: {search_query}")
        
        try:
            agent, session = await self.create_agent_executor()
            
            messages = [
                {
                    "role": "system",
                    "content": """
                    Te egy Rockwool termék kereső especialista vagy.
                    Használd a search engine tools-okat Rockwool termékek keresésére.
                    
                    Konkrétan a rockwool.hu vagy rockwool.com oldalakon keress.
                    Gyűjts össze termék URL-eket és alapadatokat.
                    """
                },
                {
                    "role": "user", 
                    "content": f"Keress Rockwool termékeket: {search_query}"
                }
            ]
            
            response = await agent.ainvoke({"messages": messages})
            
            # URL-ek kinyerése a válaszból
            search_results = self._extract_urls_from_response(response['messages'][-1].content)
            
            logger.info(f"Keresés eredmény: {len(search_results)} URL találat")
            return search_results
            
        except Exception as e:
            logger.error(f"Termék keresési hiba: {e}")
            return []
    
    def _extract_urls_from_response(self, response_text: str) -> List[Dict]:
        """URL-ek kinyerése az AI válaszból"""
        import re
        
        # Rockwool URL-ek keresése
        url_pattern = r'https?://(?:www\.)?rockwool\.(?:hu|com)/[^\s\)]*'
        urls = re.findall(url_pattern, response_text)
        
        results = []
        for url in urls:
            results.append({
                'url': url,
                'source': 'search_engine',
                'found_at': datetime.now().isoformat()
            })
            
        return results
    
    def get_scraping_statistics(self) -> Dict:
        """Scraping statisztikák lekérése"""
        return {
            **self.scraping_stats,
            'success_rate': (
                self.scraping_stats['successful_scrapes'] / 
                max(self.scraping_stats['requests_made'], 1)
            ) * 100,
            'average_time_per_request': (
                self.scraping_stats['total_time'] / 
                max(self.scraping_stats['requests_made'], 1)
            )
        }
    
    async def test_mcp_connection(self) -> Dict:
        """MCP kapcsolat tesztelése"""
        try:
            agent, session = await self.create_agent_executor()
            
            # Egyszerű teszt
            messages = [
                {
                    "role": "user",
                    "content": "List available tools and test basic functionality"
                }
            ]
            
            response = await agent.ainvoke({"messages": messages})
            
            return {
                'success': True,
                'message': 'BrightData MCP kapcsolat sikeres',
                'tools_available': True,
                'response_received': bool(response),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"MCP kapcsolat teszt sikertelen: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'BrightData MCP kapcsolat sikertelen',
                'timestamp': datetime.now().isoformat()
            } 