"""
Mixture of Experts (MoE) Architecture for PDF Extraction
======================================================

This module implements a sophisticated MoE system that routes PDF extraction
tasks to the most appropriate expert based on document characteristics,
manufacturer patterns, and extraction requirements.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import logging

# ML/AI imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Project imports
from .models import ExtractionResult, StrategyType, ExtractionTask
from .strategies import BaseExtractionStrategy, PDFPlumberStrategy, PyMuPDFStrategy

logger = logging.getLogger(__name__)


class ExpertType(Enum):
    """Types of experts in the MoE system"""
    MANUFACTURER_SPECIFIC = "manufacturer_specific"
    DOCUMENT_TYPE_SPECIFIC = "document_type_specific"
    EXTRACTION_METHOD_SPECIFIC = "extraction_method_specific"
    AI_VALIDATION_SPECIFIC = "ai_validation_specific"
    CONFIDENCE_SCORING = "confidence_scoring"


class DocumentType(Enum):
    """Document types that require different extraction approaches"""
    TECHNICAL_DATASHEET = "technical_datasheet"
    PRICE_LIST = "price_list"
    BROCHURE = "brochure"
    CATALOG = "catalog"
    PERFORMANCE_DECLARATION = "performance_declaration"
    INSTALLATION_GUIDE = "installation_guide"
    UNKNOWN = "unknown"


@dataclass
class ExpertCapability:
    """Defines what an expert can handle"""
    expert_type: ExpertType
    confidence_threshold: float = 0.7
    cost_factor: float = 1.0
    processing_time_estimate: float = 30.0
    supported_manufacturers: List[str] = field(default_factory=list)
    supported_document_types: List[DocumentType] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=lambda: ["hungarian", "english"])
    

@dataclass
class RoutingDecision:
    """Routing decision made by the MoE gating network"""
    selected_experts: List[str]
    confidence_scores: Dict[str, float]
    routing_rationale: str
    estimated_cost: float
    estimated_processing_time: float
    fallback_strategy: Optional[str] = None


class BaseExpert(ABC):
    """Base class for all experts in the MoE system"""
    
    def __init__(self, name: str, capabilities: ExpertCapability):
        self.name = name
        self.capabilities = capabilities
        self.performance_history = []
        self.specialization_score = 0.0
        
    @abstractmethod
    async def can_handle(self, task: ExtractionTask) -> float:
        """Return confidence score (0-1) for handling this task"""
        pass
    
    @abstractmethod
    async def extract(self, task: ExtractionTask) -> ExtractionResult:
        """Perform extraction using this expert's specialization"""
        pass
    
    async def evaluate_performance(self, result: ExtractionResult) -> float:
        """Evaluate and update performance metrics"""
        score = result.confidence_score * result.data_completeness
        self.performance_history.append({
            'timestamp': time.time(),
            'score': score,
            'processing_time': result.execution_time_seconds
        })
        
        # Keep only last 100 performance records
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Update specialization score (exponential moving average)
        if self.performance_history:
            recent_scores = [p['score'] for p in self.performance_history[-10:]]
            self.specialization_score = np.mean(recent_scores)
        
        return score


