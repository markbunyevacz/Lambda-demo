"""
Database Celery Tasks - Adatbázis karbantartási feladatok

Ez a modul tartalmazza az adatbázis karbantartásával, 
tisztításával és optimalizálásával kapcsolatos Celery feladatokat.
"""

import logging
from typing import Dict
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.product import Product
from ..models.manufacturer import Manufacturer
from ..models.category import Category

logger = logging.getLogger(__name__)


@shared_task
def database_maintenance():
    """
    Napi adatbázis karbantartási feladatok
    
    Returns:
        Dict: Karbantartási eredmények
    """
    start_time = datetime.now()
    logger.info("Adatbázis karbantartás indítása")
    
    results = {
        'success': True,
        'started_at': start_time.isoformat(),
        'tasks_completed': [],
        'errors': []
    }
    
    db = next(get_db())
    
    try:
        # 1. Régi scraped adatok cleanup (30 napnál régebbiek)
        try:
            cleanup_result = cleanup_old_scraped_data(db)
            results['tasks_completed'].append({
                'task': 'cleanup_old_scraped_data',
                'result': cleanup_result
            })
        except Exception as e:
            logger.error(f"Cleanup hiba: {e}")
            results['errors'].append(f"cleanup_old_scraped_data: {str(e)}")
        
        # 2. Duplikátumok eltávolítása
        try:
            dedup_result = remove_product_duplicates(db)
            results['tasks_completed'].append({
                'task': 'remove_product_duplicates', 
                'result': dedup_result
            })
        except Exception as e:
            logger.error(f"Deduplikáció hiba: {e}")
            results['errors'].append(f"remove_product_duplicates: {str(e)}")
        
        # 3. Inaktív termékek kezelése
        try:
            inactive_result = mark_inactive_products(db)
            results['tasks_completed'].append({
                'task': 'mark_inactive_products',
                'result': inactive_result
            })
        except Exception as e:
            logger.error(f"Inaktív termékek hiba: {e}")
            results['errors'].append(f"mark_inactive_products: {str(e)}")
        
        # 4. Adatbázis statisztikák frissítése
        try:
            stats_result = update_database_statistics(db)
            results['tasks_completed'].append({
                'task': 'update_database_statistics',
                'result': stats_result
            })
        except Exception as e:
            logger.error(f"Statisztika frissítés hiba: {e}")
            results['errors'].append(f"update_database_statistics: {str(e)}")
        
        # 5. VACUUM és ANALYZE (PostgreSQL)
        try:
            vacuum_result = vacuum_analyze_tables(db)
            results['tasks_completed'].append({
                'task': 'vacuum_analyze_tables',
                'result': vacuum_result
            })
        except Exception as e:
            logger.error(f"VACUUM hiba: {e}")
            results['errors'].append(f"vacuum_analyze_tables: {str(e)}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Adatbázis karbantartás általános hiba: {e}")
        results['success'] = False
        results['errors'].append(f"general_error: {str(e)}")
        db.rollback()
        
    finally:
        db.close()
    
    duration = (datetime.now() - start_time).total_seconds()
    results['completed_at'] = datetime.now().isoformat()
    results['duration_seconds'] = duration
    results['success'] = len(results['errors']) == 0
    
    logger.info(f"Adatbázis karbantartás befejezve: {results}")
    return results


def cleanup_old_scraped_data(db: Session) -> Dict:
    """Régi scraped adatok eltávolítása"""
    cutoff_date = datetime.now() - timedelta(days=30)
    
    # Régi scraped adatok keresése
    old_products = db.query(Product).filter(
        Product.scraped_at < cutoff_date,
        Product.is_active == False
    )
    
    count_before = old_products.count()
    
    if count_before > 0:
        # Törlés
        old_products.delete(synchronize_session=False)
        db.commit()
    
    return {
        'old_products_removed': count_before,
        'cutoff_date': cutoff_date.isoformat()
    }


def remove_product_duplicates(db: Session) -> Dict:
    """Termék duplikátumok eltávolítása source_url alapján"""
    
    # Duplikátumok keresése
    duplicates_query = db.query(
        Product.source_url,
        func.count(Product.id).label('count'),
        func.array_agg(Product.id).label('ids')
    ).group_by(Product.source_url).having(func.count(Product.id) > 1)
    
    duplicates = duplicates_query.all()
    
    removed_count = 0
    
    for duplicate in duplicates:
        product_ids = duplicate.ids
        # Legújabbat megtartjuk, a többit töröljük
        ids_to_remove = product_ids[:-1]  # Utolsó kivételével mindent
        
        db.query(Product).filter(
            Product.id.in_(ids_to_remove)
        ).delete(synchronize_session=False)
        
        removed_count += len(ids_to_remove)
    
    db.commit()
    
    return {
        'duplicate_groups_found': len(duplicates),
        'products_removed': removed_count
    }


