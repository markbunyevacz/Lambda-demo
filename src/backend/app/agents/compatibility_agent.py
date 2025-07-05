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
from functools import lru_cache

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
        self.agent_id = f"compatibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.compatibility_cache: Dict[Tuple[int, int], List[CompatibilityResult]] = {}
        self.compatibility_stats = self._initialize_stats()
        
        self.technical_compatibility_rules = self._load_technical_rules()
        self.application_compatibility_matrix = self._load_application_matrix()
        self.standards_database = self._load_standards_database()
        
        self.check_dispatch_table = self._initialize_dispatch_table()

    def _initialize_stats(self) -> Dict[str, Any]:
        """Inicializálja a statisztikai szótárat."""
        return {
            'total_checks_performed': 0,
            'fully_compatible_pairs': 0,
            'partially_compatible_pairs': 0,
            'incompatible_pairs': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_check': None,
            'average_confidence': 0.0
        }

    def _load_technical_rules(self) -> Dict[str, Any]:
        """Betölti a műszaki kompatibilitási szabályokat."""
        return {
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

    def _load_application_matrix(self) -> Dict[str, List[str]]:
        """Betölti az alkalmazási terület kompatibilitási mátrixot."""
        return {
            'homlokzat': ['külső fal', 'facade', 'külső'],
            'padlás': ['tetőtér', 'födém', 'tető'],
            'ipari': ['csővezeték', 'tartály', 'berendezés'],
            'tűzvédelem': ['menekülés', 'szerkezetvédelem', 'osztály'],
            'hangszigetelés': ['akusztika', 'zajvédelem', 'studio'],
            'tetőszigetelés': ['fedél', 'vízszigetelés', 'tető']
        }

    def _load_standards_database(self) -> Dict[str, Any]:
        """Betölti a szabványok adatbázisát."""
        return {
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
    
    def _initialize_dispatch_table(self) -> Dict[CompatibilityType, Any]:
        """Inicializálja a check-függvények diszpécser tábláját."""
        return {
            CompatibilityType.TECHNICAL_SPECS: self._check_technical_compatibility,
            CompatibilityType.APPLICATION_AREAS: self._check_application_compatibility,
            CompatibilityType.STANDARDS_COMPLIANCE: self._check_standards_compatibility,
            CompatibilityType.INSTALLATION_METHOD: self._check_installation_compatibility,
            CompatibilityType.ENVIRONMENTAL_CONDITIONS: self._check_environmental_compatibility,
            CompatibilityType.SYSTEM_INTEGRATION: self._check_system_integration_compatibility,
        }
    
    async def check_compatibility(self, 
                                product_a_id: int, 
                                product_b_id: int,
                                compatibility_types: Optional[List[CompatibilityType]] = None) -> Dict:
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
        
        effective_compatibility_types = compatibility_types or [
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
            tasks = []
            for comp_type in effective_compatibility_types:
                check_method = self.check_dispatch_table.get(comp_type)
                if check_method:
                    logger.info(f"Ellenőrzés típus ütemezve: {comp_type.value}")
                    tasks.append(check_method(product_a, product_b))
                else:
                    logger.warning(f"Ismeretlen kompatibilitás típus: {comp_type}")

            compatibility_results = [result for result in await asyncio.gather(*tasks) if result]
            
            # Eredmények cache-elése
            self.compatibility_cache[cache_key] = compatibility_results
            
            # Statisztikák frissítése
            self._update_statistics(compatibility_results)
            
            response = self._format_compatibility_response(compatibility_results, False)
            response['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Kompatibilitás ellenőrzés befejezve: {response.get('overall_compatibility')}")
            return response
            
        except Exception as e:
            logger.error(f"Kompatibilitás ellenőrzési hiba: {e}", exc_info=True)
            return {
                'agent_id': self.agent_id,
                'error': str(e),
                'product_a_id': product_a_id,
                'product_b_id': product_b_id,
                'timestamp': datetime.now().isoformat()
            }

    def _update_statistics(self, compatibility_results: List[CompatibilityResult]):
        """Frissíti a kompatibilitási statisztikákat."""
        self.compatibility_stats['total_checks_performed'] += 1
        self.compatibility_stats['last_check'] = datetime.now().isoformat()
        
        overall_level = self._calculate_overall_compatibility(compatibility_results)
        if overall_level == CompatibilityLevel.FULLY_COMPATIBLE:
            self.compatibility_stats['fully_compatible_pairs'] += 1
        elif overall_level == CompatibilityLevel.PARTIALLY_COMPATIBLE:
            self.compatibility_stats['partially_compatible_pairs'] += 1
        elif overall_level == CompatibilityLevel.INCOMPATIBLE:
            self.compatibility_stats['incompatible_pairs'] += 1
        
        if compatibility_results:
            avg_confidence = sum(r.confidence_score for r in compatibility_results) / len(compatibility_results)
            # EMA (Exponential Moving Average) for average confidence
            alpha = 0.1
            current_avg = self.compatibility_stats.get('average_confidence', 0.0)
            self.compatibility_stats['average_confidence'] = alpha * avg_confidence + (1 - alpha) * current_avg

    @lru_cache(maxsize=128)
    def _get_db_session(self):
        return get_db()

    async def _get_products(self, product_a_id: int, product_b_id: int) -> Tuple[Optional[Product], Optional[Product]]:
        """Termékek lekérése adatbázisból"""
        try:
            db = self._get_db_session()
            product_a = db.query(Product).filter(Product.id == product_a_id).first()
            product_b = db.query(Product).filter(Product.id == product_b_id).first()
            return product_a, product_b
        except Exception as e:
            logger.error(f"Termék lekérési hiba: {e}")
            return None, None
        finally:
            if db:
                db.close()
    
    def _check_single_spec(self, spec_name: str, value_a: Any, value_b: Any) -> Tuple[Optional[float], str, Optional[str]]:
        """Egyetlen műszaki paraméter kompatibilitását ellenőrzi."""
        rule = self.technical_compatibility_rules[spec_name]
        normalized_a = self._normalize_technical_value(value_a)
        normalized_b = self._normalize_technical_value(value_b)

        if normalized_a is None or normalized_b is None:
            return None, f"{rule['description']}: Hiányzó érték.", None

        if rule.get('exact_match_required', False):
            if normalized_a == normalized_b:
                return rule['weight'], f"{rule['description']}: Pontos egyezés ({normalized_a})", None
            else:
                return 0.0, f"{rule['description']}: Eltérés ({normalized_a} vs {normalized_b})", f"Ellenőrizze a {spec_name} kompatibilitását"
        
        if isinstance(normalized_a, (int, float)) and isinstance(normalized_b, (int, float)):
            if max(normalized_a, normalized_b) == 0:
                return rule['weight'] if normalized_a == normalized_b else 0.0, f"{rule['description']}: Egyik érték sem nulla.", None

            tolerance = rule.get('tolerance_percentage', 10) / 100
            diff_percentage = abs(normalized_a - normalized_b) / max(normalized_a, normalized_b)
            
            if diff_percentage <= tolerance:
                score = (1 - diff_percentage / tolerance) * rule['weight']
                return score, f"{rule['description']}: Kompatibilis ({diff_percentage*100:.1f}% eltérés)", None
            else:
                return 0.2, f"{rule['description']}: Nagy eltérés ({diff_percentage*100:.1f}%)", f"Fontoljon meg alternatívát a {spec_name} miatt"

        return None, f"{rule['description']}: Nem numerikus értékek", None

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
        common_spec_names = set(specs_a.keys()) & set(specs_b.keys()) & set(self.technical_compatibility_rules.keys())
        
        if not common_spec_names:
            return CompatibilityResult(
                product_a_id=product_a.id,
                product_b_id=product_b.id,
                compatibility_type=CompatibilityType.TECHNICAL_SPECS,
                compatibility_level=CompatibilityLevel.UNKNOWN,
                confidence_score=0.1,
                reasons=['Nincs közös, szabályozott műszaki paraméter'],
                recommendations=['Kérjen további műszaki adatokat'],
                technical_notes=['Hiányos vagy nem releváns műszaki specifikáció'],
                checked_at=datetime.now()
            )
        
        for spec_name in common_spec_names:
            score, reason, recommendation = self._check_single_spec(spec_name, specs_a.get(spec_name), specs_b.get(spec_name))
            if score is not None:
                compatibility_scores.append(score)
            if reason:
                reasons.append(reason)
            if recommendation:
                recommendations.append(recommendation)
            
            technical_notes.append(f"{spec_name}: {specs_a.get(spec_name)} <-> {specs_b.get(spec_name)}")

        # Összesített kompatibilitási pontszám
        if compatibility_scores:
            total_weight = sum(self.technical_compatibility_rules[spec]['weight'] for spec in common_spec_names)
            if total_weight > 0:
                overall_score = sum(compatibility_scores) / total_weight
            else:
                overall_score = 0.5
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
            confidence_score=min(1.0, overall_score),
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=technical_notes,
            checked_at=datetime.now()
        )
    
    @lru_cache(maxsize=1024)
    def _normalize_technical_value(self, value: Any) -> Optional[Any]:
        """Műszaki érték normalizálása, cache-eléssel."""
        if value is None:
            return None
        
        # Szöveges értékek számra konvertálása
        if isinstance(value, str):
            # Számjegyek kinyerése
            cleaned_value = value.replace(',', '.')
            numbers = re.findall(r'-?\d+\.?\d*', cleaned_value)
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
        compatible_matches = {
            (app_a, app_b)
            for app_a in apps_a
            for app_b in apps_b
            if app_a != app_b and self._are_applications_compatible(app_a, app_b)
        }
        
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
            comp_apps = [f"{a} ~ {b}" for a, b in compatible_matches]
            reasons.append(f"Hasonló alkalmazások: {', '.join(comp_apps)}")
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
            app_a_match = base_app in app_a or any(comp in app_a for comp in compatible_apps)
            app_b_match = base_app in app_b or any(comp in app_b for comp in compatible_apps)
            if app_a_match and app_b_match:
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
        
        # Kompatibilis szabványok ellenőrzése
        compatible_standards = self._find_compatible_standards(
            list(set(standards_a) - common_standards),
            list(set(standards_b) - common_standards)
        )

        if common_standards:
            confidence = 0.9
            level = CompatibilityLevel.FULLY_COMPATIBLE
            reasons.append(f"Közös szabványok: {', '.join(common_standards)}")
        elif compatible_standards:
            confidence = 0.7
            level = CompatibilityLevel.PARTIALLY_COMPATIBLE
            reasons.append(f"Kompatibilis szabványok: {', '.join(compatible_standards)}")
        elif standards_a and standards_b:
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
        text_content = f"{product.name} {product.description} {str(product.technical_specs)} {str(product.properties)}"
        
        # Szabvány pattern-ek
        standard_patterns = [
            r'EN\s+\d+[\-:\d]*',
            r'MSZ\s+EN\s+\d+[\-:\d]*',
            r'MSZ\s+\d+[\-:\d]*',
            r'ISO\s+\d+[\-:\d]*'
        ]
        
        for pattern in standard_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            standards.extend([match.replace(' ', ' ').upper() for match in matches])
        
        # From properties
        product_standards = product.properties.get("standards", [])
        if isinstance(product_standards, list):
            standards.extend(product_standards)

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
    
    def _get_standard_base_number(self, std: str) -> Optional[str]:
        """Kinyeri egy szabvány alap számát."""
        match = re.search(r'\d+', std)
        return match.group() if match else None

    def _is_en_family(self, std: str) -> bool:
        """Ellenőrzi, hogy a szabvány az EN családba tartozik-e."""
        return 'EN' in std.upper()

    def _are_standards_compatible(self, std_a: str, std_b: str) -> bool:
        """Két szabvány kompatibilitásának ellenőrzése, kibővített logikával."""
        if std_a == std_b:
            return True

        is_en_a, is_en_b = self._is_en_family(std_a), self._is_en_family(std_b)
        
        # Ha mindkettő EN szabvány, az alapszámot hasonlítjuk össze
        if is_en_a and is_en_b:
            base_a = self._get_standard_base_number(std_a)
            base_b = self._get_standard_base_number(std_b)
            if base_a and base_b and base_a == base_b:
                return True
        
        # MSZ EN vs EN kompatibilitás
        is_msz_en_a = 'MSZ EN' in std_a.upper()
        is_msz_en_b = 'MSZ EN' in std_b.upper()

        if (is_msz_en_a and is_en_b and not is_msz_en_b) or \
           (is_en_a and not is_msz_en_a and is_msz_en_b):
            base_a = self._get_standard_base_number(std_a)
            base_b = self._get_standard_base_number(std_b)
            if base_a and base_b and base_a == base_b:
                return True
        
        return False
    
    def _create_placeholder_result(self, product_a: Product, product_b: Product, comp_type: CompatibilityType, reason: str, recommendation: str) -> CompatibilityResult:
        """Létrehoz egy placeholder kompatibilitási eredményt."""
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=comp_type,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.5,
            reasons=[reason],
            recommendations=[recommendation],
            technical_notes=[],
            checked_at=datetime.now()
        )

    async def _check_installation_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Telepítési módszerek kompatibilitásának ellenőrzése"""
        logger.info("Telepítési módszerek kompatibilitás ellenőrzése")
        return self._create_placeholder_result(
            product_a, product_b,
            CompatibilityType.INSTALLATION_METHOD,
            'Telepítési módszer ellenőrzés nem implementált',
            'Konzultáljon kivitelezővel'
        )
    
    async def _check_environmental_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Környezeti feltételek kompatibilitásának ellenőrzése"""
        logger.info("Környezeti feltételek kompatibilitás ellenőrzése")
        return self._create_placeholder_result(
            product_a, product_b,
            CompatibilityType.ENVIRONMENTAL_CONDITIONS,
            'Környezeti feltételek ellenőrzés nem implementált',
            'Ellenőrizze a klimatikus feltételeket'
        )
    
    async def _check_system_integration_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Rendszer integráció kompatibilitásának ellenőrzése"""
        logger.info("Rendszer integráció kompatibilitás ellenőrzése")
        return self._create_placeholder_result(
            product_a, product_b,
            CompatibilityType.SYSTEM_INTEGRATION,
            'Rendszer integráció ellenőrzés nem implementált',
            'Kérjen rendszer tervezői véleményt'
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
    
    def _format_compatibility_response(
        self, results: List[CompatibilityResult], from_cache: bool
    ) -> Dict:
        """Kompatibilitási válasz formázása."""
        overall_level = self._calculate_overall_compatibility(results)
        
        avg_confidence = 0
        if results:
            avg_confidence = sum(r.confidence_score for r in results) / len(results)

        highest_conf_check = None
        if results:
            max_res = max(results, key=lambda r: r.confidence_score)
            highest_conf_check = max_res.compatibility_type.value

        details = {
            res.compatibility_type.value: self._format_single_result(res)
            for res in results
        }

        summary = {
            'total_checks': len(results),
            'average_confidence': avg_confidence,
            'highest_confidence_check': highest_conf_check,
        }

        return {
            'agent_id': self.agent_id,
            'product_a_id': results[0].product_a_id if results else None,
            'product_b_id': results[0].product_b_id if results else None,
            'overall_compatibility': overall_level.value,
            'details': details,
            'from_cache': from_cache,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }

    def _format_single_result(self, result: CompatibilityResult) -> Dict:
        """Egyetlen kompatibilitási eredményt formáz."""
        return {
            'compatibility_level': result.compatibility_level.value,
            'confidence_score': result.confidence_score,
            'reasons': result.reasons,
            'recommendations': result.recommendations,
            'technical_notes': result.technical_notes,
            'checked_at': result.checked_at.isoformat()
        }
    
    async def analyze_compatibility_matrix(self, product_ids: List[int]) -> Dict:
        """Termékek kompatibilitási mátrixának elemzése"""
        logger.info(f"Kompatibilitási mátrix elemzés: {len(product_ids)} termék")
        
        comparison_tasks = []
        product_pairs = []

        for i, product_a_id in enumerate(product_ids):
            for j, product_b_id in enumerate(product_ids):
                if i < j:
                    product_pairs.append((product_a_id, product_b_id))
                    comparison_tasks.append(self.check_compatibility(product_a_id, product_b_id))
        
        results = await asyncio.gather(*comparison_tasks)

        compatibility_matrix = {
            f"{pair[0]}_{pair[1]}": {
                'overall_compatibility': result.get('overall_compatibility'),
                'average_confidence': result.get('summary', {}).get('average_confidence', 0)
            }
            for pair, result in zip(product_pairs, results)
        }
        
        # Statisztikák
        compatibility_levels = [entry['overall_compatibility'] for entry in compatibility_matrix.values()]
        
        return {
            'agent_id': self.agent_id,
            'matrix_size': f"{len(product_ids)}x{len(product_ids)}",
            'total_comparisons': len(compatibility_matrix),
            'compatibility_matrix': compatibility_matrix,
            'statistics': {
                'fully_compatible': compatibility_levels.count(CompatibilityLevel.FULLY_COMPATIBLE.value),
                'partially_compatible': compatibility_levels.count(CompatibilityLevel.PARTIALLY_COMPATIBLE.value),
                'conditionally_compatible': compatibility_levels.count(CompatibilityLevel.CONDITIONALLY_COMPATIBLE.value),
                'incompatible': compatibility_levels.count(CompatibilityLevel.INCOMPATIBLE.value),
                'unknown': compatibility_levels.count(CompatibilityLevel.UNKNOWN.value)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Kiszámolja a cache találati arányt."""
        hits = self.compatibility_stats['cache_hits']
        misses = self.compatibility_stats['cache_misses']
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        health_status = {
            'agent_id': self.agent_id,
            'status': 'healthy',
            'checks': {},
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Adatbázis kapcsolat ellenőrzés
        try:
            db = self._get_db_session()
            db.query(Product).count()
            health_status['checks']['database_connection'] = 'ok'
        except Exception as e:
            health_status['checks']['database_connection'] = 'error'
            health_status['errors'].append(f'Adatbázis kapcsolat hiba: {str(e)}')
        finally:
            if db:
                db.close()
        
        # Szabályok és adatbázisok ellenőrzése
        if self.technical_compatibility_rules:
            health_status['checks']['technical_rules_loaded'] = 'ok'
        else:
            health_status['checks']['technical_rules_loaded'] = 'error'
            health_status['errors'].append('Műszaki kompatibilitási szabályok nincsenek betöltve')

        if self.standards_database:
            health_status['checks']['standards_database_loaded'] = 'ok'
        else:
            health_status['checks']['standards_database_loaded'] = 'error'
            health_status['errors'].append('Szabványok adatbázis nincs betöltve')
            
        # Cache integritás ellenőrzés
        try:
            corrupted_cache_entries = 0
            for key, results in self.compatibility_cache.items():
                if not isinstance(results, list) or not all(isinstance(r, CompatibilityResult) for r in results):
                    corrupted_cache_entries += 1
            health_status['checks']['cache_integrity'] = 'ok' if corrupted_cache_entries == 0 else 'error'
            if corrupted_cache_entries > 0:
                health_status['errors'].append(f'{corrupted_cache_entries} sérült cache bejegyzés')
        except Exception as e:
            health_status['checks']['cache_integrity'] = 'error'
            health_status['errors'].append(f'Cache ellenőrzési hiba: {str(e)}')
        
        if health_status['errors']:
            health_status['status'] = 'unhealthy'
        
        return health_status 