class ManufacturerSpecificExpert(BaseExpert):
    """Expert specialized for specific manufacturer's document patterns"""
    
    def __init__(self, manufacturer: str, document_patterns: Dict[str, Any]):
        capabilities = ExpertCapability(
            expert_type=ExpertType.MANUFACTURER_SPECIFIC,
            confidence_threshold=0.8,
            cost_factor=1.2,
            processing_time_estimate=25.0,
            supported_manufacturers=[manufacturer]
        )
        
        super().__init__(f"{manufacturer}_expert", capabilities)
        self.manufacturer = manufacturer
        self.document_patterns = document_patterns
        self.extraction_strategy = self._create_specialized_strategy()
    
    def _create_specialized_strategy(self) -> BaseExtractionStrategy:
        """Create extraction strategy optimized for this manufacturer"""
        if self.manufacturer.upper() == "ROCKWOOL":
            return RockwoolSpecializedStrategy()
        elif self.manufacturer.upper() == "LEIER":
            return LeierSpecializedStrategy()
        elif self.manufacturer.upper() == "BAUMIT":
            return BaumitSpecializedStrategy()
        else:
            return PDFPlumberStrategy()  # Default fallback
    
    async def can_handle(self, task: ExtractionTask) -> float:
        """Determine if this expert can handle the task"""
        # Check if manufacturer matches
        if hasattr(task, 'manufacturer') and task.manufacturer:
            if task.manufacturer.upper() == self.manufacturer.upper():
                return 0.95  # High confidence for manufacturer match
        
        # Check document patterns in filename/content
        pdf_path = Path(task.pdf_path)
        filename = pdf_path.name.lower()
        
        # Manufacturer-specific filename patterns
        if self.manufacturer.lower() in filename:
            return 0.8
        
        # Check document patterns
        for pattern, confidence in self.document_patterns.items():
            if pattern.lower() in filename:
                return confidence
        
        return 0.1  # Low confidence for unknown documents
    
    async def extract(self, task: ExtractionTask) -> ExtractionResult:
        """Extract using manufacturer-specific optimizations"""
        start_time = time.time()
        
        try:
            # Use specialized extraction strategy
            result = await self.extraction_strategy.extract(task.pdf_path)
            
            # Apply manufacturer-specific enhancements
            if result.success:
                result = await self._enhance_with_manufacturer_knowledge(result, task)
            
            execution_time = time.time() - start_time
            result.execution_time_seconds = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExtractionResult(
                strategy_type=StrategyType.MANUFACTURER_SPECIFIC,
                success=False,
                execution_time_seconds=execution_time,
                error_message=f"{self.manufacturer} expert failed: {str(e)}",
                confidence_score=0.0
            )
    
    async def _enhance_with_manufacturer_knowledge(self, result: ExtractionResult, task: ExtractionTask) -> ExtractionResult:
        """Apply manufacturer-specific knowledge to improve extraction"""
        if not result.extracted_data:
            return result
        
        # Manufacturer-specific enhancements
        if self.manufacturer.upper() == "ROCKWOOL":
            result = await self._enhance_rockwool_extraction(result)
        elif self.manufacturer.upper() == "LEIER":
            result = await self._enhance_leier_extraction(result)
        elif self.manufacturer.upper() == "BAUMIT":
            result = await self._enhance_baumit_extraction(result)
        
        return result
    
    async def _enhance_rockwool_extraction(self, result: ExtractionResult) -> ExtractionResult:
        """ROCKWOOL-specific enhancements"""
        data = result.extracted_data
        
        # ROCKWOOL-specific technical specifications
        if 'technical_specs' in data:
            specs = data['technical_specs']
            
            # Normalize ROCKWOOL thermal conductivity format
            if 'thermal_conductivity' in specs:
                tc = specs['thermal_conductivity']
                if isinstance(tc, dict) and 'value' in tc:
                    # ROCKWOOL typically uses λD values
                    if tc['value'] > 0.01 and tc['value'] < 0.1:  # Typical range
                        specs['thermal_conductivity_classification'] = 'λD'
                        specs['thermal_conductivity_confidence'] = 0.9
        
        # ROCKWOOL product naming patterns
        if 'product_name' in data:
            name = data['product_name']
            if any(pattern in name.upper() for pattern in ['FRONTROCK', 'ROCKWOOL', 'MONROCK']):
                data['manufacturer_confidence'] = 0.95
                data['product_series'] = self._extract_rockwool_series(name)
        
        result.extracted_data = data
        return result
    
    async def _enhance_leier_extraction(self, result: ExtractionResult) -> ExtractionResult:
        """LEIER-specific enhancements"""
        data = result.extracted_data
        
        # LEIER-specific patterns
        if 'product_name' in data:
            name = data['product_name']
            if any(pattern in name.upper() for pattern in ['LEIER', 'DURISOL', 'THERMOPLAN']):
                data['manufacturer_confidence'] = 0.95
                data['product_category'] = self._extract_leier_category(name)
        
        result.extracted_data = data
        return result
    
    async def _enhance_baumit_extraction(self, result: ExtractionResult) -> ExtractionResult:
        """BAUMIT-specific enhancements"""
        data = result.extracted_data
        
        # BAUMIT-specific patterns
        if 'product_name' in data:
            name = data['product_name']
            if any(pattern in name.upper() for pattern in ['BAUMIT', 'LIFE', 'STAR']):
                data['manufacturer_confidence'] = 0.95
                data['color_system'] = self._extract_baumit_color_system(name)
        
        result.extracted_data = data
        return result
    
    def _extract_rockwool_series(self, name: str) -> str:
        """Extract ROCKWOOL product series from name"""
        series_patterns = {
            'FRONTROCK': 'Facade Insulation',
            'MONROCK': 'Flat Roof Insulation',
            'ROCKWOOL': 'General Insulation'
        }
        
        for pattern, series in series_patterns.items():
            if pattern in name.upper():
                return series
        
        return 'Unknown Series'
    
    def _extract_leier_category(self, name: str) -> str:
        """Extract LEIER product category from name"""
        category_patterns = {
            'DURISOL': 'Concrete Blocks',
            'THERMOPLAN': 'Thermal Blocks'
        }
        
        for pattern, category in category_patterns.items():
            if pattern in name.upper():
                return category
        
        return 'Unknown Category'
    
    def _extract_baumit_color_system(self, name: str) -> str:
        """Extract BAUMIT color system from name"""
        if 'LIFE' in name.upper():
            return 'Baumit Life Color System'
        elif 'STAR' in name.upper():
            return 'Baumit Star System'
        return 'Standard System'


