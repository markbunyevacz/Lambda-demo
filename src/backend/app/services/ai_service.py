
import os
import json
import logging
from typing import Dict, List, Any

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeAIAnalyzer:
    """Real Claude AI analysis for PDF content - no simulations"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ ANTHROPIC_API_KEY not found in environment variables"
            )
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"
        
        logger.info(f"✅ Claude AI initialized: {self.model}")
    
    async def claude_api_call(self, prompt: str) -> str:
        """Simple Claude API call for raw text extraction"""
        
        try:
            # Call Claude API directly with raw prompt
            response = self.client.messages.create(
                model=self.model,
                max_tokens=12000,
                temperature=0.0,  # Low temperature for factual extraction
                system="I need losless extration from this PDF, without summarization, agrregation and compress of text",
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Return raw response text
            response_text = response.content[0].text
            response_len = len(response_text)
            logger.info(f"✅ Claude API call complete, length: {response_len}")
            return response_text
            
        except Exception as e:
            logger.error(f"❌ Claude API call error: {e}")
            raise

    async def analyze_rockwool_pdf(
        self, text_content: str, tables_data: List[Dict], filename: str
    ) -> Dict[str, Any]:
        """Analyze ROCKWOOL PDF content with Claude AI"""
        
        # Prepare context for Claude
        context = self._prepare_analysis_context(text_content, tables_data, filename)
        
        # Create prompt for structured extraction
        prompt = self._create_extraction_prompt(context)
        
        try:
            # Call Claude API using the async method
            response_text = await self.claude_api_call(prompt)
            
            # Parse Claude's response
            analysis_result = self._parse_claude_response(response_text)
            
            logger.info(f"✅ Claude analysis complete for {filename}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            # Return a safe fallback structure
            return {
                "product_identification": {},
                "technical_specifications": {},
                "extraction_metadata": {
                    "confidence_score": 0.0,
                    "extraction_method": "failed",
                    "error": str(e),
                    "found_fields": [],
                    "missing_fields": ["all"]
                }
            }
    
    def _prepare_analysis_context(
        self, text: str, tables: List[Dict], filename: str
    ) -> Dict[str, Any]:
        """Prepare context for Claude analysis"""
        
        context = {
            "filename": filename,
            "text_length": len(text),
            "tables_count": len(tables),
            "extracted_text": text[:8000],  # Limit text for API
            "tables_summary": [],
        }
        
        # Summarize tables
        for table in tables[:5]:  # Limit to first 5 tables
            table_summary = {
                "page": table.get("page", "unknown"),
                "headers": table.get("headers", []),
                "row_count": len(table.get("data", [])),
                "sample_data": table.get("data", [])[:3],  # First 3 rows
            }
            context["tables_summary"].append(table_summary)
        
        return context
    
    def _create_extraction_prompt(self, context: Dict[str, Any]) -> str:
        """Create a dynamic, adaptive prompt for Claude based on actual PDF content."""
        
        # Analyze the PDF content structure first
        content_analysis = self._analyze_pdf_structure(context)
        
        # Build adaptive prompt based on what we actually found
        prompt = f"""
🔍 DINAMIKUS TARTALOM ELEMZÉS - '{context['filename']}'

📊 AUTOMATIKUS STRUKTÚRA FELISMERÉS:
{content_analysis['structure_summary']}

🎯 ADAPTÍV KINYERÉSI STRATÉGIA:
{content_analysis['extraction_strategy']}

📋 TALÁLT TARTALOM TÍPUSOK:
{content_analysis['content_type']}

DOKUMENTUM TARTALOM:
{context['extracted_text']}
"""
        
        # Add tables only if they exist and are meaningful
        if context["tables_summary"] and content_analysis['has_meaningful_tables']:
            prompt += f"\n\n🔍 TÁBLÁZAT ADATOK ({len(context['tables_summary'])} db):\n"
            for i, table in enumerate(context["tables_summary"], 1):
                prompt += f"\nTáblázat {i}:\n"
                prompt += f"Fejlécek: {table['headers']}\n"
                prompt += f"Adatok: {table['sample_data']}\n"
        
        # Dynamic field mapping based on content
        field_mapping = self._generate_dynamic_field_mapping(content_analysis)
        prompt += f"\n\n🗺️ DINAMIKUS MEZŐ LEKÉPEZÉS:\n{field_mapping}\n"
        
        # Adaptive extraction instructions
        prompt += f"""
🤖 ADAPTÍV KINYERÉSI UTASÍTÁSOK:

1. TARTALOM ALAPÚ MEGKÖZELÍTÉS:
   - Elemezd a tényleges tartalmat, ne keress előre definiált mezőket
   - Azonosítsd a műszaki adatokat bárhol is legyenek
   - Használd a kontextust az adatok értelmezéséhez

2. DINAMIKUS STRUKTÚRA KEZELÉS:
   - Ha táblázat van → prioritás a táblázat adatoknak
   - Ha csak szöveg van → regex és pattern matching
   - Ha vegyes tartalom → kombináld a módszereket

