"""
BrightData MCP Agent - Fejlett scraping képességek AI-val

Ez a modul integrálja a BrightData MCP szervert a Lambda demo-ba,
lehetővé téve fejlett web scraping funkciókat AI irányítással.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

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
        
        # Initialize MCP state before validation
        self.mcp_available = False
        self.model = None
        
        # Environment változók ellenőrzése
        self._validate_environment()
        
        # Scraping statisztikák
        self._initialize_scraping_stats()
        
        # Lazy init for dependencies
        self._init_dependencies()

    def _initialize_scraping_stats(self):
        """Initializes the scraping statistics dictionary."""
        self.scraping_stats = {
            'requests_made': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'total_time': 0,
            'tools_used': []
        }
        
    def _validate_environment(self):
        """Ellenőrzi a szükséges környezeti változókat"""
        print("=== REAL AGENT VALIDATION DEBUG ===")
        
        required_vars = [
            'BRIGHTDATA_API_TOKEN',
            'BRIGHTDATA_WEB_UNLOCKER_ZONE', 
            'ANTHROPIC_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            print(f"{var} = {repr(value)}")
            if not value or value == f'your-{var.lower().replace("_", "-")}-here':
                missing_vars.append(var)
                print("  ❌ FAILED")
            else:
                print("  ✅ PASSED")
        
        print(f"Missing vars: {missing_vars}")
        
        if missing_vars:
            logger.warning(f"Hiányzó környezeti változók: {missing_vars}")
            logger.warning("A BrightData MCP agent nem lesz elérhető")
            self.mcp_available = False
            print("Setting mcp_available = False")
        else:
            self.mcp_available = True
            print("Setting mcp_available = True")
            
        print(f"Final mcp_available: {self.mcp_available}")
        print("=== END VALIDATION DEBUG ===")
    
    def _init_dependencies(self):
        """Dependency inicializálás csak ha szükséges"""
        print("=== INIT DEPENDENCIES DEBUG ===")
        print(f"self.mcp_available = {self.mcp_available}")
        
        if not self.mcp_available:
            logger.info("BrightData MCP agent disable - hiányzó konfiguráció")
            print("Returning early due to mcp_available = False")
            return
            
        print("Proceeding with dependency initialization...")
        
        try:
            self._import_mcp_dependencies()
            self._initialize_claude_model()
            self._initialize_server_params()
            logger.info("BrightData MCP agent sikeresen inicializálva")
            
        except ImportError as e:
            logger.warning(f"MCP dependencies hiányoznak: {e}")
            self.mcp_available = False
        except Exception as e:
            logger.error(f"MCP agent inicializálás hiba: {e}")
            self.mcp_available = False

    def _import_mcp_dependencies(self):
        """Handles the import of all MCP-related dependencies."""
        logger.info("Importing MCP dependencies...")
        try:
            from mcp import stdio_client, StdioServerParameters, ClientSession
            from langchain_anthropic import ChatAnthropic
            from langchain_mcp_adapters.tools import load_mcp_tools
            from langgraph.prebuilt import chat_agent_executor
            
            self.stdio_client = stdio_client
            self.StdioServerParameters = StdioServerParameters
            self.ClientSession = ClientSession
            self.load_mcp_tools = load_mcp_tools
            self.chat_agent_executor = chat_agent_executor
            self.ChatAnthropic = ChatAnthropic
            logger.info("✅ MCP imports successful")
        except ImportError as e:
            logger.error(f"❌ Failed to import MCP components: {e}")
            raise

    def _initialize_claude_model(self):
        """Initializes the Claude model for the agent."""
        self.model = self.ChatAnthropic(
            model="claude-3-5-haiku-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    def _initialize_server_params(self):
        """Initializes the server parameters for the MCP client."""
        import platform
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        
        self.server_params = self.StdioServerParameters(
            command=npx_cmd,
            env={
                "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
                "BROWSER_AUTH": os.getenv("BRIGHTDATA_BROWSER_AUTH"),
                "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_WEB_UNLOCKER_ZONE")
            },
            args=["-y", "@brightdata/mcp"]
        )
    
    async def create_agent_executor(self):
        """MCP Agent executor létrehozása"""
        if not self.mcp_available:
            raise Exception("BrightData MCP agent nem elérhető")
            
        try:
            async with self.stdio_client(self.server_params) as (read, write):
                async with self.ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # MCP tools betöltése
                    tools = await self.load_mcp_tools(session)
                    logger.info(
                        "BrightData MCP tools betöltve: %d tool elérhető",
                        len(tools)
                    )
                    
                    # Agent executor létrehozása
                    agent = self.chat_agent_executor.create_tool_calling_executor(
                        self.model, 
                        tools
                    )
                    
                    return agent, session
                    
        except Exception as e:
            logger.error(
                "MCP Agent executor létrehozása sikertelen: %s", e
            )
            raise
    
    async def scrape_rockwool_with_ai(
        self, target_urls: List[str], task_description: str = None
    ) -> List[Dict]:
        """
        AI-vezérelt Rockwool scraping BrightData eszközökkel.
        Orchestrates the scraping of multiple URLs.
        """
        if not self.mcp_available:
            logger.warning("BrightData MCP nem elérhető - üres lista visszaadása")
            return []
            
        start_time = datetime.now()
        logger.info(f"AI-vezérelt scraping indítása: {len(target_urls)} URL")
        
        scraped_products = []
        
        try:
            agent, _ = await self.create_agent_executor()
            for i, url in enumerate(target_urls):
                product_data = await self._process_single_url(
                    agent, url, i, len(target_urls), task_description
                )
                if product_data:
                    scraped_products.append(product_data)
                await asyncio.sleep(2)  # Delay between requests
                
        except Exception as e:
            logger.error(f"AI scraping általános hiba: {e}")
            
        total_time = (datetime.now() - start_time).total_seconds()
        self.scraping_stats['total_time'] += total_time
        
        logger.info(f"AI scraping befejezve: {len(scraped_products)} termék összegyűjtve")
        return scraped_products

    async def _process_single_url(
        self, agent, url: str, index: int, total: int, 
        task_description: Optional[str]
    ) -> Optional[Dict]:
        """Processes a single URL for scraping."""
        try:
            self.scraping_stats['requests_made'] += 1
            logger.info(f"URL feldolgozása ({index + 1}/{total}): {url}")

            messages = self._build_ai_messages(url, task_description)
            
            response = await agent.ainvoke({"messages": messages})
            
            ai_response_content = response['messages'][-1].content
            product_data = self._parse_ai_response(ai_response_content, url)
            
            if product_data:
                self.scraping_stats['successful_scrapes'] += 1
                logger.info(
                    "Sikeres scraping: %s", product_data.get('name', 'Névtelen termék')
                )
                return product_data
            else:
                logger.warning(f"Parsing hiba: {url}")
                self.scraping_stats['failed_scrapes'] += 1
                return None

        except Exception as e:
            logger.error(f"URL scraping hiba {url}: {e}")
            self.scraping_stats['failed_scrapes'] += 1
            return None

    def _build_ai_messages(
        self, url: str, task_description: Optional[str]
    ) -> List[Dict]:
        """Builds the list of messages to be sent to the AI agent."""
        if not task_description:
            task_description = """
            Rockwool építőipari szigetelőanyag adatokat kell összegyűjteni.
            Minden termékhez gyűjts össze:
            - Termék név és leírás
            - Műszaki paraméterek (λ érték, tűzállóság, méret)
            - Alkalmazási területek
            - Kategória
            - Esetleges ár információ
            """

        system_prompt = f"""
            Te egy szakértő web scraper vagy, aki Rockwool építőipari termékeket elemez.
            
            Feladat: {task_description}
            
            Használd a rendelkezésre álló BrightData tools-okat az alábbi URL elemzéséhez.
            
            A válaszodat strukturáld JSON formátumban:
            {{
                "name": "termék név",
                "description": "termék leírás", 
                "category": "kategória",
                "technical_specs": {{"param": "érték"}},
                "applications": ["alkalmazás1"],
                "source_url": "{url}"
            }}
            """
        
        return [
            {"role": "system", "content": system_prompt.strip()},
            {
                "role": "user", 
                "content": f"Elemezd ezt a Rockwool terméket: {url}"
            }
        ]
    
    def _parse_ai_response(self, ai_response: str, source_url: str) -> Optional[Dict]:
        """
        AI válasz parsing és normalizálás.
        Tries multiple strategies to extract JSON data from the AI response.
        """
        logger.info(f"Parsing AI response for URL: {source_url}")
        logger.debug(f"Full AI Response: {ai_response}")

        parsing_strategies = [
            self._parse_json_from_code_block,
            self._find_and_parse_json_object,
        ]

        for strategy in parsing_strategies:
            product_data = strategy(ai_response)
            if product_data:
                return self._finalize_product_data(product_data, source_url)

        # Fallback strategies if no JSON is found
        product_data = self._parse_from_structured_patterns(ai_response)
        if product_data:
            return self._finalize_product_data(product_data, source_url)

        logger.warning("No structured data found - creating minimal product data")
        return self._create_minimal_product_data(source_url)

    def _parse_json_from_code_block(self, ai_response: str) -> Optional[Dict]:
        """Strategy 1: Look for JSON in a markdown code block."""
        import re
        import json
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_str = json_match.group(1)
            try:
                logger.info("Found and parsed JSON from code block.")
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON in code block is invalid: {e}")
        return None

    def _find_and_parse_json_object(self, ai_response: str) -> Optional[Dict]:
        """Strategy 2: Find any valid JSON object in the response."""
        import re
        import json
        json_matches = re.findall(
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_response, re.DOTALL
        )
        for match in reversed(json_matches):  # Often the last one is the full object
            try:
                data = json.loads(match)
                logger.info(
                    "Found and parsed a valid JSON object from response."
                )
                return data
            except json.JSONDecodeError:
                continue
        return None

    def _parse_from_structured_patterns(self, ai_response: str) -> Optional[Dict]:
        """Strategy 3: Look for key-value patterns if no JSON is found."""
        import re
        name_match = re.search(
            r'(?:name|név)[\s:]*([^\n\r]+)', ai_response, re.IGNORECASE
        )
        category_match = re.search(
            r'(?:category|kategória)[\s:]*([^\n\r]+)', 
            ai_response, 
            re.IGNORECASE
        )

        if name_match or category_match:
            logger.info(
                "No JSON found, but extracting data from key-value patterns."
            )
            return {
                "name": name_match.group(1).strip() if name_match else "Rockwool termék",
                "category": category_match.group(1).strip() if category_match else "Szigetelőanyag",
                "description": "Extracted from unstructured response",
                "technical_specs": {},
                "applications": []
            }
        return None
    
    def _finalize_product_data(self, product_data: Dict, source_url: str) -> Dict:
        """Finalize and validate product data"""
        # Kötelező mezők
        product_data['source_url'] = source_url
        product_data['scraped_at'] = datetime.now().isoformat()
        product_data['scraper_type'] = 'brightdata_ai'
        
        # Alapértelmezések és validálás
        if 'name' not in product_data or not product_data['name']:
            product_data['name'] = self._extract_name_from_url(source_url)
        if 'category' not in product_data or not product_data['category']:
            product_data['category'] = 'Szigetelőanyag'
        if 'description' not in product_data:
            product_data['description'] = 'Rockwool szigetelőanyag termék'
        if 'technical_specs' not in product_data:
            product_data['technical_specs'] = {}
        if 'applications' not in product_data:
            product_data['applications'] = []
            
        return product_data
    
    def _create_minimal_product_data(self, source_url: str) -> Dict:
        """Create minimal product data when parsing fails"""
        return {
            'name': self._extract_name_from_url(source_url),
            'description': 'Rockwool szigetelőanyag termék - részletek nem állnak rendelkezésre',
            'category': 'Szigetelőanyag',
            'technical_specs': {},
            'applications': [],
            'source_url': source_url,
            'scraped_at': datetime.now().isoformat(),
            'scraper_type': 'brightdata_ai_fallback',
            'parsing_status': 'minimal_data_created'
        }
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract product name from URL"""
        import re
        
        # Extract the last meaningful part of the URL
        parts = url.rstrip('/').split('/')
        if len(parts) > 1:
            last_part = parts[-1]
            # Convert URL-friendly format to readable name
            name = re.sub(r'[-_]', ' ', last_part)
            name = re.sub(r'\.(html?|php)$', '', name, re.IGNORECASE)
            return name.title() if name else 'Rockwool Termék'
        return 'Rockwool Termék'
    
    async def search_rockwool_products(self, search_query: str) -> List[Dict]:
        """Rockwool termékek keresése AI-val"""
        if not self.mcp_available:
            return []
            
        logger.info(f"Rockwool termék keresése: {search_query}")
        
        try:
            agent, session = await self.create_agent_executor()
            
            messages = [
                {
                    "role": "system",
                    "content": """
                    Használd a search engine tools-okat Rockwool termékek keresésére.
                    Konkrétan a rockwool.hu vagy rockwool.com oldalakon keress.
                    """
                },
                {
                    "role": "user", 
                    "content": f"Keress Rockwool termékeket: {search_query}"
                }
            ]
            
            response = await agent.ainvoke({"messages": messages})
            
            # URL-ek kinyerése
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
            'mcp_available': self.mcp_available,
            'success_rate': (
                self.scraping_stats['successful_scrapes'] / 
                max(self.scraping_stats['requests_made'], 1)
            ) * 100 if self.scraping_stats['requests_made'] > 0 else 0
        }
    
    async def test_mcp_connection(self) -> Dict:
        """MCP kapcsolat tesztelése"""
        if not self.mcp_available:
            return {
                'success': False,
                'error': 'Környezeti változók hiányoznak',
                'message': 'BrightData MCP agent nem elérhető',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            agent, session = await self.create_agent_executor()
            
            # Egyszerű teszt
            messages = [
                {
                    "role": "user",
                    "content": "Test basic functionality"
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