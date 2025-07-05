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


class TechnicalCompatibilityChecker:
    """
    Műszaki kompatibilitás ellenőrzésért felelős osztály.
    Encapsulates all technical specification checking logic.
    """
    
    def __init__(self):
        self.technical_rules = self._load_technical_rules()
    
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
    
    @lru_cache(maxsize=1024)
    def _normalize_technical_value(self, value: Any) -> Optional[Any]:
        """Normalizálja a műszaki értékeket."""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Extract numeric value from string
            import re
            match = re.search(r'[\d.,]+', value.replace(',', '.'))
            if match:
                try:
                    return float(match.group().replace(',', '.'))
                except ValueError:
                    pass
        
        return value
    
    def _check_exact_match_spec(self, rule: Dict, normalized_a: Any, normalized_b: Any) -> Tuple[float, str, Optional[str]]:
        """Handles exact match requirements for specifications."""
        if normalized_a == normalized_b:
            return rule['weight'], f"{rule['description']}: Pontos egyezés ({normalized_a})", None
        else:
            return 0.0, f"{rule['description']}: Eltérés ({normalized_a} vs {normalized_b})", f"Ellenőrizze a kompatibilitást"
    
    def _check_tolerance_spec(self, spec_name: str, rule: Dict, normalized_a: Any, normalized_b: Any) -> Tuple[float, str, Optional[str]]:
        """Handles tolerance-based specifications."""
        if max(normalized_a, normalized_b) == 0:
            score = rule['weight'] if normalized_a == normalized_b else 0.0
            return score, f"{rule['description']}: Egyik érték sem nulla.", None

        tolerance = rule.get('tolerance_percentage', 10) / 100
        diff_percentage = abs(normalized_a - normalized_b) / max(normalized_a, normalized_b)
        
        if diff_percentage <= tolerance:
            score = (1 - diff_percentage / tolerance) * rule['weight']
            return score, f"{rule['description']}: Kompatibilis ({diff_percentage*100:.1f}% eltérés)", None
        else:
            return 0.2, f"{rule['description']}: Nagy eltérés ({diff_percentage*100:.1f}%)", f"Fontoljon meg alternatívát a {spec_name} miatt"
    
    def check_single_spec(self, spec_name: str, value_a: Any, value_b: Any) -> Tuple[Optional[float], str, Optional[str]]:
        """Egyetlen műszaki paraméter kompatibilitását ellenőrzi."""
        if spec_name not in self.technical_rules:
            return None, f"Ismeretlen műszaki paraméter: {spec_name}", None
            
        rule = self.technical_rules[spec_name]
        normalized_a = self._normalize_technical_value(value_a)
        normalized_b = self._normalize_technical_value(value_b)

        if normalized_a is None or normalized_b is None:
            return None, f"{rule['description']}: Hiányzó érték.", None

        if rule.get('exact_match_required', False):
            return self._check_exact_match_spec(rule, normalized_a, normalized_b)
        
        if isinstance(normalized_a, (int, float)) and isinstance(normalized_b, (int, float)):
            return self._check_tolerance_spec(spec_name, rule, normalized_a, normalized_b)

        return None, f"{rule['description']}: Nem numerikus értékek", None
    
    def check_technical_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Műszaki specifikációk kompatibilitásának ellenőrzése"""
        logger.info("Műszaki specifikációk kompatibilitás ellenőrzése")
        
        specs_a = product_a.technical_specs or {}
        specs_b = product_b.technical_specs or {}
        
        # Find common specifications
        common_specs = set(specs_a.keys()) & set(specs_b.keys()) & set(self.technical_rules.keys())
        
        if not common_specs:
            return self._create_unknown_result(product_a, product_b)
        
        return self._evaluate_common_specs(product_a, product_b, specs_a, specs_b, common_specs)
    
    def _create_unknown_result(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Creates result when no common specifications are found."""
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
    
    def _evaluate_common_specs(self, product_a: Product, product_b: Product, 
                              specs_a: Dict, specs_b: Dict, common_specs: set) -> CompatibilityResult:
        """Evaluates compatibility for common specifications."""
        compatibility_scores = []
        reasons = []
        recommendations = []
        technical_notes = []
        
        for spec_name in common_specs:
            score, reason, recommendation = self.check_single_spec(
                spec_name, specs_a.get(spec_name), specs_b.get(spec_name)
            )
            
            if score is not None:
                compatibility_scores.append(score)
            if reason:
                reasons.append(reason)
            if recommendation:
                recommendations.append(recommendation)
            
            technical_notes.append(f"{spec_name}: {specs_a.get(spec_name)} <-> {specs_b.get(spec_name)}")

        # Calculate overall score
        overall_score = self._calculate_technical_score(compatibility_scores, common_specs)
        level = self._determine_compatibility_level(overall_score)
        
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
    
    def _calculate_technical_score(self, compatibility_scores: List[float], common_specs: set) -> float:
        """Calculates the overall technical compatibility score."""
        if compatibility_scores:
            total_weight = sum(self.technical_rules[spec]['weight'] for spec in common_specs)
            if total_weight > 0:
                return sum(compatibility_scores) / total_weight
        return 0.5
    
    def _determine_compatibility_level(self, score: float) -> CompatibilityLevel:
        """Determines compatibility level based on score."""
        if score >= 0.8:
            return CompatibilityLevel.FULLY_COMPATIBLE
        elif score >= 0.6:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif score >= 0.3:
            return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        else:
            return CompatibilityLevel.INCOMPATIBLE


