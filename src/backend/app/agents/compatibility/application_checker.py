"""
Alkalmazási kompatibilitás ellenőrző
"""

import logging
from typing import Dict, List
from datetime import datetime

from ....models.product import Product
from .models import CompatibilityResult, CompatibilityLevel, CompatibilityType
from .utils import determine_compatibility_level

logger = logging.getLogger(__name__)


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
    
    def check_application_compatibility(
        self, product_a: Product, product_b: Product
    ) -> CompatibilityResult:
        """Alkalmazási területek kompatibilitásának ellenőrzése"""
        logger.info(
            "Alkalmazási területek kompatibilitás ellenőrzése: %s vs %s",
            product_a.name,
            product_b.name
        )
        
        apps_a = self._extract_applications(product_a)
        apps_b = self._extract_applications(product_b)
        
        if not apps_a or not apps_b:
            return self._create_application_unknown_result(
                product_a, product_b, apps_a, apps_b
            )
        
        return self._evaluate_application_compatibility(
            product_a, product_b, apps_a, apps_b
        )
    
    def _extract_applications(self, product: Product) -> List[str]:
        """Extract applications from product data."""
        applications = []
        
        if product.description:
            applications.extend(
                self._extract_apps_from_text(product.description.lower())
            )
        
        if product.name:
            applications.extend(
                self._extract_apps_from_text(product.name.lower())
            )
        
        if product.technical_specs and 'applications' in product.technical_specs:
            app_field = product.technical_specs['applications']
            if isinstance(app_field, list):
                applications.extend(app_field)
            elif isinstance(app_field, str):
                applications.extend(
                    self._extract_apps_from_text(app_field.lower())
                )
        
        return list(set(applications))
    
    def _extract_apps_from_text(self, text: str) -> List[str]:
        """Extract application keywords from text."""
        found_apps = []
        for app_category, keywords in self.application_matrix.items():
            if any(keyword in text for keyword in keywords):
                found_apps.append(app_category)
        return found_apps
    
    def _create_application_unknown_result(
        self, product_a: Product, product_b: Product, 
        apps_a: List[str], apps_b: List[str]
    ) -> CompatibilityResult:
        """Creates result when application data is insufficient."""
        reason = []
        if not apps_a:
            reason.append(
                f"Termék A ({product_a.name}) alkalmazási "
                "területe nem meghatározható"
            )
        if not apps_b:
            reason.append(
                f"Termék B ({product_b.name}) alkalmazási "
                "területe nem meghatározható"
            )
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.APPLICATION_AREAS,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.1,
            reasons=reason,
            recommendations=['Kérjen részletes alkalmazási területeket'],
            technical_notes=[
                f"A alkalmazások: {apps_a}",
                f"B alkalmazások: {apps_b}"
            ],
            checked_at=datetime.now()
        )
    
    def _evaluate_application_compatibility(
        self, product_a: Product, product_b: Product, 
        apps_a: List[str], apps_b: List[str]
    ) -> CompatibilityResult:
        """Evaluates application area compatibility."""
        common_apps = set(apps_a) & set(apps_b)
        total_apps = set(apps_a) | set(apps_b)
        
        if common_apps:
            compatibility_score = (
                len(common_apps) / len(total_apps) if total_apps else 0
            )
            level = self._determine_app_compatibility_level(compatibility_score)
            reasons = [
                f"Közös alkalmazási területek: {', '.join(common_apps)}"
            ]
            recommendations = []
        else:
            related_score = self._check_related_applications(apps_a, apps_b)
            compatibility_score = related_score
            level = self._determine_app_compatibility_level(related_score)
            reasons = [
                "Nincs közös alkalmazási terület, de "
                "kapcsolódó területek találhatók"
            ]
            recommendations = ['Ellenőrizze a konkrét felhasználási módokat']
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.APPLICATION_AREAS,
            compatibility_level=level,
            confidence_score=compatibility_score,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=[
                f"A alkalmazások: {apps_a}",
                f"B alkalmazások: {apps_b}"
            ],
            checked_at=datetime.now()
        )
    
    def _check_related_applications(
        self, apps_a: List[str], apps_b: List[str]
    ) -> float:
        """Check for related applications between two lists."""
        if self._are_both_building_related(
            apps_a, apps_b
        ) or self._are_both_industrial(apps_a, apps_b):
            return 0.3
        
        return 0.1

    def _are_both_building_related(
        self, apps_a: List[str], apps_b: List[str]
    ) -> bool:
        """Checks if both app lists are for building applications."""
        building_terms = ["homlokzat", "padlás", "tetőszigetelés"]
        a_is_building = any(app in building_terms for app in apps_a)
        b_is_building = any(app in building_terms for app in apps_b)
        return a_is_building and b_is_building

    def _are_both_industrial(
        self, apps_a: List[str], apps_b: List[str]
    ) -> bool:
        """Checks if both app lists are for industrial applications."""
        industrial_terms = ["ipari"]
        a_is_industrial = any(app in industrial_terms for app in apps_a)
        b_is_industrial = any(app in industrial_terms for app in apps_b)
        return a_is_industrial and b_is_industrial
    
    def _determine_app_compatibility_level(self, score: float) -> CompatibilityLevel:
        """Determines application compatibility level based on score."""
        return determine_compatibility_level(
            score,
            {'fully': 0.7, 'partially': 0.4, 'conditionally': 0.2}
        ) 