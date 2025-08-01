"""
Production scrapers package for Lambda.hu

This package contains real web scrapers for building material manufacturers.
No mock or placeholder scrapers are included.
"""

from .rockwool_scraper import RockwoolScraper

__all__ = ['RockwoolScraper']