class DocumentTypeExpert(BaseExpert):
    """Expert specialized for specific document types"""
    
    def __init__(self, document_type: DocumentType, extraction_patterns: Dict[str, Any]):
        capabilities = ExpertCapability(
            expert_type=ExpertType.DOCUMENT_TYPE_SPECIFIC,
            confidence_threshold=0.7,
            cost_factor=1.0,
            processing_time_estimate=20.0,
            supported_document_types=[document_type]
        )
        
        super().__init__(f"{document_type.value}_expert", capabilities)
        self.document_type = document_type
        self.extraction_patterns = extraction_patterns
    
    async def can_handle(self, task: ExtractionTask) -> float:
        """Determine if this expert can handle the document type"""
        # Analyze filename patterns
        pdf_path = Path(task.pdf_path)
        filename = pdf_path.name.lower()
        
        # Document type patterns
        type_patterns = {
            DocumentType.TECHNICAL_DATASHEET: ['datasheet', 'műszaki', 'technical', 'specs'],
            DocumentType.PRICE_LIST: ['price', 'árlista', 'pricing', 'cost'],
            DocumentType.BROCHURE: ['brochure', 'prospektus', 'catalog', 'brosúra'],
            DocumentType.PERFORMANCE_DECLARATION: ['declaration', 'nyilatkozat', 'performance', 'teljesítmény'],
            DocumentType.INSTALLATION_GUIDE: ['installation', 'guide', 'szerelési', 'útmutató']
        }
        
        patterns = type_patterns.get(self.document_type, [])
        for pattern in patterns:
            if pattern in filename:
                return 0.8
        
        return 0.2  # Low confidence for unknown document types
    
    async def extract(self, task: ExtractionTask) -> ExtractionResult:
        """Extract using document-type-specific optimizations"""
        start_time = time.time()
        
        try:
            # Use appropriate extraction strategy based on document type
            if self.document_type == DocumentType.TECHNICAL_DATASHEET:
                result = await self._extract_technical_datasheet(task)
            elif self.document_type == DocumentType.PRICE_LIST:
                result = await self._extract_price_list(task)
            elif self.document_type == DocumentType.BROCHURE:
                result = await self._extract_brochure(task)
            else:
                # Use generic extraction
                strategy = PDFPlumberStrategy()
                result = await strategy.extract(task.pdf_path)
            
            execution_time = time.time() - start_time
            result.execution_time_seconds = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExtractionResult(
                strategy_type=StrategyType.DOCUMENT_TYPE_SPECIFIC,
                success=False,
                execution_time_seconds=execution_time,
                error_message=f"{self.document_type.value} expert failed: {str(e)}",
                confidence_score=0.0
            )
    
    async def _extract_technical_datasheet(self, task: ExtractionTask) -> ExtractionResult:
        """Extract technical datasheet with focus on specifications"""
        # Use table-focused extraction for technical data
        strategy = PDFPlumberStrategy()
        result = await strategy.extract(task.pdf_path)
        
        if result.success and result.extracted_data:
            # Enhance with technical specification parsing
            text = result.extracted_data.get('full_text', '')
            enhanced_specs = self._extract_advanced_technical_specs(text)
            result.extracted_data['enhanced_technical_specs'] = enhanced_specs
            
            # Boost confidence for technical documents
            if enhanced_specs:
                result.confidence_score = min(result.confidence_score + 0.1, 1.0)
        
        return result
    
    async def _extract_price_list(self, task: ExtractionTask) -> ExtractionResult:
        """Extract price list with focus on tabular data"""
        # Use table-focused extraction for pricing data
        strategy = PDFPlumberStrategy()
        result = await strategy.extract(task.pdf_path)
        
        if result.success and result.extracted_data:
            # Enhance with price extraction
            pricing_data = self._extract_pricing_information(result.extracted_data)
            result.extracted_data['pricing_data'] = pricing_data
            
            # Boost confidence for price lists
            if pricing_data:
                result.confidence_score = min(result.confidence_score + 0.15, 1.0)
        
        return result
    
    async def _extract_brochure(self, task: ExtractionTask) -> ExtractionResult:
        """Extract brochure with focus on product descriptions"""
        # Use text-focused extraction for brochures
        strategy = PyMuPDFStrategy()
        result = await strategy.extract(task.pdf_path)
        
        if result.success and result.extracted_data:
            # Enhance with marketing content extraction
            marketing_data = self._extract_marketing_content(result.extracted_data)
            result.extracted_data['marketing_content'] = marketing_data
            
            # Boost confidence for brochures
            if marketing_data:
                result.confidence_score = min(result.confidence_score + 0.1, 1.0)
        
        return result
    
    def _extract_advanced_technical_specs(self, text: str) -> Dict[str, Any]:
        """Extract advanced technical specifications"""
        specs = {}
        
        # Advanced regex patterns for Hungarian technical documents
        import re
        
        # Thermal conductivity (more comprehensive)
        thermal_patterns = [
            r'(?:hővezetési\s+tényező|λ[\s\w]*)[:\s]*(\d+[.,]\d+)\s*(?:w/mk|w/m·k|w/m\*k)',
            r'thermal\s+conductivity[:\s]*(\d+[.,]\d+)\s*(?:w/mk|w/m·k)',
            r'λ[\s]*=[\s]*(\d+[.,]\d+)\s*(?:w/mk|w/m·k)',
        ]
        
        for pattern in thermal_patterns:
            match = re.search(pattern, text.lower())
            if match:
                value = match.group(1).replace(',', '.')
                try:
                    specs['thermal_conductivity'] = {
                        'value': float(value),
                        'unit': 'W/mK',
                        'confidence': 0.9
                    }
                    break
                except ValueError:
                    pass
        
        # Fire resistance (comprehensive)
        fire_patterns = [
            r'(?:tűzvédelmi\s+osztály|fire\s+class|euroclass)[:\s]*([a-z0-9\-s]+)',
            r'(?:tűzállóság|fire\s+resistance)[:\s]*([a-z0-9\-s]+)',
            r'(?:éghetőség|combustibility)[:\s]*([a-z0-9\-s]+)',
        ]
        
        for pattern in fire_patterns:
            match = re.search(pattern, text.lower())
            if match:
                fire_class = match.group(1).upper()
                specs['fire_resistance'] = {
                    'class': fire_class,
                    'confidence': 0.85
                }
                break
        
        # Density (comprehensive)
        density_patterns = [
            r'(?:sűrűség|density)[:\s]*(\d+)\s*(?:kg/m³|kg/m3)',
            r'(?:térfogatsűrűség|bulk\s+density)[:\s]*(\d+)\s*(?:kg/m³|kg/m3)',
            r'ρ[\s]*=[\s]*(\d+)\s*(?:kg/m³|kg/m3)',
        ]
        
        for pattern in density_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    specs['density'] = {
                        'value': int(match.group(1)),
                        'unit': 'kg/m³',
                        'confidence': 0.9
                    }
                    break
                except ValueError:
                    pass
        
        return specs
    
    def _extract_pricing_information(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pricing information from tables"""
        pricing_data = {}
        
        # Look for pricing in tables
        for key, value in extracted_data.items():
            if 'table' in key.lower() and isinstance(value, list):
                for table in value:
                    if isinstance(table, list) and len(table) > 0:
                        pricing_data.update(self._parse_pricing_table(table))
        
        return pricing_data
    
    def _parse_pricing_table(self, table: List[List[str]]) -> Dict[str, Any]:
        """Parse pricing from a table structure"""
        prices = {}
        
        # Look for currency patterns
        import re
        currency_pattern = r'(\d+[.,]\d+)\s*(?:ft|huf|eur|€)'
        
        for row in table:
            if isinstance(row, list):
                for cell in row:
                    if isinstance(cell, str):
                        match = re.search(currency_pattern, cell.lower())
                        if match:
                            price_str = match.group(1).replace(',', '.')
                            try:
                                price = float(price_str)
                                prices[f'price_{len(prices)}'] = {
                                    'value': price,
                                    'currency': 'HUF',
                                    'confidence': 0.8
                                }
                            except ValueError:
                                pass
        
        return prices
    
    def _extract_marketing_content(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract marketing content from brochures"""
        marketing_data = {}
        
        text = extracted_data.get('full_text', '')
        if text:
            # Extract key marketing phrases
            marketing_phrases = self._find_marketing_phrases(text)
            if marketing_phrases:
                marketing_data['key_phrases'] = marketing_phrases
                marketing_data['content_type'] = 'marketing'
                marketing_data['confidence'] = 0.7
        
        return marketing_data
    
    def _find_marketing_phrases(self, text: str) -> List[str]:
        """Find marketing phrases in text"""
        marketing_keywords = [
            'kiváló', 'excellent', 'prémium', 'premium',
            'innováció', 'innovation', 'megoldás', 'solution',
            'környezetbarát', 'eco-friendly', 'fenntartható', 'sustainable'
        ]
        
        phrases = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in marketing_keywords):
                if len(sentence) > 20 and len(sentence) < 200:
                    phrases.append(sentence)
        
        return phrases[:5]  # Return top 5 marketing phrases


