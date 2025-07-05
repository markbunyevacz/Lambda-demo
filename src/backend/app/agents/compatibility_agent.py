"""
Compatibility Agent - Kompatibilitási Agent

Ez az agent felelős a termékek kompatibilitásának ellenőrzéséért,
műszaki specifikációk összehasonlításáért, alkalmazási területek elemzéséért
és szabványok ellenőrzéséért.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from functools import lru_cache
from dataclasses import dataclass

from ...models.product import Product
from ...database import get_db

from .compatibility.models import CompatibilityType, CompatibilityResult
from .compatibility.technical_checker import TechnicalCompatibilityChecker
from .compatibility.application_checker import ApplicationCompatibilityChecker
from .compatibility.standards_checker import StandardsCompatibilityChecker
from .compatibility.cache import CompatibilityCache


logger = logging.getLogger(__name__)


@dataclass
class PlaceholderContext:
    """Context for creating placeholder compatibility results."""
    product_a: Product
    product_b: Product
    comp_type: CompatibilityType
    reason: str
    recommendation: str


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
            CompatibilityType.TECHNICAL_SPECS: 
                self.technical_checker.check_technical_compatibility,
            CompatibilityType.APPLICATION_AREAS: 
                self.application_checker.check_application_compatibility,
            CompatibilityType.STANDARDS_COMPLIANCE: 
                self.standards_checker.check_standards_compatibility,
            CompatibilityType.INSTALLATION_METHOD: 
                self._check_installation_compatibility,
            CompatibilityType.ENVIRONMENTAL_CONDITIONS: 
                self._check_environmental_compatibility,
            CompatibilityType.SYSTEM_INTEGRATION: 
                self._check_system_integration_compatibility,
        }

    @lru_cache(maxsize=128)
    def _get_db_session(self):
        # This will be tricky because the generator needs to be iterated.
        # For simplicity in this structure, we'll call it each time.
        # A more robust solution might involve a dependency injection framework.
        db_gen = get_db()
        try:
            db = next(db_gen)
            return db
        finally:
            # The session is closed by the original context manager in a real app
            pass


    async def _get_products(
        self, product_a_id: int, product_b_id: int
    ) -> Tuple[Optional[Product], Optional[Product]]:
        """Termékek lekérése adatbázisból"""
        db = None
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

    async def check_compatibility(
        self, 
        product_a_id: int, 
        product_b_id: int,
        compatibility_types: Optional[List[CompatibilityType]] = None
    ) -> Dict:
        """
        Főbb kompatibilitás ellenőrzési funkció
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
            cached_results = self.cache_manager.get_cached_result(
                product_a_id, product_b_id
            )
            if cached_results:
                logger.info("Kompatibilitási eredmény cache-ből")
                return self._format_compatibility_response(cached_results, True)
            
            product_a, product_b = await self._get_products(product_a_id, product_b_id)
            if not product_a or not product_b:
                return {
                    'error': 'Termékek nem találhatók',
                    'product_a_id': product_a_id,
                    'product_b_id': product_b_id
                }
            
            compatibility_results = await self._execute_compatibility_checks(
                product_a, product_b, effective_compatibility_types
            )
            
            self.cache_manager.cache_result(
                product_a_id, product_b_id, compatibility_results
            )
            
            self.cache_manager.update_statistics(compatibility_results)
            
            response = self._format_compatibility_response(compatibility_results, False)
            response['duration_seconds'] = (
                datetime.now() - start_time
            ).total_seconds()
            
            logger.info(
                "Kompatibilitás ellenőrzés befejezve: %s",
                response.get('overall_compatibility')
            )
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
    
    async def _execute_compatibility_checks(
        self, product_a: Product, product_b: Product, 
        compatibility_types: List[CompatibilityType]
    ) -> List[CompatibilityResult]:
        """Execute all requested compatibility checks."""
        tasks = []
        for comp_type in compatibility_types:
            check_method = self.check_dispatch_table.get(comp_type)
            if check_method:
                # Assuming the checker methods are now synchronous
                tasks.append(asyncio.to_thread(check_method, product_a, product_b))
            else:
                logger.warning(f"Ismeretlen kompatibilitás típus: {comp_type}")

        results = await asyncio.gather(*tasks)
        return [result for result in results if result]

    def _create_placeholder_result(
        self, context: PlaceholderContext
    ) -> CompatibilityResult:
        """Placeholder eredmény létrehozása"""
        return CompatibilityResult(
            product_a_id=context.product_a.id,
            product_b_id=context.product_b.id,
            compatibility_type=context.comp_type,
            compatibility_level='unknown', # Placeholder
            confidence_score=0.1,
            reasons=[context.reason],
            recommendations=[context.recommendation],
            technical_notes=[],
            checked_at=datetime.now()
        )

    async def _check_installation_compatibility(
        self, product_a: Product, product_b: Product
    ) -> CompatibilityResult:
        """Telepítési módszerek kompatibilitásának ellenőrzése"""
        context = PlaceholderContext(
            product_a, product_b,
            CompatibilityType.INSTALLATION_METHOD,
            'Telepítési módszer ellenőrzés még nem implementált',
            'Konzultáljon kivitelezővel'
        )
        return self._create_placeholder_result(context)
    
    async def _check_environmental_compatibility(
        self, product_a: Product, product_b: Product
    ) -> CompatibilityResult:
        """Környezeti feltételek kompatibilitásának ellenőrzése"""
        context = PlaceholderContext(
            product_a, product_b,
            CompatibilityType.ENVIRONMENTAL_CONDITIONS,
            'Környezeti feltételek ellenőrzése még nem implementált',
            'Ellenőrizze a klimatikus feltételeket'
        )
        return self._create_placeholder_result(context)
    
    async def _check_system_integration_compatibility(
        self, product_a: Product, product_b: Product
    ) -> CompatibilityResult:
        """Rendszer integráció kompatibilitásának ellenőrzése"""
        context = PlaceholderContext(
            product_a, product_b,
            CompatibilityType.SYSTEM_INTEGRATION,
            'Rendszer integráció ellenőrzése még nem implementált',
            'Kérjen rendszer integrációs tervet'
        )
        return self._create_placeholder_result(context)

    def _format_compatibility_response(
        self, results: List[CompatibilityResult], from_cache: bool
    ) -> Dict:
        """Kompatibilitási válasz formázása"""
        overall_compatibility = self.cache_manager._calculate_overall_compatibility(
            results
        )
        
        response = {
            'agent_id': self.agent_id,
            'overall_compatibility': overall_compatibility.value,
            'from_cache': from_cache,
            'results_count': len(results),
            'detailed_results': [
                self._format_single_result(result) for result in results
            ],
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
        
        tasks = []
        product_pairs = []
        for i in range(len(product_ids)):
            for j in range(i + 1, len(product_ids)):
                product_a_id = product_ids[i]
                product_b_id = product_ids[j]
                product_pairs.append((product_a_id, product_b_id))
                tasks.append(self.check_compatibility(product_a_id, product_b_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for pair, result in zip(product_pairs, results):
            pair_key = f"{pair[0]}-{pair[1]}"
            total_pairs += 1
            if isinstance(result, Exception):
                matrix_results[pair_key] = {
                    'error': str(result),
                    'product_a_id': pair[0],
                    'product_b_id': pair[1]
                }
            elif 'error' not in result:
                matrix_results[pair_key] = result
                successful_pairs += 1
            else:
                 matrix_results[pair_key] = result

        return {
            'agent_id': self.agent_id,
            'matrix_results': matrix_results,
            'total_pairs': total_pairs,
            'successful_pairs': successful_pairs,
            'success_rate': (
                successful_pairs / total_pairs * 100 if total_pairs > 0 else 0
            ),
            'timestamp': datetime.now().isoformat()
        }

    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        db = None
        try:
            db = self._get_db_session()
            db_status = "healthy" if db else "unhealthy"
            
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
        finally:
            if db:
                db.close()

    def get_compatibility_statistics(self) -> Dict:
        """Kompatibilitási statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            **self.cache_manager.get_statistics()
        } 