"""
Szabvány kompatibilitás ellenőrző
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from ....models.product import Product
from .models import (
    CompatibilityResult, 
    CompatibilityLevel, 
    CompatibilityType,
    StandardType
)
from .utils import determine_compatibility_level

logger = logging.getLogger(__name__)


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
                'key_requirements': [
                    'λ érték', 'vastagság tolerancia', 'méretek'
                ]
            },
            'EN 13501-1': {
                'type': StandardType.FIRE_SAFETY,
                'description': 'Építőanyagok tűzvédelmi osztályozása',
                'key_requirements': [
                    'Euroclass', 'füstképzés', 'égő cseppek'
                ]
            },
            'EN 12667': {
                'type': StandardType.THERMAL_PERFORMANCE,
                'description': 'Hővezetési tényező meghatározás',
                'key_requirements': [
                    'mérési módszer', 'referencia hőmérséklet'
                ]
            },
            'MSZ EN 13162': {
                'type': StandardType.EN_EUROPEAN,
                'description': 'Magyar szabvány kőzetgyapot termékekre',
                'key_requirements': [
                    'nemzeti kiegészítések', 'alkalmazási területek'
                ]
            }
        }
    
    def check_standards_compatibility(
        self, product_a: Product, product_b: Product
    ) -> CompatibilityResult:
        """Szabványok kompatibilitásának ellenőrzése"""
        logger.info(
            "Szabványok kompatibilitás ellenőrzése: %s vs %s",
            product_a.name,
            product_b.name
        )
        
        standards_a = self._extract_standards_from_product(product_a)
        standards_b = self._extract_standards_from_product(product_b)
        
        if not standards_a or not standards_b:
            return self._create_standards_unknown_result(
                product_a, product_b, standards_a, standards_b
            )
        
        return self._evaluate_standards_compatibility(
            product_a, product_b, standards_a, standards_b
        )
    
    def _extract_standards_from_product(self, product: Product) -> List[str]:
        """Szabványok kinyerése termék adatokból"""
        standards = set()

        if product.description:
            standards.update(self._find_standards_in_text(product.description))

        if product.technical_specs:
            standards.update(
                self._extract_standards_from_specs(product.technical_specs)
            )

        return list(standards)

    def _extract_standards_from_specs(
        self, specs: Dict[str, Any]
    ) -> List[str]:
        """Extracts standards from the technical specifications dictionary."""
        standards = []
        for key, value in specs.items():
            if isinstance(value, str):
                standards.extend(self._find_standards_in_text(value))
            elif key.lower() in ["standards", "szabványok", "certifications"]:
                if isinstance(value, list):
                    standards.extend(value)
                elif isinstance(value, str):
                    standards.extend(self._find_standards_in_text(value))
        return standards
    
    def _find_standards_in_text(self, text: str) -> List[str]:
        """Szabványok keresése szövegben regex-szel"""
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
    
    def _create_standards_unknown_result(
        self, product_a: Product, product_b: Product, 
        standards_a: List[str], standards_b: List[str]
    ) -> CompatibilityResult:
        """Creates result when standards data is insufficient."""
        reasons = []
        if not standards_a:
            reasons.append(
                f"Termék A ({product_a.name}) szabványai nem "
                "meghatározhatók"
            )
        if not standards_b:
            reasons.append(
                f"Termék B ({product_b.name}) szabványai nem "
                "meghatározhatók"
            )
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.STANDARDS_COMPLIANCE,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.1,
            reasons=reasons,
            recommendations=[
                'Kérjen szabvány megfelelőségi tanúsítványokat'
            ],
            technical_notes=[
                f"A szabványok: {standards_a}",
                f"B szabványok: {standards_b}"
            ],
            checked_at=datetime.now()
        )
    
    def _evaluate_standards_compatibility(
        self, product_a: Product, product_b: Product, 
        standards_a: List[str], standards_b: List[str]
    ) -> CompatibilityResult:
        """Evaluates standards compatibility."""
        compatible_standards = self._find_compatible_standards(
            standards_a, standards_b
        )
        
        if compatible_standards:
            max_len = max(len(standards_a), len(standards_b))
            compatibility_score = (
                len(compatible_standards) / max_len if max_len > 0 else 0
            )
            level = self._determine_standards_compatibility_level(
                compatibility_score
            )
            reasons = [
                "Kompatibilis szabványok: "
                f"{', '.join(compatible_standards)}"
            ]
            recommendations = []
        else:
            compatibility_score = 0.1
            level = CompatibilityLevel.INCOMPATIBLE
            reasons = ['Nincs közös vagy kompatibilis szabvány']
            recommendations = [
                'Ellenőrizze a szabványok egyenértékűségét szakértővel'
            ]
        
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.STANDARDS_COMPLIANCE,
            compatibility_level=level,
            confidence_score=compatibility_score,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=[
                f"A szabványok: {standards_a}",
                f"B szabványok: {standards_b}"
            ],
            checked_at=datetime.now()
        )
    
    def _find_compatible_standards(
        self, standards_a: List[str], standards_b: List[str]
    ) -> List[str]:
        """Kompatibilis szabványok keresése"""
        compatible = []
        
        for std_a in standards_a:
            for std_b in standards_b:
                if self._are_standards_compatible(std_a, std_b):
                    compatible.append(f"{std_a} ↔ {std_b}")
        
        return compatible
    
    def _are_standards_compatible(self, std_a: str, std_b: str) -> bool:
        """Két szabvány kompatibilitásának ellenőrzése"""
        if std_a.strip().upper() == std_b.strip().upper():
            return True
        
        base_a = self._get_standard_base_number(std_a)
        base_b = self._get_standard_base_number(std_b)
        
        if base_a and base_b and base_a == base_b:
            return True
        
        if self._is_en_family(std_a) and self._is_en_family(std_b):
            return base_a == base_b
        
        return False
    
    def _get_standard_base_number(self, std: str) -> Optional[str]:
        """Szabvány alapszámának kinyerése"""
        match = re.search(r'\d+(?:-\d+)*', std)
        return match.group() if match else None
    
    def _is_en_family(self, std: str) -> bool:
        """Ellenőrzi, hogy EN családba tartozik-e"""
        return 'EN' in std.upper()
    
    def _determine_standards_compatibility_level(
        self, score: float
    ) -> CompatibilityLevel:
        """Determines standards compatibility level based on score."""
        return determine_compatibility_level(
            score,
            {'fully': 0.8, 'partially': 0.5, 'conditionally': 0.2}
        ) 