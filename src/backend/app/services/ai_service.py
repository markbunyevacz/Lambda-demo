"""
Real AI Service Implementation for Claude Haiku 3.5

This service provides production-ready AI functionality for the Lambda.hu system.
Replaces any mock or placeholder AI implementations with real Anthropic Claude API integration.
"""

import logging
from typing import Dict, List, Any
from anthropic import AsyncAnthropic
from ..config.settings import settings


class BuildingMaterialsAI:
    """
    Production AI service for building materials analysis and recommendations.
    
    This service uses Claude Haiku 3.5 for real PDF content analysis and 
    natural language product recommendations.
    """
    
    def __init__(self):
        """Initialize the AI service with production API clients."""
        # Get API key from environment - PRODUCTION REQUIREMENT
        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in environment for production use. "
                "No mock or placeholder API keys allowed."
            )
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = settings.ai.model_name
        self.temperature = settings.ai.temperature
        self.max_tokens = settings.ai.max_tokens
        
        logging.info("AI service initialized with model: %s", self.model)
    
    async def extract_product_specifications(
        self, 
        pdf_content: str, 
        product_name: str = ""
    ) -> Dict[str, Any]:
        """
        Extract technical specifications from PDF content using Claude Haiku 3.5.
        
        Args:
            pdf_content: Raw text extracted from PDF
            product_name: Optional product name for context
            
        Returns:
            Dictionary with extracted specifications
        """
        try:
            # Production prompt for specification extraction
            prompt = f"""
            Elemezd az alábbi épitőanyag termék dokumentum tartalmát és nyerd ki a műszaki adatokat.
            
            Termék neve (ha ismert): {product_name}
            
            Dokumentum tartalom:
            {pdf_content[:settings.ai.max_text_length]}
            
            Kérlek adj vissza egy strukturált JSON formátumban a következő adatokkal:
            {{
                "termek_azonositas": {{
                    "nev": "termék neve",
                    "gyarto": "gyártó neve",
                    "kategoria": "termék kategória"
                }},
                "muszaki_adatok": {{
                    "hovezetesi_tenyezo": {{"ertek": "érték", "egyseg": "W/mK"}},
                    "tuzvedelem": {{"osztaly": "A1/A2/stb"}},
                    "nyomoszilardsag": {{"ertek": "érték", "egyseg": "kPa"}},
                    "testsureseg": {{"ertek": "érték", "egyseg": "kg/m³"}},
                    "vastagság": {{"ertek": "érték", "egyseg": "mm"}}
                }},
                "alkalmazas": {{
                    "felhasznalasi_terulet": ["lista", "a", "területekről"],
                    "kompatibilis_rendszerek": ["rendszer1", "rendszer2"]
                }},
                "kinyeresi_metaadatok": {{
                    "megbizhatos agi_pontszam": 0.0-1.0,
                    "forrás_minőseg": "magas/közepes/alacsony"
                }}
            }}
            
            Csak a JSON választ add vissza, magyarázat nélkül.
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            import json
            try:
                result = json.loads(response.content[0].text)
                logging.info(f"Successfully extracted specs for: {product_name}")
                return result
            except json.JSONDecodeError:
                logging.error(f"Failed to parse AI response for {product_name}")
                return {
                    "termek_azonositas": {"nev": product_name or "Ismeretlen"},
                    "muszaki_adatok": {},
                    "alkalmazas": {"felhasznalasi_terulet": [], "kompatibilis_rendszerek": []},
                    "kinyeresi_metaadatok": {"megbizhatos agi_pontszam": 0.0, "forrás_minőseg": "alacsony"}
                }
                
        except Exception as e:
            logging.error(f"AI service error for {product_name}: {e}")
            raise
    
    async def get_product_recommendations(
        self, 
        user_query: str, 
        context_products: List[Dict[str, Any]]
    ) -> str:
        """
        Generate product recommendations based on user query and available products.
        
        Args:
            user_query: Natural language query from user
            context_products: List of relevant products from vector search
            
        Returns:
            Hungarian language recommendation text
        """
        try:
            # Create context from products
            product_context = ""
            for idx, product in enumerate(context_products, 1):
                product_context += f"""
                {idx}. {product.get('name', 'Névtelen termék')}
                   - Gyártó: {product.get('manufacturer', 'N/A')}
                   - Kategória: {product.get('category', 'N/A')}
                   - Leírás: {product.get('description', 'Nincs leírás')}
                   - Műszaki adatok: {product.get('technical_specs', {})}
                """
            
            # Production prompt for recommendations
            prompt = f"""
            Te egy építőipari szakértő vagy, aki segít megtalálni a megfelelő építőanyagokat.
            
            Felhasználó kérdése: "{user_query}"
            
            Elérhető termékek a keresés alapján:
            {product_context}
            
            Kérlek adj egy szakértői választ magyar nyelven, amely:
            1. Válaszol a felhasználó kérdésére
            2. Ajánl konkrét termékeket a listából
            3. Megindokolja az ajánlást műszaki szempontokból
            4. Ha releváns, figyelmeztet korlátokra vagy követelményekre
            
            A válasz legyen szakmai, de közérthető.
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            recommendation = response.content[0].text
            logging.info(f"Generated recommendation for query: {user_query}")
            return recommendation
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            return f"Sajnálom, hiba történt az ajánlás generálása során: {str(e)}"
    
    async def analyze_system_compatibility(
        self, 
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze compatibility between multiple building materials.
        
        Args:
            products: List of products to analyze for compatibility
            
        Returns:
            Compatibility analysis results
        """
        try:
            product_specs = ""
            for product in products:
                product_specs += f"- {product.get('name', 'N/A')}: {product.get('technical_specs', {})}\n"
            
            prompt = f"""
            Elemezd az alábbi építőanyagok kompatibilitását egymással:
            
            {product_specs}
            
            Add vissza JSON formátumban:
            {{
                "kompatibilitas_eredmeny": "kompatibilis/részben_kompatibilis/nem_kompatibilis",
                "figyelmeztesek": ["lista", "a", "problémákról"],
                "ajanlasok": ["lista", "az", "ajánlásokról"],
                "szakmai_indoklas": "részletes magyarázat"
            }}
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json
            return json.loads(response.content[0].text)
            
        except Exception as e:
            logging.error(f"Compatibility analysis error: {e}")
            return {
                "kompatibilitas_eredmeny": "nem_elemezheto",
                "figyelmeztesek": ["Hiba történt az elemzés során"],
                "ajanlasok": [],
                "szakmai_indoklas": f"Technikai hiba: {str(e)}"
            }


# Global AI service instance for production use
ai_service = BuildingMaterialsAI()