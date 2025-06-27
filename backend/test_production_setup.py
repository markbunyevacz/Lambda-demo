#!/usr/bin/env python3
"""
Lambda.hu Production Testing Suite
Comprehensive testing of BrightData MCP integration
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List

# Color output for better readability
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_step(step: int, text: str):
    print(f"{Colors.PURPLE}{Colors.BOLD}[STEP {step}]{Colors.END} {text}")


class ProductionTester:
    """Comprehensive production testing suite"""
    
    def __init__(self):
        self.test_results = {
            'environment': {},
            'dependencies': {},
            'api_connections': {},
            'scraping_tests': {},
            'performance': {},
            'errors': []
        }
        
    async def run_all_tests(self):
        """Run complete production test suite"""
        print_header("🚀 LAMBDA.HU PRODUCTION TESTING SUITE")
        start_time = time.time()
        
        try:
            # Test sequence
            await self.test_environment_variables()
            await self.test_python_dependencies()
            await self.test_node_js_setup()
            await self.test_api_connections()
            await self.test_basic_scraping()
            await self.test_advanced_scraping()
            await self.test_coordination_strategies()
            await self.test_celery_tasks()
            await self.test_performance_limits()
            
            # Final report
            duration = time.time() - start_time
            await self.generate_test_report(duration)
            
        except Exception as e:
            print_error(f"Critical test failure: {e}")
            self.test_results['errors'].append(str(e))
            return False
    
    async def test_environment_variables(self):
        """Test 1: Environment Configuration"""
        print_step(1, "Testing Environment Variables")
        
        required_vars = {
            'BRIGHTDATA_API_TOKEN': 'BrightData API Token',
            'ANTHROPIC_API_KEY': 'Anthropic Claude API Key',
            'BRIGHTDATA_WEB_UNLOCKER_ZONE': 'BrightData Zone',
            'DATABASE_URL': 'Database Connection',
            'REDIS_URL': 'Redis Connection'
        }
        
        missing_vars = []
        placeholder_vars = []
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing_vars.append(f"{var} ({description})")
                print_error(f"Missing: {var}")
            elif value.startswith('your-') or value.startswith('YOUR_'):
                placeholder_vars.append(f"{var} ({description})")
                print_warning(f"Placeholder value: {var}")
            else:
                print_success(f"Configured: {var}")
        
        self.test_results['environment'] = {
            'missing_vars': missing_vars,
            'placeholder_vars': placeholder_vars,
            'properly_configured': len(required_vars) - len(missing_vars) - len(placeholder_vars)
        }
        
        if missing_vars or placeholder_vars:
            print_warning("Environment issues detected. Check .env configuration.")
            return False
        
        print_success("All environment variables properly configured")
        return True
    
    async def test_python_dependencies(self):
        """Test 2: Python Dependencies"""
        print_step(2, "Testing Python Dependencies")
        
        required_packages = [
            'langchain',
            'langchain_anthropic', 
            'langchain_mcp_adapters',
            'langgraph',
            'mcp',
            'httpx',
            'celery',
            'redis'
        ]
        
        missing_packages = []
        working_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                working_packages.append(package)
                print_success(f"Available: {package}")
            except ImportError:
                missing_packages.append(package)
                print_error(f"Missing: {package}")
        
        self.test_results['dependencies'] = {
            'missing_packages': missing_packages,
            'working_packages': working_packages
        }
        
        if missing_packages:
            print_error(f"Install missing packages: pip install {' '.join(missing_packages)}")
            return False
        
        print_success("All Python dependencies available")
        return True
    
    async def test_node_js_setup(self):
        """Test 3: Node.js and MCP Server"""
        print_step(3, "Testing Node.js & MCP Server Setup")
        
        try:
            import subprocess
            
            # Check Node.js
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print_success(f"Node.js available: {node_version}")
            else:
                print_error("Node.js not found")
                return False
            
            # Check NPX
            result = subprocess.run(['npx', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                npx_version = result.stdout.strip()
                print_success(f"NPX available: {npx_version}")
            else:
                print_error("NPX not found")
                return False
            
            print_success("Node.js environment ready for MCP server")
            return True
            
        except Exception as e:
            print_error(f"Node.js test failed: {e}")
            return False
    
    async def test_api_connections(self):
        """Test 4: API Connectivity"""
        print_step(4, "Testing API Connections")
        
        try:
            from app.agents import BrightDataMCPAgent
            
            # Test BrightData MCP connection
            print_info("Testing BrightData MCP connection...")
            agent = BrightDataMCPAgent()
            
            connection_test = await agent.test_mcp_connection()
            
            if connection_test['success']:
                print_success("BrightData MCP connection successful")
                self.test_results['api_connections']['brightdata_mcp'] = True
            else:
                print_error(f"BrightData MCP failed: {connection_test.get('error', 'Unknown')}")
                self.test_results['api_connections']['brightdata_mcp'] = False
                
            return connection_test['success']
            
        except Exception as e:
            print_error(f"API connection test failed: {e}")
            self.test_results['api_connections']['brightdata_mcp'] = False
            return False
    
    async def test_basic_scraping(self):
        """Test 5: Basic Scraping Functionality"""
        print_step(5, "Testing Basic Scraping")
        
        try:
            from app.agents import BrightDataMCPAgent
            
            agent = BrightDataMCPAgent()
            
            # Test simple scraping
            test_urls = ["https://www.rockwool.hu"]
            print_info(f"Testing basic scraping on: {test_urls[0]}")
            
            start_time = time.time()
            products = await agent.scrape_rockwool_with_ai(
                test_urls, 
                "Extract basic information from this Rockwool page"
            )
            duration = time.time() - start_time
            
            if products and len(products) > 0:
                print_success(f"Basic scraping successful: {len(products)} products in {duration:.2f}s")
                self.test_results['scraping_tests']['basic'] = {
                    'success': True,
                    'products_found': len(products),
                    'duration': duration
                }
                return True
            else:
                print_warning("Basic scraping completed but no products extracted")
                self.test_results['scraping_tests']['basic'] = {
                    'success': False,
                    'products_found': 0,
                    'duration': duration
                }
                return False
                
        except Exception as e:
            print_error(f"Basic scraping test failed: {e}")
            self.test_results['scraping_tests']['basic'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_advanced_scraping(self):
        """Test 6: Advanced Scraping Features"""
        print_step(6, "Testing Advanced Scraping Features")
        
        try:
            from app.agents import BrightDataMCPAgent
            
            agent = BrightDataMCPAgent()
            
            # Test search functionality
            print_info("Testing search and scraping...")
            search_results = await agent.search_rockwool_products("Rockwool szigetelés")
            
            if search_results:
                print_success(f"Search successful: {len(search_results)} results found")
                
                # Test scraping found URLs
                urls_to_test = [result['url'] for result in search_results[:2]]
                products = await agent.scrape_rockwool_with_ai(urls_to_test)
                
                print_success(f"Advanced scraping: {len(products)} products extracted")
                self.test_results['scraping_tests']['advanced'] = {
                    'search_results': len(search_results),
                    'products_extracted': len(products),
                    'success': True
                }
                return True
            else:
                print_warning("Search returned no results")
                self.test_results['scraping_tests']['advanced'] = {
                    'success': False,
                    'search_results': 0
                }
                return False
                
        except Exception as e:
            print_error(f"Advanced scraping test failed: {e}")
            self.test_results['scraping_tests']['advanced'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_coordination_strategies(self):
        """Test 7: Scraping Coordination"""
        print_step(7, "Testing Scraping Coordination Strategies")
        
        try:
            from app.agents import ScrapingCoordinator
            from app.agents.scraping_coordinator import ScrapingStrategy
            
            coordinator = ScrapingCoordinator()
            
            # Test scraper availability
            print_info("Testing scraper availability...")
            test_results = await coordinator.test_all_scrapers()
            
            api_available = test_results['api_scraper']['available']
            mcp_available = test_results['mcp_agent']['available']
            recommended = test_results['coordination']['recommended_strategy']
            
            print_info(f"API Scraper: {'✅' if api_available else '❌'}")
            print_info(f"MCP Agent: {'✅' if mcp_available else '❌'}")
            print_info(f"Recommended Strategy: {recommended}")
            
            # Test coordination
            print_info("Testing coordinated scraping...")
            results = await coordinator.scrape_products(target_input=3)
            
            if results and len(results) > 0:
                print_success(f"Coordination successful: {len(results)} products")
                self.test_results['scraping_tests']['coordination'] = {
                    'api_available': api_available,
                    'mcp_available': mcp_available,
                    'recommended_strategy': recommended,
                    'products_extracted': len(results),
                    'success': True
                }
                return True
            else:
                print_warning("Coordination completed but no products")
                return False
                
        except Exception as e:
            print_error(f"Coordination test failed: {e}")
            return False
    
    async def test_celery_tasks(self):
        """Test 8: Celery Task Integration"""
        print_step(8, "Testing Celery Task Integration")
        
        try:
            # Test import
            from app.celery_tasks.brightdata_tasks import test_brightdata_mcp_connection
            print_success("BrightData Celery tasks imported successfully")
            
            # Note: In production, you'd actually run the task:
            # result = test_brightdata_mcp_connection.delay()
            # task_result = result.get(timeout=60)
            
            print_info("Celery tasks ready (run manually with .delay() for full test)")
            return True
            
        except Exception as e:
            print_error(f"Celery task test failed: {e}")
            return False
    
    async def test_performance_limits(self):
        """Test 9: Performance & Rate Limits"""
        print_step(9, "Testing Performance & Rate Limits")
        
        try:
            from app.agents import BrightDataMCPAgent
            
            agent = BrightDataMCPAgent()
            
            # Test performance with small batch
            print_info("Testing performance with 3 concurrent requests...")
            
            urls = [
                "https://www.rockwool.hu",
                "https://www.rockwool.hu/termekek/",
                "https://www.rockwool.hu/megoldasok/"
            ]
            
            start_time = time.time()
            products = await agent.scrape_rockwool_with_ai(urls[:3])
            duration = time.time() - start_time
            
            throughput = len(products) / duration if duration > 0 else 0
            
            print_success(f"Performance test: {len(products)} products in {duration:.2f}s")
            print_info(f"Throughput: {throughput:.2f} products/second")
            
            self.test_results['performance'] = {
                'test_duration': duration,
                'products_processed': len(products),
                'throughput': throughput
            }
            
            return True
            
        except Exception as e:
            print_error(f"Performance test failed: {e}")
            return False
    
    async def generate_test_report(self, total_duration: float):
        """Generate comprehensive test report"""
        print_header("📊 PRODUCTION TEST REPORT")
        
        # Summary
        print(f"{Colors.BOLD}Test Duration:{Colors.END} {total_duration:.2f} seconds")
        print(f"{Colors.BOLD}Timestamp:{Colors.END} {datetime.now().isoformat()}")
        
        # Environment Status
        env = self.test_results.get('environment', {})
        if env:
            print(f"\n{Colors.BOLD}Environment:{Colors.END}")
            print(f"  ✅ Configured: {env.get('properly_configured', 0)}")
            if env.get('missing_vars'):
                print(f"  ❌ Missing: {len(env['missing_vars'])}")
            if env.get('placeholder_vars'):
                print(f"  ⚠️  Placeholder: {len(env['placeholder_vars'])}")
        
        # API Connections
        api = self.test_results.get('api_connections', {})
        if api:
            print(f"\n{Colors.BOLD}API Connections:{Colors.END}")
            for service, status in api.items():
                icon = "✅" if status else "❌"
                print(f"  {icon} {service}: {'Connected' if status else 'Failed'}")
        
        # Scraping Tests
        scraping = self.test_results.get('scraping_tests', {})
        if scraping:
            print(f"\n{Colors.BOLD}Scraping Tests:{Colors.END}")
            for test_name, result in scraping.items():
                if isinstance(result, dict) and result.get('success'):
                    products = result.get('products_extracted', result.get('products_found', 0))
                    print(f"  ✅ {test_name}: {products} products extracted")
                else:
                    print(f"  ❌ {test_name}: Failed")
        
        # Performance
        perf = self.test_results.get('performance', {})
        if perf:
            print(f"\n{Colors.BOLD}Performance:{Colors.END}")
            print(f"  📊 Throughput: {perf.get('throughput', 0):.2f} products/second")
            print(f"  ⏱️  Duration: {perf.get('test_duration', 0):.2f} seconds")
        
        # Errors
        if self.test_results.get('errors'):
            print(f"\n{Colors.BOLD}{Colors.RED}Errors:{Colors.END}")
            for error in self.test_results['errors']:
                print(f"  ❌ {error}")
        
        # Overall Status
        print(f"\n{Colors.BOLD}Overall Status:{Colors.END}")
        if (env.get('properly_configured', 0) > 3 and 
            api.get('brightdata_mcp', False) and
            scraping.get('basic', {}).get('success', False)):
            print_success("🎉 Production environment ready for deployment!")
        else:
            print_warning("⚠️  Issues detected - review configuration before production")
        
        # Save detailed report
        report_file = f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print_info(f"Detailed report saved: {report_file}")


async def main():
    """Run production testing suite"""
    tester = ProductionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 