3. ADAPTÍV KIMENETI SÉMA:
   - Csak azokat a mezőket add vissza, amik ténylegesen megtalálhatók
   - Null értékek helyett hagyd ki a hiányzó mezőket
   - Confidence score legyen reális a talált adatok alapján

4. MINŐSÉGI VALIDÁCIÓ:
   - Ellenőrizd az értékek konzisztenciáját
   - Mértékegységek és szabványok pontossága
   - Logikus értéktartományok (pl. λ: 0.02-0.1 W/mK)

📤 KIMENETI JSON FORMÁTUM (DINAMIKUS):
{{
  "product_identification": {{
    // Csak a ténylegesen talált adatok
    {content_analysis['likely_fields']['product_identification']}
  }},
  "technical_specifications": {{
    // Csak a PDF-ben szereplő műszaki adatok
    {content_analysis['likely_fields']['technical_specifications']}
  }},
  "extraction_metadata": {{
    "content_type": "{content_analysis['content_type']}",
    "extraction_method": "{content_analysis['best_extraction_method']}",
    "data_completeness": "0.0-1.0 között",
    "confidence_score": "0.0-1.0 között",
    "found_fields": ["lista", "a", "talált", "mezőkről"],
    "missing_fields": ["lista", "a", "hiányzó", "mezőkről"]
  }}
}}

