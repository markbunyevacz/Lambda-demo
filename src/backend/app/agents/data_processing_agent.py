"""
Data Processing Agent - Adatfeldolgozó Agent

Ez az agent felelős a raw adatok normalizálásáért, duplikátumok eltávolításáért,
kategorizálásért és minőségbiztosításért a Lambda demo számára.
"""

import asyncio
import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
from difflib import SequenceMatcher

from ..models.product import Product
from ..scraper.data_validator import DataValidator
from ..database import get_db

logger = logging.getLogger(__name__)


class ProcessingType(Enum):
    """Feldolgozási típusok"""
    NORMALIZATION = "normalization"
    DEDUPLICATION = "deduplication"
    CATEGORIZATION = "categorization"
    QUALITY_ASSURANCE = "quality_assurance"
    TEXT_EXTRACTION = "text_extraction"
    TECHNICAL_SPEC_PARSING = "technical_spec_parsing"


class ProcessingStatus(Enum):
    """Feldolgozási állapotok"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DataProcessingAgent:
    """
    Adatfeldolgozó Agent osztály
    
    Funkcionalitás:
    - Raw adatok normalizálása
    - Duplikátumok eltávolítása
    - Kategorizálás és címkézés
    - Minőségbiztosítás
    - Műszaki paraméterek kinyerése
    - Szöveges tartalom tisztítása
    """
    
    def __init__(self, similarity_threshold: float = 0.85, batch_size: int = 100):
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        self.validator = DataValidator()
        
        # Agent állapot
        self.agent_id = f"data_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.status = ProcessingStatus.PENDING
        
        # Feldolgozási statisztikák
        self.processing_stats = {
            'total_items_processed': 0,
            'normalized_items': 0,
            'duplicates_removed': 0,
            'categorized_items': 0,
            'quality_improved': 0,
            'processing_duration': 0,
            'last_processing': None,
            'errors_encountered': 0
        }
        
        # Kategória mapping (Rockwool specifikus)
        self.category_keywords = {
            'Hőszigetelő lemez': ['lemez', 'panel', 'hőszigetelő', 'külső'],
            'Padlásfödém szigetelés': ['padlás', 'födém', 'tető', 'blown'],
            'Homlokzati rendszer': ['homlokzat', 'facade', 'külső fal'],
            'Tetőszigetelés': ['tető', 'roof', 'fedél', 'bitumen'],
            'Ipari alkalmazás': ['ipari', 'industrial', 'csővezeték', 'tartály'],
            'Tűzvédelem': ['tűz', 'fire', 'védelem', 'resistance'],
            'Akusztikai megoldás': ['hang', 'acoustic', 'zaj', 'sound']
        }
        
        # Műszaki paraméter regexek
        self.technical_patterns = {
            'lambda_value': r'λ\s*[:=]\s*([0-9,\.]+)',
            'thermal_conductivity': r'hővezetési?\s*tényező\s*[:=]\s*([0-9,\.]+)',
            'fire_resistance': r'tűzállóság\s*[:=]\s*([A-Z0-9]+)',
            'thickness': r'vastagság\s*[:=]\s*([0-9]+)\s*mm',
            'density': r'sűrűség\s*[:=]\s*([0-9]+)\s*kg/m³',
            'compressive_strength': r'nyomószilárdság\s*[:=]\s*([0-9]+)\s*kPa'
        }
    
    async def process_data(self, data: List[Dict], 
                          processing_types: List[ProcessingType] = None,
                          save_results: bool = True) -> Dict:
        """
        Főbb adatfeldolgozási funkció
        
        Args:
            data: Feldolgozandó raw adatok
            processing_types: Végrehajtandó feldolgozási lépések
            save_results: Eredmények mentése adatbázisba
            
        Returns:
            Feldolgozási eredmény és statisztikák
        """
        if not processing_types:
            processing_types = [
                ProcessingType.NORMALIZATION,
                ProcessingType.DEDUPLICATION,
                ProcessingType.CATEGORIZATION,
                ProcessingType.QUALITY_ASSURANCE
            ]
        
        start_time = datetime.now()
        self.status = ProcessingStatus.IN_PROGRESS
        
        logger.info(f"Adatfeldolgozás indítása - Agent ID: {self.agent_id}")
        logger.info(f"Feldolgozási típusok: {[t.value for t in processing_types]}")
        logger.info(f"Bemeneti adatok: {len(data)} elem")
        
        processed_data = data.copy()
        processing_results = {}
        
        try:
            # Feldolgozási lépések végrehajtása sorrendben
            for processing_type in processing_types:
                logger.info(f"Feldolgozási lépés: {processing_type.value}")
                
                if processing_type == ProcessingType.NORMALIZATION:
                    processed_data = await self._normalize_data(processed_data)
                    processing_results['normalization'] = {
                        'completed': True,
                        'items_processed': len(processed_data)
                    }
                
                elif processing_type == ProcessingType.DEDUPLICATION:
                    original_count = len(processed_data)
                    processed_data = await self._remove_duplicates(processed_data)
                    duplicates_removed = original_count - len(processed_data)
                    self.processing_stats['duplicates_removed'] += duplicates_removed
                    processing_results['deduplication'] = {
                        'completed': True,
                        'duplicates_removed': duplicates_removed,
                        'remaining_items': len(processed_data)
                    }
                
                elif processing_type == ProcessingType.CATEGORIZATION:
                    processed_data = await self._categorize_data(processed_data)
                    processing_results['categorization'] = {
                        'completed': True,
                        'categorized_items': len([item for item in processed_data if item.get('category')])
                    }
                
                elif processing_type == ProcessingType.QUALITY_ASSURANCE:
                    original_count = len(processed_data)
                    processed_data = await self._ensure_quality(processed_data)
                    quality_improved = len([item for item in processed_data if item.get('quality_score', 0) > 0.7])
                    self.processing_stats['quality_improved'] += quality_improved
                    processing_results['quality_assurance'] = {
                        'completed': True,
                        'quality_improved': quality_improved,
                        'high_quality_items': quality_improved
                    }
                
                elif processing_type == ProcessingType.TECHNICAL_SPEC_PARSING:
                    processed_data = await self._parse_technical_specs(processed_data)
                    processing_results['technical_spec_parsing'] = {
                        'completed': True,
                        'specs_extracted': len([item for item in processed_data if item.get('technical_specs')])
                    }
            
            # Adatok mentése ha kérte
            if save_results and processed_data:
                await self._save_processed_data(processed_data)
            
            # Statisztikák frissítése
            self.processing_stats['total_items_processed'] += len(processed_data)
            self.processing_stats['processing_duration'] = (datetime.now() - start_time).total_seconds()
            self.processing_stats['last_processing'] = datetime.now().isoformat()
            
            self.status = ProcessingStatus.COMPLETED
            
            result = {
                'agent_id': self.agent_id,
                'status': self.status.value,
                'original_count': len(data),
                'processed_count': len(processed_data),
                'processing_results': processing_results,
                'statistics': self.processing_stats.copy(),
                'data': processed_data if not save_results else None,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Adatfeldolgozás befejezve: {len(data)} -> {len(processed_data)} elem")
            return result
            
        except Exception as e:
            self.status = ProcessingStatus.FAILED
            self.processing_stats['errors_encountered'] += 1
            logger.error(f"Adatfeldolgozás kritikus hiba: {e}")
            return {
                'agent_id': self.agent_id,
                'status': self.status.value,
                'error': str(e),
                'processed_count': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _normalize_data(self, data: List[Dict]) -> List[Dict]:
        """Adatok normalizálása"""
        logger.info(f"Adatok normalizálása: {len(data)} elem")
        
        normalized_data = []
        
        for item in data:
            try:
                normalized_item = {
                    # Alapmezők normalizálása
                    'name': self._normalize_text(item.get('name', '')),
                    'description': self._normalize_text(item.get('description', '')),
                    'category': self._normalize_text(item.get('category', '')),
                    'source_url': item.get('source_url', ''),
                    'scraped_at': item.get('scraped_at', datetime.now().isoformat()),
                    'data_source': item.get('data_source', 'unknown'),
                    
                    # Technikai specifikációk normalizálása
                    'technical_specs': self._normalize_technical_specs(item.get('technical_specs', {})),
                    'applications': self._normalize_applications(item.get('applications', [])),
                    
                    # Metaadatok
                    'processing_timestamp': datetime.now().isoformat(),
                    'processing_agent': self.agent_id,
                    'quality_score': 0.0  # Később számoljuk ki
                }
                
                # Raw data megtartása
                if 'raw_data' in item:
                    normalized_item['raw_data'] = item['raw_data']
                
                normalized_data.append(normalized_item)
                self.processing_stats['normalized_items'] += 1
                
            except Exception as e:
                logger.error(f"Normalizálási hiba: {e}")
                self.processing_stats['errors_encountered'] += 1
        
        logger.info(f"Normalizálás befejezve: {len(normalized_data)} elem")
        return normalized_data
    
    def _normalize_text(self, text: str) -> str:
        """Szöveg normalizálása"""
        if not text:
            return ""
        
        # Whitespace tisztítás
        text = re.sub(r'\s+', ' ', text.strip())
        
        # HTML/XML tagek eltávolítása
        text = re.sub(r'<[^>]+>', '', text)
        
        # Speciális karakterek kezelése
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        return text
    
    def _normalize_technical_specs(self, specs: Dict) -> Dict:
        """Műszaki specifikációk normalizálása"""
        normalized_specs = {}
        
        for key, value in specs.items():
            # Kulcs normalizálása
            normalized_key = key.lower().strip().replace(' ', '_')
            
            # Érték normalizálása
            if isinstance(value, str):
                normalized_value = self._normalize_text(value)
            else:
                normalized_value = value
            
            normalized_specs[normalized_key] = normalized_value
        
        return normalized_specs
    
    def _normalize_applications(self, applications: List) -> List[str]:
        """Alkalmazási területek normalizálása"""
        normalized_apps = []
        
        for app in applications:
            if isinstance(app, str):
                normalized_app = self._normalize_text(app)
                if normalized_app and normalized_app not in normalized_apps:
                    normalized_apps.append(normalized_app)
        
        return normalized_apps
    
    async def _remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        """Duplikátumok eltávolítása"""
        logger.info(f"Duplikátum eltávolítás: {len(data)} elem")
        
        unique_data = []
        seen_signatures = set()
        
        for item in data:
            try:
                # Aláírás készítése a termékhez
                signature = self._generate_item_signature(item)
                
                if signature not in seen_signatures:
                    # Hasonlóság ellenőrzés meglévő elemekkel
                    is_duplicate = await self._check_similarity_with_existing(item, unique_data)
                    
                    if not is_duplicate:
                        seen_signatures.add(signature)
                        unique_data.append(item)
                    else:
                        logger.debug(f"Duplikátum eltávolítva: {item.get('name', 'Névtelen')}")
                        
            except Exception as e:
                logger.error(f"Duplikátum ellenőrzési hiba: {e}")
                # Biztonság kedvéért megtartjuk
                unique_data.append(item)
        
        logger.info(f"Duplikátum eltávolítás befejezve: {len(data)} -> {len(unique_data)} elem")
        return unique_data
    
    def _generate_item_signature(self, item: Dict) -> str:
        """Termék aláírás generálása duplikátum ellenőrzéshez"""
        name = item.get('name', '').lower().strip()
        url = item.get('source_url', '').lower().strip()
        
        # Hash készítése
        signature_text = f"{name}|{url}"
        return hashlib.md5(signature_text.encode()).hexdigest()[:16]
    
    async def _check_similarity_with_existing(self, item: Dict, existing_items: List[Dict]) -> bool:
        """Hasonlóság ellenőrzés meglévő elemekkel"""
        item_name = item.get('name', '').lower()
        item_desc = item.get('description', '').lower()
        
        for existing in existing_items:
            existing_name = existing.get('name', '').lower()
            existing_desc = existing.get('description', '').lower()
            
            # Név hasonlóság
            name_similarity = SequenceMatcher(None, item_name, existing_name).ratio()
            
            # Leírás hasonlóság
            desc_similarity = SequenceMatcher(None, item_desc, existing_desc).ratio()
            
            # Átlagos hasonlóság
            avg_similarity = (name_similarity + desc_similarity) / 2
            
            if avg_similarity >= self.similarity_threshold:
                return True
        
        return False
    
    async def _categorize_data(self, data: List[Dict]) -> List[Dict]:
        """Adatok kategorizálása"""
        logger.info(f"Adatok kategorizálása: {len(data)} elem")
        
        for item in data:
            try:
                # Jelenlegi kategória ellenőrzés
                current_category = item.get('category', '')
                
                if not current_category or current_category in ['unknown', 'Ismeretlen']:
                    # Automatikus kategorizálás
                    detected_category = self._detect_category(item)
                    item['category'] = detected_category
                    item['category_confidence'] = self._calculate_category_confidence(item, detected_category)
                
                self.processing_stats['categorized_items'] += 1
                
            except Exception as e:
                logger.error(f"Kategorizálási hiba: {e}")
                self.processing_stats['errors_encountered'] += 1
        
        logger.info(f"Kategorizálás befejezve")
        return data
    
    def _detect_category(self, item: Dict) -> str:
        """Kategória automatikus felismerése"""
        text_to_analyze = (
            item.get('name', '') + ' ' + 
            item.get('description', '') + ' ' + 
            str(item.get('raw_data', ''))
        ).lower()
        
        best_category = 'Általános szigetelőanyag'
        best_score = 0
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category
    
    def _calculate_category_confidence(self, item: Dict, category: str) -> float:
        """Kategorizálás megbízhatóságának számítása"""
        keywords = self.category_keywords.get(category, [])
        text_to_analyze = (
            item.get('name', '') + ' ' + 
            item.get('description', '')
        ).lower()
        
        matches = sum(1 for keyword in keywords if keyword.lower() in text_to_analyze)
        confidence = min(matches / max(len(keywords), 1), 1.0)
        
        return confidence
    
    async def _ensure_quality(self, data: List[Dict]) -> List[Dict]:
        """Minőségbiztosítás"""
        logger.info(f"Minőségbiztosítás: {len(data)} elem")
        
        quality_improved_data = []
        
        for item in data:
            try:
                # Minőségi pontszám számítása
                quality_score = self._calculate_quality_score(item)
                item['quality_score'] = quality_score
                
                # Minőség javítás
                if quality_score < 0.7:
                    improved_item = self._improve_item_quality(item)
                    improved_item['quality_score'] = self._calculate_quality_score(improved_item)
                    quality_improved_data.append(improved_item)
                else:
                    quality_improved_data.append(item)
                
            except Exception as e:
                logger.error(f"Minőségbiztosítási hiba: {e}")
                quality_improved_data.append(item)
                self.processing_stats['errors_encountered'] += 1
        
        logger.info(f"Minőségbiztosítás befejezve")
        return quality_improved_data
    
    def _calculate_quality_score(self, item: Dict) -> float:
        """Termék minőségi pontszámának számítása"""
        score = 0.0
        total_weight = 0.0
        
        # Név minősége (20%)
        name = item.get('name', '')
        if name and len(name) > 5:
            score += 0.2
        total_weight += 0.2
        
        # Leírás minősége (30%)
        description = item.get('description', '')
        if description and len(description) > 20:
            score += 0.3
        total_weight += 0.3
        
        # Kategória minősége (15%)
        category = item.get('category', '')
        if category and category != 'unknown':
            score += 0.15
        total_weight += 0.15
        
        # Műszaki specifikációk (20%)
        tech_specs = item.get('technical_specs', {})
        if tech_specs and len(tech_specs) > 0:
            score += 0.2
        total_weight += 0.2
        
        # Forrás URL (15%)
        source_url = item.get('source_url', '')
        if source_url and source_url.startswith('http'):
            score += 0.15
        total_weight += 0.15
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _improve_item_quality(self, item: Dict) -> Dict:
        """Termék minőségének javítása"""
        improved_item = item.copy()
        
        # Név javítása
        if not improved_item.get('name') or len(improved_item.get('name', '')) < 5:
            if 'raw_data' in improved_item:
                extracted_name = self._extract_name_from_raw_data(improved_item['raw_data'])
                if extracted_name:
                    improved_item['name'] = extracted_name
        
        # Leírás javítása
        if not improved_item.get('description') or len(improved_item.get('description', '')) < 20:
            if 'raw_data' in improved_item:
                extracted_desc = self._extract_description_from_raw_data(improved_item['raw_data'])
                if extracted_desc:
                    improved_item['description'] = extracted_desc
        
        # Műszaki paraméterek kinyerése
        if not improved_item.get('technical_specs') or len(improved_item.get('technical_specs', {})) == 0:
            if 'raw_data' in improved_item:
                extracted_specs = self._extract_technical_specs_from_raw_data(improved_item['raw_data'])
                if extracted_specs:
                    improved_item['technical_specs'] = extracted_specs
        
        return improved_item
    
    def _extract_name_from_raw_data(self, raw_data: str) -> Optional[str]:
        """Termék név kinyerése raw adatokból"""
        if not raw_data:
            return None
        
        # Rockwool terméknevekre jellemző minták
        patterns = [
            r'ROCKWOOL\s+([A-Z][A-Za-z\s\d]+)',
            r'([A-Z][A-Za-z]+\s+\d+)',
            r'Termék:\s*([A-Za-z\s\d]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_data)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_description_from_raw_data(self, raw_data: str) -> Optional[str]:
        """Termék leírás kinyerése raw adatokból"""
        if not raw_data or len(raw_data) < 50:
            return None
        
        # Első 300 karakter mint leírás
        description = raw_data[:300].strip()
        
        # Mondatok végének keresése
        sentences = re.split(r'[.!?]', description)
        if len(sentences) > 1:
            return '. '.join(sentences[:2]) + '.'
        
        return description
    
    def _extract_technical_specs_from_raw_data(self, raw_data: str) -> Dict:
        """Műszaki paraméterek kinyerése raw adatokból"""
        if not raw_data:
            return {}
        
        extracted_specs = {}
        
        for spec_name, pattern in self.technical_patterns.items():
            match = re.search(pattern, raw_data, re.IGNORECASE)
            if match:
                extracted_specs[spec_name] = match.group(1)
        
        return extracted_specs
    
    async def _parse_technical_specs(self, data: List[Dict]) -> List[Dict]:
        """Műszaki specifikációk részletes feldolgozása"""
        logger.info(f"Műszaki specifikációk feldolgozása: {len(data)} elem")
        
        for item in data:
            try:
                raw_data = item.get('raw_data', '')
                existing_specs = item.get('technical_specs', {})
                
                # Új specifikációk kinyerése
                new_specs = self._extract_technical_specs_from_raw_data(raw_data)
                
                # Meglévőkkel való kombináció
                combined_specs = {**existing_specs, **new_specs}
                item['technical_specs'] = combined_specs
                
            except Exception as e:
                logger.error(f"Műszaki spec feldolgozási hiba: {e}")
                self.processing_stats['errors_encountered'] += 1
        
        return data
    
    async def _save_processed_data(self, data: List[Dict]) -> None:
        """Feldolgozott adatok mentése"""
        logger.info(f"Feldolgozott adatok mentése: {len(data)} elem")
        
        try:
            db = get_db()
            saved_count = 0
            
            for item in data:
                try:
                    # Ellenőrizzük, hogy már létezik-e
                    existing = db.query(Product).filter(
                        Product.source_url == item.get('source_url')
                    ).first()
                    
                    if existing:
                        # Frissítés
                        existing.name = item.get('name')
                        existing.description = item.get('description')
                        existing.category = item.get('category')
                        existing.technical_specs = item.get('technical_specs', {})
                        existing.applications = item.get('applications', [])
                        existing.updated_at = datetime.now()
                    else:
                        # Új termék
                        product = Product(
                            name=item.get('name'),
                            description=item.get('description'),
                            category=item.get('category'),
                            source_url=item.get('source_url'),
                            technical_specs=item.get('technical_specs', {}),
                            applications=item.get('applications', []),
                            scraped_at=datetime.fromisoformat(item.get('scraped_at', datetime.now().isoformat())),
                            data_source=item.get('data_source')
                        )
                        db.add(product)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Termék mentési hiba: {e}")
            
            db.commit()
            logger.info(f"Adatmentés befejezve: {saved_count} elem mentve")
            
        except Exception as e:
            logger.error(f"Adatbázis mentési hiba: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def get_processing_statistics(self) -> Dict:
        """Feldolgozási statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'statistics': self.processing_stats.copy(),
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
            # Validator teszt
            if not hasattr(self.validator, 'validate_product'):
                health_status['errors'].append('Data validator nem elérhető')
                health_status['healthy'] = False
            
            # Kategória mapping teszt
            if not self.category_keywords:
                health_status['errors'].append('Kategória mapping nincs betöltve')
                health_status['healthy'] = False
            
            # Pattern teszt
            if not self.technical_patterns:
                health_status['errors'].append('Műszaki paraméter patterns nincsenek betöltve')
                health_status['healthy'] = False
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['errors'].append(f'Health check hiba: {str(e)}')
        
        return health_status 