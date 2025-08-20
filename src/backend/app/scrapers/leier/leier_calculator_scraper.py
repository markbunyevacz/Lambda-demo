"""
LEIER Calculator & Pricing Scraper
---------------------------------

This scraper focuses on extracting calculator tools and pricing data
from LEIER Hungary. It complements the documents scraper by targeting
interactive tools and pricing information.

Priority: MEDIUM - Important for cost estimation and pricing insights
Target Areas:
- Cost estimation calculators
- Material quantity calculators  
- Pricing matrices and formulas
- Calculator parameters and formulas

Entry Points:
- /hu/kalkulatorok (Calculators)
- /hu/arkalkulatorok (Price calculators)
- /hu/anyagmennyseg-szamolo (Material calculators)
- /hu/koltsegbecsles (Cost estimation)
"""

import asyncio
import logging
import json
import httpx
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parents[5]
CALC_STORAGE = (
    PROJECT_ROOT / "src" / "downloads" / "leier_materials" / "calculators"
)
PRICING_STORAGE = (
    PROJECT_ROOT / "src" / "downloads" / "leier_materials" / "pricing_data"
)

# Ensure directories exist
CALC_STORAGE.mkdir(parents=True, exist_ok=True)
PRICING_STORAGE.mkdir(parents=True, exist_ok=True)

# LEIER calculator configuration
BASE_URL = "https://www.leier.hu"
CALCULATOR_URLS = {
    'main_calculators': "https://www.leier.hu/hu/kalkulatorok",
    'price_calculators': "https://www.leier.hu/hu/arkalkulatorok",
    'material_calculators': (
        "https://www.leier.hu/hu/anyagmennyseg-szamolo"
    ),
    'cost_estimation': "https://www.leier.hu/hu/koltsegbecsles"
}

# Calculator type patterns
CALC_PATTERNS = {
    'cost_estimation': [
        r'költség.*becslés', r'cost.*estimation', r'ár.*kalkulátor',
        r'price.*calculator'
    ],
    'material_quantity': [
        r'anyag.*mennyiség', r'material.*quantity', r'mennyiség.*számológép',
        r'quantity.*calculator'
    ],
    'technical_calculator': [
        r'műszaki.*kalkulátor', r'technical.*calculator', r'számító.*eszköz',
        r'engineering.*tool'
    ],
    'pricing_tool': [
        r'ár.*eszköz', r'pricing.*tool', r'árlista.*kalkulátor',
        r'price.*list.*tool'
    ]
}


@dataclass
class LeierCalculator:
    """Data structure for LEIER calculators"""
    name: str
    url: str
    calc_type: str
    description: Optional[str] = None
    parameters: Optional[List[str]] = None
    formulas: Optional[List[str]] = None
    price_data: Optional[Dict[str, Any]] = None
    interactive_elements: Optional[List[str]] = None


