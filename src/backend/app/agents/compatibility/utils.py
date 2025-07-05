"""
Kompatibilitási segédfüggvények
"""
from .models import CompatibilityLevel


def determine_compatibility_level(
    score: float, thresholds: dict
) -> CompatibilityLevel:
    """
    Determines compatibility level based on a score and defined thresholds.
    
    Args:
        score: The calculated compatibility score.
        thresholds: A dictionary with level names as keys and score
                    thresholds as values.
                    Example: {'fully': 0.8, 'partially': 0.5, 
                              'conditionally': 0.2}

    Returns:
        The calculated compatibility level.
    """
    if score >= thresholds.get('fully', 0.8):
        return CompatibilityLevel.FULLY_COMPATIBLE
    elif score >= thresholds.get('partially', 0.5):
        return CompatibilityLevel.PARTIALLY_COMPATIBLE
    elif score >= thresholds.get('conditionally', 0.2):
        return CompatibilityLevel.CONDITIONALLY_COMPATIBLE
    
    return CompatibilityLevel.INCOMPATIBLE 