class ApplicationCompatibilityChecker:
    """
    Alkalmazási terület kompatibilitás ellenőrzésért felelős osztály.
    """
    
    def __init__(self):
        self.application_matrix = self._load_application_matrix()
    
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
    
    def check_application_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Alkalmazási területek kompatibilitásának ellenőrzése"""
        logger.info("Alkalmazási területek kompatibilitás ellenőrzése")
        
        apps_a = self._extract_applications(product_a)
        apps_b = self._extract_applications(product_b)
        
        if not apps_a or not apps_b:
            return self._create_application_unknown_result(product_a, product_b, apps_a, apps_b)
        
        return self._evaluate_application_compatibility(product_a, product_b, apps_a, apps_b)
    
    def _extract_applications(self, product: Product) -> List[str]:
        """Extract applications from product data."""
        applications = []
        
        # From description
        if product.description:
            applications.extend(self._extract_apps_from_text(product.description.lower()))
        
        # From name
        if product.name:
            applications.extend(self._extract_apps_from_text(product.name.lower()))
        
        # From technical specs
        if product.technical_specs and 'applications' in product.technical_specs:
            app_field = product.technical_specs['applications']
            if isinstance(app_field, list):
                applications.extend(app_field)
            elif isinstance(app_field, str):
                applications.extend(self._extract_apps_from_text(app_field.lower()))
        
        return list(set(applications))  # Remove duplicates
    
    def _extract_apps_from_text(self, text: str) -> List[str]:
        """Extract application keywords from text."""
        found_apps = []
        for app_category, keywords in self.application_matrix.items():
            if any(keyword in text for keyword in keywords):
                found_apps.append(app_category)
        return found_apps
    
    def _create_application_unknown_result(self, product_a: Product, product_b: Product, 
                                         apps_a: List[str], apps_b: List[str]) -> CompatibilityResult:
        """Creates result when application data is insufficient."""
        reason = []
        if not apps_a:
            reason.append(f"Termék A ({product_a.name}) alkalmazási területe nem meghatározható")
        if not apps_b:
            reason.append(f"Termék B ({product_b.name}) alkalmazási területe nem meghatározható")
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.APPLICATION_AREAS,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.1,
            reasons=reason,
            recommendations=['Kérjen részletes alkalmazási területeket'],
            technical_notes=[f"A alkalmazások: {apps_a}", f"B alkalmazások: {apps_b}"],
            checked_at=datetime.now()
        )
    
    def _evaluate_application_compatibility(self, product_a: Product, product_b: Product, 
                                          apps_a: List[str], apps_b: List[str]) -> CompatibilityResult:
        """Evaluates application area compatibility."""
        common_apps = set(apps_a) & set(apps_b)
        total_apps = set(apps_a) | set(apps_b)
        
        if common_apps:
            compatibility_score = len(common_apps) / len(total_apps)
            level = self._determine_app_compatibility_level(compatibility_score)
            reasons = [f"Közös alkalmazási területek: {', '.join(common_apps)}"]
            recommendations = []
        else:
            # Check for related applications
            related_score = self._check_related_applications(apps_a, apps_b)
            compatibility_score = related_score
            level = self._determine_app_compatibility_level(related_score)
            reasons = [f"Nincs közös alkalmazási terület, de kapcsolódó területek találhatók"]
            recommendations = ['Ellenőrizze a konkrét felhasználási módokat']
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.APPLICATION_AREAS,
            compatibility_level=level,
            confidence_score=compatibility_score,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=[f"A alkalmazások: {apps_a}", f"B alkalmazások: {apps_b}"],
            checked_at=datetime.now()
        )
    
    def _check_related_applications(self, apps_a: List[str], apps_b: List[str]) -> float:
        """Check for related applications between two lists."""
        # Simple heuristic: if both contain building-related terms
        building_terms = ['homlokzat', 'padlás', 'tetőszigetelés']
        industrial_terms = ['ipari']
        
        a_building = any(app in building_terms for app in apps_a)
        b_building = any(app in building_terms for app in apps_b)
        a_industrial = any(app in industrial_terms for app in apps_a)
        b_industrial = any(app in industrial_terms for app in apps_b)
        
        if (a_building and b_building) or (a_industrial and b_industrial):
            return 0.3  # Some compatibility
        
        return 0.1  # Minimal compatibility
    
    def _determine_app_compatibility_level(self, score: float) -> CompatibilityLevel:
        """Determines application compatibility level based on score."""
        if score >= 0.7:
            return CompatibilityLevel.FULLY_COMPATIBLE
        elif score >= 0.4:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif score >= 0.2:
            return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        else:
            return CompatibilityLevel.INCOMPATIBLE


class StandardsCompatibilityChecker:
    """
    Szabványok kompatibilitás ellenőrzésért felelős osztály.
    """
    
    def __init__(self):
        self.standards_database = self._load_standards_database()
    
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
    
    def check_standards_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Szabványok kompatibilitásának ellenőrzése"""
        logger.info("Szabványok kompatibilitás ellenőrzése")
        
        standards_a = self._extract_standards_from_product(product_a)
        standards_b = self._extract_standards_from_product(product_b)
        
        if not standards_a or not standards_b:
            return self._create_standards_unknown_result(product_a, product_b, standards_a, standards_b)
        
        return self._evaluate_standards_compatibility(product_a, product_b, standards_a, standards_b)
    
    def _extract_standards_from_product(self, product: Product) -> List[str]:
        """Szabványok kinyerése termék adatokból"""
        standards = []
        
        # Search in description
        if product.description:
            standards.extend(self._find_standards_in_text(product.description))
        
        # Search in technical specs
        if product.technical_specs:
            for key, value in product.technical_specs.items():
                if isinstance(value, str):
                    standards.extend(self._find_standards_in_text(value))
                elif key.lower() in ['standards', 'szabványok', 'certifications']:
                    if isinstance(value, list):
                        standards.extend(value)
                    elif isinstance(value, str):
                        standards.extend(self._find_standards_in_text(value))
        
        return list(set(standards))  # Remove duplicates
    
    def _find_standards_in_text(self, text: str) -> List[str]:
        """Szabványok keresése szövegben regex-szel"""
        import re
        patterns = [
            r'EN\s*\d+(?:-\d+)*',
            r'MSZ\s*EN\s*\d+(?:-\d+)*',
            r'ISO\s*\d+(?:-\d+)*',
            r'DIN\s*\d+(?:-\d+)*'
        ]
        
        found_standards = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_standards.extend([match.strip() for match in matches])
        
        return found_standards
    
    def _create_standards_unknown_result(self, product_a: Product, product_b: Product, 
                                       standards_a: List[str], standards_b: List[str]) -> CompatibilityResult:
        """Creates result when standards data is insufficient."""
        reasons = []
        if not standards_a:
            reasons.append(f"Termék A ({product_a.name}) szabványai nem meghatározhatók")
        if not standards_b:
            reasons.append(f"Termék B ({product_b.name}) szabványai nem meghatározhatók")
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.STANDARDS_COMPLIANCE,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.1,
            reasons=reasons,
            recommendations=['Kérjen szabvány megfelelőségi tanúsítványokat'],
            technical_notes=[f"A szabványok: {standards_a}", f"B szabványok: {standards_b}"],
            checked_at=datetime.now()
        )
    
    def _evaluate_standards_compatibility(self, product_a: Product, product_b: Product, 
                                        standards_a: List[str], standards_b: List[str]) -> CompatibilityResult:
        """Evaluates standards compatibility."""
        compatible_standards = self._find_compatible_standards(standards_a, standards_b)
        
        if compatible_standards:
            compatibility_score = len(compatible_standards) / max(len(standards_a), len(standards_b))
            level = self._determine_standards_compatibility_level(compatibility_score)
            reasons = [f"Kompatibilis szabványok: {', '.join(compatible_standards)}"]
            recommendations = []
        else:
            compatibility_score = 0.1
            level = CompatibilityLevel.INCOMPATIBLE
            reasons = ['Nincs közös vagy kompatibilis szabvány']
            recommendations = ['Ellenőrizze a szabványok egyenértékűségét szakértővel']
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.STANDARDS_COMPLIANCE,
            compatibility_level=level,
            confidence_score=compatibility_score,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=[f"A szabványok: {standards_a}", f"B szabványok: {standards_b}"],
            checked_at=datetime.now()
        )
    
    def _find_compatible_standards(self, standards_a: List[str], standards_b: List[str]) -> List[str]:
        """Kompatibilis szabványok keresése"""
        compatible = []
        
        for std_a in standards_a:
            for std_b in standards_b:
                if self._are_standards_compatible(std_a, std_b):
                    compatible.append(f"{std_a} ↔ {std_b}")
        
        return compatible
    
    def _are_standards_compatible(self, std_a: str, std_b: str) -> bool:
        """Két szabvány kompatibilitásának ellenőrzése"""
        # Exact match
        if std_a.strip().upper() == std_b.strip().upper():
            return True
        
        # Same base number (e.g., EN 13162 and MSZ EN 13162)
        base_a = self._get_standard_base_number(std_a)
        base_b = self._get_standard_base_number(std_b)
        
        if base_a and base_b and base_a == base_b:
            return True
        
        # EN family compatibility
        if self._is_en_family(std_a) and self._is_en_family(std_b):
            return base_a == base_b
        
        return False
    
    def _get_standard_base_number(self, std: str) -> Optional[str]:
        """Szabvány alapszámának kinyerése"""
        import re
        match = re.search(r'\d+(?:-\d+)*', std)
        return match.group() if match else None
    
    def _is_en_family(self, std: str) -> bool:
        """Ellenőrzi, hogy EN családba tartozik-e"""
        return 'EN' in std.upper()
    
    def _determine_standards_compatibility_level(self, score: float) -> CompatibilityLevel:
        """Determines standards compatibility level based on score."""
        if score >= 0.8:
            return CompatibilityLevel.FULLY_COMPATIBLE
        elif score >= 0.5:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif score >= 0.2:
            return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        else:
            return CompatibilityLevel.INCOMPATIBLE


