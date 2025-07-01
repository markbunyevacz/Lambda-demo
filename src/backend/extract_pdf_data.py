#!/usr/bin/env python3
"""
Extract Real PDF Processing Results to CSV
Shows extracted tables and text content from Claude AI analysis
"""

import json
import csv
import pandas as pd
from pathlib import Path

def extract_pdf_results():
    """Extract and display PDF processing results"""
    
    # Load the production report
    try:
        with open('/app/production_pdf_report.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🔍 REAL PDF PROCESSING RESULTS")
        print("=" * 60)
        print(f"Processing Type: {data.get('processing_type', 'unknown')}")
        print(f"Total PDFs: {data.get('stats', {}).get('pdfs_processed', 0)}")
        print(f"Timestamp: {data.get('timestamp', 'unknown')}")
        print()
        
        # Check if there are results
        if 'results' in data and data['results']:
            print(f"📄 Found results for {len(data['results'])} PDFs")
            print("=" * 60)
            
            # Create CSV data
            csv_data = []
            
            for i, result in enumerate(data['results'], 1):
                print(f"\n📦 PRODUCT #{i}")
                print("-" * 40)
                print(f"Product Name: {result.get('product_name', 'Unknown')}")
                print(f"Source File: {result.get('source_filename', 'Unknown')}")
                print(f"Extraction Method: {result.get('extraction_method', 'Unknown')}")
                print(f"Confidence Score: {result.get('confidence_score', 0.0)}")
                print(f"Processing Time: {result.get('processing_time', 0.0):.2f}s")
                
                # Extract technical specs
                tech_specs = result.get('technical_specs', {})
                print(f"\n🔧 Technical Specifications:")
                for spec_category, spec_data in tech_specs.items():
                    if isinstance(spec_data, dict):
                        print(f"   {spec_category}:")
                        for key, value in spec_data.items():
                            print(f"     {key}: {value}")
                
                # Extract tables data
                tables_data = result.get('tables_data', [])
                print(f"\n📊 Tables Found: {len(tables_data)}")
                
                for j, table in enumerate(tables_data, 1):
                    print(f"   Table {j} (Page {table.get('page', 'unknown')}):")
                    headers = table.get('headers', [])
                    print(f"     Headers: {headers}")
                    
                    table_rows = table.get('data', [])
                    print(f"     Rows: {len(table_rows)}")
                    
                    # Add to CSV data
                    for row_idx, row in enumerate(table_rows[:3]):  # First 3 rows
                        csv_row = {
                            'Product': result.get('product_name', 'Unknown'),
                            'Source_File': result.get('source_filename', 'Unknown'),
                            'Table_Number': j,
                            'Page': table.get('page', 'unknown'),
                            'Row_Number': row_idx + 1,
                            'Headers': str(headers),
                            'Row_Data': str(row),
                            'Confidence': result.get('confidence_score', 0.0)
                        }
                        csv_data.append(csv_row)
                
                # Show extracted text sample
                extracted_text = result.get('extracted_text', '')
                if extracted_text:
                    print(f"\n📄 Extracted Text (first 500 chars):")
                    print(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                
                print("\n" + "=" * 60)
            
            # Save to CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                csv_filename = '/app/pdf_tables_extracted.csv'
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"\n💾 CSV saved: {csv_filename}")
                print(f"📊 Total table rows exported: {len(csv_data)}")
            
        else:
            print("⚠️ No results found in the report")
    
    except FileNotFoundError:
        print("❌ production_pdf_report.json not found")
    except Exception as e:
        print(f"❌ Error processing results: {e}")

if __name__ == "__main__":
    extract_pdf_results() 