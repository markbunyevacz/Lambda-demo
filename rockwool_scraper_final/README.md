# Rockwool Direct Scraper Module

This directory contains the final, working solution for scraping and downloading all PDF product datasheets from the Rockwool Hungary website.

## Architecture

This solution uses a **direct scraping** approach, which is simple, robust, and avoids the complexities and potential inconsistencies of an AI agent-based workflow for the scraping step itself.

The process is as follows:

1.  **MCP Server Connection**: The script initializes a connection to the BrightData MCP (Model Context Protocol) server running locally via `npx @brightdata/mcp`.
2.  **Direct Tool Call**: Instead of asking an AI to choose a tool, the script directly calls the `scrape_as_html` tool on the target Rockwool URL. This is deterministic and reliable.
3.  **HTML Parsing**: The raw HTML content is returned from the tool. The script then uses a specific regular expression to locate and extract the JSON data embedded within the `O74DocumentationList` React component on the page.
4.  **Data Extraction**: The JSON data is parsed to get a list of all products, including their names, descriptions, categories, and direct PDF download URLs.
5.  **Asynchronous PDF Downloading**: The script then uses `httpx` and `asyncio` to download all the found PDFs concurrently, which is highly efficient.

## Parametrization

The scraper is configured using environment variables, which should be stored in a `.env` file in the project root.

*   `BRIGHTDATA_API_TOKEN`: Your API token from your BrightData account. This is required to use the scraping tools.

## Connection Between Elements

-   **`rockwool_scraper_final.py`**: The main executable script. It orchestrates the entire process.
-   **`BrightData MCP Server`**: Provides the powerful, headless-browser scraping capability needed to render the dynamic JavaScript on the Rockwool website.
-   **`httpx` Library**: Used for making efficient, asynchronous HTTP requests to download the PDF files.
-   **`.env` file**: Securely provides the necessary `BRIGHTDATA_API_TOKEN` to the script.

## Role of the AI Agent (in the Broader Project)

It is critical to understand that for **this specific scraping task, the AI agent is NOT used.** We are calling the BrightData tool directly for reliability.

However, the **output** of this module is designed to be the **input** for the AI in the next phase of the project:

1.  **Scraping (This Module):** Produces a clean, structured collection of PDF documents.
2.  **AI Processing (Next Phase):** The AI Agent will be used to perform Retrieval-Augmented Generation (RAG) on the *content* of these downloaded PDFs. It will read, understand, and index the text from these documents to answer user questions about Rockwool products.

This separation of concerns is key:
- **Use direct, reliable code** for predictable tasks like scraping and downloading.
- **Use the powerful AI agent** for complex, language-based tasks like document analysis and Q&A.

## How to Run

Ensure your `.env` file is present in the project root and contains your `BRIGHTDATA_API_TOKEN`.

To run the scraper, execute the following command from the project root:

```bash
python rockwool_scraper_final.py
```

The script will log its progress to the console and save the downloaded PDFs to the `downloads/rockwool_datasheets` directory. 