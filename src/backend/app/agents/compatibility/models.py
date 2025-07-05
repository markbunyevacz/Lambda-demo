"""
Kompatibilitási modellek és enums
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


class CompatibilityType(Enum):
    """Kompatibilitás típusok"""
    TECHNICAL_SPECS = "technical_specs"
    APPLICATION_AREAS = "application_areas"
    STANDARDS_COMPLIANCE = "standards_compliance"
    INSTALLATION_METHOD = "installation_method"
    ENVIRONMENTAL_CONDITIONS = "environmental_conditions"
    SYSTEM_INTEGRATION = "system_integration"


class CompatibilityLevel(Enum):
    """Kompatibilitási szintek"""
    FULLY_COMPATIBLE = "fully_compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    CONDITIONALLY_COMPATIBLE = "conditionally_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class StandardType(Enum):
    """Szabvány típusok"""
    EN_EUROPEAN = "en_european"
    MSZ_HUNGARIAN = "msz_hungarian"
    ISO_INTERNATIONAL = "iso_international"
    FIRE_SAFETY = "fire_safety"
    THERMAL_PERFORMANCE = "thermal_performance"
    ACOUSTIC_PERFORMANCE = "acoustic_performance"


@dataclass
class CompatibilityResult:
    """Kompatibilitási eredmény adatstruktúra"""
    product_a_id: int
    product_b_id: int
    compatibility_type: CompatibilityType
    compatibility_level: CompatibilityLevel
    confidence_score: float
    reasons: List[str]
    recommendations: List[str]
    technical_notes: List[str]
    checked_at: datetime


@dataclass
class StandardCompliance:
    """Szabványnak való megfelelés adatstruktúra"""
    standard_name: str
    standard_type: StandardType
    compliance_level: str
    requirements: List[str]
    verified: bool
    notes: Optional[str] = None 