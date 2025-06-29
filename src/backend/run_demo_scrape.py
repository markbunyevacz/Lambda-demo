"""
DEMO Scraper Indító Szkript
---------------------------

Ez a szkript felelős a DEMO adatgyűjtési folyamatának elindításáért.
Sorban meghívja a scraper-eket, és az eredményeket elmenti az adatbázisba
a DEMO-ra optimalizált `save_product_for_demo` funkció segítségével.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Alapvető logging konfiguráció
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Elfogja a Rockwool oldal hálózati kéréseit, hogy megtaláljuk a helyes API URL-t.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()

        # Eseményfigyelő a hálózati kérések naplózására
        def log_request(request):
            if "api" in request.url and "search" in request.url:
                logging.info(f" >> API KÉRÉS ELFOGVA: {request.method} {request.url}")

        page.on("request", log_request)

        logging.info("A böngésző elindult. Kérlek, navigálj a Termékadatlapok oldalra.")
        logging.info("Kattints a szűrőkre, lapozz, amíg meg nem jelennek az API hívások a konzolon.")
        logging.info("Ha megvan a helyes URL, írj be egy 'q'-t és nyomj Entert a böngésző bezárásához.")

        await page.goto("https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/")
        
        # Várakozás a felhasználói beavatkozásra
        await asyncio.to_thread(input, "Nyomj Entert a kilépéshez, miután megvan az URL...\n")

        await browser.close()

# BrightData MCP Demo funkciók hozzáadása
async def demo_brightdata_mcp():
    """
    BrightData MCP Agent demo funkció
    """
    print("\n" + "="*60)
    print("🤖 BRIGHTDATA MCP AI AGENT DEMO")
    print("="*60)
    
    try:
        from app.agents import BrightDataMCPAgent
        
        # MCP Agent inicializálás
        agent = BrightDataMCPAgent()
        
        # Kapcsolat teszt
        print("📡 BrightData MCP kapcsolat tesztelése...")
        connection_test = await agent.test_mcp_connection()
        
        if connection_test['success']:
            print("✅ BrightData MCP kapcsolat sikeres!")
            print(f"   📋 Státusz: {connection_test['message']}")
            
            # AI-vezérelt scraping demo
            print("\n🎯 AI-vezérelt Rockwool scraping demo...")
            
            demo_urls = [
                "https://www.rockwool.hu",
                "https://www.rockwool.hu/termekek/"
            ]
            
            scraped_products = await agent.scrape_rockwool_with_ai(
                demo_urls, 
                "Gyűjts össze Rockwool termék információkat a demo számára"
            )
            
            print(f"🎉 AI scraping eredmény: {len(scraped_products)} termék")
            
            # Első termék részletei
            if scraped_products:
                sample_product = scraped_products[0]
                print(f"\n📦 Minta termék:")
                print(f"   🏷️  Név: {sample_product.get('name', 'N/A')}")
                print(f"   📝 Kategória: {sample_product.get('category', 'N/A')}")
                print(f"   🔗 URL: {sample_product.get('source_url', 'N/A')}")
            
            # Statisztikák
            stats = agent.get_scraping_statistics()
            print(f"\n📊 AI Scraping statisztikák:")
            print(f"   🎯 Sikeres scraping-ek: {stats['successful_scrapes']}")
            print(f"   ❌ Hibás scraping-ek: {stats['failed_scrapes']}")
            print(f"   📈 Sikerességi arány: {stats.get('success_rate', 0):.1f}%")
            
        else:
            print("❌ BrightData MCP kapcsolat sikertelen!")
            print(f"   🚫 Hiba: {connection_test.get('error', 'Ismeretlen')}")
            print("   💡 Ellenőrizd a környezeti változókat (.env.sample)")
    
    except ImportError:
        print("⚠️  BrightData MCP dependencies hiányoznak")
        print("   📦 Futtasd: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ BrightData MCP demo hiba: {e}")


async def demo_coordinated_scraping():
    """
    Koordinált scraping demo - összes módszer tesztelése
    """
    print("\n" + "="*60)
    print("🎛️  KOORDINÁLT SCRAPING DEMO")
    print("="*60)
    
    try:
        from app.agents import ScrapingCoordinator
        from app.agents.scraping_coordinator import ScrapingStrategy
        
        # Coordinator inicializálás
        coordinator = ScrapingCoordinator()
        
        # Összes scraper tesztelése
        print("🔍 Scraper elérhetőség tesztelése...")
        test_results = await coordinator.test_all_scrapers()
        
        print(f"\n📊 Scraper elérhetőség:")
        print(f"   🤖 API Scraper: {'✅' if test_results['api_scraper']['available'] else '❌'}")
        print(f"   🧠 BrightData MCP: {'✅' if test_results['mcp_agent']['available'] else '❌'}")
        
        recommended_strategy = test_results['coordination']['recommended_strategy']
        print(f"   💡 Ajánlott stratégia: {recommended_strategy}")
        
        # Demo scraping az ajánlott stratégiával
        if recommended_strategy != "NONE_AVAILABLE":
            print(f"\n🚀 Demo scraping - Stratégia: {recommended_strategy}")
            
            # Stratégia beállítás
            if recommended_strategy == ScrapingStrategy.PARALLEL.value:
                coordinator.strategy = ScrapingStrategy.PARALLEL
            elif recommended_strategy == ScrapingStrategy.API_ONLY.value:
                coordinator.strategy = ScrapingStrategy.API_ONLY
            elif recommended_strategy == ScrapingStrategy.MCP_ONLY.value:
                coordinator.strategy = ScrapingStrategy.MCP_ONLY
            
            # Demo scraping
            demo_products = await coordinator.scrape_products(target_input=3)  # 3 termék limit
            
            print(f"🎉 Koordinált scraping eredmény: {len(demo_products)} termék")
            
            # Coordination statisztikák
            coord_stats = coordinator.get_coordination_statistics()
            print(f"\n📈 Koordináció statisztikák:")
            print(f"   ✅ API sikerek: {coord_stats['api_successful']}")
            print(f"   🧠 MCP sikerek: {coord_stats['mcp_successful']}")
            print(f"   🔄 Fallback használat: {coord_stats['fallback_used']}")
            print(f"   📊 Összesített sikerességi arány: {coord_stats['success_rate']:.1f}%")
        else:
            print("❌ Egyik scraper sem elérhető - konfigurációs problémák")
    
    except ImportError:
        print("⚠️  Koordináció dependencies hiányoznak")
    except Exception as e:
        print(f"❌ Koordinált scraping demo hiba: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 