@dataclass  
class CalculatorData:
    """Extracted calculator data and parameters"""
    calculator_id: str
    parameters: Dict[str, Any]
    formulas: List[str]
    default_values: Dict[str, Any]
    price_matrix: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class LeierCalculatorScraper:
    """Scraper for LEIER calculators and pricing tools"""
    
    def __init__(self):
        self.calculators: List[LeierCalculator] = []
        self.calculator_data: List[CalculatorData] = []
        self.visited_urls: Set[str] = set()
        self.stats = {
            'calculators_found': 0,
            'interactive_tools': 0,
            'pricing_data_extracted': 0,
            'parameters_captured': 0
        }
    
    async def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page content with fallback methods"""
        try:
            return await self._fetch_with_mcp(url)
        except Exception as e:
            logger.warning(f"MCP failed for {url}: {e}")
            return await self._fetch_direct(url)
    
    async def _initialize_mcp_session(self):
        """Initializes the BrightData MCP session and returns a client session."""
        from mcp import stdio_client, StdioServerParameters, ClientSession
        import platform
        
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        api_token = os.getenv('BRIGHTDATA_API_TOKEN')
        
        if not api_token:
            raise ValueError("No BRIGHTDATA_API_TOKEN found")
        
        server_params = StdioServerParameters(
            command=npx_cmd,
            env={"API_TOKEN": api_token},
            args=["-y", "@brightdata/mcp"]
        )
        
        read, write = await stdio_client(server_params)
        session = ClientSession(read, write)
        await session.initialize()
        return session

    async def _find_scrape_tool(self, session) -> Optional[Any]:
        """Finds a scraping tool from the available MCP tools."""
        tools = await session.list_tools()
        for tool in tools.tools:
            if 'scrape' in tool.name.lower():
                return tool
        return None

    async def _fetch_with_mcp(self, url: str) -> Optional[str]:
        """Fetch using BrightData MCP"""
        session = None
        try:
            session = await self._initialize_mcp_session()
            scrape_tool = await self._find_scrape_tool(session)
            
            if scrape_tool:
                response = await session.call_tool(
                    scrape_tool.name, {"url": url}
                )
                if response.content:
                    return response.content[0].text
            return None
        except Exception as e:
            logger.debug(f"MCP fetch error: {e}")
            raise
        finally:
            if session:
                await session.close()
    
    async def _fetch_direct(self, url: str) -> Optional[str]:
        """Direct HTTP fetch as fallback"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Direct fetch failed for {url}: {e}")
            return None
    
    def classify_calculator(self, name: str, url: str, description: str = "") -> str:
        """Classify calculator into appropriate category"""
        combined_text = f"{name} {url} {description}".lower()
        
        for calc_type, patterns in CALC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    return calc_type
        
        return 'technical_calculator'  # Default
    
    async def discover_calculators(self) -> List[str]:
        """Discover all calculator URLs from main pages"""
        logger.info("🔍 Discovering LEIER calculators...")
        
        all_calc_urls = set()
        
        for page_name, url in CALCULATOR_URLS.items():
            logger.info(f"📄 Checking {page_name}: {url}")
            content = await self.fetch_page_content(url)
            
            if content:
                calc_urls = self._extract_calculator_urls(content, url)
                all_calc_urls.update(calc_urls)
                logger.info(f"✅ Found {len(calc_urls)} calculators on {page_name}")
        
        calculator_list = list(all_calc_urls)
        logger.info(
            f"📊 Total unique calculators found: {len(calculator_list)}"
        )
        return calculator_list
    
    def _get_calculator_link_selectors(self) -> List[str]:
        """Returns CSS selectors for finding calculator links."""
        return [
            'a[href*="kalkulat"]',
            'a[href*="calculator"]', 
            'a[href*="szamolo"]',
            'a[href*="eszko"]',
            '.calculator-link',
            '.tool-link',
            '.calc-button'
        ]

    def _extract_links_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Extracts all calculator-related hrefs from the soup."""
        hrefs = []
        selectors = self._get_calculator_link_selectors()
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    hrefs.append(href)
        return hrefs

    def _extract_calculator_urls(
        self, content: str, base_url: str
    ) -> List[str]:
        """Extract calculator URLs from page content"""
        soup = BeautifulSoup(content, 'html.parser')
        hrefs = self._extract_links_from_soup(soup)
        
        calculator_urls = []
        for href in hrefs:
            full_url = urljoin(BASE_URL, href)
            if self._is_valid_calculator_url(full_url):
                calculator_urls.append(full_url)
        
        return list(set(calculator_urls))  # Remove duplicates
    
    def _is_valid_calculator_url(self, url: str) -> bool:
        """Check if URL is a valid calculator URL"""
        url_lower = url.lower()
        return (
            url.startswith(BASE_URL) and
            any(keyword in url_lower for keyword in [
                'kalkulat', 'calculator', 'szamolo', 'eszko', 'tool'
            ]) and
            url not in self.visited_urls
        )
    
    async def analyze_calculator(self, url: str) -> Optional[LeierCalculator]:
        """Analyze a single calculator page"""
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        logger.info(f"🔧 Analyzing calculator: {url}")
        
        content = await self.fetch_page_content(url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract calculator information
        name = self._extract_calculator_name(soup, url)
        description = self._extract_description(soup)
        calc_type = self.classify_calculator(name, url, description or "")
        
        # Extract interactive elements
        interactive_elements = self._extract_interactive_elements(soup)
        parameters = self._extract_parameters(soup)
        formulas = self._extract_formulas(soup, content)
        price_data = self._extract_price_data(soup)
        
        calculator = LeierCalculator(
            name=name,
            url=url,
            calc_type=calc_type,
            description=description,
            parameters=parameters,
            formulas=formulas,
            price_data=price_data,
            interactive_elements=interactive_elements
        )
        
        # Update statistics
        self._update_stats(calculator)
        
        return calculator
    
    def _get_name_from_selectors(self, soup: BeautifulSoup) -> Optional[str]:
        """Extracts calculator name using a list of CSS selectors."""
        name_selectors = [
            'h1', '.page-title', '.calculator-title', '.tool-title', 'title'
        ]
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and len(name) < 100:
                    return name
        return None

    def _get_name_from_url(self, url: str) -> str:
        """Extracts a fallback name from the URL path."""
        path_parts = urlparse(url).path.split('/')
        for part in reversed(path_parts):
            if part and len(part) > 2:
                return part.replace('-', ' ').title()
        return "Unknown Calculator"

    def _extract_calculator_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract calculator name from page"""
        name = self._get_name_from_selectors(soup)
        if name:
            return name
        return self._get_name_from_url(url)
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract calculator description"""
        desc_selectors = [
            '.calculator-description', '.tool-description',
            '.page-description', 'p.description'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc = element.get_text(strip=True)
                if desc and len(desc) > 20:
                    return desc[:300]  # Limit length
        
        return None
    
    def _extract_interactive_elements(self, soup: BeautifulSoup) -> List[str]:
        """Extract interactive form elements"""
        elements = []
        
        # Input fields
        inputs = soup.find_all(['input', 'select', 'textarea'])
        for inp in inputs:
            element_info = {
                'type': inp.name,
                'name': inp.get('name', ''),
                'id': inp.get('id', ''),
                'label': inp.get('placeholder', '')
            }
            elements.append(str(element_info))
        
        # Buttons
        buttons = soup.find_all(['button', 'input[type="submit"]'])
        for btn in buttons:
            btn_text = btn.get_text(strip=True) or btn.get('value', '')
            if btn_text:
                elements.append(f"button: {btn_text}")
        
        return elements
    
    def _extract_labels_for_parameters(
        self, soup: BeautifulSoup
    ) -> Set[str]:
        """Extracts parameter names from <label> tags."""
        parameters = set()
        labels = soup.find_all('label')
        for label in labels:
            label_text = label.get_text(strip=True)
            if label_text and len(label_text) < 50:
                parameters.add(label_text)
        return parameters

    def _extract_inputs_for_parameters(
        self, soup: BeautifulSoup
    ) -> Set[str]:
        """Extracts parameter names from <input> tags."""
        parameters = set()
        inputs = soup.find_all('input')
        for inp in inputs:
            name = inp.get('name', '')
            placeholder = inp.get('placeholder', '')
            if name:
                parameters.add(f"field: {name}")
            if placeholder:
                parameters.add(f"placeholder: {placeholder}")
        return parameters

    def _extract_parameters(self, soup: BeautifulSoup) -> List[str]:
        """Extract calculator parameters"""
        labels = self._extract_labels_for_parameters(soup)
        inputs = self._extract_inputs_for_parameters(soup)
        return list(labels.union(inputs))
    
    def _extract_formulas_from_scripts(
        self, soup: BeautifulSoup
    ) -> List[str]:
        """Extracts formulas from <script> tags."""
        formulas = []
        script_tags = soup.find_all('script')
        for script in script_tags:
            script_content = script.get_text()
            if not script_content:
                continue
            
            math_patterns = [
                r'[a-zA-Z_]\w*\s*=\s*[^;]+[+\-*/][^;]+',
                r'Math\.[a-zA-Z]+\([^)]+\)',
                r'calculate\w*\([^)]*\)\s*{[^}]+}',
                r'price\s*[*+\-/]\s*\w+'
            ]
            
            for pattern in math_patterns:
                matches = re.findall(pattern, script_content)
                formulas.extend(matches)
        return formulas

    def _extract_formulas_from_text(self, content: str) -> List[str]:
        """Extracts formulas from visible text content."""
        formulas = []
        formula_keywords = ['formula', 'képlet', 'számítás', 'calculation']
        for keyword in formula_keywords:
            pattern = rf'{keyword}[^.]*[=+\-*/][^.]*\.'
            matches = re.findall(pattern, content, re.IGNORECASE)
            formulas.extend(matches)
        return formulas

    def _extract_formulas(self, soup: BeautifulSoup, content: str) -> List[str]:
        """Extract calculation formulas from JavaScript or text"""
        script_formulas = self._extract_formulas_from_scripts(soup)
        text_formulas = self._extract_formulas_from_text(content)
        all_formulas = script_formulas + text_formulas
        return all_formulas[:10]  # Limit to reasonable number
    
    def _extract_price_table_data(
        self, soup: BeautifulSoup
    ) -> Optional[List[List[str]]]:
        """Extracts pricing data from tables."""
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text().lower()
            if any(
                word in table_text for word in ['ár', 'price', 'cost', 'költség']
            ):
                rows = table.find_all('tr')
                table_data = []
                for row in rows:
                    cells = [
                        cell.get_text(strip=True) 
                        for cell in row.find_all(['td', 'th'])
                    ]
                    if any(cells):
                        table_data.append(cells)
                if table_data:
                    return table_data
        return None

    def _extract_price_mentions_from_text(self, content: str) -> List[str]:
        """Extracts price mentions from text content."""
        price_patterns = [
            r'\d+[\d\s,]*\s*Ft', 
            r'\d+[\d\s,]*\s*EUR', 
            r'\d+[\d\s,]*\s*HUF'
        ]
        prices_found = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            prices_found.extend(matches)
        return prices_found[:20]

    def _extract_price_data(
        self, soup: BeautifulSoup, content: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Extract pricing information"""
        price_data = {}
        
        table_data = self._extract_price_table_data(soup)
        if table_data:
            price_data['price_table'] = table_data
        
        price_mentions = self._extract_price_mentions_from_text(
            soup.get_text()
        )
        if price_mentions:
            price_data['price_mentions'] = price_mentions
        
        return price_data if price_data else None
    
    def _update_stats(self, calculator: LeierCalculator):
        """Updates the scraping statistics based on the extracted calculator data."""
        self.stats['calculators_found'] += 1
        if calculator.interactive_elements:
            self.stats['interactive_tools'] += 1
        if calculator.price_data:
            self.stats['pricing_data_extracted'] += 1
        if calculator.parameters:
            self.stats['parameters_captured'] += len(calculator.parameters)

    async def save_calculator_data(self, calculator: LeierCalculator):
        """Save calculator data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save individual calculator data
        calc_filename = (
            f"calculator_{calculator.calc_type}_"
            f"{timestamp}_{len(self.calculators)}.json"
        )
        calc_path = CALC_STORAGE / calc_filename
        
        with open(calc_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(calculator), f, indent=2, ensure_ascii=False)
        
        # Save pricing data separately if available
        if calculator.price_data:
            price_filename = (
                f"pricing_data_{timestamp}_{len(self.calculators)}.json"
            )
            price_path = PRICING_STORAGE / price_filename
            
            with open(price_path, 'w', encoding='utf-8') as f:
                json.dump(calculator.price_data, f, indent=2, ensure_ascii=False)
    
    async def run_calculator_scrape(self):
        """Execute complete calculator scraping process"""
        start_time = datetime.now()
        
        logger.info("🚀 LEIER Calculator Scraper Starting")
        logger.info("=" * 50)
        
        try:
            # Step 1: Discover all calculators
            calc_urls = await self.discover_calculators()
            
            if not calc_urls:
                logger.warning("⚠️  No calculators found")
                return
            
            # Step 2: Analyze each calculator
            logger.info(f"🔧 Analyzing {len(calc_urls)} calculators...")
            
            tasks = [self.analyze_calculator(url) for url in calc_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, LeierCalculator):
                    self.calculators.append(result)
                    await self.save_calculator_data(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error analyzing calculator: {result}")

            # Step 3: Generate report
            self.generate_calculator_report(start_time)
            
        except Exception as e:
            logger.critical(
                f"💥 Critical error in scraper run: {e}", exc_info=True
            )
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"🏁 LEIER Calculator Scraper Finished in {duration:.2f}s")

    def _get_type_counts(self) -> Dict[str, int]:
        """Counts the number of calculators of each type."""
        type_counts = {}
        for calc in self.calculators:
            type_counts[calc.calc_type] = type_counts.get(calc.calc_type, 0) + 1
        return type_counts

    def generate_calculator_report(self, start_time: datetime):
        """Generate and save a comprehensive report"""
        end_time = datetime.now()
        type_counts = self._get_type_counts()
        self.save_comprehensive_report(start_time, end_time, type_counts)

    def save_comprehensive_report(self, start_time: datetime, end_time: datetime, 
                                type_counts: Dict[str, int]):
        """Saves a comprehensive JSON report."""
        timestamp = end_time.strftime("%Y%m%d_%H%M%S")
        report_filename = f"leier_comprehensive_report_{timestamp}.json"
        report_path = (
            PRICING_STORAGE.parent / "reports" / report_filename
        )
        report_path.parent.mkdir(exist_ok=True)
        
        report = {
            'run_timestamp': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'stats': self.stats,
            'calculator_type_counts': type_counts,
            'calculators': [asdict(c) for c in self.calculators]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📊 Comprehensive report saved to {report_path}")


async def main():
    """Main execution entry point"""
    scraper = LeierCalculatorScraper()
    await scraper.run_calculator_scrape()


if __name__ == "__main__":
    asyncio.run(main()) 