def mark_inactive_products(db: Session) -> Dict:
    """Régen nem frissített termékek inaktívvá jelölése"""
    cutoff_date = datetime.now() - timedelta(days=14)
    
    # Régen nem frissített termékek
    old_products = db.query(Product).filter(
        Product.scraped_at < cutoff_date,
        Product.is_active == True
    )
    
    count = old_products.count()
    
    if count > 0:
        old_products.update({
            'is_active': False,
            'updated_at': datetime.now()
        }, synchronize_session=False)
        
        db.commit()
    
    return {
        'products_marked_inactive': count,
        'cutoff_date': cutoff_date.isoformat()
    }


def update_database_statistics(db: Session) -> Dict:
    """Adatbázis statisztikák számítása"""
    
    # Termékek statisztikái
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.is_active == True).count()
    products_with_images = db.query(Product).filter(
        Product.images != None,
        func.json_array_length(Product.images) > 0
    ).count()
    products_with_specs = db.query(Product).filter(
        Product.technical_specs != None
    ).count()
    
    # Gyártók statisztikái
    total_manufacturers = db.query(Manufacturer).count()
    
    # Kategóriák statisztikái
    total_categories = db.query(Category).count()
    
    # Legutóbbi scraping dátum
    latest_scraping = db.query(func.max(Product.scraped_at)).scalar()
    
    return {
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': total_products - active_products,
        'products_with_images': products_with_images,
        'products_with_technical_specs': products_with_specs,
        'total_manufacturers': total_manufacturers,
        'total_categories': total_categories,
        'latest_scraping': latest_scraping.isoformat() if latest_scraping else None,
        'calculated_at': datetime.now().isoformat()
    }


def vacuum_analyze_tables(db: Session) -> Dict:
    """PostgreSQL VACUUM és ANALYZE futtatása"""
    
    tables = ['products', 'manufacturers', 'categories']
    results = {}
    
    for table in tables:
        try:
            # VACUUM
            db.execute(text(f"VACUUM {table}"))
            
            # ANALYZE
            db.execute(text(f"ANALYZE {table}"))
            
            results[table] = 'success'
            
        except Exception as e:
            logger.error(f"VACUUM/ANALYZE hiba {table}: {e}")
            results[table] = f'error: {str(e)}'
    
    db.commit()
    
    return {
        'tables_processed': results,
        'total_tables': len(tables),
        'successful_tables': sum(1 for v in results.values() if v == 'success')
    }


@shared_task
def backup_database_statistics():
    """
    Adatbázis statisztikák mentése és archiválása
    
    Returns:
        Dict: Mentési eredmény
    """
    start_time = datetime.now()
    logger.info("Adatbázis statisztikák mentése")
    
    try:
        db = next(get_db())
        
        try:
            stats = update_database_statistics(db)
            
            # Itt lehetne egy külön statistics táblába menteni
            # vagy fájlba exportálni a statisztikákat
            
            return {
                'success': True,
                'started_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat(),
                'statistics': stats
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Statisztika mentés hiba: {e}")
        return {
            'success': False,
            'error': str(e),
            'started_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat()
        }


@shared_task
def check_database_health():
    """
    Adatbázis egészségügyi ellenőrzés
    
    Returns:
        Dict: Egészségügyi állapot jelentés
    """
    start_time = datetime.now()
    
    try:
        db = next(get_db())
        
        try:
            # Kapcsolat teszt
            db.execute(text("SELECT 1"))
            
            # Tábla méretek ellenőrzése
            tables_info = {}
            for table in ['products', 'manufacturers', 'categories']:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                tables_info[table] = result
            
            # Indexek ellenőrzése
            index_query = text("""
                SELECT schemaname, tablename, indexname, indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            indexes = db.execute(index_query).fetchall()
            
            return {
                'success': True,
                'checked_at': start_time.isoformat(),
                'database_connection': 'healthy',
                'table_counts': tables_info,
                'indexes_count': len(indexes),
                'response_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Adatbázis egészségügyi ellenőrzés hiba: {e}")
        return {
            'success': False,
            'error': str(e),
            'checked_at': start_time.isoformat(),
            'database_connection': 'unhealthy'
        } 