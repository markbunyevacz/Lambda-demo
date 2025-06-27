"""
Price Monitoring Agent - Árfigyelő Agent

Ez az agent felelős az árak monitorozásáért különböző forrásokon,
trend analízisért, riasztások generálásáért és historikus adatok kezeléséért.
"""

import asyncio
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from ..models.product import Product
from ..database import get_db
from .brightdata_agent import BrightDataMCPAgent

logger = logging.getLogger(__name__)


class PriceSource(Enum):
    """Ár források"""
    ROCKWOOL_OFFICIAL = "rockwool_official"
    DISTRIBUTOR_WEBSITES = "distributor_websites"
    MARKETPLACE = "marketplace"
    BRIGHTDATA_SCRAPING = "brightdata_scraping"
    MANUAL_INPUT = "manual_input"
    API_FEEDS = "api_feeds"


class PriceTrend(Enum):
    """Ár trendek"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class AlertType(Enum):
    """Riasztás típusok"""
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase"
    PRICE_TARGET_REACHED = "price_target_reached"
    COMPETITIVE_PRICING = "competitive_pricing"
    AVAILABILITY_CHANGE = "availability_change"


@dataclass
class PricePoint:
    """Ár pont adatstruktúra"""
    product_id: int
    price: float
    currency: str
    source: PriceSource
    timestamp: datetime
    url: Optional[str] = None
    availability: bool = True
    discount_percentage: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class PriceAlert:
    """Ár riasztás adatstruktúra"""
    alert_id: str
    product_id: int
    alert_type: AlertType
    threshold_value: float
    current_value: float
    message: str
    triggered_at: datetime
    source: PriceSource


class PriceMonitoringAgent:
    """
    Árfigyelő Agent osztály
    
    Funkcionalitás:
    - Ár tracking különböző forrásokon
    - Trend analízis
    - Riasztások generálása
    - Historikus adatok kezelése
    - Versenyképes árképzés elemzése
    - Availability monitoring
    """
    
    def __init__(self, monitoring_interval_hours: int = 24, price_change_threshold: float = 5.0):
        self.monitoring_interval_hours = monitoring_interval_hours
        self.price_change_threshold = price_change_threshold  # Százalék
        
        # Agent állapot
        self.agent_id = f"price_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.is_monitoring = False
        
        # Árfigyelési adatok
        self.price_history: Dict[int, List[PricePoint]] = {}
        self.active_alerts: List[PriceAlert] = []
        self.price_targets: Dict[int, Dict] = {}  # product_id -> target config
        
        # Monitoring statisztikák
        self.monitoring_stats = {
            'total_price_checks': 0,
            'successful_price_updates': 0,
            'failed_price_updates': 0,
            'alerts_generated': 0,
            'products_monitored': 0,
            'last_monitoring_run': None,
            'monitoring_duration': 0,
            'sources_used': []
        }
        
        # External agents
        self.mcp_agent = BrightDataMCPAgent()
        
        # Distributor URL patterns (Hungarian market focus)
        self.distributor_patterns = {
            'obi.hu': r'https://www\.obi\.hu/.*',
            'bauhaus.hu': r'https://www\.bauhaus\.hu/.*',
            'praktiker.hu': r'https://www\.praktiker\.hu/.*',
            'lazarus.hu': r'https://www\.lazarus\.hu/.*',
            'epitoanyag.hu': r'https://.*epitoanyag\.hu/.*'
        }
    
    async def monitor_prices(self, product_ids: List[int] = None, 
                           sources: List[PriceSource] = None) -> Dict:
        """
        Főbb árfigyelési funkció
        
        Args:
            product_ids: Monitorozandó termékek (None = összes)
            sources: Használandó források (None = összes elérhető)
            
        Returns:
            Monitoring eredmény és statisztikák
        """
        start_time = datetime.now()
        self.is_monitoring = True
        
        logger.info(f"Árfigyelés indítása - Agent ID: {self.agent_id}")
        
        if not sources:
            sources = [
                PriceSource.ROCKWOOL_OFFICIAL,
                PriceSource.BRIGHTDATA_SCRAPING,
                PriceSource.DISTRIBUTOR_WEBSITES
            ]
        
        try:
            # Termékek lekérése
            monitored_products = await self._get_products_to_monitor(product_ids)
            self.monitoring_stats['products_monitored'] = len(monitored_products)
            
            logger.info(f"Monitorozandó termékek: {len(monitored_products)}")
            
            # Párhuzamos árgyűjtés forrásokból
            price_updates = []
            for source in sources:
                logger.info(f"Árgyűjtés forrásból: {source.value}")
                source_updates = await self._collect_prices_from_source(source, monitored_products)
                price_updates.extend(source_updates)
                self.monitoring_stats['sources_used'].append(source.value)
            
            # Árak feldolgozása és történet frissítése
            await self._process_price_updates(price_updates)
            
            # Trend analízis
            trend_analysis = await self._analyze_price_trends(monitored_products)
            
            # Riasztások ellenőrzése
            new_alerts = await self._check_price_alerts(monitored_products)
            
            # Statisztikák frissítése
            self.monitoring_stats['total_price_checks'] += len(price_updates)
            self.monitoring_stats['successful_price_updates'] += len([u for u in price_updates if u])
            self.monitoring_stats['alerts_generated'] += len(new_alerts)
            self.monitoring_stats['monitoring_duration'] = (datetime.now() - start_time).total_seconds()
            self.monitoring_stats['last_monitoring_run'] = datetime.now().isoformat()
            
            result = {
                'agent_id': self.agent_id,
                'monitoring_completed': True,
                'products_monitored': len(monitored_products),
                'price_updates_collected': len(price_updates),
                'successful_updates': len([u for u in price_updates if u]),
                'new_alerts': len(new_alerts),
                'alerts': [self._alert_to_dict(alert) for alert in new_alerts],
                'trend_analysis': trend_analysis,
                'statistics': self.monitoring_stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Árfigyelés befejezve: {len(price_updates)} ár frissítés, {len(new_alerts)} riasztás")
            return result
            
        except Exception as e:
            logger.error(f"Árfigyelési hiba: {e}")
            return {
                'agent_id': self.agent_id,
                'monitoring_completed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self.is_monitoring = False
    
    async def _get_products_to_monitor(self, product_ids: Optional[List[int]]) -> List[Product]:
        """Monitorozandó termékek lekérése"""
        try:
            db = get_db()
            
            if product_ids:
                products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            else:
                # Csak URL-lel rendelkező termékek
                products = db.query(Product).filter(Product.source_url.isnot(None)).all()
            
            db.close()
            return products
            
        except Exception as e:
            logger.error(f"Termék lekérési hiba: {e}")
            return []
    
    async def _collect_prices_from_source(self, source: PriceSource, products: List[Product]) -> List[Optional[PricePoint]]:
        """Árak gyűjtése egy forrásból"""
        price_points = []
        
        try:
            if source == PriceSource.ROCKWOOL_OFFICIAL:
                price_points = await self._collect_rockwool_official_prices(products)
            elif source == PriceSource.BRIGHTDATA_SCRAPING:
                price_points = await self._collect_brightdata_prices(products)
            elif source == PriceSource.DISTRIBUTOR_WEBSITES:
                price_points = await self._collect_distributor_prices(products)
            elif source == PriceSource.MARKETPLACE:
                price_points = await self._collect_marketplace_prices(products)
            else:
                logger.warning(f"Nem támogatott ár forrás: {source}")
            
        except Exception as e:
            logger.error(f"Ár gyűjtési hiba {source.value}: {e}")
        
        return price_points
    
    async def _collect_rockwool_official_prices(self, products: List[Product]) -> List[Optional[PricePoint]]:
        """Rockwool hivatalos árak gyűjtése"""
        logger.info("Rockwool hivatalos árak gyűjtése")
        price_points = []
        
        # Rockwool hivatalos oldalakról való scraping
        rockwool_urls = [p.source_url for p in products if p.source_url and 'rockwool' in p.source_url.lower()]
        
        if not rockwool_urls:
            logger.info("Nincs Rockwool URL a termékek között")
            return price_points
        
        # MCP agent használata árgyűjtéshez
        try:
            scraped_data = await self.mcp_agent.scrape_rockwool_with_ai(
                rockwool_urls,
                "Gyűjts össze ár információkat HUF-ban. Keress 'ár', 'price', 'Ft' szavakat."
            )
            
            for item in scraped_data:
                # Ár kinyerése a scraped adatokból
                price = self._extract_price_from_scraped_data(item)
                if price:
                    # Termék ID meghatározása URL alapján
                    product_id = self._find_product_id_by_url(products, item.get('source_url'))
                    if product_id:
                        price_point = PricePoint(
                            product_id=product_id,
                            price=price,
                            currency='HUF',
                            source=PriceSource.ROCKWOOL_OFFICIAL,
                            timestamp=datetime.now(),
                            url=item.get('source_url'),
                            availability=True
                        )
                        price_points.append(price_point)
                        
        except Exception as e:
            logger.error(f"Rockwool ár scraping hiba: {e}")
        
        logger.info(f"Rockwool árak: {len(price_points)} ár pont")
        return price_points
    
    async def _collect_brightdata_prices(self, products: List[Product]) -> List[Optional[PricePoint]]:
        """BrightData általános ár scraping"""
        logger.info("BrightData ár scraping")
        price_points = []
        
        # Termék nevek alapján keresés különböző weboldalakon
        for product in products[:5]:  # Limitálás demo céljából
            try:
                search_query = f"{product.name} ár Hungary site:obi.hu OR site:bauhaus.hu"
                search_results = await self.mcp_agent.search_rockwool_products(search_query)
                
                if search_results:
                    # Első találat scraping
                    first_result_url = search_results[0].get('url')
                    if first_result_url:
                        scraped_data = await self.mcp_agent.scrape_rockwool_with_ai(
                            [first_result_url],
                            f"Keresd meg a {product.name} termék árát HUF-ban."
                        )
                        
                        for item in scraped_data:
                            price = self._extract_price_from_scraped_data(item)
                            if price:
                                price_point = PricePoint(
                                    product_id=product.id,
                                    price=price,
                                    currency='HUF',
                                    source=PriceSource.BRIGHTDATA_SCRAPING,
                                    timestamp=datetime.now(),
                                    url=first_result_url,
                                    availability=True
                                )
                                price_points.append(price_point)
                                break
                        
            except Exception as e:
                logger.error(f"BrightData ár scraping hiba {product.name}: {e}")
                continue
        
        logger.info(f"BrightData árak: {len(price_points)} ár pont")
        return price_points
    
    async def _collect_distributor_prices(self, products: List[Product]) -> List[Optional[PricePoint]]:
        """Forgalmazói árak gyűjtése"""
        logger.info("Forgalmazói árak gyűjtése")
        # Placeholder - valós implementációhoz specifikus distributor API-k kellenének
        return []
    
    async def _collect_marketplace_prices(self, products: List[Product]) -> List[Optional[PricePoint]]:
        """Marketplace árak gyűjtése"""
        logger.info("Marketplace árak gyűjtése")
        # Placeholder - Amazon, eBay, stb. integrációhoz
        return []
    
    def _extract_price_from_scraped_data(self, scraped_item: Dict) -> Optional[float]:
        """Ár kinyerése scraped adatokból"""
        import re
        
        # Szöveges tartalom ahol árakat keresünk
        text_content = (
            scraped_item.get('name', '') + ' ' +
            scraped_item.get('description', '') + ' ' +
            str(scraped_item.get('raw_data', ''))
        )
        
        # Magyar ár pattern: 1.234 Ft, 1 234 Ft, 1234 Ft
        price_patterns = [
            r'(\d{1,3}(?:[\s\.]?\d{3})*)\s*(?:Ft|HUF|forint)',
            r'(\d{1,6})\s*(?:Ft|HUF)',
            r'ár[:\s]*(\d{1,3}(?:[\s\.]?\d{3})*)',
            r'price[:\s]*(\d{1,6})',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                try:
                    # Számjegyek kinyerése és konvertálás
                    clean_price = re.sub(r'[^\d]', '', match)
                    price = float(clean_price)
                    
                    # Ésszerű ár ellenőrzés (100 Ft - 1M Ft)
                    if 100 <= price <= 1000000:
                        return price
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _find_product_id_by_url(self, products: List[Product], url: str) -> Optional[int]:
        """Termék ID meghatározása URL alapján"""
        if not url:
            return None
        
        for product in products:
            if product.source_url and product.source_url == url:
                return product.id
        
        return None
    
    async def _process_price_updates(self, price_updates: List[Optional[PricePoint]]) -> None:
        """Ár frissítések feldolgozása"""
        logger.info(f"Ár frissítések feldolgozása: {len(price_updates)} frissítés")
        
        for price_point in price_updates:
            if price_point:
                # Történethez hozzáadás
                if price_point.product_id not in self.price_history:
                    self.price_history[price_point.product_id] = []
                
                self.price_history[price_point.product_id].append(price_point)
                
                # Történet limitálása (max 100 pont termékenkén)
                if len(self.price_history[price_point.product_id]) > 100:
                    self.price_history[price_point.product_id] = \
                        self.price_history[price_point.product_id][-100:]
                
                self.monitoring_stats['successful_price_updates'] += 1
            else:
                self.monitoring_stats['failed_price_updates'] += 1
    
    async def _analyze_price_trends(self, products: List[Product]) -> Dict:
        """Ár trend analízis"""
        logger.info("Ár trend analízis")
        
        trend_analysis = {
            'overall_trend': PriceTrend.UNKNOWN.value,
            'product_trends': {},
            'average_change_percentage': 0.0,
            'volatile_products': [],
            'stable_products': []
        }
        
        product_changes = []
        
        for product in products:
            if product.id in self.price_history:
                history = self.price_history[product.id]
                
                if len(history) >= 2:
                    # Trend számítás az utolsó 30 napra
                    recent_history = [
                        pp for pp in history 
                        if pp.timestamp >= datetime.now() - timedelta(days=30)
                    ]
                    
                    if len(recent_history) >= 2:
                        trend = self._calculate_price_trend(recent_history)
                        volatility = self._calculate_price_volatility(recent_history)
                        
                        # Változás százalék
                        price_change = (recent_history[-1].price - recent_history[0].price) / recent_history[0].price * 100
                        product_changes.append(price_change)
                        
                        trend_analysis['product_trends'][product.id] = {
                            'product_name': product.name,
                            'trend': trend.value,
                            'volatility': volatility,
                            'price_change_percentage': price_change,
                            'current_price': recent_history[-1].price,
                            'currency': recent_history[-1].currency
                        }
                        
                        # Kategorizálás
                        if volatility > 10:  # 10% feletti volatilitás
                            trend_analysis['volatile_products'].append(product.id)
                        elif abs(price_change) < 2:  # 2% alatti változás
                            trend_analysis['stable_products'].append(product.id)
        
        # Általános trend
        if product_changes:
            avg_change = statistics.mean(product_changes)
            trend_analysis['average_change_percentage'] = avg_change
            
            if avg_change > 5:
                trend_analysis['overall_trend'] = PriceTrend.INCREASING.value
            elif avg_change < -5:
                trend_analysis['overall_trend'] = PriceTrend.DECREASING.value
            elif statistics.stdev(product_changes) > 15:
                trend_analysis['overall_trend'] = PriceTrend.VOLATILE.value
            else:
                trend_analysis['overall_trend'] = PriceTrend.STABLE.value
        
        return trend_analysis
    
    def _calculate_price_trend(self, price_history: List[PricePoint]) -> PriceTrend:
        """Ár trend számítás egy termékre"""
        if len(price_history) < 2:
            return PriceTrend.UNKNOWN
        
        prices = [pp.price for pp in price_history]
        
        # Lineáris regresszió egyszerű implementációja
        n = len(prices)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(prices)
        sum_xy = sum(x * y for x, y in zip(x_values, prices))
        sum_x2 = sum(x * x for x in x_values)
        
        # Slope számítás
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Trend meghatározás
        if slope > prices[0] * 0.01:  # 1% növekedés
            return PriceTrend.INCREASING
        elif slope < -prices[0] * 0.01:  # 1% csökkenés
            return PriceTrend.DECREASING
        else:
            return PriceTrend.STABLE
    
    def _calculate_price_volatility(self, price_history: List[PricePoint]) -> float:
        """Ár volatilitás számítás (CV - coefficient of variation)"""
        if len(price_history) < 2:
            return 0.0
        
        prices = [pp.price for pp in price_history]
        mean_price = statistics.mean(prices)
        
        if mean_price == 0:
            return 0.0
        
        std_dev = statistics.stdev(prices)
        return (std_dev / mean_price) * 100  # Százalékban
    
    async def _check_price_alerts(self, products: List[Product]) -> List[PriceAlert]:
        """Ár riasztások ellenőrzése"""
        new_alerts = []
        
        for product in products:
            if product.id in self.price_history and product.id in self.price_targets:
                recent_prices = self.price_history[product.id]
                if recent_prices:
                    current_price = recent_prices[-1].price
                    target_config = self.price_targets[product.id]
                    
                    # Célár ellenőrzés
                    if 'target_price' in target_config:
                        target_price = target_config['target_price']
                        if current_price <= target_price:
                            alert = PriceAlert(
                                alert_id=f"target_{product.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                product_id=product.id,
                                alert_type=AlertType.PRICE_TARGET_REACHED,
                                threshold_value=target_price,
                                current_value=current_price,
                                message=f"{product.name} elérte a célárát: {current_price} HUF",
                                triggered_at=datetime.now(),
                                source=recent_prices[-1].source
                            )
                            new_alerts.append(alert)
                    
                    # Változás százalék ellenőrzés
                    if len(recent_prices) >= 2:
                        previous_price = recent_prices[-2].price
                        change_percentage = abs((current_price - previous_price) / previous_price * 100)
                        
                        if change_percentage >= self.price_change_threshold:
                            alert_type = AlertType.PRICE_INCREASE if current_price > previous_price else AlertType.PRICE_DROP
                            alert = PriceAlert(
                                alert_id=f"change_{product.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                product_id=product.id,
                                alert_type=alert_type,
                                threshold_value=self.price_change_threshold,
                                current_value=change_percentage,
                                message=f"{product.name} ára {change_percentage:.1f}%-ot {'emelkedett' if current_price > previous_price else 'csökkent'}",
                                triggered_at=datetime.now(),
                                source=recent_prices[-1].source
                            )
                            new_alerts.append(alert)
        
        # Aktív riasztások frissítése
        self.active_alerts.extend(new_alerts)
        
        return new_alerts
    
    def _alert_to_dict(self, alert: PriceAlert) -> Dict:
        """Alert objektum átalakítása dictionary-vá"""
        return {
            'alert_id': alert.alert_id,
            'product_id': alert.product_id,
            'alert_type': alert.alert_type.value,
            'threshold_value': alert.threshold_value,
            'current_value': alert.current_value,
            'message': alert.message,
            'triggered_at': alert.triggered_at.isoformat(),
            'source': alert.source.value
        }
    
    async def set_price_target(self, product_id: int, target_price: float, 
                              alert_on_drop: bool = True, alert_on_increase: bool = False) -> Dict:
        """Ár célérték beállítása"""
        self.price_targets[product_id] = {
            'target_price': target_price,
            'alert_on_drop': alert_on_drop,
            'alert_on_increase': alert_on_increase,
            'set_at': datetime.now().isoformat()
        }
        
        logger.info(f"Ár célérték beállítva termék {product_id}: {target_price} HUF")
        
        return {
            'success': True,
            'product_id': product_id,
            'target_price': target_price,
            'message': f'Ár célérték beállítva: {target_price} HUF'
        }
    
    async def get_price_history(self, product_id: int, days: int = 30) -> Dict:
        """Termék ár történet lekérése"""
        if product_id not in self.price_history:
            return {
                'product_id': product_id,
                'price_history': [],
                'message': 'Nincs ár történet'
            }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            {
                'price': pp.price,
                'currency': pp.currency,
                'source': pp.source.value,
                'timestamp': pp.timestamp.isoformat(),
                'url': pp.url,
                'availability': pp.availability
            }
            for pp in self.price_history[product_id]
            if pp.timestamp >= cutoff_date
        ]
        
        return {
            'product_id': product_id,
            'price_history': recent_history,
            'days_requested': days,
            'data_points': len(recent_history)
        }
    
    async def get_monitoring_statistics(self) -> Dict:
        """Monitoring statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            'is_monitoring': self.is_monitoring,
            'statistics': self.monitoring_stats.copy(),
            'active_alerts_count': len(self.active_alerts),
            'price_targets_count': len(self.price_targets),
            'products_with_history': len(self.price_history),
            'timestamp': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        health_status = {
            'agent_id': self.agent_id,
            'is_monitoring': self.is_monitoring,
            'healthy': True,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # MCP agent ellenőrzés
            if not self.mcp_agent.mcp_available:
                health_status['errors'].append('BrightData MCP agent nem elérhető')
                # Nem critical hiba árfigyeléshez
            
            # Adatbázis kapcsolat ellenőrzés
            try:
                db = get_db()
                db.query(Product).count()
                db.close()
            except Exception as e:
                health_status['errors'].append(f'Adatbázis kapcsolat hiba: {str(e)}')
                health_status['healthy'] = False
            
            # Price history integrity ellenőrzés
            corrupted_histories = 0
            for product_id, history in self.price_history.items():
                if not history or not all(isinstance(pp, PricePoint) for pp in history):
                    corrupted_histories += 1
            
            if corrupted_histories > 0:
                health_status['errors'].append(f'{corrupted_histories} sérült ár történet')
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['errors'].append(f'Health check hiba: {str(e)}')
        
        return health_status 