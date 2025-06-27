# BrightData MCP Complete Setup Documentation

## 📋 Overview

This document provides complete documentation for the **BrightData Model Context Protocol (MCP)** integration in the Lambda.hu project. This setup enables **AI-powered web scraping** with advanced capabilities like CAPTCHA solving, anti-detection, and intelligent data extraction.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Lambda.hu     │    │  BrightData MCP  │    │   BrightData    │
│   Backend       │◄──►│     Server       │◄──►│     Cloud       │
│                 │    │   (Node.js)      │    │   Infrastructure│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐            ┌──────────┐            ┌──────────┐
    │ Claude  │            │   48     │            │ Web      │
    │   AI    │            │ Tools    │            │ Scrapers │
    │ Agent   │            │Available │            │Anti-Bot  │
    └─────────┘            └──────────┘            └──────────┘
```

## 🔧 Required Dependencies & Their Purposes

### 1. Core MCP Framework
```bash
pip install mcp>=1.0.0
```
**Purpose:** Model Context Protocol client/server communication
- `mcp.stdio_client` - Stdio-based MCP client for process communication
- `mcp.StdioServerParameters` - Configuration for MCP server processes
- `mcp.ClientSession` - Session management for MCP connections

**Why needed:** Enables communication between Python backend and Node.js MCP server

### 2. LangChain MCP Integration
```bash
pip install langchain-mcp-adapters>=0.1.7
```
**Purpose:** Bridges MCP tools with LangChain framework
- `langchain_mcp_adapters.tools.load_mcp_tools` - Converts MCP tools to LangChain tools
- Provides seamless integration with AI agents

**Why needed:** Makes BrightData's 48 tools available to LangChain agents

### 3. Claude AI Integration
```bash
pip install langchain-anthropic>=0.3.16
```
**Purpose:** Claude AI model integration for intelligent scraping
- `ChatAnthropic` - Claude model wrapper for LangChain
- Supports Claude 3.5 Sonnet for advanced reasoning

**Why needed:** Provides AI decision-making for complex scraping scenarios

### 4. LangGraph Agent Framework
```bash
pip install langgraph>=0.5.0
```
**Purpose:** Advanced agent orchestration and execution
- `langgraph.prebuilt.chat_agent_executor` - Pre-built chat agent with tool calling
- Manages conversation flow and tool execution

**Why needed:** Orchestrates the AI agent's interaction with BrightData tools

### 5. Core LangChain Framework
```bash
pip install langchain>=0.3.26
```
**Purpose:** Base framework for LLM applications
- Provides foundational classes and utilities
- Memory management, prompt templates, chains

**Why needed:** Foundation for all LangChain-based functionality

### 6. HTTP Streaming Support
```bash
pip install httpx-sse>=0.4.0
```
**Purpose:** Server-Sent Events support for real-time communication
- Enables streaming responses from MCP server
- Real-time status updates during scraping

**Why needed:** Provides responsive feedback during long-running scraping operations

### 7. Node.js Runtime (External Dependency)
**Installation:** Download from [nodejs.org](https://nodejs.org)
**Purpose:** Runtime for BrightData MCP server
- `npx` command for running BrightData MCP server
- Package: `@brightdata/mcp` (auto-installed via npx)

**Why needed:** BrightData MCP server is a Node.js application

## 🔑 API Keys & Environment Configuration

### Required API Keys

#### 1. BrightData API Token
```bash
# Get from: https://brdta.com/techwithtim_mcp
BRIGHTDATA_API_TOKEN=brd_super_proxy_xxxxxxxxxx
BRIGHTDATA_WEB_UNLOCKER_ZONE=web_unlocker
```
**Purpose:** Authentication for BrightData services
- Provides access to web unlocking capabilities
- CAPTCHA solving and anti-detection

#### 2. Anthropic Claude API Key
```bash
# Get from: console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxx
```
**Purpose:** Claude AI model access
- Powers intelligent scraping decisions
- Natural language processing of scraped content

### Environment Variables Setup
Create `.env` file in project root:
```bash
# Core Lambda Configuration
DATABASE_URL=postgresql://admin:admin123@postgres:5432/lambda_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
DEBUG=False
ENVIRONMENT=production