class MoEGatingNetwork:
    """Intelligent routing system for the MoE architecture"""
    
    def __init__(self, experts: List[BaseExpert]):
        self.experts = experts
        self.routing_history = []
        self.performance_weights = {}
        
        # Initialize expert weights
        for expert in experts:
            self.performance_weights[expert.name] = 1.0
    
    async def route_task(self, task: ExtractionTask) -> RoutingDecision:
        """Route task to appropriate expert(s)"""
        # Get capabilities from all experts
        expert_scores = {}
        
        for expert in self.experts:
            score = await expert.can_handle(task)
            expert_scores[expert.name] = score * self.performance_weights[expert.name]
        
        # Select top experts
        sorted_experts = sorted(expert_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Routing logic
        if sorted_experts[0][1] > 0.8:
            # High confidence - use single expert
            selected_experts = [sorted_experts[0][0]]
            rationale = f"High confidence routing to {sorted_experts[0][0]}"
        elif sorted_experts[0][1] > 0.6:
            # Medium confidence - use top 2 experts
            selected_experts = [sorted_experts[0][0], sorted_experts[1][0]]
            rationale = f"Medium confidence routing to {sorted_experts[0][0]} and {sorted_experts[1][0]}"
        else:
            # Low confidence - use ensemble of top 3 experts
            selected_experts = [expert[0] for expert in sorted_experts[:3]]
            rationale = f"Low confidence ensemble routing to top 3 experts"
        
        # Calculate estimated cost and time
        estimated_cost = self._calculate_cost(selected_experts)
        estimated_time = self._calculate_time(selected_experts)
        
        # Create routing decision
        decision = RoutingDecision(
            selected_experts=selected_experts,
            confidence_scores={expert: score for expert, score in sorted_experts},
            routing_rationale=rationale,
            estimated_cost=estimated_cost,
            estimated_processing_time=estimated_time,
            fallback_strategy=sorted_experts[-1][0] if len(sorted_experts) > 1 else None
        )
        
        # Record routing decision
        self.routing_history.append({
            'timestamp': time.time(),
            'task': task,
            'decision': decision
        })
        
        return decision
    
    def _calculate_cost(self, selected_experts: List[str]) -> float:
        """Calculate estimated cost for selected experts"""
        total_cost = 0.0
        
        for expert_name in selected_experts:
            expert = self._find_expert(expert_name)
            if expert:
                total_cost += expert.capabilities.cost_factor
        
        return total_cost
    
    def _calculate_time(self, selected_experts: List[str]) -> float:
        """Calculate estimated processing time"""
        if len(selected_experts) == 1:
            expert = self._find_expert(selected_experts[0])
            return expert.capabilities.processing_time_estimate if expert else 30.0
        else:
            # Parallel processing - max time of selected experts
            max_time = 0.0
            for expert_name in selected_experts:
                expert = self._find_expert(expert_name)
                if expert:
                    max_time = max(max_time, expert.capabilities.processing_time_estimate)
            return max_time
    
    def _find_expert(self, expert_name: str) -> Optional[BaseExpert]:
        """Find expert by name"""
        for expert in self.experts:
            if expert.name == expert_name:
                return expert
        return None
    
    async def update_performance_weights(self, expert_name: str, performance_score: float):
        """Update performance weights based on results"""
        if expert_name in self.performance_weights:
            # Exponential moving average
            current_weight = self.performance_weights[expert_name]
            new_weight = 0.8 * current_weight + 0.2 * performance_score
            self.performance_weights[expert_name] = max(0.1, min(2.0, new_weight))


class MoEOrchestrator:
    """Main orchestrator for the MoE system"""
    
    def __init__(self):
        self.experts = []
        self.gating_network = None
        self.initialize_experts()
    
    def initialize_experts(self):
        """Initialize all experts in the system"""
        # Manufacturer-specific experts
        self.experts.extend([
            ManufacturerSpecificExpert("ROCKWOOL", {
                'frontrock': 0.9,
                'monrock': 0.9,
                'rockwool': 0.8,
                'műszaki': 0.7
            }),
            ManufacturerSpecificExpert("LEIER", {
                'leier': 0.9,
                'durisol': 0.8,
                'thermoplan': 0.8,
                'teljesítménynyilatkozat': 0.7
            }),
            ManufacturerSpecificExpert("BAUMIT", {
                'baumit': 0.9,
                'life': 0.8,
                'star': 0.8,
                'színrendszer': 0.7
            })
        ])
        
        # Document-type specific experts
        self.experts.extend([
            DocumentTypeExpert(DocumentType.TECHNICAL_DATASHEET, {}),
            DocumentTypeExpert(DocumentType.PRICE_LIST, {}),
            DocumentTypeExpert(DocumentType.BROCHURE, {}),
            DocumentTypeExpert(DocumentType.PERFORMANCE_DECLARATION, {})
        ])
        
        # Initialize gating network
        self.gating_network = MoEGatingNetwork(self.experts)
    
    async def process_pdf(self, task: ExtractionTask) -> ExtractionResult:
        """Process PDF using MoE architecture"""
        start_time = time.time()
        
        try:
            # Route task to appropriate expert(s)
            routing_decision = await self.gating_network.route_task(task)
            
            logger.info(f"MoE Routing: {routing_decision.routing_rationale}")
            
            # Execute selected experts
            if len(routing_decision.selected_experts) == 1:
                # Single expert execution
                expert_name = routing_decision.selected_experts[0]
                expert = self._find_expert(expert_name)
                if expert:
                    result = await expert.extract(task)
                    
                    # Update performance weights
                    performance_score = await expert.evaluate_performance(result)
                    await self.gating_network.update_performance_weights(expert_name, performance_score)
                    
                    return result
            else:
                # Multiple expert execution with consensus
                return await self._execute_consensus(routing_decision.selected_experts, task)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"MoE processing failed: {str(e)}")
            
            return ExtractionResult(
                strategy_type=StrategyType.MOE,
                success=False,
                execution_time_seconds=execution_time,
                error_message=f"MoE processing failed: {str(e)}",
                confidence_score=0.0
            )
    
    async def _execute_consensus(self, expert_names: List[str], task: ExtractionTask) -> ExtractionResult:
        """Execute multiple experts and build consensus"""
        results = []
        
        # Execute all experts in parallel
        tasks = []
        for expert_name in expert_names:
            expert = self._find_expert(expert_name)
            if expert:
                tasks.append(expert.extract(task))
        
        if tasks:
            expert_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            for result in expert_results:
                if isinstance(result, ExtractionResult) and result.success:
                    results.append(result)
        
        if not results:
            return ExtractionResult(
                strategy_type=StrategyType.MOE,
                success=False,
                error_message="No experts succeeded",
                confidence_score=0.0
            )
        
        # Build consensus result
        consensus_result = self._build_consensus(results)
        
        # Update expert performance weights
        for i, expert_name in enumerate(expert_names):
            if i < len(results):
                expert = self._find_expert(expert_name)
                if expert:
                    performance_score = await expert.evaluate_performance(results[i])
                    await self.gating_network.update_performance_weights(expert_name, performance_score)
        
        return consensus_result
    
    def _build_consensus(self, results: List[ExtractionResult]) -> ExtractionResult:
        """Build consensus from multiple expert results"""
        if not results:
            return ExtractionResult(
                strategy_type=StrategyType.MOE,
                success=False,
                error_message="No results to build consensus from",
                confidence_score=0.0
            )
        
        if len(results) == 1:
            return results[0]
        
        # Weighted consensus based on confidence scores
        consensus_data = {}
        total_weight = sum(result.confidence_score for result in results)
        
        if total_weight == 0:
            return results[0]  # Return first result if all have zero confidence
        
        # Merge extracted data with weighted consensus
        all_keys = set()
        for result in results:
            if result.extracted_data:
                all_keys.update(result.extracted_data.keys())
        
        for key in all_keys:
            values = []
            weights = []
            
            for result in results:
                if result.extracted_data and key in result.extracted_data:
                    values.append(result.extracted_data[key])
                    weights.append(result.confidence_score)
            
            if values:
                # Use value from highest confidence result
                max_weight_idx = weights.index(max(weights))
                consensus_data[key] = values[max_weight_idx]
        
        # Calculate consensus metrics
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        max_confidence = max(r.confidence_score for r in results)
        avg_time = sum(r.execution_time_seconds for r in results) / len(results)
        
        return ExtractionResult(
            strategy_type=StrategyType.MOE,
            success=True,
            execution_time_seconds=avg_time,
            extracted_data=consensus_data,
            confidence_score=max_confidence,  # Use max confidence
            method_used="moe_consensus",
            pages_processed=max(r.pages_processed for r in results if r.pages_processed),
            tables_found=max(r.tables_found for r in results if r.tables_found),
            text_length=max(r.text_length for r in results if r.text_length),
            data_completeness=max(r.data_completeness for r in results if r.data_completeness),
            structure_quality=max(r.structure_quality for r in results if r.structure_quality)
        )
    
    def _find_expert(self, expert_name: str) -> Optional[BaseExpert]:
        """Find expert by name"""
        for expert in self.experts:
            if expert.name == expert_name:
                return expert
        return None
    
    def get_expert_statistics(self) -> Dict[str, Any]:
        """Get statistics about expert performance"""
        stats = {}
        
        for expert in self.experts:
            stats[expert.name] = {
                'specialization_score': expert.specialization_score,
                'performance_weight': self.gating_network.performance_weights.get(expert.name, 1.0),
                'total_tasks': len(expert.performance_history),
                'average_score': np.mean([p['score'] for p in expert.performance_history]) if expert.performance_history else 0.0,
                'average_time': np.mean([p['processing_time'] for p in expert.performance_history]) if expert.performance_history else 0.0
            }
        
        return stats


