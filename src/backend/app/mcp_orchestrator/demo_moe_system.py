"""
Demo: Mixture of Experts (MoE) Architecture for PDF Extraction
=============================================================

This demo shows how the MoE system intelligently routes PDF extraction tasks
to the most appropriate experts based on document characteristics.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import time
import logging

from moe_architecture import MoEOrchestrator, DocumentType
from models import ExtractionTask, TaskStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MoEDemo:
    """Demonstration of the MoE PDF extraction system"""
    
    def __init__(self):
        self.orchestrator = MoEOrchestrator()
        self.demo_results = []
        
    async def run_comprehensive_demo(self):
        """Run a comprehensive demo of the MoE system"""
        
        print("\n" + "="*80)
        print("🧠 MIXTURE OF EXPERTS (MoE) PDF EXTRACTION DEMO")
        print("="*80)
        
        # Demo scenarios
        demo_scenarios = [
            # ROCKWOOL scenarios
            {
                "name": "ROCKWOOL Technical Datasheet",
                "pdf_path": "src/downloads/rockwool_datasheets/frontrock_max_e_datasheet.pdf",
                "manufacturer": "ROCKWOOL",
                "document_type": "technical_datasheet",
                "expected_expert": "ROCKWOOL_expert"
            },
            {
                "name": "ROCKWOOL Price List",
                "pdf_path": "src/downloads/rockwool_brochures/rockwool_arlista_2025.pdf",
                "manufacturer": "ROCKWOOL",
                "document_type": "price_list",
                "expected_expert": "price_list_expert"
            },
            
            # LEIER scenarios
            {
                "name": "LEIER Performance Declaration",
                "pdf_path": "src/downloads/leier_products/teljesitmenynylatkozat_le_js13225.pdf",
                "manufacturer": "LEIER",
                "document_type": "performance_declaration",
                "expected_expert": "LEIER_expert"
            },
            {
                "name": "LEIER Technical Specification",
                "pdf_path": "src/downloads/leier_products/durisol_technical_specs.pdf",
                "manufacturer": "LEIER",
                "document_type": "technical_datasheet",
                "expected_expert": "LEIER_expert"
            },
            
            # BAUMIT scenarios
            {
                "name": "BAUMIT Color System",
                "pdf_path": "src/downloads/baumit_products/baumit_life_color_chart.pdf",
                "manufacturer": "BAUMIT",
                "document_type": "brochure",
                "expected_expert": "BAUMIT_expert"
            },
            {
                "name": "BAUMIT Product Catalog",
                "pdf_path": "src/downloads/baumit_products/baumit_product_catalog.pdf",
                "manufacturer": "BAUMIT",
                "document_type": "catalog",
                "expected_expert": "BAUMIT_expert"
            },
            
            # Unknown/Mixed scenarios
            {
                "name": "Unknown Manufacturer Document",
                "pdf_path": "src/downloads/unknown/generic_building_material.pdf",
                "manufacturer": None,
                "document_type": None,
                "expected_expert": "technical_datasheet_expert"
            }
        ]
        
        # Run demo scenarios
        for scenario in demo_scenarios:
            await self._run_scenario(scenario)
        
        # Show final statistics
        await self._show_final_statistics()
        
        # Show routing analytics
        await self._show_routing_analytics()
        
        print("\n" + "="*80)
        print("✅ MoE DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
    
    async def _run_scenario(self, scenario: Dict[str, Any]):
        """Run a single demo scenario"""
        
        print(f"\n🔍 SCENARIO: {scenario['name']}")
        print("-" * 60)
        
        # Create extraction task
        task = ExtractionTask(
            pdf_path=scenario['pdf_path'],
            manufacturer=scenario.get('manufacturer'),
            document_type=scenario.get('document_type')
        )
        
        print(f"📄 PDF: {Path(scenario['pdf_path']).name}")
        print(f"🏭 Manufacturer: {scenario.get('manufacturer', 'Unknown')}")
        print(f"📑 Document Type: {scenario.get('document_type', 'Unknown')}")
        
        # Check if file exists (for demo purposes)
        if not Path(scenario['pdf_path']).exists():
            print(f"⚠️  File not found: {scenario['pdf_path']}")
            print("🔄 Using simulated processing...")
            result = await self._simulate_processing(scenario)
        else:
            print("✅ File found, processing...")
            result = await self.orchestrator.process_pdf(task)
        
        # Show results
        await self._show_scenario_results(scenario, result)
        
        # Store results for analytics
        self.demo_results.append({
            'scenario': scenario,
            'result': result,
            'timestamp': time.time()
        })
        
        print("✅ Scenario completed")
    
    async def _simulate_processing(self, scenario: Dict[str, Any]) -> Any:
        """Simulate PDF processing for demo purposes"""
        
        from models import ExtractionResult, StrategyType
        
        # Simulate routing decision
        print("\n🧠 MoE ROUTING DECISION:")
        
        # Determine best expert based on scenario
        if scenario.get('manufacturer'):
            selected_expert = f"{scenario['manufacturer']}_expert"
            confidence = 0.95
            rationale = f"High confidence manufacturer match: {scenario['manufacturer']}"
        elif scenario.get('document_type'):
            selected_expert = f"{scenario['document_type']}_expert"
            confidence = 0.8
            rationale = f"Document type match: {scenario['document_type']}"
        else:
            selected_expert = "technical_datasheet_expert"
            confidence = 0.6
            rationale = "Default routing to technical datasheet expert"
        
        print(f"   Selected Expert: {selected_expert}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Rationale: {rationale}")
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Create simulated result
        extracted_data = {
            'product_name': f"Simulated {scenario['name']} Product",
            'manufacturer': scenario.get('manufacturer', 'Unknown'),
            'document_type': scenario.get('document_type', 'Unknown'),
            'technical_specs': {
                'thermal_conductivity': {'value': 0.035, 'unit': 'W/mK', 'confidence': 0.9},
                'fire_resistance': {'class': 'A1', 'confidence': 0.85}
            },
            'full_text': f"Simulated extracted text for {scenario['name']}...",
            'page_count': 3,
            'expert_used': selected_expert,
            'optimization_applied': f"{scenario.get('manufacturer', 'generic')}_specialized"
        }
        
        return ExtractionResult(
            strategy_type=StrategyType.MOE,
            success=True,
            execution_time_seconds=0.5,
            extracted_data=extracted_data,
            confidence_score=confidence,
            method_used="moe_simulated",
            pages_processed=3,
            tables_found=2,
            text_length=1500,
            data_completeness=0.85,
            structure_quality=0.8
        )
    
    async def _show_scenario_results(self, scenario: Dict[str, Any], result: Any):
        """Show results of a scenario"""
        
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Processing Time: {result.execution_time_seconds:.2f}s")
        print(f"   Method Used: {result.method_used}")
        
        if result.success and result.extracted_data:
            print(f"   Data Completeness: {result.data_completeness:.2f}")
            print(f"   Structure Quality: {result.structure_quality:.2f}")
            
            # Show key extracted data
            data = result.extracted_data
            if 'product_name' in data:
                print(f"   Product Name: {data['product_name']}")
            if 'expert_used' in data:
                print(f"   Expert Used: {data['expert_used']}")
            if 'optimization_applied' in data:
                print(f"   Optimization: {data['optimization_applied']}")
            
            # Show technical specs if available
            if 'technical_specs' in data:
                specs = data['technical_specs']
                print(f"   Technical Specifications:")
                for spec_name, spec_data in specs.items():
                    if isinstance(spec_data, dict) and 'value' in spec_data:
                        print(f"     - {spec_name}: {spec_data['value']} {spec_data.get('unit', '')}")
        
        if not result.success:
            print(f"   Error: {result.error_message}")
    
    async def _show_final_statistics(self):
        """Show final statistics of the demo"""
        
        print(f"\n📈 FINAL STATISTICS:")
        print("-" * 60)
        
        if not self.demo_results:
            print("No results to analyze")
            return
        
        # Calculate statistics
        total_scenarios = len(self.demo_results)
        successful_scenarios = sum(1 for r in self.demo_results if r['result'].success)
        total_time = sum(r['result'].execution_time_seconds for r in self.demo_results)
        avg_confidence = sum(r['result'].confidence_score for r in self.demo_results) / total_scenarios
        
        print(f"   Total Scenarios: {total_scenarios}")
        print(f"   Successful: {successful_scenarios} ({successful_scenarios/total_scenarios*100:.1f}%)")
        print(f"   Total Processing Time: {total_time:.2f}s")
        print(f"   Average Confidence: {avg_confidence:.2f}")
        
        # Show confidence distribution
        confidence_ranges = {
            'Very High (>0.9)': 0,
            'High (0.8-0.9)': 0,
            'Medium (0.6-0.8)': 0,
            'Low (<0.6)': 0
        }
        
        for result in self.demo_results:
            conf = result['result'].confidence_score
            if conf > 0.9:
                confidence_ranges['Very High (>0.9)'] += 1
            elif conf > 0.8:
                confidence_ranges['High (0.8-0.9)'] += 1
            elif conf > 0.6:
                confidence_ranges['Medium (0.6-0.8)'] += 1
            else:
                confidence_ranges['Low (<0.6)'] += 1
        
        print(f"\n   Confidence Distribution:")
        for range_name, count in confidence_ranges.items():
            percentage = count / total_scenarios * 100
            print(f"     {range_name}: {count} ({percentage:.1f}%)")
    
    async def _show_routing_analytics(self):
        """Show routing analytics from the MoE system"""
        
        print(f"\n🧭 ROUTING ANALYTICS:")
        print("-" * 60)
        
        # Get expert statistics
        expert_stats = self.orchestrator.get_expert_statistics()
        
        print(f"   Expert Performance:")
        for expert_name, stats in expert_stats.items():
            print(f"     {expert_name}:")
            print(f"       Specialization Score: {stats['specialization_score']:.2f}")
            print(f"       Performance Weight: {stats['performance_weight']:.2f}")
            print(f"       Total Tasks: {stats['total_tasks']}")
            if stats['total_tasks'] > 0:
                print(f"       Average Score: {stats['average_score']:.2f}")
                print(f"       Average Time: {stats['average_time']:.2f}s")
    
    async def run_manufacturer_comparison(self):
        """Run a comparison between different manufacturers"""
        
        print(f"\n🔬 MANUFACTURER COMPARISON:")
        print("-" * 60)
        
        manufacturers = ['ROCKWOOL', 'LEIER', 'BAUMIT']
        
        for manufacturer in manufacturers:
            print(f"\n🏭 {manufacturer} Analysis:")
            
            # Test document recognition
            test_files = [
                f"test_{manufacturer.lower()}_datasheet.pdf",
                f"test_{manufacturer.lower()}_pricelist.pdf",
                f"test_{manufacturer.lower()}_brochure.pdf"
            ]
            
            for test_file in test_files:
                task = ExtractionTask(
                    pdf_path=test_file,
                    manufacturer=manufacturer
                )
                
                # Get routing decision (simulated)
                routing_score = await self._simulate_routing_decision(manufacturer, test_file)
                
                print(f"   {test_file}: {routing_score:.2f} confidence")
    
    async def _simulate_routing_decision(self, manufacturer: str, filename: str) -> float:
        """Simulate routing decision for a file"""
        
        # Simulate expert scoring
        if manufacturer.lower() in filename.lower():
            return 0.95
        elif any(doc_type in filename.lower() for doc_type in ['datasheet', 'pricelist', 'brochure']):
            return 0.8
        else:
            return 0.5


async def main():
    """Main demo function"""
    
    print("🚀 Starting MoE PDF Extraction Demo...")
    
    demo = MoEDemo()
    
    # Run comprehensive demo
    await demo.run_comprehensive_demo()
    
    # Run manufacturer comparison
    await demo.run_manufacturer_comparison()
    
    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())