⚡ KRITIKUS: Ne használj sablont! Elemezd a tényleges tartalmat és csak azt 
add vissza, amit ténylegesen megtalálsz!
"""
        
        return prompt
    
    def _analyze_pdf_structure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the actual PDF structure to determine extraction strategy."""
        
        text = context['extracted_text'].lower()
        tables = context['tables_summary']
        
        analysis = {
            'content_type': 'unknown',
            'has_meaningful_tables': False,
            'extraction_strategy': 'text_based',
            'structure_summary': '',
            'likely_fields': {
                'product_identification': {},
                'technical_specifications': {}
            },
            'best_extraction_method': 'pattern_matching'
        }
        
        # Detect content type
        if 'rockwool' in text or 'hőszigetelés' in text:
            analysis['content_type'] = 'insulation_datasheet'
        elif 'árlista' in text or 'ár' in text:
            analysis['content_type'] = 'price_list'
        elif 'műszaki' in text or 'technical' in text:
            analysis['content_type'] = 'technical_spec'
        
        # Analyze tables
        if tables:
            meaningful_tables = 0
            for table in tables:
                if len(table.get('headers', [])) > 1 and len(table.get('sample_data', [])) > 0:
                    meaningful_tables += 1
            
            if meaningful_tables > 0:
                analysis['has_meaningful_tables'] = True
                analysis['extraction_strategy'] = 'table_based'
                analysis['best_extraction_method'] = 'table_parsing'
        
        # Detect likely fields based on content
        tech_specs = analysis['likely_fields']['technical_specifications']
        if 'λ' in text or 'hővezetési' in text:
            tech_specs['thermal_conductivity'] = 'expected'
        if 'tűzvédelmi' in text or 'fire' in text:
            tech_specs['fire_classification'] = 'expected'
        if 'testsűrűség' in text or 'density' in text:
            tech_specs['density'] = 'expected'
        
        # Generate structure summary
        analysis['structure_summary'] = f"""
- Tartalom típus: {analysis['content_type']}
- Táblázatok: {len(tables)} db ({'jelentős' if analysis['has_meaningful_tables'] else 'kevés adat'})
- Szöveg hossz: {context['text_length']} karakter
- Ajánlott módszer: {analysis['best_extraction_method']}
"""
        
        return analysis
    
    def _generate_dynamic_field_mapping(self, analysis: Dict[str, Any]) -> str:
        """Generate field mapping based on content analysis."""
        
        mapping = "DINAMIKUS MEZŐ FELISMERÉS:\n"
        
        # Hungarian technical terms that might appear
        hungarian_terms = {
            'hővezetési tényező': 'thermal_conductivity',
            'λd': 'thermal_conductivity', 
            'lambda': 'thermal_conductivity',
            'tűzvédelmi osztály': 'fire_classification',
            'testsűrűség': 'density',
            'ρ': 'density',
            'nyomószilárdság': 'compressive_strength',
            'páradiffúziós': 'vapor_resistance',
            'μ': 'vapor_resistance',
            'vízfelvétel': 'water_absorption',
            'ws': 'water_absorption',
            'wl': 'water_absorption'
        }
        
        for hu_term, en_key in hungarian_terms.items():
            mapping += f"- '{hu_term}' → {en_key}\n"
        
        mapping += "\n🎯 ADAPTÍV STRATÉGIA: Keress hasonló kifejezéseket és értelmezd a kontextus alapján!"
        
        return mapping
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's dynamic JSON response - adapts to actual content"""
        
        logger.debug(f"📝 Parsing Claude response (length: {len(response_text)})")
        
        # ✅ ENHANCED: More flexible JSON pattern matching for Claude responses
        json_patterns = [
            (r'\{(?:[^{}]*\{[^{}]*\}[^{}]*)*[^{}]*\}', "complete JSON object"),
            (r'```json\s*(\{.*?\})\s*```', "JSON code block"),
            (r'```\s*(\{.*?\})\s*```', "code block"),
            (r'\{[\s\S]*?\}(?=\s*$|\s*\n\s*[A-Z])', "JSON at end of response"),
            (r'(?:json|JSON)[\s:]*(\{[\s\S]*?\})', "labeled JSON block"),
        ]
        
        for pattern, description in json_patterns:
            import re
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean the JSON text
                    json_text = match.strip()
                    if json_text.startswith('json'):
                        json_text = json_text[4:].strip()
                    
                    result = json.loads(json_text)
                    logger.info(f"✅ JSON parsed successfully using {description}")
                    
                    # Dynamic validation - only check for what we actually expect
                    self._validate_dynamic_structure(result)
                    
                    # Enhance with extraction metadata
                    result = self._enhance_with_metadata(result)
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"❌ Failed to parse {description}: {e}")
                    continue
        
        # Fallback: look for simple JSON block boundaries
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                
                # Try to fix common JSON issues
                json_text = self._clean_json_text(json_text)
                
                result = json.loads(json_text)
                logger.info("✅ JSON parsed using fallback method")
                
                # Dynamic validation and enhancement
                self._validate_dynamic_structure(result)
                result = self._enhance_with_metadata(result)
                
                return result
            else:
                logger.warning("⚠️ No JSON boundaries found in response")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.debug(f"Problematic JSON text: {json_text[:200]}...")
        except Exception as e:
            logger.error(f"❌ Unexpected error during JSON parsing: {e}")
        
        # Final fallback: return error structure
        logger.warning("⚠️ Using fallback response structure")
        return {
            "product_identification": {},
            "technical_specifications": {},
            "extraction_metadata": {
                "confidence_score": 0.0,
                "extraction_method": "failed",
                "error": "No valid JSON found in Claude response",
                "found_fields": [],
                "missing_fields": ["all"],
                "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }
        }
    
    def _clean_json_text(self, json_text: str) -> str:
        """✅ ENHANCED: Clean JSON text to fix common Claude AI response issues"""
        
        import re
        
        # Remove any trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Replace single quotes with double quotes (common AI mistake)
        json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)
        json_text = re.sub(r":\s*'([^']*)'", r': "\1"', json_text)
        
        # Fix Hungarian characters and Unicode issues
        hungarian_fixes = {
            '\u00e9': 'é', '\u0151': 'ő', '\u00f3': 'ó', '\u00e1': 'á',
            '\u00f6': 'ö', '\u00fc': 'ü', '\u00ed': 'í', '\u00fa': 'ú', 
            '\u0171': 'ű', '\u0170': 'Ű', '\u0150': 'Ő'
        }
        for unicode_char, normal_char in hungarian_fixes.items():
            json_text = json_text.replace(unicode_char, normal_char)
        
        # Remove comments and explanatory text
        json_text = re.sub(r'//.*$', '', json_text, flags=re.MULTILINE)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        # Remove common Claude explanation prefixes
        json_text = re.sub(r'^[^{]*(?=\{)', '', json_text)
        json_text = re.sub(r'\}[^}]*$', '}', json_text)
        
        # Fix newlines and spacing
        json_text = re.sub(r'\n\s*\n', '\n', json_text)
        
        return json_text.strip()
    
    def _validate_dynamic_structure(self, result: Dict[str, Any]) -> None:
        """Validate structure dynamically based on what was actually found"""
        
        # Ensure basic structure exists
        if "product_identification" not in result:
            result["product_identification"] = {}
        if "technical_specifications" not in result:
            result["technical_specifications"] = {}
        if "extraction_metadata" not in result:
            result["extraction_metadata"] = {}
        
        # Validate technical specifications format
        tech_specs = result.get("technical_specifications", {})
        for key, value in tech_specs.items():
            if isinstance(value, dict):
                # Ensure proper structure for technical values
                if "value" not in value:
                    logger.warning(f"Technical spec {key} missing 'value' field")
                if "unit" not in value:
                    logger.warning(f"Technical spec {key} missing 'unit' field")
    
    def _enhance_with_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance result with extraction metadata"""
        
        from datetime import datetime

        metadata = result.get("extraction_metadata", {})
        
        # Count found fields
        found_fields = []
        if result.get("product_identification"):
            found_fields.extend(result["product_identification"].keys())
        if result.get("technical_specifications"):
            found_fields.extend(result["technical_specifications"].keys())
        
        # Calculate data completeness
        expected_fields = [
            "product_identification.name",
            "technical_specifications.thermal_conductivity",
            "technical_specifications.fire_classification",
            "technical_specifications.density"
        ]
        
        completeness = len(found_fields) / len(expected_fields) if expected_fields else 0
        
        # Update metadata
        metadata.update({
            "found_fields": found_fields,
            "data_completeness": round(completeness, 2),
            "extraction_timestamp": datetime.now().isoformat()
        })
        
        result["extraction_metadata"] = metadata
        
        return result 