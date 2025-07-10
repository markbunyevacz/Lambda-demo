#!/usr/bin/env python3

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

# Explicitly load the .env file from the correct location to ensure
# the ANTHROPIC_API_KEY is found, regardless of the execution directory.
env_path = Path(__file__).resolve().parent.parent / "src/backend/.env"
load_dotenv(dotenv_path=env_path)

from src.backend.app.services.ai_service import AnalysisService


async def test_simple_ai():
    """Test simplified AI analysis"""
    
    try:
        analyzer = AnalysisService()
        
        # Simple test data
        text_content = (
            "Műszaki adatlap: ROCKWOOL Airrock HD. "
            "Kiváló hővezetési tényező λ 0.035 W/mK. "
            "Tűzvédelmi osztály: A1."
        )
        tables_data = []
        filename = "test.pdf"

        # Run analysis
        result = await analyzer.analyze_pdf_content(
            text_content, tables_data, filename
        )
        
        # Print and verify result
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        tech_specs = result.get("technical_specifications", {})
        assert "thermal_conductivity" in tech_specs
        assert tech_specs["thermal_conductivity"].get("value") == "0.035"
        assert "fire_classification" in tech_specs
        assert tech_specs["fire_classification"].get("value") == "A1"
            
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_simple_ai()) 