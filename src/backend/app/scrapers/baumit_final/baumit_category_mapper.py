"""
BAUMIT Category Mapper
---------------------

Purpose:
This module provides BAUMIT-specific category mapping functionality
following the isolated architecture pattern to prevent cross-contamination
between different manufacturers.

Key Features:
- BAUMIT-only category mappings
- Hungarian to English category translation
- Product classification logic
- Integration with the main scraper architecture

This follows the manufacturer isolation principles from FEJLESZTÉSI_BACKLOG.mdc
"""
from typing import Dict, Optional, List
import re

class BaumitCategoryMapper:
    """
    BAUMIT categories only - completely isolated from other manufacturers.
    Follows the Factory pattern for manufacturer-specific implementations.
    """
    
    def __init__(self):
        self.manufacturer = "BAUMIT"
        
        # BAUMIT-specific category mappings
        self.category_mappings = {
            # Thermal Insulation Systems
            'Hőszigetelő rendszerek': {
                'english': 'Thermal Insulation Systems',
                'keywords': ['hőszigetelő', 'szigetelő', 'etics', 'insulation'],
                'subcategories': [
                    'External Thermal Insulation',
                    'Insulation Boards',
                    'Insulation Adhesives'
                ]
            },
            
            # Façade Solutions  
            'Homlokzatfestékek': {
                'english': 'Façade Paints',
                'keywords': ['homlokzat', 'festék', 'facade', 'paint'],
                'subcategories': [
                    'Silicate Paints',
                    'Silicone Paints', 
                    'Acrylic Paints'
                ]
            },
            
            # Colored Thin-layer Renders
            'Színes vékonyvakolatok': {
                'english': 'Colored Thin-layer Renders', 
                'keywords': ['színes', 'vékony', 'vakolat', 'render'],
                'subcategories': [
                    'Mineral Renders',
                    'Silicone Renders',
                    'Acrylic Renders'
                ]
            },
            
            # Substrate Adhesive Systems
            'Aljzatképző ragasztó rendszerek': {
                'english': 'Substrate Adhesive Systems',
                'keywords': ['aljzat', 'ragasztó', 'adhesive', 'bonding'],
                'subcategories': [
                    'Installation Adhesives',
                    'Substrate Primers',
                    'Bonding Agents'
                ]
            },
            
            # Façade Renovation Systems
            'Homlokzati felújító rendszerek': {
                'english': 'Façade Renovation Systems',
                'keywords': ['felújító', 'renovation', 'restoration'],
                'subcategories': [
                    'Renovation Mortars',
                    'Restoration Systems',
                    'Protective Coatings'
                ]
            },
            
            # Interior Renders
            'Beltéri vakolatok': {
                'english': 'Interior Renders',
                'keywords': ['beltéri', 'interior', 'belső'],
                'subcategories': [
                    'Gypsum Renders',
                    'Lime Renders',
                    'Clay Renders'
                ]
            },
            
            # Fillers and Paints
            'Glettek és festékek': {
                'english': 'Fillers and Paints',
                'keywords': ['glett', 'filler', 'interior paint'],
                'subcategories': [
                    'Wall Fillers',
                    'Interior Paints',
                    'Primer Systems'
                ]
            },
            
            # Color Collections
            'Baumit Life színrendszer': {
                'english': 'Baumit Life Color System',
                'keywords': ['life', 'szín', 'color', 'collection'],
                'subcategories': [
                    'StarColor Collection',
                    'PuraColor Collection', 
                    'SilikonColor Collection'
                ]
            }
        }
        
        # Product line mappings
        self.product_lines = {
            'StarColor': 'Premium Facade Paint Line',
            'PuraColor': 'Mineral Paint Collection',
            'SilikonColor': 'Silicone Paint Systems',
            'CreativTop': 'Decorative Render Systems',
            'NanoporTop': 'Advanced Render Technology',
            'KlimaTop': 'Climate-Adaptive Systems'
        }
    
    def categorize_product(self, product_name: str, description: str = "", 
                          url: str = "") -> Dict[str, str]:
        """
        Categorize a BAUMIT product based on name, description, and URL.
        
        Args:
            product_name: Product name
            description: Product description
            url: Product URL
            
        Returns:
            Dict with category information
        """
        text = f"{product_name} {description} {url}".lower()
        
        # Check each category mapping
        for hungarian_cat, category_info in self.category_mappings.items():
            keywords = category_info['keywords']
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword.lower() in text:
                    return {
                        'category_hu': hungarian_cat,
                        'category_en': category_info['english'],
                        'manufacturer': self.manufacturer,
                        'matched_keyword': keyword,
                        'subcategories': category_info['subcategories']
                    }
        
        # Check product lines
        for line_name, line_description in self.product_lines.items():
            if line_name.lower() in text:
                return {
                    'category_hu': 'Termékcsalád',
                    'category_en': line_description,
                    'manufacturer': self.manufacturer,
                    'matched_keyword': line_name,
                    'product_line': line_name
                }
        
        # Default fallback
        return {
            'category_hu': 'Általános építőanyag',
            'category_en': 'General Building Materials',
            'manufacturer': self.manufacturer,
            'matched_keyword': None
        }
    
    def get_all_categories(self) -> List[Dict]:
        """
        Get all available BAUMIT categories.
        """
        categories = []
        for hu_name, info in self.category_mappings.items():
            categories.append({
                'name_hu': hu_name,
                'name_en': info['english'],
                'keywords': info['keywords'],
                'subcategories': info['subcategories']
            })
        return categories
    
    def get_category_by_keywords(self, keywords: List[str]) -> Optional[Dict]:
        """
        Find category by matching keywords.
        """
        keywords_lower = [k.lower() for k in keywords]
        
        for hu_name, info in self.category_mappings.items():
            category_keywords = [k.lower() for k in info['keywords']]
            
            # Check for intersection
            if any(k in category_keywords for k in keywords_lower):
                return {
                    'name_hu': hu_name,
                    'name_en': info['english'],
                    'matched_keywords': list(set(keywords_lower) & set(category_keywords))
                }
        
        return None
    
    def validate_category(self, category_name: str) -> bool:
        """
        Validate if a category exists in BAUMIT mappings.
        """
        return (category_name in self.category_mappings or 
                category_name in [info['english'] for info in self.category_mappings.values()])

# Factory function for getting BAUMIT category mapper
def get_baumit_category_mapper() -> BaumitCategoryMapper:
    """
    Factory function to get BAUMIT category mapper.
    Ensures manufacturer isolation as per FEJLESZTÉSI_BACKLOG.mdc requirements.
    """
    return BaumitCategoryMapper() 