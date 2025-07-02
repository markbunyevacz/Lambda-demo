"""
LEIER Scrapers Coordinator & Runner
-----------------------------------

This script orchestrates the complete LEIER scraping process according to priorities:
1. HIGH PRIORITY: Documents scraper (technical docs, datasheets, guides)
2. MEDIUM PRIORITY: Calculator scraper (cost estimation, pricing tools)

Usage:
    python run_leier_scrapers.py --priority high          # Documents only
    python run_leier_scrapers.py --priority medium        # Calculators only  
    python run_leier_scrapers.py --priority all           # Both (default)
    python run_leier_scrapers.py --mode test              # Test mode
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from leier_documents_scraper import LeierDocumentsScraper
    from leier_calculator_scraper import LeierCalculatorScraper
except ImportError as e:
    logger.error(f"Failed to import LEIER scrapers: {e}")
    logger.error("Make sure all scraper files are in the same directory")
    sys.exit(1)

# Project configuration
PROJECT_ROOT = Path(__file__).resolve().parents[5]
REPORTS_DIR = PROJECT_ROOT / "leier_scraping_reports"
REPORTS_DIR.mkdir(exist_ok=True)


class LeierScrapingCoordinator:
    """Coordinates all LEIER scraping activities"""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.results = {
            'documents_scraper': None,
            'calculator_scraper': None,
            'start_time': None,
            'end_time': None,
            'total_duration': 0,
            'success': False
        }
        
        if test_mode:
            logger.info("🧪 Running in TEST MODE - limited scraping")
    
    async def run_all_scrapers(self, priority: str = "all") -> Dict[str, Any]:
        """Run scrapers based on priority selection"""
        start_time = datetime.now()
        self.results['start_time'] = start_time
        
        logger.info("🎯 LEIER COMPREHENSIVE SCRAPING INITIATED")
        logger.info(f"📋 Priority Level: {priority.upper()}")
        logger.info(f"🧪 Test Mode: {'ON' if self.test_mode else 'OFF'}")
        logger.info("=" * 70)
        
        results_summary = {
            'coordinator_info': {
                'priority_level': priority,
                'test_mode': self.test_mode,
                'start_time': start_time.isoformat()
            },
            'scrapers_executed': [],
            'overall_success': True,
            'error_count': 0
        }
        
        try:
            # HIGH PRIORITY: Documents Scraper
            if priority in ['high', 'all']:
                logger.info("📄 Executing HIGH PRIORITY: Documents Scraper")
                doc_scraper = LeierDocumentsScraper()
                await doc_scraper.run_full_scrape()
                
                doc_result = {
                    'success': True,
                    'scraper_type': 'documents',
                    'priority': 'HIGH',
                    'stats': doc_scraper.stats
                }
                
                self.results['documents_scraper'] = doc_result
                results_summary['scrapers_executed'].append(doc_result)
                
                if priority == 'all':
                    logger.info("⏸️  Waiting 30 seconds before next scraper...")
                    await asyncio.sleep(30)
            
            # MEDIUM PRIORITY: Calculator Scraper
            if priority in ['medium', 'all']:
                logger.info("🔧 Executing MEDIUM PRIORITY: Calculator Scraper")
                calc_scraper = LeierCalculatorScraper()
                await calc_scraper.run_calculator_scrape()
                
                calc_result = {
                    'success': True,
                    'scraper_type': 'calculators',
                    'priority': 'MEDIUM',
                    'stats': calc_scraper.stats
                }
                
                self.results['calculator_scraper'] = calc_result
                results_summary['scrapers_executed'].append(calc_result)
            
            # Calculate total duration
            end_time = datetime.now()
            self.results['end_time'] = end_time
            self.results['total_duration'] = (end_time - start_time).total_seconds()
            self.results['success'] = True
            
            results_summary['end_time'] = end_time.isoformat()
            results_summary['total_duration_seconds'] = self.results['total_duration']
            
            # Generate comprehensive report
            await self.generate_final_report(results_summary)
            
            return results_summary
            
        except Exception as e:
            logger.error(f"❌ Critical error in scraping coordinator: {e}")
            results_summary['overall_success'] = False
            results_summary['critical_error'] = str(e)
            return results_summary
    
    async def generate_final_report(self, results_summary: Dict[str, Any]):
        """Generate comprehensive final report"""
        logger.info("=" * 80)
        logger.info("📊 LEIER SCRAPING COORDINATOR - FINAL REPORT")
        logger.info("=" * 80)
        
        # Overall summary
        start_time = datetime.fromisoformat(results_summary['coordinator_info']['start_time'])
        end_time = datetime.fromisoformat(results_summary['end_time'])
        duration = results_summary['total_duration_seconds']
        
        logger.info(f"⏱️  Total Duration: {duration:.1f} seconds")
        logger.info(f"🎯 Priority Level: {results_summary['coordinator_info']['priority_level'].upper()}")
        logger.info(f"✅ Overall Success: {results_summary['overall_success']}")
        
        # Individual scraper results
        logger.info("\n📋 Scraper Results:")
        for scraper_result in results_summary['scrapers_executed']:
            scraper_type = scraper_result['scraper_type']
            priority = scraper_result['priority']
            
            logger.info(f"   {scraper_type.upper()} ({priority}): ✅ SUCCESS")
            if 'stats' in scraper_result:
                stats = scraper_result['stats']
                logger.info(f"      Stats: {stats}")
        
        logger.info("=" * 80)
        
        # Save detailed JSON report
        await self.save_json_report(results_summary)
    
    async def save_json_report(self, results_summary: Dict[str, Any]):
        """Save comprehensive JSON report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        priority = results_summary['coordinator_info']['priority_level']
        
        report_filename = f"leier_comprehensive_report_{priority}_{timestamp}.json"
        report_path = REPORTS_DIR / report_filename
        
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Comprehensive report saved: {report_path}")


async def main():
    """Main entry point for LEIER scrapers coordinator"""
    parser = argparse.ArgumentParser(description="LEIER Comprehensive Scraping Solution")
    
    parser.add_argument(
        '--priority', 
        choices=['high', 'medium', 'all'], 
        default='all',
        help='Scraping priority level (default: all)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['normal', 'test'],
        default='normal', 
        help='Execution mode (default: normal)'
    )
    
    args = parser.parse_args()
    
    # Initialize coordinator
    coordinator = LeierScrapingCoordinator(test_mode=(args.mode == 'test'))
    
    # Execute scraping based on priority
    logger.info(f"🚀 Starting LEIER scraping with priority: {args.priority}")
    
    try:
        results = await coordinator.run_all_scrapers(priority=args.priority)
        
        if results['overall_success']:
            logger.info("🎉 LEIER scraping completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ LEIER scraping completed with errors!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Scraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 