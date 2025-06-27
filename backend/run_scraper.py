"""
Unified Scraper Runner for Lambda.hu PROS Scope
"""
import asyncio
import argparse
import logging
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ScraperRunner')

# --- Scraper Imports ---
# Import your scraper functions here as they are created
from app.scrapers.rockwool import run_rockwool_scrape
# from app.scrapers.another_site import run_another_site_scrape


async def main():
    """Main function to run the selected scraper."""
    parser = argparse.ArgumentParser(description="Run a specific scraper.")
    parser.add_argument(
        "scraper",
        type=str,
        help="The name of the scraper to run (e.g., 'rockwool').",
        choices=['rockwool']  # Add new scraper names here
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of items to scrape."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the output JSON file."
    )

    args = parser.parse_args()
    logger.info(f"Runner started for scraper: {args.scraper}")

    result = None
    if args.scraper == 'rockwool':
        result = await run_rockwool_scrape(limit=args.limit)
    # Add other scrapers here with 'elif'
    # elif args.scraper == 'another_site':
    #     result = await run_another_site_scrape(limit=args.limit)

    else:
        logger.error(f"Unknown scraper: {args.scraper}")
        return

    if result:
        logger.info(f"Scraper '{args.scraper}' finished successfully.")
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"Results saved to {args.output}")
            except Exception as e:
                logger.error(f"Failed to save results to {args.output}: {e}")
        else:
            # Pretty print a summary if no output file is specified
            print(json.dumps({
                k: v for k, v in result.items() if k != 'products'
            }, indent=2))
    else:
        logger.warning(f"Scraper '{args.scraper}' did not return any results.")


if __name__ == "__main__":
    # To run: python backend/run_scraper.py rockwool --limit 10
    asyncio.run(main()) 