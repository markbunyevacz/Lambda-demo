"""
Kompatibilitási cache és statisztikák
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .models import CompatibilityResult, CompatibilityLevel

logger = logging.getLogger(__name__)


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
    
    def get_cached_result(
        self, product_a_id: int, product_b_id: int
    ) -> Optional[List[CompatibilityResult]]:
        """Lekér egy cache-elt eredményt."""
        cache_key = self._get_cache_key(product_a_id, product_b_id)
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        self.stats['cache_misses'] += 1
        return None
    
    def cache_result(
        self, product_a_id: int, product_b_id: int, 
        results: List[CompatibilityResult]
    ):
        """Cache-el egy eredményt."""
        cache_key = self._get_cache_key(product_a_id, product_b_id)
        self.cache[cache_key] = results
    
    def update_statistics(self, compatibility_results: List[CompatibilityResult]):
        """Frissíti a kompatibilitási statisztikákat."""
        self.stats['total_checks_performed'] += 1
        self.stats['last_check'] = datetime.now().isoformat()
        
        overall_level = self._calculate_overall_compatibility(
            compatibility_results
        )
        if overall_level == CompatibilityLevel.FULLY_COMPATIBLE:
            self.stats['fully_compatible_pairs'] += 1
        elif overall_level in (
            CompatibilityLevel.PARTIALLY_COMPATIBLE, 
            CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        ):
            self.stats['partially_compatible_pairs'] += 1
        elif overall_level == CompatibilityLevel.INCOMPATIBLE:
            self.stats['incompatible_pairs'] += 1
        
        if compatibility_results:
            avg_confidence = (
                sum(r.confidence_score for r in compatibility_results) / 
                len(compatibility_results)
            )
            alpha = 0.1
            current_avg = self.stats.get('average_confidence', 0.0)
            self.stats['average_confidence'] = (
                alpha * avg_confidence + (1 - alpha) * current_avg
            )
    
    def _calculate_overall_compatibility(
        self, results: List[CompatibilityResult]
    ) -> CompatibilityLevel:
        """Összesített kompatibilitási szint meghatározása"""
        if not results:
            return CompatibilityLevel.UNKNOWN
        
        level_counts = {level: 0 for level in CompatibilityLevel}
        for result in results:
            level_counts[result.compatibility_level] += 1
        
        total_results = len(results)
        
        if level_counts[CompatibilityLevel.INCOMPATIBLE] > 0:
            return CompatibilityLevel.INCOMPATIBLE
        if level_counts[CompatibilityLevel.FULLY_COMPATIBLE] == total_results:
            return CompatibilityLevel.FULLY_COMPATIBLE
        if level_counts[CompatibilityLevel.PARTIALLY_COMPATIBLE] > 0:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        if level_counts[CompatibilityLevel.CONDITIONALLY_COMPATIBLE] > 0:
            return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
        
        return CompatibilityLevel.UNKNOWN
    
    def calculate_cache_hit_rate(self) -> float:
        """Cache találati arány kiszámítása"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        if total_requests == 0:
            return 0.0
        return (self.stats['cache_hits'] / total_requests) * 100
    
    def get_statistics(self) -> Dict[str, Any]:
        """Statisztikák lekérése."""
        stats = self.stats.copy()
        stats['cache_hit_rate_percentage'] = self.calculate_cache_hit_rate()
        return stats

    @staticmethod
    def _get_cache_key(
        product_a_id: int, product_b_id: int
    ) -> Tuple[int, int]:
        """Generates a consistent cache key."""
        return tuple(sorted((product_a_id, product_b_id))) 