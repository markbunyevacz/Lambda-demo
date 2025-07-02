"""
LEIER Calculator & Pricing Scraper
---------------------------------

This scraper focuses on extracting calculator tools and pricing data from LEIER Hungary.
It complements the documents scraper by targeting interactive tools and pricing information.

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
from typing import List, Optional, Set, Any
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parents[5]
CALC_STORAGE = PROJECT_ROOT / "src" / "downloads" / "leier_materials" / "calculators"
PRICING_STORAGE = PROJECT_ROOT / "src" / "downloads" / "leier_materials" / "pricing_data"

# Ensure directories exist
CALC_STORAGE.mkdir(parents=True, exist_ok=True)
PRICING_STORAGE.mkdir(parents=True, exist_ok=True)

# LEIER calculator configuration
BASE_URL = "https://www.leier.hu"
CALCULATOR_URLS = {
    'main_calculators': "https://www.leier.hu/hu/kalkulatorok",
    'price_calculators': "https://www.leier.hu/hu/arkalkulatorok",
    'material_calculators': "https://www.leier.hu/hu/anyagmennyseg-szamolo",
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
    price_data: Optional[dict] = None
    interactive_elements: Optional[List[str]] = None


@dataclass  
class CalculatorData:
    """Extracted calculator data and parameters"""
    calculator_id: str
    parameters: dict
    formulas: List[str]
    default_values: dict
    price_matrix: Optional[dict] = None
    validation_rules: Optional[dict] = None


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
    
    async def _fetch_with_mcp(self, url: str) -> Optional[str]:
        """Fetch using BrightData MCP"""
        try:
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
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    tools = await session.list_tools()
                    scrape_tool = None
                    
                    for tool in tools.tools:
                        if 'scrape' in tool.name.lower():
                            scrape_tool = tool
                            break
                    
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
        logger.info(f"📊 Total unique calculators found: {len(calculator_list)}")
        return calculator_list
    
    def _extract_calculator_urls(self, content: str, base_url: str) -> List[str]:
        """Extract calculator URLs from page content"""
        soup = BeautifulSoup(content, 'html.parser')
        calculator_urls = []
        
        # Look for calculator-specific selectors
        calc_selectors = [
            'a[href*="kalkulat"]',
            'a[href*="calculator"]', 
            'a[href*="szamolo"]',
            'a[href*="eszko"]',
            '.calculator-link',
            '.tool-link',
            '.calc-button'
        ]
        
        for selector in calc_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
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
        price_data = self._extract_price_data(soup, content)
        
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
        self.stats['calculators_found'] += 1
        if interactive_elements:
            self.stats['interactive_tools'] += 1
        if price_data:
            self.stats['pricing_data_extracted'] += 1
        if parameters:
            self.stats['parameters_captured'] += len(parameters)
        
        return calculator
    
    def _extract_calculator_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract calculator name from page"""
        name_selectors = [
            'h1', '.page-title', '.calculator-title', 
            '.tool-title', 'title'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and len(name) < 100:
                    return name
        
        # Fallback to URL path
        path_parts = urlparse(url).path.split('/')
        for part in reversed(path_parts):
            if part and len(part) > 2:
                return part.replace('-', ' ').title()
        
        return "Unknown Calculator"
    
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
    
    def _extract_parameters(self, soup: BeautifulSoup) -> List[str]:
        """Extract calculator parameters"""
        parameters = []
        
        # Form field labels
        labels = soup.find_all('label')
        for label in labels:
            label_text = label.get_text(strip=True)
            if label_text and len(label_text) < 50:
                parameters.append(label_text)
        
        # Input field names and placeholders
        inputs = soup.find_all('input')
        for inp in inputs:
            name = inp.get('name', '')
            placeholder = inp.get('placeholder', '')
            if name:
                parameters.append(f"field: {name}")
            if placeholder:
                parameters.append(f"placeholder: {placeholder}")
        
        return list(set(parameters))  # Remove duplicates
    
    def _extract_formulas(self, soup: BeautifulSoup, content: str) -> List[str]:
        """Extract calculation formulas from JavaScript or text"""
        formulas = []
        
        # Look for JavaScript calculation functions
        script_tags = soup.find_all('script')
        for script in script_tags:
            script_content = script.get_text()
            if script_content:
                # Look for mathematical expressions
                math_patterns = [
                    r'[a-zA-Z_]\w*\s*=\s*[^;]+[+\-*/][^;]+',
                    r'Math\.[a-zA-Z]+\([^)]+\)',
                    r'calculate\w*\([^)]*\)\s*{[^}]+}',
                    r'price\s*[*+\-/]\s*\w+'
                ]
                
                for pattern in math_patterns:
                    matches = re.findall(pattern, script_content)
                    formulas.extend(matches)
        
        # Look for formula descriptions in text
        formula_keywords = ['formula', 'képlet', 'számítás', 'calculation']
        for keyword in formula_keywords:
            pattern = rf'{keyword}[^.]*[=+\-*/][^.]*\.'
            matches = re.findall(pattern, content, re.IGNORECASE)
            formulas.extend(matches)
        
        return formulas[:10]  # Limit to reasonable number
    
    def _extract_price_data(self, soup: BeautifulSoup, content: str) -> Optional[dict]:
        """Extract pricing information"""
        price_data = {}
        
        # Look for price tables
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text().lower()
            if any(word in table_text for word in ['ár', 'price', 'cost', 'költség']):
                # Extract table data
                rows = table.find_all('tr')
                table_data = []
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if any(cell for cell in row_data):
                        table_data.append(row_data)
                
                if table_data:
                    price_data['price_table'] = table_data
        
        # Look for price patterns in text
        price_patterns = [
            r'\d+[\d\s,]*\s*Ft',
            r'\d+[\d\s,]*\s*EUR',
            r'\d+[\d\s,]*\s*HUF'
        ]
        
        prices_found = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            prices_found.extend(matches)
        
        if prices_found:
            price_data['price_mentions'] = prices_found[:20]  # Limit
        
        return price_data if price_data else None
    
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
            price_filename = f"pricing_data_{timestamp}_{len(self.calculators)}.json"
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
            
            for i, url in enumerate(calc_urls, 1):
                logger.info(f"🔧 Calculator {i}/{len(calc_urls)}: {url}")
                
                calculator = await self.analyze_calculator(url)
                if calculator:
                    self.calculators.append(calculator)
                    await self.save_calculator_data(calculator)
                
                # Rate limiting
                await asyncio.sleep(1.0)
            
            # Step 3: Generate report
            self.generate_calculator_report(start_time)
            
        except Exception as e:
            logger.error(f"❌ Calculator scraping failed: {e}")
            raise
    
    def generate_calculator_report(self, start_time: datetime):
        """Generate comprehensive calculator report"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculator type breakdown
        type_counts = {}
        for calc in self.calculators:
            type_counts[calc.calc_type] = type_counts.get(calc.calc_type, 0) + 1
        
        logger.info("=" * 70)
        logger.info("📊 LEIER CALCULATOR SCRAPER - FINAL REPORT")
        logger.info("=" * 70)
        
        # Overall statistics
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"🔧 Calculators found: {self.stats['calculators_found']}")
        logger.info(f"⚙️  Interactive tools: {self.stats['interactive_tools']}")
        logger.info(f"💰 Pricing data extracted: {self.stats['pricing_data_extracted']}")
        logger.info(f"📝 Parameters captured: {self.stats['parameters_captured']}")
        
        # Type breakdown
        logger.info("\n📊 Calculators by Type:")
        for calc_type, count in type_counts.items():
            logger.info(f"   {calc_type}: {count}")
        
        # Sample calculators
        logger.info("\n🔧 Sample Calculators:")
        for calc in self.calculators[:5]:  # Show first 5
            logger.info(f"   - {calc.name} ({calc.calc_type})")
        
        logger.info("=" * 70)
        
        # Save comprehensive report
        self.save_comprehensive_report(start_time, end_time, type_counts)
    
    def save_comprehensive_report(self, start_time: datetime, end_time: datetime, 
                                type_counts: dict):
        """Save detailed report to JSON file"""
        report = {
            'scraper_info': {
                'name': 'LEIER Calculator Scraper',
                'version': '1.0',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            },
            'statistics': self.stats,
            'type_breakdown': type_counts,
            'storage_locations': {
                'calculators': str(CALC_STORAGE),
                'pricing_data': str(PRICING_STORAGE)
            },
            'calculators': [
                {
                    'name': calc.name,
                    'url': calc.url,
                    'type': calc.calc_type,
                    'has_price_data': bool(calc.price_data),
                    'parameter_count': len(calc.parameters or []),
                    'formula_count': len(calc.formulas or [])
                }
                for calc in self.calculators
            ]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = PROJECT_ROOT / f"leier_calculator_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Calculator report saved: {report_file}")


async def main():
    """Main entry point for LEIER calculator scraper"""
    scraper = LeierCalculatorScraper()
    await scraper.run_calculator_scrape()


if __name__ == "__main__":
    asyncio.run(main()) 