class CompatibilityCache:
    """
    Kompatibilitási cache és statisztikák kezelésért felelős osztály.
    """
    
    def __init__(self):
        self.cache: Dict[Tuple[int, int], List[CompatibilityResult]] = {}
        self.stats = self._initialize_stats()
    
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
    
    def get_cached_result(self, product_a_id: int, product_b_id: int) -> Optional[List[CompatibilityResult]]:
        """Lekér egy cache-elt eredményt."""
        cache_key = (min(product_a_id, product_b_id), max(product_a_id, product_b_id))
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        self.stats['cache_misses'] += 1
        return None
    
    def cache_result(self, product_a_id: int, product_b_id: int, results: List[CompatibilityResult]):
        """Cache-el egy eredményt."""
        cache_key = (min(product_a_id, product_b_id), max(product_a_id, product_b_id))
        self.cache[cache_key] = results
    
    def update_statistics(self, compatibility_results: List[CompatibilityResult]):
        """Frissíti a kompatibilitási statisztikákat."""
        self.stats['total_checks_performed'] += 1
        self.stats['last_check'] = datetime.now().isoformat()
        
        overall_level = self._calculate_overall_compatibility(compatibility_results)
        if overall_level == CompatibilityLevel.FULLY_COMPATIBLE:
            self.stats['fully_compatible_pairs'] += 1
        elif overall_level == CompatibilityLevel.PARTIALLY_COMPATIBLE:
            self.stats['partially_compatible_pairs'] += 1
        elif overall_level == CompatibilityLevel.INCOMPATIBLE:
            self.stats['incompatible_pairs'] += 1
        
        if compatibility_results:
            avg_confidence = sum(r.confidence_score for r in compatibility_results) / len(compatibility_results)
            # EMA (Exponential Moving Average) for average confidence
            alpha = 0.1
            current_avg = self.stats.get('average_confidence', 0.0)
            self.stats['average_confidence'] = alpha * avg_confidence + (1 - alpha) * current_avg
    
    def _calculate_overall_compatibility(self, results: List[CompatibilityResult]) -> CompatibilityLevel:
        """Összesített kompatibilitási szint meghatározása"""
        if not results:
            return CompatibilityLevel.UNKNOWN
        
        # Count compatibility levels
        level_counts = {}
        for result in results:
            level = result.compatibility_level
            level_counts[level] = level_counts.get(level, 0) + 1
        
        total_results = len(results)
        
        # Decision logic
        if level_counts.get(CompatibilityLevel.INCOMPATIBLE, 0) > total_results * 0.5:
            return CompatibilityLevel.INCOMPATIBLE
        elif level_counts.get(CompatibilityLevel.FULLY_COMPATIBLE, 0) > total_results * 0.7:
            return CompatibilityLevel.FULLY_COMPATIBLE
        elif level_counts.get(CompatibilityLevel.PARTIALLY_COMPATIBLE, 0) > 0:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        else:
            return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
    
    def calculate_cache_hit_rate(self) -> float:
        """Cache találati arány kiszámítása"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        if total_requests == 0:
            return 0.0
        return (self.stats['cache_hits'] / total_requests) * 100
    
    def get_statistics(self) -> Dict[str, Any]:
        """Statisztikák lekérése."""
        return {
            **self.stats,
            'cache_hit_rate_percentage': self.calculate_cache_hit_rate()
        }


class CompatibilityAgent:
    """
    Főbb kompatibilitási koordinátor osztály.
    Simplified orchestrator that delegates to specialized checkers.
    """
    
    def __init__(self, min_confidence_threshold: float = 0.7):
        self.min_confidence_threshold = min_confidence_threshold
        self.agent_id = f"compatibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize specialized checkers
        self.technical_checker = TechnicalCompatibilityChecker()
        self.application_checker = ApplicationCompatibilityChecker()
        self.standards_checker = StandardsCompatibilityChecker()
        self.cache_manager = CompatibilityCache()
        
        # Dispatch table for different compatibility types
        self.check_dispatch_table = {
            CompatibilityType.TECHNICAL_SPECS: self.technical_checker.check_technical_compatibility,
            CompatibilityType.APPLICATION_AREAS: self.application_checker.check_application_compatibility,
            CompatibilityType.STANDARDS_COMPLIANCE: self.standards_checker.check_standards_compatibility,
            CompatibilityType.INSTALLATION_METHOD: self._check_installation_compatibility,
            CompatibilityType.ENVIRONMENTAL_CONDITIONS: self._check_environmental_compatibility,
            CompatibilityType.SYSTEM_INTEGRATION: self._check_system_integration_compatibility,
        }

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
            # Check cache first
            cached_results = self.cache_manager.get_cached_result(product_a_id, product_b_id)
            if cached_results:
                logger.info("Kompatibilitási eredmény cache-ből")
                return self._format_compatibility_response(cached_results, True)
            
            # Get products from database
            product_a, product_b = await self._get_products(product_a_id, product_b_id)
            if not product_a or not product_b:
                return {
                    'error': 'Termékek nem találhatók',
                    'product_a_id': product_a_id,
                    'product_b_id': product_b_id
                }
            
            # Execute compatibility checks
            compatibility_results = await self._execute_compatibility_checks(
                product_a, product_b, effective_compatibility_types
            )
            
            # Cache results
            self.cache_manager.cache_result(product_a_id, product_b_id, compatibility_results)
            
            # Update statistics
            self.cache_manager.update_statistics(compatibility_results)
            
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
    
    async def _execute_compatibility_checks(self, product_a: Product, product_b: Product, 
                                          compatibility_types: List[CompatibilityType]) -> List[CompatibilityResult]:
        """Execute all requested compatibility checks."""
        tasks = []
        for comp_type in compatibility_types:
            check_method = self.check_dispatch_table.get(comp_type)
            if check_method:
                logger.info(f"Ellenőrzés típus ütemezve: {comp_type.value}")
                tasks.append(check_method(product_a, product_b))
            else:
                logger.warning(f"Ismeretlen kompatibilitás típus: {comp_type}")

        results = await asyncio.gather(*tasks)
        return [result for result in results if result]

    def _create_placeholder_result(self, product_a: Product, product_b: Product, comp_type: CompatibilityType, reason: str, recommendation: str) -> CompatibilityResult:
        """Placeholder eredmény létrehozása"""
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=comp_type,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.1,
            reasons=[reason],
            recommendations=[recommendation],
            technical_notes=[],
            checked_at=datetime.now()
        )

    async def _check_installation_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Telepítési módszerek kompatibilitásának ellenőrzése"""
        return self._create_placeholder_result(
            product_a, product_b, 
            CompatibilityType.INSTALLATION_METHOD,
            'Telepítési módszer ellenőrzés még nem implementált',
            'Konzultáljon kivitelezővel'
        )
    
    async def _check_environmental_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Környezeti feltételek kompatibilitásának ellenőrzése"""
        return self._create_placeholder_result(
            product_a, product_b,
            CompatibilityType.ENVIRONMENTAL_CONDITIONS,
            'Környezeti feltételek ellenőrzése még nem implementált',
            'Ellenőrizze a klimatikus feltételeket'
        )
    
    async def _check_system_integration_compatibility(self, product_a: Product, product_b: Product) -> CompatibilityResult:
        """Rendszer integráció kompatibilitásának ellenőrzése"""
        return self._create_placeholder_result(
            product_a, product_b,
            CompatibilityType.SYSTEM_INTEGRATION,
            'Rendszer integráció ellenőrzése még nem implementált',
            'Kérjen rendszer integrációs tervet'
        )

    def _format_compatibility_response(
        self, results: List[CompatibilityResult], from_cache: bool
    ) -> Dict:
        """Kompatibilitási válasz formázása"""
        overall_compatibility = self.cache_manager._calculate_overall_compatibility(results)
        
        response = {
            'agent_id': self.agent_id,
            'overall_compatibility': overall_compatibility.value,
            'from_cache': from_cache,
            'results_count': len(results),
            'detailed_results': [self._format_single_result(result) for result in results],
            'timestamp': datetime.now().isoformat(),
            'statistics': self.cache_manager.get_statistics()
        }
        
        return response

    def _format_single_result(self, result: CompatibilityResult) -> Dict:
        """Egyetlen kompatibilitási eredmény formázása"""
        return {
            'compatibility_type': result.compatibility_type.value,
            'compatibility_level': result.compatibility_level.value,
            'confidence_score': result.confidence_score,
            'reasons': result.reasons,
            'recommendations': result.recommendations,
            'technical_notes': result.technical_notes,
            'checked_at': result.checked_at.isoformat()
        }

    async def analyze_compatibility_matrix(self, product_ids: List[int]) -> Dict:
        """Kompatibilitási mátrix elemzése több termékre"""
        logger.info(f"Kompatibilitási mátrix elemzése {len(product_ids)} termékre")
        
        if len(product_ids) < 2:
            return {
                'error': 'Legalább 2 termék szükséges a mátrix elemzéshez',
                'provided_count': len(product_ids)
            }
        
        matrix_results = {}
        total_pairs = 0
        successful_pairs = 0
        
        for i in range(len(product_ids)):
            for j in range(i + 1, len(product_ids)):
                product_a_id = product_ids[i]
                product_b_id = product_ids[j]
                pair_key = f"{product_a_id}-{product_b_id}"
                
                total_pairs += 1
                
                try:
                    result = await self.check_compatibility(product_a_id, product_b_id)
                    if 'error' not in result:
                        matrix_results[pair_key] = result
                        successful_pairs += 1
                    else:
                        matrix_results[pair_key] = result
                except Exception as e:
                    matrix_results[pair_key] = {
                        'error': str(e),
                        'product_a_id': product_a_id,
                        'product_b_id': product_b_id
                    }
        
        return {
            'agent_id': self.agent_id,
            'matrix_results': matrix_results,
            'total_pairs': total_pairs,
            'successful_pairs': successful_pairs,
            'success_rate': (successful_pairs / total_pairs) * 100 if total_pairs > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }

    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        try:
            # Test database connection
            db = self._get_db_session()
            db_status = "healthy" if db else "unhealthy"
            if db:
                db.close()
            
            return {
                'agent_id': self.agent_id,
                'status': 'healthy',
                'database_connection': db_status,
                'cache_hit_rate': self.cache_manager.calculate_cache_hit_rate(),
                'statistics': self.cache_manager.get_statistics(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agent_id': self.agent_id,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_compatibility_statistics(self) -> Dict:
        """Kompatibilitási statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            **self.cache_manager.get_statistics()
        } 