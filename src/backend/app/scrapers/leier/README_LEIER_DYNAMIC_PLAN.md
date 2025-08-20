# LEIER Dynamic Content Scraping Plan

This document outlines the strategy for scraping the LEIER website, which relies heavily on JavaScript for dynamic content loading. This plan leverages the BrightData MCP's advanced capabilities, building upon the successful architecture used for the ROCKWOOL and BAUMIT projects.

## 1. Core Challenge

The existing LEIER scraper failed because it only reads the initial static HTML, which does not contain the document or product links. The actual content is loaded dynamically via JavaScript (AJAX) after the initial page load.

## 2. Technical Solution & Architecture

We will implement an enhanced scraper that utilizes browser automation capabilities to render JavaScript and extract the fully-loaded content.

### Key Capabilities:
- **Browser Automation**: We will use the **BrightData Scraping Browser** integrated into our `run_brightdata_mcp.py` script. This provides full browser rendering without the need for a local Selenium or Playwright setup, significantly speeding up development.
- **JavaScript Rendering**: The Scraping Browser will execute all on-page JavaScript, just like a real user's browser.
- **Dynamic Content Waiting**: The scraper will be configured to wait for specific elements (e.g., the document list container) to appear on the page before attempting to extract data. This ensures we scrape the final, fully-rendered HTML.
- **AJAX Endpoint Discovery (Future Optimization)**: While full browser rendering is the primary strategy, we can later analyze the network requests made by the Scraping Browser to identify direct API/AJAX endpoints. Calling these endpoints directly can be a more efficient long-term solution.

### Architectural Reuse:
We will adapt the existing `leier_documents_scraper.py` and `run_leier_scrapers.py` scripts to incorporate these new features, maintaining our proven modular and resilient architecture.

## 3. Implementation Steps

1.  **Enhance BrightData Integration**: Modify the scraper to use BrightData's `scrape_as_html` tool with parameters that enable full JavaScript rendering and content waiting (e.g., `wait_for_selector`).
2.  **Identify Target Selectors**: Analyze the LEIER "dokumentumtar" page to find unique CSS selectors for the container that holds the document links once they are loaded.
3.  **Update Extraction Logic**: Refine the BeautifulSoup parsing logic to correctly identify and extract links from the dynamically-rendered HTML structure.
4.  **Create New Coordinator**: Develop a new master script (`run_leier_dynamic_scraper.py`) to execute and test the enhanced scraper.
5.  **Test and Validate**: Run the dynamic scraper in test mode to confirm successful extraction of document links before proceeding to a full production run.

This plan allows us to systematically solve the dynamic content challenge and successfully extract the required data from the LEIER website. 