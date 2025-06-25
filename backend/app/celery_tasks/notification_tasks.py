"""
Notification Celery Tasks - Értesítési és riportolási feladatok

Ez a modul tartalmazza az email értesítésekkel, 
riportokkal és monitoringgal kapcsolatos Celery feladatokat.
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_daily_scraping_report():
    """
    Napi scraping jelentés küldése
    
    Returns:
        Dict: Email küldés eredménye
    """
    start_time = datetime.now()
    logger.info("Napi scraping jelentés készítése")
    
    try:
        # Scraping statisztikák összegyűjtése
        from ..database import get_db
        from ..models.product import Product
        from sqlalchemy import func
        
        db = next(get_db())
        
        try:
            # Mai scraping aktivitás
            today = datetime.now().date()
            
            products_scraped_today = db.query(Product).filter(
                func.date(Product.scraped_at) == today
            ).count()
            
            total_products = db.query(Product).count()
            active_products = db.query(Product).filter(
                Product.is_active == True
            ).count()
            
            # Legutóbbi scraping
            latest_scraping = db.query(func.max(Product.scraped_at)).scalar()
            
            report_data = {
                'date': today.isoformat(),
                'products_scraped_today': products_scraped_today,
                'total_products': total_products,
                'active_products': active_products,
                'latest_scraping': latest_scraping.isoformat() if latest_scraping else None,
                'generated_at': start_time.isoformat()
            }
            
            # Email küldés (placeholder - implementálandó)
            email_result = send_email_report(report_data)
            
            return {
                'success': True,
                'report_data': report_data,
                'email_sent': email_result['success'],
                'generated_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Napi jelentés hiba: {e}")
        return {
            'success': False,
            'error': str(e),
            'generated_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat()
        }


@shared_task
def send_scraping_error_alert(error_details: Dict):
    """
    Scraping hiba riasztás küldése
    
    Args:
        error_details: Hiba részletei
        
    Returns:
        Dict: Riasztás küldés eredménye
    """
    logger.info(f"Scraping hiba riasztás: {error_details}")
    
    try:
        # Email riasztás küldése (placeholder)
        alert_data = {
            'type': 'scraping_error',
            'error_details': error_details,
            'timestamp': datetime.now().isoformat(),
            'severity': 'high' if 'critical' in str(error_details).lower() else 'medium'
        }
        
        email_result = send_alert_email(alert_data)
        
        return {
            'success': True,
            'alert_sent': email_result['success'],
            'alert_data': alert_data
        }
        
    except Exception as e:
        logger.error(f"Riasztás küldési hiba: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def send_weekly_summary_report():
    """
    Heti összefoglaló jelentés
    
    Returns:
        Dict: Heti riport eredménye
    """
    start_time = datetime.now()
    logger.info("Heti összefoglaló jelentés készítése")
    
    try:
        from ..database import get_db
        from ..models.product import Product
        from sqlalchemy import func
        
        db = next(get_db())
        
        try:
            # Heti adatok
            week_ago = datetime.now() - timedelta(days=7)
            
            # Új termékek a héten
            new_products_this_week = db.query(Product).filter(
                Product.created_at >= week_ago
            ).count()
            
            # Frissített termékek
            updated_products_this_week = db.query(Product).filter(
                Product.updated_at >= week_ago,
                Product.created_at < week_ago
            ).count()
            
            # Kategóriánkénti bontás
            category_stats = db.query(
                Product.category_id,
                func.count(Product.id).label('count')
            ).group_by(Product.category_id).all()
            
            weekly_summary = {
                'week_ending': start_time.date().isoformat(),
                'new_products': new_products_this_week,
                'updated_products': updated_products_this_week,
                'category_breakdown': [
                    {'category_id': stat[0], 'product_count': stat[1]}
                    for stat in category_stats
                ],
                'generated_at': start_time.isoformat()
            }
            
            # Email küldés
            email_result = send_weekly_email_report(weekly_summary)
            
            return {
                'success': True,
                'weekly_summary': weekly_summary,
                'email_sent': email_result['success'],
                'generated_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Heti jelentés hiba: {e}")
        return {
            'success': False,
            'error': str(e),
            'generated_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat()
        }


def send_email_report(report_data: Dict) -> Dict:
    """
    Email riport küldése (placeholder implementáció)
    
    Args:
        report_data: Riport adatok
        
    Returns:
        Dict: Küldés eredménye
    """
    # TODO: Valós email service integráció (pl. SendGrid, SMTP)
    logger.info(f"Email riport küldése: {report_data}")
    
    # Placeholder - mindig sikeres
    return {
        'success': True,
        'recipient': 'admin@lambda.hu',
        'subject': f"Lambda.hu Napi Scraping Jelentés - {report_data.get('date')}",
        'message': 'Email küldés placeholder - implementálandó'
    }


def send_alert_email(alert_data: Dict) -> Dict:
    """
    Riasztó email küldése (placeholder)
    
    Args:
        alert_data: Riasztás adatok
        
    Returns:
        Dict: Küldés eredménye
    """
    logger.warning(f"Riasztó email küldése: {alert_data}")
    
    # Placeholder
    return {
        'success': True,
        'recipient': 'alerts@lambda.hu',
        'subject': f"Lambda.hu Scraping Riasztás - {alert_data.get('severity', 'unknown')}",
        'message': 'Riasztás email placeholder - implementálandó'
    }


def send_weekly_email_report(weekly_data: Dict) -> Dict:
    """
    Heti email riport küldése (placeholder)
    
    Args:
        weekly_data: Heti adatok
        
    Returns:
        Dict: Küldés eredménye
    """
    logger.info(f"Heti email riport küldése: {weekly_data}")
    
    # Placeholder
    return {
        'success': True,
        'recipient': 'reports@lambda.hu',
        'subject': f"Lambda.hu Heti Összefoglaló - {weekly_data.get('week_ending')}",
        'message': 'Heti riport email placeholder - implementálandó'
    }


@shared_task
def monitor_scraper_health():
    """
    Scraper egészségügyi monitoring
    
    Returns:
        Dict: Monitoring eredmény
    """
    start_time = datetime.now()
    
    try:
        # Scraper kapcsolat teszt
        from ..scraper import RockwoolScraper, ScrapingConfig
        
        config = ScrapingConfig(timeout=10)
        scraper = RockwoolScraper(config)
        
        # Egyszerű kapcsolat teszt
        import requests
        response = requests.get('https://www.rockwool.hu', timeout=10)
        
        health_status = {
            'timestamp': start_time.isoformat(),
            'rockwool_website': {
                'accessible': response.status_code == 200,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'status_code': response.status_code
            },
            'scraper_ready': True
        }
        
        # Ha nem elérhető, riasztás küldése
        if response.status_code != 200:
            send_scraping_error_alert.delay({
                'type': 'website_unreachable',
                'website': 'https://www.rockwool.hu',
                'status_code': response.status_code,
                'timestamp': start_time.isoformat()
            })
        
        return {
            'success': True,
            'health_status': health_status,
            'checked_at': start_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scraper health monitoring hiba: {e}")
        
        # Kritikus hiba riasztás
        send_scraping_error_alert.delay({
            'type': 'health_check_failed',
            'error': str(e),
            'timestamp': start_time.isoformat(),
            'severity': 'critical'
        })
        
        return {
            'success': False,
            'error': str(e),
            'checked_at': start_time.isoformat()
        } 