# BrightData MCP Configuration
BRIGHTDATA_API_TOKEN=your-brightdata-token-here
BRIGHTDATA_WEB_UNLOCKER_ZONE=web_unlocker
BRIGHTDATA_BROWSER_AUTH=your-browser-connection-string-here

# Anthropic Claude AI
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# MCP Server Configuration
MCP_SERVER_TIMEOUT=60
MCP_MAX_RETRIES=3
```

## 🚀 Setup Process (Step-by-Step)

### Step 1: Install Python Dependencies
```bash
cd backend

# Install core MCP framework
pip install "mcp>=1.0.0"

# Install LangChain ecosystem
pip install langchain>=0.3.26
pip install langchain-anthropic>=0.3.16
pip install langchain-mcp-adapters>=0.1.7
pip install langgraph>=0.5.0

# Install streaming support
pip install httpx-sse>=0.4.0
```

### Step 2: Verify Node.js Installation
```bash
node --version  # Should show v20.x or higher
npx --version   # Should show 10.x or higher
```

### Step 3: Test BrightData MCP Server
```bash
# Test MCP server installation (auto-downloads on first run)
npx -y @brightdata/mcp
```

### Step 4: Configure Environment Variables
Create `.env` file with your API keys (see above)

### Step 5: Test the Integration
```bash
python run_brightdata_mcp.py
```

## 📁 File Structure & Components

### Core Implementation Files

#### 1. `run_brightdata_mcp.py`
**Purpose:** Standalone AI-powered scraping script
**Key Features:**
- Direct MCP server communication
- Claude AI integration
- JSON result export
- Error handling with detailed logging

#### 2. `app/agents/brightdata_agent.py`
**Purpose:** Production-ready BrightData MCP agent class
**Key Features:**
- Environment validation
- Lazy dependency initialization
- Statistics tracking
- Async operation support

#### 3. `app/celery_tasks/brightdata_tasks.py`
**Purpose:** Background task integration for production
**Key Features:**
- Retry logic with exponential backoff
- Database integration
- Multiple scraping strategies
- Coordination with traditional scrapers

#### 4. `app/agents/scraping_coordinator.py`
**Purpose:** Intelligent strategy selection and fallback logic
**Key Features:**
- 5 different scraping strategies
- Availability testing
- Performance optimization
- Failure handling

## 🛠️ Available BrightData Tools (48 Tools)

Your integration provides access to **48 specialized scraping tools**:

### E-commerce Tools
- `mcp_brightdata_web_data_amazon_product` - Amazon product scraping
- `mcp_brightdata_web_data_walmart_product` - Walmart product data
- `mcp_brightdata_web_data_ebay_product` - eBay product information
- `mcp_brightdata_web_data_etsy_products` - Etsy marketplace data

### Social Media Tools
- `mcp_brightdata_web_data_linkedin_person_profile` - LinkedIn profiles
- `mcp_brightdata_web_data_facebook_posts` - Facebook content
- `mcp_brightdata_web_data_instagram_profiles` - Instagram data
- `mcp_brightdata_web_data_tiktok_profiles` - TikTok profiles

### General Web Scraping
- `mcp_brightdata_scrape_as_markdown` - Any webpage to Markdown
- `mcp_brightdata_scrape_as_html` - Raw HTML extraction
- `mcp_brightdata_search_engine` - Google/Bing search results

### Business Intelligence
- `mcp_brightdata_web_data_crunchbase_company` - Company data
- `mcp_brightdata_web_data_yahoo_finance_business` - Financial data
- `mcp_brightdata_web_data_google_maps_reviews` - Location reviews

## 🎯 Usage Patterns

### 1. Direct Script Usage (Development/Testing)
```bash
# Simple scraping test
python run_brightdata_simple.py

