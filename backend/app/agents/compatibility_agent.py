"""
Compatibility Agent - Kompatibilitási Agent

Ez az agent felelős a termékek kompatibilitásának ellenőrzéséért,
műszaki specifikációk összehasonlításáért, alkalmazási területek elemzéséért
és szabványok ellenőrzéséért.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from ..models.product import Product
from ..database import get_db

logger = logging.getLogger(__name__)


class CompatibilityType(Enum):
    """Kompatibilitás típusok"""
    TECHNICAL_SPECS = "technical_specs"
    APPLICATION_AREAS = "application_areas"
    STANDARDS_COMPLIANCE = "standards_compliance"
    INSTALLATION_METHOD = "installation_method"
    ENVIRONMENTAL_CONDITIONS = "environmental_conditions"
    SYSTEM_INTEGRATION = "system_integration"


class CompatibilityLevel(Enum):
    """Kompatibilitási szintek"""
    FULLY_COMPATIBLE = "fully_compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    CONDITIONALLY_COMPATIBLE = "conditionally_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class StandardType(Enum):
    """Szabvány típusok"""
    EN_EUROPEAN = "en_european"
    MSZ_HUNGARIAN = "msz_hungarian"
    ISO_INTERNATIONAL = "iso_international"
    FIRE_SAFETY = "fire_safety"
    THERMAL_PERFORMANCE = "thermal_performance"
    ACOUSTIC_PERFORMANCE = "acoustic_performance"


@dataclass
class CompatibilityResult:
    """Kompatibilitási eredmény adatstruktúra"""
    product_a_id: int
    product_b_id: int
    compatibility_type: CompatibilityType
    compatibility_level: CompatibilityLevel
    confidence_score: float
    reasons: List[str]
    recommendations: List[str]
    technical_notes: List[str]
    checked_at: datetime


@dataclass
class StandardCompliance:
    """Szabványnak való megfelelés adatstruktúra"""
    standard_name: str
    standard_type: StandardType
    compliance_level: str
    requirements: List[str]
    verified: bool
    notes: Optional[str] = None


class CompatibilityAgent:
    """
    Kompatibilitási Agent osztály
    
    Funkcionalitás:
    - Termékek kompatibilitásának ellenőrzése
    - Műszaki specifikációk összehasonlítása
    - Alkalmazási területek elemzése
    - Szabványok ellenőrzése
    - Rendszer integráció elemzése
    - Telepítési módszerek kompatibilitása
    """
    
    def __init__(self, min_confidence_threshold: float = 0.7):
        self.min_confidence_threshold = min_confidence_threshold
        
        # Agent állapot
        self.agent_id = f"compatibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Kompatibilitási cache
        self.compatibility_cache: Dict[Tuple[int, int], List[CompatibilityResult]] = {}
        
        # Kompatibilitási statisztikák
        self.compatibility_stats = {
            'total_checks_performed': 0,
            'fully_compatible_pairs': 0,
            'partially_compatible_pairs': 0,
            'incompatible_pairs': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_check': None,
            'average_confidence': 0.0
        }
        
        # Műszaki paraméter kompatibilitási szabályok
        self.technical_compatibility_rules = {
            'lambda_value': {
                'tolerance_percentage': 15,
                'weight': 0.8,
                'description': 'Hővezetési tényező kompatibilitás'
            },
            'fire_resistance': {
                'exact_match_required': True,
                'weight': 1.0,
                'description': 'Tűzállósági osztály egyezés'
            },
            'density': {
                'tolerance_percentage': 25,
                'weight': 0.6,
                'description': 'Sűrűség kompatibilitás'
            },
            'thickness': {
                'tolerance_percentage': 10,
                'weight': 0.7,
                'description': 'Vastagság kompatibilitás'
            },
            'compressive_strength': {
                'tolerance_percentage': 20,
                'weight': 0.7,
                'description': 'Nyomószilárdság kompatibilitás'
            }
        }
        
        # Alkalmazási terület kompatibilitási mátrix
        self.application_compatibility_matrix = {
            'homlokzat': ['külső fal', 'facade', 'külső'],
            'padlás': ['tetőtér', 'födém', 'tető'],
            'ipari': ['csővezeték', 'tartály', 'berendezés'],
            'tűzvédelem': ['menekülés', 'szerkezetvédelem', 'osztály'],
            'hangszigetelés': ['akusztika', 'zajvédelem', 'studio'],
            'tetőszigetelés': ['fedél', 'vízszigetelés', 'tető']
        }
        
        # Európai szabványok adatbázis
        self.standards_database = {
            'EN 13162': {
                'type': StandardType.THERMAL_PERFORMANCE,
                'description': 'Hőszigetelő termékek gyártva kőzetgyapotból',
                'key_requirements': ['λ érték', 'vastagság tolerancia', 'méretek']
            },
            'EN 13501-1': {
                'type': StandardType.FIRE_SAFETY,
                'description': 'Építőanyagok tűzvédelmi osztályozása',
                'key_requirements': ['Euroclass', 'füstképzés', 'égő cseppek']
            },
            'EN 12667': {
                'type': StandardType.THERMAL_PERFORMANCE,
                'description': 'Hővezetési tényező meghatározás',
                'key_requirements': ['mérési módszer', 'referencia hőmérséklet']
            },
            'MSZ EN 13162': {
                'type': StandardType.EN_EUROPEAN,
                'description': 'Magyar szabvány kőzetgyapot termékekre',
                'key_requirements': ['nemzeti kiegészítések', 'alkalmazási területek']
            }
        }
    
    async def check_compatibility(self, 
                                product_a_id: int, 
                                product_b_id: int,
                                compatibility_types: List[CompatibilityType] = None) -> Dict:
        """
        Főbb kompatibilitás ellenőrzési funkció
        
        Args:
            product_a_id: Első termék ID
            product_b_id: Második termék ID
            compatibility_types: Ellenőrizendő kompatibilitás típusok
            
        Returns:
            Kompatibilitási eredmény és részletek
        """
        start_time = datetime.now()
        
        logger.info(f"Kompatibilitás ellenőrzés - Agent ID: {self.agent_id}")
        logger.info(f"Termékek: {product_a_id} <-> {product_b_id}")
        
        if not compatibility_types:
            compatibility_types = [
                CompatibilityType.TECHNICAL_SPECS,
                CompatibilityType.APPLICATION_AREAS,
                CompatibilityType.STANDARDS_COMPLIANCE
            ]
        
        try:
            # Cache ellenőrzés
            cache_key = (min(product_a_id, product_b_id), max(product_a_id, product_b_id))
            if cache_key in self.compatibility_cache:
                logger.info("Kompatibilitási eredmény cache-ből")
                self.compatibility_stats['cache_hits'] += 1
                cached_results = self.compatibility_cache[cache_key]
                return self._format_compatibility_response(cached_results, True)
            
            self.compatibility_stats['cache_misses'] += 1
            
            # Termékek lekérése
            product_a, product_b = await self._get_products(product_a_id, product_b_id)
            if not product_a or not product_b:
                return {
                    'error': 'Termékek nem találhatók',
                    'product_a_id': product_a_id,
                    'product_b_id': product_b_id
                }
            
            # Kompatibilitási ellenőrzések végrehajtása
            compatibility_results = []
            
            for comp_type in compatibility_types:
                logger.info(f"Ellenőrzés típus: {comp_type.value}")
                
                if comp_type == CompatibilityType.TECHNICAL_SPECS:
                    result = await self._check_technical_compatibility(product_a, product_b)
                elif comp_type == CompatibilityType.APPLICATION_AREAS:
                    result = await self._check_application_compatibility(product_a, product_b)
                elif comp_type == CompatibilityType.STANDARDS_COMPLIANCE:
                    result = await self._check_standards_compatibility(product_a, product_b)
                elif comp_type == CompatibilityType.INSTALLATION_METHOD:
                    result = await self._check_installation_compatibility(product_a, product_b)
                elif comp_type == CompatibilityType.ENVIRONMENTAL_CONDITIONS:
                    result = await self._check_environmental_compatibility(product_a, product_b)
                elif comp_type == CompatibilityType.SYSTEM_INTEGRATION:
                    result = await self._check_system_integration_compatibility(product_a, product_b)
                else:
                    logger.warning(f"Ismeretlen kompatibilitás típus: {comp_type}")
                    continue
                
                if result:
                    compatibility_results.append(result)
            
            # Eredmények cache-elése
            self.compatibility_cache[cache_key] = compatibility_results
            
            # Statisztikák frissítése
            self.compatibility_stats['total_checks_performed'] += 1
            self.compatibility_stats['last_check'] = datetime.now().isoformat()
            
            # Kompatibilitási szintek statisztikája
            overall_level = self._calculate_overall_compatibility(compatibility_results)
            if overall_level == CompatibilityLevel.FULLY_COMPATIBLE:
                self.compatibility_stats['fully_compatible_pairs'] += 1
            elif overall_level == CompatibilityLevel.PARTIALLY_COMPATIBLE:
                self.compatibility_stats['partially_compatible_pairs'] += 1
            elif overall_level == CompatibilityLevel.INCOMPATIBLE:
                self.compatibility_stats['incompatible_pairs'] += 1
            
            # Átlagos konfidencia
            if compatibility_results:
                avg_confidence = sum(r.confidence_score for r in compatibility_results) / len(compatibility_results)
                self.compatibility_stats['average_confidence'] = avg_confidence
            
            response = self._format_compatibility_response(compatibility_results, False)
            response['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Kompatibilitás ellenőrzés befejezve: {overall_level.value}")
            return response
            
        except Exception as e:
            logger.error(f"Kompatibilitás ellenőrzési hiba: {e}")
            return {
                'agent_id': self.agent_id,
                'error': str(e),
                'product_a_id': product_a_id,
                'product_b_id': product_b_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_products(self, product_a_id: int, product_b_id: int) -> Tuple[Optional[Product], Optional[Product]]:
        """Termékek lekérése adatbázisból"""
        try:
            db = get_db()
            product_a = db.query(Product).filter(Product.id == product_a_id).first()
            product_b = db.query(Product).filter(Product.id == product_b_id).first()
            db.close()
            return product_a, product_b
        except Exception as e:
            logger.error(f"Termék lekérési hiba: {e}")
            return None, None
    
    async def _check_technical_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Műszaki specifikációk kompatibilitásának ellenőrzése"""
        logger.info("Műszaki specifikációk kompatibilitás ellenőrzése")
        
        specs_a = product_a.technical_specs or {}
        specs_b = product_b.technical_specs or {}
        
        compatibility_scores = []
        reasons = []
        recommendations = []
        technical_notes = []
        
        # Közös paraméterek ellenőrzése
        common_specs = set(specs_a.keys()) & set(specs_b.keys())
        
        if not common_specs:
            return CompatibilityResult(
                product_a_id=product_a.id,
                product_b_id=product_b.id,
                compatibility_type=CompatibilityType.TECHNICAL_SPECS,
                compatibility_level=CompatibilityLevel.UNKNOWN,
                confidence_score=0.1,
                reasons=['Nincs közös műszaki paraméter'],
                recommendations=['Kérjen további műszaki adatokat'],
                technical_notes=['Hiányos műszaki specifikáció'],
                checked_at=datetime.now()
            )
        
        for spec_name in common_specs:
            if spec_name in self.technical_compatibility_rules:
                rule = self.technical_compatibility_rules[spec_name]
                
                value_a = self._normalize_technical_value(specs_a[spec_name])
                value_b = self._normalize_technical_value(specs_b[spec_name])
                
                if value_a is not None and value_b is not None:
                    if rule.get('exact_match_required', False):
                        # Pontos egyezés szükséges
                        if value_a == value_b:
                            compatibility_scores.append(rule['weight'])
                            reasons.append(f"{rule['description']}: Pontos egyezés ({value_a})")
                        else:
                            compatibility_scores.append(0.0)
                            reasons.append(f"{rule['description']}: Eltérés ({value_a} vs {value_b})")
                            recommendations.append(f"Ellenőrizze a {spec_name} kompatibilitását")
                    else:
                        # Tolerancia alapú egyezés
                        tolerance = rule.get('tolerance_percentage', 10) / 100
                        if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
                            diff_percentage = abs(value_a - value_b) / max(value_a, value_b)
                            
                            if diff_percentage <= tolerance:
                                score = (1 - diff_percentage / tolerance) * rule['weight']
                                compatibility_scores.append(score)
                                reasons.append(f"{rule['description']}: Kompatibilis ({diff_percentage*100:.1f}% eltérés)")
                            else:
                                compatibility_scores.append(0.2)
                                reasons.append(f"{rule['description']}: Nagy eltérés ({diff_percentage*100:.1f}%)")
                                recommendations.append(f"Fontoljon meg alternatívát a {spec_name} miatt")
                                
                        technical_notes.append(f"{spec_name}: {value_a} <-> {value_b}")
        
        # Összesített kompatibilitási pontszám
        if compatibility_scores:
            overall_score = sum(compatibility_scores) / len(compatibility_scores)
        else:
            overall_score = 0.5
        
        # Kompatibilitási szint meghatározása
        if overall_score >= 0.8:
            level = CompatibilityLevel.FULLY_COMPATIBLE
        elif overall_score >= 0.6:
            level = CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif overall_score >= 0.3:
            level = CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        else:
            level = CompatibilityLevel.INCOMPATIBLE
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.TECHNICAL_SPECS,
            compatibility_level=level,
            confidence_score=overall_score,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=technical_notes,
            checked_at=datetime.now()
        )
    
    def _normalize_technical_value(self, value: Any) -> Optional[Any]:
        """Műszaki érték normalizálása"""
        if value is None:
            return None
        
        # Szöveges értékek számra konvertálása
        if isinstance(value, str):
            # Számjegyek kinyerése
            numbers = re.findall(r'\d+\.?\d*', value.replace(',', '.'))
            if numbers:
                try:
                    return float(numbers[0])
                except ValueError:
                    return value.lower().strip()
            return value.lower().strip()
        
        return value
    
    async def _check_application_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Alkalmazási területek kompatibilitásának ellenőrzése"""
        logger.info("Alkalmazási területek kompatibilitás ellenőrzése")
        
        apps_a = set(app.lower() for app in (product_a.applications or []))
        apps_b = set(app.lower() for app in (product_b.applications or []))
        
        # Közvetlen egyezések
        direct_matches = apps_a & apps_b
        
        # Kompatibilis alkalmazások keresése mátrix alapján
        compatible_matches = set()
        for app_a in apps_a:
            for app_b in apps_b:
                if self._are_applications_compatible(app_a, app_b):
                    compatible_matches.add((app_a, app_b))
        
        reasons = []
        recommendations = []
        
        # Értékelés
        if direct_matches:
            confidence = 0.9
            level = CompatibilityLevel.FULLY_COMPATIBLE
            reasons.append(f"Közös alkalmazási területek: {', '.join(direct_matches)}")
        elif compatible_matches:
            confidence = 0.7
            level = CompatibilityLevel.PARTIALLY_COMPATIBLE
            comp_apps = [f"{a} <-> {b}" for a, b in compatible_matches]
            reasons.append(f"Kompatibilis alkalmazások: {', '.join(comp_apps)}")
        elif apps_a and apps_b:
            confidence = 0.3
            level = CompatibilityLevel.CONDITIONALLY_COMPATIBLE
            reasons.append("Nincs közvetlen alkalmazási terület egyezés")
            recommendations.append("Ellenőrizze a specifikus használati feltételeket")
        else:
            confidence = 0.1
            level = CompatibilityLevel.UNKNOWN
            reasons.append("Hiányos alkalmazási terület információ")
            recommendations.append("Kérjen részletes alkalmazási útmutatót")
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.APPLICATION_AREAS,
            compatibility_level=level,
            confidence_score=confidence,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=[f"Termék A: {', '.join(apps_a)}", f"Termék B: {', '.join(apps_b)}"],
            checked_at=datetime.now()
        )
    
    def _are_applications_compatible(self, app_a: str, app_b: str) -> bool:
        """Alkalmazási területek kompatibilitásának ellenőrzése"""
        for base_app, compatible_apps in self.application_compatibility_matrix.items():
            if base_app in app_a and any(comp in app_b for comp in compatible_apps):
                return True
            if base_app in app_b and any(comp in app_a for comp in compatible_apps):
                return True
        return False
    
    async def _check_standards_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Szabványok kompatibilitásának ellenőrzése"""
        logger.info("Szabványok kompatibilitás ellenőrzése")
        
        # Szabványok kinyerése termék adatokból
        standards_a = self._extract_standards_from_product(product_a)
        standards_b = self._extract_standards_from_product(product_b)
        
        reasons = []
        recommendations = []
        technical_notes = []
        
        # Közös szabványok
        common_standards = set(standards_a) & set(standards_b)
        
        if common_standards:
            confidence = 0.9
            level = CompatibilityLevel.FULLY_COMPATIBLE
            reasons.append(f"Közös szabványok: {', '.join(common_standards)}")
        elif standards_a and standards_b:
            # Kompatibilis szabványok ellenőrzése
            compatible_standards = self._find_compatible_standards(standards_a, standards_b)
            if compatible_standards:
                confidence = 0.7
                level = CompatibilityLevel.PARTIALLY_COMPATIBLE
                reasons.append(f"Kompatibilis szabványok: {', '.join(compatible_standards)}")
            else:
                confidence = 0.4
                level = CompatibilityLevel.CONDITIONALLY_COMPATIBLE
                reasons.append("Eltérő szabványok, további ellenőrzés szükséges")
                recommendations.append("Konzultáljon műszaki szakértővel a szabványok kompatibilitásáról")
        else:
            confidence = 0.2
            level = CompatibilityLevel.UNKNOWN
            reasons.append("Hiányos szabvány információ")
            recommendations.append("Kérjen szabványmegfelelőségi tanúsítványokat")
        
        technical_notes.extend([
            f"Termék A szabványok: {', '.join(standards_a) if standards_a else 'Nincs adat'}",
            f"Termék B szabványok: {', '.join(standards_b) if standards_b else 'Nincs adat'}"
        ])
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.STANDARDS_COMPLIANCE,
            compatibility_level=level,
            confidence_score=confidence,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=technical_notes,
            checked_at=datetime.now()
        )
    
    def _extract_standards_from_product(self, product: Product) -> List[str]:
        """Szabványok kinyerése termék adatokból"""
        standards = []
        
        # Szöveges tartalom elemzése
        text_content = f"{product.name} {product.description} {str(product.technical_specs)}"
        
        # Szabvány pattern-ek
        standard_patterns = [
            r'EN\s+\d+[\-\d]*',
            r'MSZ\s+EN\s+\d+[\-\d]*',
            r'MSZ\s+\d+[\-\d]*',
            r'ISO\s+\d+[\-\d]*'
        ]
        
        for pattern in standard_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            standards.extend([match.replace(' ', ' ').upper() for match in matches])
        
        return list(set(standards))  # Duplikátumok eltávolítása
    
    def _find_compatible_standards(self, standards_a: List[str], standards_b: List[str]) -> List[str]:
        """Kompatibilis szabványok keresése"""
        compatible = []
        
        for std_a in standards_a:
            for std_b in standards_b:
                # Ugyanazon szabványcsalád ellenőrzése
                if self._are_standards_compatible(std_a, std_b):
                    compatible.append(f"{std_a} <-> {std_b}")
        
        return compatible
    
    def _are_standards_compatible(self, std_a: str, std_b: str) -> bool:
        """Két szabvány kompatibilitásának ellenőrzése"""
        # EN szabványok általában kompatibilisek
        if 'EN' in std_a and 'EN' in std_b:
            # Alapszám kinyerése
            num_a = re.search(r'\d+', std_a)
            num_b = re.search(r'\d+', std_b)
            if num_a and num_b and num_a.group() == num_b.group():
                return True
        
        # MSZ EN és EN kompatibilitás
        if ('MSZ EN' in std_a and 'EN' in std_b) or ('EN' in std_a and 'MSZ EN' in std_b):
            return True
        
        return False
    
    async def _check_installation_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Telepítési módszerek kompatibilitásának ellenőrzése"""
        logger.info("Telepítési módszerek kompatibilitás ellenőrzése")
        
        # Placeholder implementáció
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.INSTALLATION_METHOD,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.5,
            reasons=['Telepítési módszer ellenőrzés nem implementált'],
            recommendations=['Konzultáljon kivitelezővel'],
            technical_notes=[],
            checked_at=datetime.now()
        )
    
    async def _check_environmental_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Környezeti feltételek kompatibilitásának ellenőrzése"""
        logger.info("Környezeti feltételek kompatibilitás ellenőrzése")
        
        # Placeholder implementáció
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.ENVIRONMENTAL_CONDITIONS,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.5,
            reasons=['Környezeti feltételek ellenőrzés nem implementált'],
            recommendations=['Ellenőrizze a klimatikus feltételeket'],
            technical_notes=[],
            checked_at=datetime.now()
        )
    
    async def _check_system_integration_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Rendszer integráció kompatibilitásának ellenőrzése"""
        logger.info("Rendszer integráció kompatibilitás ellenőrzése")
        
        # Placeholder implementáció  
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.SYSTEM_INTEGRATION,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.5,
            reasons=['Rendszer integráció ellenőrzés nem implementált'],
            recommendations=['Kérjen rendszer tervezői véleményt'],
            technical_notes=[],
            checked_at=datetime.now()
        )
    
    def _calculate_overall_compatibility(self, results: List[CompatibilityResult]) -> CompatibilityLevel:
        """Összesített kompatibilitási szint számítása"""
        if not results:
            return CompatibilityLevel.UNKNOWN
        
        # Legrosszabb szint szerint
        levels = [r.compatibility_level for r in results]
        
        if CompatibilityLevel.INCOMPATIBLE in levels:
            return CompatibilityLevel.INCOMPATIBLE
        elif CompatibilityLevel.CONDITIONALLY_COMPATIBLE in levels:
            return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        elif CompatibilityLevel.PARTIALLY_COMPATIBLE in levels:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif CompatibilityLevel.FULLY_COMPATIBLE in levels:
            return CompatibilityLevel.FULLY_COMPATIBLE
        else:
            return CompatibilityLevel.UNKNOWN
    
    def _format_compatibility_response(self, results: List[CompatibilityResult], from_cache: bool) -> Dict:
        """Kompatibilitási válasz formázása"""
        overall_level = self._calculate_overall_compatibility(results)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'compatibility_type': result.compatibility_type.value,
                'compatibility_level': result.compatibility_level.value,
                'confidence_score': result.confidence_score,
                'reasons': result.reasons,
                'recommendations': result.recommendations,
                'technical_notes': result.technical_notes,
                'checked_at': result.checked_at.isoformat()
            })
        
        return {
            'agent_id': self.agent_id,
            'product_a_id': results[0].product_a_id if results else None,
            'product_b_id': results[0].product_b_id if results else None,
            'overall_compatibility': overall_level.value,
            'compatibility_checks': formatted_results,
            'from_cache': from_cache,
            'summary': {
                'total_checks': len(results),
                'average_confidence': sum(r.confidence_score for r in results) / len(results) if results else 0,
                'highest_confidence_check': max(results, key=lambda r: r.confidence_score).compatibility_type.value if results else None
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def analyze_compatibility_matrix(self, product_ids: List[int]) -> Dict:
        """Termékek kompatibilitási mátrixának elemzése"""
        logger.info(f"Kompatibilitási mátrix elemzés: {len(product_ids)} termék")
        
        compatibility_matrix = {}
        
        for i, product_a_id in enumerate(product_ids):
            for j, product_b_id in enumerate(product_ids):
                if i < j:  # Csak egyszer ellenőrizzük mindkét irányban
                    result = await self.check_compatibility(product_a_id, product_b_id)
                    
                    key = f"{product_a_id}_{product_b_id}"
                    compatibility_matrix[key] = {
                        'overall_compatibility': result.get('overall_compatibility'),
                        'average_confidence': result.get('summary', {}).get('average_confidence', 0)
                    }
        
        # Statisztikák
        compatibility_levels = [entry['overall_compatibility'] for entry in compatibility_matrix.values()]
        
        return {
            'agent_id': self.agent_id,
            'matrix_size': f"{len(product_ids)}x{len(product_ids)}",
            'total_comparisons': len(compatibility_matrix),
            'compatibility_matrix': compatibility_matrix,
            'statistics': {
                'fully_compatible_pairs': compatibility_levels.count(CompatibilityLevel.FULLY_COMPATIBLE.value),
                'partially_compatible_pairs': compatibility_levels.count(CompatibilityLevel.PARTIALLY_COMPATIBLE.value),
                'conditionally_compatible_pairs': compatibility_levels.count(CompatibilityLevel.CONDITIONALLY_COMPATIBLE.value),
                'incompatible_pairs': compatibility_levels.count(CompatibilityLevel.INCOMPATIBLE.value),
                'unknown_pairs': compatibility_levels.count(CompatibilityLevel.UNKNOWN.value)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_compatibility_statistics(self) -> Dict:
        """Kompatibilitási statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            'statistics': self.compatibility_stats.copy(),
            'cache_info': {
                'cached_comparisons': len(self.compatibility_cache),
                'cache_hit_rate': (
                    self.compatibility_stats['cache_hits'] / 
                    max(self.compatibility_stats['cache_hits'] + self.compatibility_stats['cache_misses'], 1)
                ) * 100
            },
            'standards_database_size': len(self.standards_database),
            'compatibility_rules_count': len(self.technical_compatibility_rules),
            'timestamp': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        health_status = {
            'agent_id': self.agent_id,
            'healthy': True,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Adatbázis kapcsolat ellenőrzés
            try:
                db = get_db()
                db.query(Product).count()
                db.close()
            except Exception as e:
                health_status['errors'].append(f'Adatbázis kapcsolat hiba: {str(e)}')
                health_status['healthy'] = False
            
            # Kompatibilitási szabályok ellenőrzése
            if not self.technical_compatibility_rules:
                health_status['errors'].append('Műszaki kompatibilitási szabályok nincsenek betöltve')
                health_status['healthy'] = False
            
            # Szabványok adatbázis ellenőrzése
            if not self.standards_database:
                health_status['errors'].append('Szabványok adatbázis nincs betöltve')
                health_status['healthy'] = False
            
            # Cache integritás ellenőrzés
            corrupted_cache_entries = 0
            for key, results in self.compatibility_cache.items():
                if not isinstance(results, list) or not all(isinstance(r, CompatibilityResult) for r in results):
                    corrupted_cache_entries += 1
            
            if corrupted_cache_entries > 0:
                health_status['errors'].append(f'{corrupted_cache_entries} sérült cache bejegyzés')
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['errors'].append(f'Health check hiba: {str(e)}')
        
        return health_status 