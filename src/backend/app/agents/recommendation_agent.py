"""
Recommendation Agent - Ajánlási Agent (RAG-alapú)

Ez az agent felelős a termék ajánlásokért, összehasonlításokért és
RAG (Retrieval-Augmented Generation) alapú válaszgenerálásért.
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..models.product import Product
from ..database import get_db

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Ajánlás típusok"""
    SIMILAR_PRODUCTS = "similar_products"
    COMPLEMENTARY_PRODUCTS = "complementary_products"
    PRICE_BASED = "price_based"
    APPLICATION_BASED = "application_based"
    TECHNICAL_MATCH = "technical_match"
    CATEGORY_RECOMMENDATIONS = "category_recommendations"


class RecommendationStatus(Enum):
    """Ajánlási állapotok"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_MATCHES = "no_matches"


class RecommendationAgent:
    """
    Ajánlási Agent osztály (RAG-alapú)
    
    Funkcionalitás:
    - Termék összehasonlítás
    - Személyre szabott ajánlások
    - RAG alapú válaszgenerálás
    - Kontextus megértés
    - Hasonlóság alapú keresés
    - Műszaki kompatibilitás ellenőrzés
    """
    
    def __init__(self, max_recommendations: int = 10, similarity_threshold: float = 0.3):
        self.max_recommendations = max_recommendations
        self.similarity_threshold = similarity_threshold
        
        # Agent állapot
        self.agent_id = f"recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.status = RecommendationStatus.PENDING
        
        # Vectorizer a hasonlóság számításhoz
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['a', 'az', 'és', 'vagy', 'de', 'hogy', 'nem', 'is', 'el'],
            ngram_range=(1, 2)
        )
        
        # Termék cache
        self.product_cache = {}
        self.similarity_matrix = None
        self.feature_matrix = None
        
        # Ajánlási statisztikák
        self.recommendation_stats = {
            'total_recommendations_generated': 0,
            'successful_recommendations': 0,
            'failed_recommendations': 0,
            'avg_similarity_score': 0.0,
            'recommendation_duration': 0,
            'last_recommendation': None,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Alkalmazási terület mapping
        self.application_compatibility = {
            'Hőszigetelő lemez': ['homlokzat', 'külső fal', 'térfal'],
            'Padlásfödém szigetelés': ['padlás', 'födém', 'tetőtér'],
            'Homlokzati rendszer': ['homlokzat', 'facade', 'külső'],
            'Tetőszigetelés': ['tető', 'fedél', 'vízszigetelés'],
            'Ipari alkalmazás': ['csővezeték', 'tartály', 'berendezés'],
            'Tűzvédelem': ['menekülés', 'szerkezetvédelem', 'osztály'],
            'Akusztikai megoldás': ['hangszigetelés', 'zajvédelem', 'studio']
        }
    
    async def generate_recommendations(self, 
                                     user_context: Dict,
                                     recommendation_type: RecommendationType = RecommendationType.SIMILAR_PRODUCTS,
                                     reference_product_id: Optional[int] = None) -> Dict:
        """
        Főbb ajánlásigenerálási funkció
        
        Args:
            user_context: Felhasználói kontextus (projekt, igények, preferenciák)
            recommendation_type: Ajánlás típusa
            reference_product_id: Referencia termék ID (hasonlóság alapú ajánláshoz)
            
        Returns:
            Ajánlási eredmény és metrikák
        """
        start_time = datetime.now()
        self.status = RecommendationStatus.IN_PROGRESS
        
        logger.info(f"Ajánlás generálás indítása - Agent ID: {self.agent_id}")
        logger.info(f"Ajánlás típus: {recommendation_type.value}")
        logger.info(f"Felhasználói kontextus: {user_context}")
        
        try:
            # Termékek betöltése és cache frissítése
            await self._update_product_cache()
            
            # Ajánlások generálása típus alapján
            if recommendation_type == RecommendationType.SIMILAR_PRODUCTS:
                recommendations = await self._generate_similar_products(user_context, reference_product_id)
            elif recommendation_type == RecommendationType.COMPLEMENTARY_PRODUCTS:
                recommendations = await self._generate_complementary_products(user_context, reference_product_id)
            elif recommendation_type == RecommendationType.APPLICATION_BASED:
                recommendations = await self._generate_application_based(user_context)
            elif recommendation_type == RecommendationType.TECHNICAL_MATCH:
                recommendations = await self._generate_technical_match(user_context)
            elif recommendation_type == RecommendationType.CATEGORY_RECOMMENDATIONS:
                recommendations = await self._generate_category_recommendations(user_context)
            else:
                logger.warning(f"Ismeretlen ajánlás típus: {recommendation_type}")
                recommendations = []
            
            # Ajánlások rendezése és limitálása
            ranked_recommendations = self._rank_recommendations(recommendations, user_context)
            final_recommendations = ranked_recommendations[:self.max_recommendations]
            
            # Részletes információk hozzáadása
            enriched_recommendations = await self._enrich_recommendations(final_recommendations, user_context)
            
            # Statisztikák frissítése
            self.recommendation_stats['total_recommendations_generated'] += 1
            if enriched_recommendations:
                self.recommendation_stats['successful_recommendations'] += 1
                self.recommendation_stats['avg_similarity_score'] = np.mean([
                    rec.get('similarity_score', 0) for rec in enriched_recommendations
                ])
            else:
                self.recommendation_stats['failed_recommendations'] += 1
                self.status = RecommendationStatus.NO_MATCHES
            
            self.recommendation_stats['recommendation_duration'] = (datetime.now() - start_time).total_seconds()
            self.recommendation_stats['last_recommendation'] = datetime.now().isoformat()
            
            if enriched_recommendations:
                self.status = RecommendationStatus.COMPLETED
            
            result = {
                'agent_id': self.agent_id,
                'status': self.status.value,
                'recommendation_type': recommendation_type.value,
                'recommendations_count': len(enriched_recommendations),
                'recommendations': enriched_recommendations,
                'user_context': user_context,
                'statistics': self.recommendation_stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Ajánlás generálás befejezve: {len(enriched_recommendations)} ajánlás")
            return result
            
        except Exception as e:
            self.status = RecommendationStatus.FAILED
            self.recommendation_stats['failed_recommendations'] += 1
            logger.error(f"Ajánlás generálás kritikus hiba: {e}")
            return {
                'agent_id': self.agent_id,
                'status': self.status.value,
                'error': str(e),
                'recommendations_count': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _update_product_cache(self) -> None:
        """Termék cache frissítése"""
        try:
            db = get_db()
            products = db.query(Product).all()
            
            self.product_cache = {}
            product_texts = []
            
            for product in products:
                # Termék szöveges reprezentációja
                text_representation = f"{product.name} {product.description} {' '.join(product.applications or [])} {product.category}"
                
                self.product_cache[product.id] = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'category': product.category,
                    'applications': product.applications or [],
                    'technical_specs': product.technical_specs or {},
                    'source_url': product.source_url,
                    'text_representation': text_representation
                }
                
                product_texts.append(text_representation)
            
            # TF-IDF feature matrix számítása
            if product_texts:
                self.feature_matrix = self.vectorizer.fit_transform(product_texts)
                self.similarity_matrix = cosine_similarity(self.feature_matrix)
            
            logger.info(f"Termék cache frissítve: {len(self.product_cache)} termék")
            db.close()
            
        except Exception as e:
            logger.error(f"Cache frissítési hiba: {e}")
    
    async def _generate_similar_products(self, user_context: Dict, reference_product_id: Optional[int]) -> List[Dict]:
        """Hasonló termékek ajánlása"""
        if not reference_product_id or reference_product_id not in self.product_cache:
            logger.warning("Nincs referencia termék megadva vagy nem található")
            return []
        
        reference_product = self.product_cache[reference_product_id]
        similar_products = []
        
        # Hasonlóság számítás a similarity matrix alapján
        if self.similarity_matrix is not None:
            product_ids = list(self.product_cache.keys())
            ref_index = product_ids.index(reference_product_id)
            
            similarities = self.similarity_matrix[ref_index]
            
            # Hasonló termékek kiválasztása
            for i, similarity_score in enumerate(similarities):
                if i != ref_index and similarity_score >= self.similarity_threshold:
                    product_id = product_ids[i]
                    product = self.product_cache[product_id]
                    
                    similar_products.append({
                        'product': product,
                        'similarity_score': float(similarity_score),
                        'match_reason': 'Hasonló műszaki paraméterek és alkalmazási terület'
                    })
        
        # Rendezés hasonlóság szerint
        similar_products.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"Hasonló termékek: {len(similar_products)} találat")
        return similar_products
    
    async def _generate_complementary_products(self, user_context: Dict, reference_product_id: Optional[int]) -> List[Dict]:
        """Kiegészítő termékek ajánlása"""
        if not reference_product_id or reference_product_id not in self.product_cache:
            return []
        
        reference_product = self.product_cache[reference_product_id]
        ref_category = reference_product['category']
        complementary_products = []
        
        # Kiegészítő kategóriák meghatározása
        complementary_categories = self._get_complementary_categories(ref_category)
        
        for product_id, product in self.product_cache.items():
            if product_id != reference_product_id and product['category'] in complementary_categories:
                # Alkalmazási terület kompatibilitás ellenőrzés
                compatibility_score = self._calculate_application_compatibility(
                    reference_product['applications'],
                    product['applications']
                )
                
                if compatibility_score > 0.3:
                    complementary_products.append({
                        'product': product,
                        'compatibility_score': compatibility_score,
                        'match_reason': f'Kiegészíti a {ref_category} kategóriát'
                    })
        
        # Rendezés kompatibilitás szerint
        complementary_products.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        logger.info(f"Kiegészítő termékek: {len(complementary_products)} találat")
        return complementary_products
    
    def _get_complementary_categories(self, category: str) -> List[str]:
        """Kiegészítő kategóriák meghatározása"""
        complementary_mapping = {
            'Hőszigetelő lemez': ['Homlokzati rendszer', 'Tűzvédelem'],
            'Padlásfödém szigetelés': ['Tetőszigetelés', 'Akusztikai megoldás'],
            'Homlokzati rendszer': ['Hőszigetelő lemez', 'Tűzvédelem'],
            'Tetőszigetelés': ['Padlásfödém szigetelés', 'Tűzvédelem'],
            'Ipari alkalmazás': ['Tűzvédelem', 'Akusztikai megoldás'],
            'Tűzvédelem': ['Hőszigetelő lemez', 'Homlokzati rendszer'],
            'Akusztikai megoldás': ['Hőszigetelő lemez', 'Ipari alkalmazás']
        }
        
        return complementary_mapping.get(category, [])
    
    def _calculate_application_compatibility(self, apps1: List[str], apps2: List[str]) -> float:
        """Alkalmazási területek kompatibilitásának számítása"""
        if not apps1 or not apps2:
            return 0.0
        
        # Közös alkalmazási területek
        common_apps = set(apps1) & set(apps2)
        total_apps = set(apps1) | set(apps2)
        
        if not total_apps:
            return 0.0
        
        return len(common_apps) / len(total_apps)
    
    async def _generate_application_based(self, user_context: Dict) -> List[Dict]:
        """Alkalmazási terület alapú ajánlás"""
        target_application = user_context.get('application', '')
        project_type = user_context.get('project_type', '')
        
        if not target_application and not project_type:
            logger.warning("Nincs alkalmazási terület megadva")
            return []
        
        matching_products = []
        search_terms = [target_application, project_type]
        
        for product_id, product in self.product_cache.items():
            match_score = 0.0
            match_reasons = []
            
            # Alkalmazási területek ellenőrzése
            for app in product['applications']:
                for search_term in search_terms:
                    if search_term and search_term.lower() in app.lower():
                        match_score += 0.5
                        match_reasons.append(f"Alkalmas: {app}")
            
            # Kategória ellenőrzése
            if target_application:
                for category, keywords in self.application_compatibility.items():
                    if product['category'] == category:
                        for keyword in keywords:
                            if keyword.lower() in target_application.lower():
                                match_score += 0.3
                                match_reasons.append(f"Kategória egyezés: {category}")
            
            if match_score > 0.3:
                matching_products.append({
                    'product': product,
                    'match_score': match_score,
                    'match_reason': '; '.join(match_reasons)
                })
        
        # Rendezés egyezés szerint
        matching_products.sort(key=lambda x: x['match_score'], reverse=True)
        
        logger.info(f"Alkalmazás alapú ajánlás: {len(matching_products)} találat")
        return matching_products
    
    async def _generate_technical_match(self, user_context: Dict) -> List[Dict]:
        """Műszaki paraméterek alapú ajánlás"""
        required_specs = user_context.get('technical_requirements', {})
        
        if not required_specs:
            logger.warning("Nincsenek műszaki követelmények megadva")
            return []
        
        matching_products = []
        
        for product_id, product in self.product_cache.items():
            product_specs = product['technical_specs']
            match_score = 0.0
            match_reasons = []
            
            for req_key, req_value in required_specs.items():
                if req_key in product_specs:
                    try:
                        # Numerikus összehasonlítás
                        req_num = float(str(req_value).replace(',', '.'))
                        prod_num = float(str(product_specs[req_key]).replace(',', '.'))
                        
                        # Tolerancia alapú egyezés (±10%)
                        tolerance = 0.1
                        if abs(prod_num - req_num) / req_num <= tolerance:
                            match_score += 1.0
                            match_reasons.append(f"{req_key}: {product_specs[req_key]} (≈{req_value})")
                        elif prod_num >= req_num * 0.8:  # Minimális követelmény
                            match_score += 0.5
                            match_reasons.append(f"{req_key}: {product_specs[req_key]} (min. {req_value})")
                            
                    except (ValueError, ZeroDivisionError):
                        # Szöveges egyezés
                        if str(req_value).lower() in str(product_specs[req_key]).lower():
                            match_score += 0.5
                            match_reasons.append(f"{req_key}: {product_specs[req_key]}")
            
            if match_score > 0.5:
                matching_products.append({
                    'product': product,
                    'match_score': match_score,
                    'match_reason': '; '.join(match_reasons)
                })
        
        # Rendezés műszaki egyezés szerint
        matching_products.sort(key=lambda x: x['match_score'], reverse=True)
        
        logger.info(f"Műszaki paraméter alapú ajánlás: {len(matching_products)} találat")
        return matching_products
    
    async def _generate_category_recommendations(self, user_context: Dict) -> List[Dict]:
        """Kategória alapú ajánlás"""
        preferred_category = user_context.get('preferred_category', '')
        
        if not preferred_category:
            logger.warning("Nincs preferált kategória megadva")
            return []
        
        category_products = []
        
        for product_id, product in self.product_cache.items():
            if preferred_category.lower() in product['category'].lower():
                # Minőségi pontszám a termék részletessége alapján
                quality_score = self._calculate_product_quality_score(product)
                
                category_products.append({
                    'product': product,
                    'quality_score': quality_score,
                    'match_reason': f'Kategória: {product["category"]}'
                })
        
        # Rendezés minőség szerint
        category_products.sort(key=lambda x: x['quality_score'], reverse=True)
        
        logger.info(f"Kategória alapú ajánlás: {len(category_products)} találat")
        return category_products
    
    def _calculate_product_quality_score(self, product: Dict) -> float:
        """Termék minőségi pontszámának számítása"""
        score = 0.0
        
        # Név minősége
        if len(product['name']) > 10:
            score += 0.2
        
        # Leírás minősége
        if len(product['description']) > 50:
            score += 0.3
        
        # Műszaki specifikációk
        if len(product['technical_specs']) > 2:
            score += 0.3
        
        # Alkalmazási területek
        if len(product['applications']) > 1:
            score += 0.2
        
        return score
    
    def _rank_recommendations(self, recommendations: List[Dict], user_context: Dict) -> List[Dict]:
        """Ajánlások rangsorolása"""
        if not recommendations:
            return []
        
        # Rangsorolási súlyok
        weights = {
            'similarity_score': 0.4,
            'match_score': 0.4,
            'compatibility_score': 0.3,
            'quality_score': 0.2
        }
        
        for rec in recommendations:
            final_score = 0.0
            
            for score_type, weight in weights.items():
                if score_type in rec:
                    final_score += rec[score_type] * weight
            
            rec['final_score'] = final_score
        
        # Rendezés végső pontszám szerint
        recommendations.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return recommendations
    
    async def _enrich_recommendations(self, recommendations: List[Dict], user_context: Dict) -> List[Dict]:
        """Ajánlások részletes információkkal való bővítése"""
        enriched = []
        
        for rec in recommendations:
            product = rec['product']
            
            enriched_rec = {
                'product_id': product['id'],
                'name': product['name'],
                'description': product['description'],
                'category': product['category'],
                'applications': product['applications'],
                'technical_specs': product['technical_specs'],
                'source_url': product['source_url'],
                'recommendation_score': rec.get('final_score', rec.get('similarity_score', rec.get('match_score', 0))),
                'match_reason': rec.get('match_reason', 'Általános egyezés'),
                'confidence': min(rec.get('final_score', 0) * 100, 100),
                'recommendation_context': {
                    'user_context': user_context,
                    'recommendation_timestamp': datetime.now().isoformat(),
                    'agent_id': self.agent_id
                }
            }
            
            enriched.append(enriched_rec)
        
        return enriched
    
    async def compare_products(self, product_ids: List[int], comparison_criteria: List[str] = None) -> Dict:
        """Termékek összehasonlítása"""
        if not comparison_criteria:
            comparison_criteria = ['technical_specs', 'applications', 'category']
        
        logger.info(f"Termék összehasonlítás: {len(product_ids)} termék")
        
        try:
            await self._update_product_cache()
            
            products = []
            for product_id in product_ids:
                if product_id in self.product_cache:
                    products.append(self.product_cache[product_id])
            
            if len(products) < 2:
                return {
                    'error': 'Legalább 2 termék szükséges az összehasonlításhoz',
                    'products_found': len(products)
                }
            
            comparison_result = {
                'products': products,
                'comparison_criteria': comparison_criteria,
                'comparison_matrix': {},
                'recommendations': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Összehasonlítási mátrix
            for criterion in comparison_criteria:
                comparison_result['comparison_matrix'][criterion] = {}
                
                for i, product1 in enumerate(products):
                    for j, product2 in enumerate(products):
                        if i != j:
                            similarity = self._calculate_criterion_similarity(
                                product1, product2, criterion
                            )
                            key = f"{product1['id']}_vs_{product2['id']}"
                            comparison_result['comparison_matrix'][criterion][key] = similarity
            
            # Ajánlások az összehasonlítás alapján
            best_product = max(products, key=lambda p: self._calculate_overall_score(p))
            comparison_result['recommendations'].append({
                'type': 'best_overall',
                'product_id': best_product['id'],
                'reason': 'Legjobb összesített pontszám'
            })
            
            logger.info("Termék összehasonlítás befejezve")
            return comparison_result
            
        except Exception as e:
            logger.error(f"Termék összehasonlítási hiba: {e}")
            return {'error': str(e)}
    
    def _calculate_criterion_similarity(self, product1: Dict, product2: Dict, criterion: str) -> float:
        """Kritérium alapú hasonlóság számítása"""
        if criterion == 'technical_specs':
            specs1 = product1.get('technical_specs', {})
            specs2 = product2.get('technical_specs', {})
            
            common_keys = set(specs1.keys()) & set(specs2.keys())
            if not common_keys:
                return 0.0
            
            similarities = []
            for key in common_keys:
                try:
                    val1 = float(str(specs1[key]).replace(',', '.'))
                    val2 = float(str(specs2[key]).replace(',', '.'))
                    similarity = 1 - abs(val1 - val2) / max(val1, val2)
                    similarities.append(max(similarity, 0))
                except (ValueError, ZeroDivisionError):
                    # Szöveges egyezés
                    if str(specs1[key]).lower() == str(specs2[key]).lower():
                        similarities.append(1.0)
                    else:
                        similarities.append(0.0)
            
            return np.mean(similarities) if similarities else 0.0
        
        elif criterion == 'applications':
            apps1 = set(product1.get('applications', []))
            apps2 = set(product2.get('applications', []))
            
            if not apps1 and not apps2:
                return 1.0
            if not apps1 or not apps2:
                return 0.0
            
            intersection = len(apps1 & apps2)
            union = len(apps1 | apps2)
            return intersection / union if union > 0 else 0.0
        
        elif criterion == 'category':
            cat1 = product1.get('category', '').lower()
            cat2 = product2.get('category', '').lower()
            return 1.0 if cat1 == cat2 else 0.0
        
        return 0.0
    
    def _calculate_overall_score(self, product: Dict) -> float:
        """Termék összesített pontszámának számítása"""
        score = 0.0
        
        # Műszaki specifikációk száma
        score += len(product.get('technical_specs', {})) * 0.1
        
        # Alkalmazási területek száma
        score += len(product.get('applications', [])) * 0.2
        
        # Leírás hossza
        score += min(len(product.get('description', '')), 500) / 500 * 0.3
        
        # Név informatívussága
        score += min(len(product.get('name', '')), 100) / 100 * 0.2
        
        return score
    
    async def get_recommendation_statistics(self) -> Dict:
        """Ajánlási statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'statistics': self.recommendation_stats.copy(),
            'cache_info': {
                'products_cached': len(self.product_cache),
                'feature_matrix_shape': self.feature_matrix.shape if self.feature_matrix is not None else None,
                'similarity_matrix_shape': self.similarity_matrix.shape if self.similarity_matrix is not None else None
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        health_status = {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'healthy': True,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Cache ellenőrzés
            if not self.product_cache:
                health_status['errors'].append('Termék cache üres')
                health_status['healthy'] = False
            
            # Vectorizer ellenőrzés
            if not hasattr(self.vectorizer, 'fit_transform'):
                health_status['errors'].append('TF-IDF vectorizer nem elérhető')
                health_status['healthy'] = False
            
            # Feature matrix ellenőrzés
            if self.feature_matrix is None:
                health_status['errors'].append('Feature matrix nincs inicializálva')
                # Nem critical hiba
            
            # Adatbázis kapcsolat ellenőrzés
            try:
                db = get_db()
                db.query(Product).count()
                db.close()
            except Exception as e:
                health_status['errors'].append(f'Adatbázis kapcsolat hiba: {str(e)}')
                health_status['healthy'] = False
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['errors'].append(f'Health check hiba: {str(e)}')
        
        return health_status 