# Full AI-powered scraping
python run_brightdata_mcp.py

# Comprehensive demo
python run_demo_scrape.py
```

### 2. Programmatic Usage (Applications)
```python
import asyncio
from app.agents import BrightDataMCPAgent

async def scrape_products():
    agent = BrightDataMCPAgent()
    
    # Test connection
    status = await agent.test_mcp_connection()
    if not status['success']:
        print(f"MCP not available: {status['error']}")
        return
    
    # AI-powered scraping
    urls = ["https://www.rockwool.hu/termekek/"]
    products = await agent.scrape_rockwool_with_ai(urls)
    
    print(f"Scraped {len(products)} products")
    return products

# Run the scraper
results = asyncio.run(scrape_products())
```

### 3. Background Task Usage (Production)
```python
from app.celery_tasks.brightdata_tasks import ai_powered_rockwool_scraping

# Schedule background scraping
task = ai_powered_rockwool_scraping.delay(
    target_urls=["https://www.rockwool.hu/termekek/"],
    max_products=20,
    save_to_database=True
)

# Get results
result = task.get()
print(f"Background scraping completed: {result['scraped_products']} products")
```

## 🔄 Scraping Strategy System

### Available Strategies

#### 1. `API_ONLY`
- **Use case:** Fast, reliable PDF datasheet extraction
- **Pros:** Fast, consistent, low cost
- **Cons:** Limited data richness

#### 2. `MCP_ONLY`
- **Use case:** Complex sites with JavaScript/CAPTCHA
- **Pros:** Maximum data richness, handles any site
- **Cons:** Slower, higher cost

#### 3. `API_FALLBACK_MCP` ⭐ **Recommended**
- **Use case:** Production environment with reliability
- **Pros:** Optimal balance of speed and richness
- **Logic:** Try API first, fall back to MCP if insufficient data

#### 4. `MCP_FALLBACK_API`
- **Use case:** Data richness priority
- **Pros:** Maximum data collection
- **Logic:** Try MCP first, fall back to API if MCP fails

#### 5. `PARALLEL`
- **Use case:** Speed priority, high resource availability
- **Pros:** Fastest results, maximum data
- **Cons:** Highest resource usage

## 🐛 Troubleshooting Guide

### Common Issues & Solutions

#### 1. "MCP dependencies missing"
**Error:** `cannot import name 'stdio' from 'mcp'`
**Solution:**
```bash
pip uninstall mcp -y
pip install "mcp>=1.0.0"
```

#### 2. "No module named 'langgraph.prebuilts'"
**Error:** Import error for langgraph
**Solution:**
```bash
pip install langgraph>=0.5.0
# Note: Use 'prebuilt' not 'prebuilts'
```

#### 3. "npx command not found"
**Error:** Node.js not installed or not in PATH
**Solution:**
```bash
# Windows
winget install OpenJS.NodeJS
# Or download from https://nodejs.org
```

#### 4. "BrightData API token invalid"
**Error:** 401 Authentication error
**Solution:**
- Check `.env` file exists and is loaded
- Verify token format: `brd_super_proxy_xxxxxxxxxx`
- Check BrightData dashboard for token status

## 💡 Best Practices

### 1. Resource Management
- Use connection pooling for high-volume scraping
- Implement rate limiting to respect target sites
- Monitor API usage to avoid overages

### 2. Error Handling
- Always implement try-catch for MCP operations
- Use exponential backoff for retries
- Log detailed error information for debugging

### 3. Data Quality
- Validate scraped data before database storage
- Implement data normalization and cleaning
- Use AI validation for complex data structures

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-27  
**Author:** Lambda.hu Development Team  
**Status:** Production Ready ✅ 