# Specialized extraction strategies for manufacturers
class RockwoolSpecializedStrategy(PDFPlumberStrategy):
    """ROCKWOOL-optimized extraction strategy"""
    
    async def extract(self, pdf_path: str) -> ExtractionResult:
        # Use base PDFPlumber extraction
        result = await super().extract(pdf_path)
        
        if result.success and result.extracted_data:
            # Apply ROCKWOOL-specific optimizations
            result.extracted_data['manufacturer'] = 'ROCKWOOL'
            result.extracted_data['optimization_applied'] = 'rockwool_specialized'
            
            # ROCKWOOL-specific confidence boost
            result.confidence_score = min(result.confidence_score + 0.1, 1.0)
        
        return result


class LeierSpecializedStrategy(PDFPlumberStrategy):
    """LEIER-optimized extraction strategy"""
    
    async def extract(self, pdf_path: str) -> ExtractionResult:
        # Use base PDFPlumber extraction
        result = await super().extract(pdf_path)
        
        if result.success and result.extracted_data:
            # Apply LEIER-specific optimizations
            result.extracted_data['manufacturer'] = 'LEIER'
            result.extracted_data['optimization_applied'] = 'leier_specialized'
            
            # LEIER-specific confidence boost
            result.confidence_score = min(result.confidence_score + 0.1, 1.0)
        
        return result


class BaumitSpecializedStrategy(PDFPlumberStrategy):
    """BAUMIT-optimized extraction strategy"""
    
    async def extract(self, pdf_path: str) -> ExtractionResult:
        # Use base PDFPlumber extraction
        result = await super().extract(pdf_path)
        
        if result.success and result.extracted_data:
            # Apply BAUMIT-specific optimizations
            result.extracted_data['manufacturer'] = 'BAUMIT'
            result.extracted_data['optimization_applied'] = 'baumit_specialized'
            
            # BAUMIT-specific confidence boost
            result.confidence_score = min(result.confidence_score + 0.1, 1.0)
        
        return result


# Update StrategyType enum to include MoE
try:
    StrategyType.MOE = "moe"
    StrategyType.MANUFACTURER_SPECIFIC = "manufacturer_specific"
    StrategyType.DOCUMENT_TYPE_SPECIFIC = "document_type_specific"
except AttributeError:
    # Enum already has these values
    pass