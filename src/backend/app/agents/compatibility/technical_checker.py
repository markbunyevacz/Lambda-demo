"""
Műszaki kompatibilitás ellenőrző
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional, List
from functools import lru_cache
from datetime import datetime
from dataclasses import dataclass

from ....models.product import Product
from .models import CompatibilityResult, CompatibilityLevel, CompatibilityType
from .utils import determine_compatibility_level

logger = logging.getLogger(__name__)


@dataclass
class SpecsEvaluationContext:
    """Context for evaluating common specifications."""
    product_a: Product
    product_b: Product
    specs_a: Dict
    specs_b: Dict
    common_specs: set


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
    
    def _check_tolerance_spec(
        self, spec_name: str, rule: Dict, normalized_a: Any, normalized_b: Any
    ) -> Tuple[float, str, Optional[str]]:
        """Handles tolerance-based specifications."""
        if not isinstance(normalized_a, (int, float)) or not isinstance(
            normalized_b, (int, float)
        ):
            return (
                0.0,
                f"{rule['description']}: Nem numerikus értékek a toleranciához.",
                f"Érvénytelen adat a {spec_name}-hez",
            )

        if max(normalized_a, normalized_b) == 0:
            score = rule["weight"] if normalized_a == normalized_b else 0.0
            return (
                score,
                f"{rule['description']}: Egyik érték sem nulla.",
                None,
            )

        tolerance = rule.get("tolerance_percentage", 10) / 100
        diff_percentage = abs(normalized_a - normalized_b) / max(
            normalized_a, normalized_b
        )

        if diff_percentage <= tolerance:
            score = (1 - diff_percentage / tolerance) * rule["weight"]
            reason = (
                f"{rule['description']}: Kompatibilis "
                f"({diff_percentage*100:.1f}% eltérés)"
            )
            return score, reason, None
        
        reason = (
            f"{rule['description']}: Nagy eltérés "
            f"({diff_percentage*100:.1f}%)"
        )
        recommendation = f"Fontoljon meg alternatívát a {spec_name} miatt"
        return 0.2, reason, recommendation

    def check_single_spec(
        self, spec_name: str, value_a: Any, value_b: Any
    ) -> Tuple[Optional[float], str, Optional[str]]:
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
        logger.info(
            "Műszaki specifikációk kompatibilitás ellenőrzése: %s vs %s",
            product_a.name,
            product_b.name
        )
        
        specs_a = product_a.technical_specs or {}
        specs_b = product_b.technical_specs or {}
        
        common_specs = set(specs_a.keys()) & set(specs_b.keys()) & set(self.technical_rules.keys())
        
        if not common_specs:
            return self._create_unknown_result(product_a, product_b)

        return self._evaluate_common_specs(
            SpecsEvaluationContext(
                product_a, product_b, specs_a, specs_b, common_specs
            )
        )
    
    def _create_unknown_result(
        self, product_a: Product, product_b: Product
    ) -> CompatibilityResult:
        """Creates result when no common specifications are found."""
        return CompatibilityResult(
            product_a_id=product_a.id,
            product_b_id=product_b.id,
            compatibility_type=CompatibilityType.TECHNICAL_SPECS,
            compatibility_level=CompatibilityLevel.UNKNOWN,
            confidence_score=0.1,
            reasons=["Nincs közös, szabályozott műszaki paraméter"],
            recommendations=["Kérjen további műszaki adatokat"],
            technical_notes=[
                "Hiányos vagy nem releváns műszaki specifikáció"
            ],
            checked_at=datetime.now(),
        )

    def _evaluate_common_specs(
        self, context: SpecsEvaluationContext
    ) -> CompatibilityResult:
        """Evaluates compatibility for common specifications."""
        compatibility_scores = []
        reasons = []
        recommendations = []
        technical_notes = []
        
        for spec_name in context.common_specs:
            score, reason, recommendation = self.check_single_spec(
                spec_name, 
                context.specs_a.get(spec_name), 
                context.specs_b.get(spec_name)
            )
            
            if score is not None:
                compatibility_scores.append(score)
            if reason:
                reasons.append(reason)
            if recommendation:
                recommendations.append(recommendation)

            note = (
                f"{spec_name}: {context.specs_a.get(spec_name)} <-> "
                f"{context.specs_b.get(spec_name)}"
            )
            technical_notes.append(note)

        overall_score = self._calculate_technical_score(
            compatibility_scores, context.common_specs
        )
        level = determine_compatibility_level(
            overall_score,
            {'fully': 0.8, 'partially': 0.6, 'conditionally': 0.3}
        )

        return CompatibilityResult(
            product_a_id=context.product_a.id,
            product_b_id=context.product_b.id,
            compatibility_type=CompatibilityType.TECHNICAL_SPECS,
            compatibility_level=level,
            confidence_score=overall_score,
            reasons=reasons,
            recommendations=recommendations,
            technical_notes=technical_notes,
            checked_at=datetime.now(),
        )

    def _calculate_technical_score(
        self, compatibility_scores: List[float], common_specs: set
    ) -> float:
        """Calculates the overall technical compatibility score."""
        if not compatibility_scores:
            return 0.5

        total_weight = sum(
            self.technical_rules[spec]["weight"]
            for spec in common_specs
            if spec in self.technical_rules
        )
        if total_weight > 0:
            return sum(compatibility_scores) / total_weight

        return 0.5 