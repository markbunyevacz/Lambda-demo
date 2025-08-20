# Rockwool Brochure & Pricelist Scraper

This document describes the secondary scraper designed to download brochures, pricelists, and other non-datasheet documents from the Rockwool Hungary website.

## Architecture & Purpose

This scraper complements the main `scraper.py` by targeting a different section of the website:
- **Target URL:** `https://www.rockwool.com/hu/muszaki-informaciok/arlistak-es-prospektusok/`

It follows the same robust, direct-scraping architecture:

1.  **MCP Server Connection**: Connects to the BrightData MCP server.
2.  **Direct Tool Call**: Uses the `scrape_as_html` tool with a `wait_for_selector` parameter (`.o-20-multiple-links__item`) to ensure all dynamic content is loaded.
3.  **Robust Parsing**: It uses the `BeautifulSoup` library to parse the fully-rendered HTML, which is more reliable than regular expressions for this page's structure. It is designed to:
    - Find all document "cards" (`<div class="o-20-multiple-links__item">`).
    - Extract the title from heading tags (`<h6>`).
    - Extract the PDF URL from the download button (`<a>` tag).
4.  **Asynchronous Downloading**: Downloads all found PDFs concurrently.

## Parametrization

This scraper uses the same `.env` configuration as the main scraper:

*   `BRIGHTDATA_API_TOKEN`: Your API token from your BrightData account.

## How to Run

Ensure your `.env` file is present in the project root.

To run this specific scraper, execute the following command from the project root:

```bash
python backend/app/scrapers/rockwool_final/brochure_scraper.py
```

Downloaded files will be saved to the `downloads/rockwool_brochures/` directory, keeping them separate from the technical datasheets.

## Relationship to AI Agent

Just like the main scraper, this module's purpose is **data acquisition only**. The AI agent is **not used** for the scraping process itself.

The brochures and pricelists downloaded by this script are now ready to be used as context for the AI Agent in the next phase of the project, alongside the technical datasheets. 

✅ Égetett kerámia falazóelemek (Fired ceramic masonry elements)
✅ Nyílásáthidalók (Lintels)
✅ Beton zsaluzóelemek (Concrete formwork elements)
✅ Durisol falazóelemek (Durisol masonry elements)
✅ Betoncserepek (Concrete tiles)
✅ Kémények (Chimneys)
✅ Előregyártott falak/födémek/lépcsők (Precast walls/slabs/stairs)
✅ Speciális előregyártott vasbeton elemek (Special precast concrete)
✅ Térburkoló kövek (Paving stones)
✅ Burkolólapok (Tiles)
✅ 12+ additional categories available
✅ Hőszigetelő rendszerek (Thermal insulation systems)
✅ Színes vékonyvakolatok (Colored thin-layer renders)
✅ Homlokzatfestékek (Façade paints)
✅ Aljzatképző ragasztó rendszerek (Substrate adhesive systems)
✅ Homlokzati felújító rendszerek (Façade renovation systems)
✅ Beltéri vakolatok (Interior renders)
✅ Glettek és festékek (Fillers and paints)
✅ StarColor, PuraColor, SilikonColor product lines
✅ Technical Datasheets: Product specifications, installation guides
✅ Price Lists: Comprehensive pricing by category
✅ CAD Files: Technical drawings and dimensions
✅ Installation Manuals: Step-by-step construction guides
✅ Warranty Information: Product guarantees and conditions
✅ Product Catalogs: Complete technical specifications
✅ Application Guides: Professional installation instructions
✅ Color Charts: Baumit Life color collection
✅ System Specifications: Complete system solutions
✅ Training Materials: Professional education content 