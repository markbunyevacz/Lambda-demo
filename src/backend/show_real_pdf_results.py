#!/usr/bin/env python3
"""
Show Real PDF Processing Results
Extract and display actual AI results from ROCKWOOL PDFs
"""

import sys
import json
import csv
from pathlib import Path

# Add path for imports
sys.path.append('/app')

try:
    from real_pdf_processor import RealPDFProcessor
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def show_pdf_results():
    """Process PDFs and show detailed results"""
    
    print("🔍 REAL PDF PROCESSING RESULTS EXTRACTION")
    print("=" * 70)
    print("📄 Processing all ROCKWOOL PDFs with Claude AI...")
    print()
    
    try:
        # Initialize processor
        processor = RealPDFProcessor()
        
        # Set PDF directory
        pdf_directory = Path("/app/src/downloads/rockwool_datasheets")
        
        # Get PDF files
        pdf_files = list(pdf_directory.glob("*.pdf"))
        product_pdfs = [f for f in pdf_files if "duplicates" not in str(f)]
        
        print(f"📁 Found {len(product_pdfs)} PDF files")
        print("=" * 70)
        
        # Process first 5 PDFs to show detailed results
        csv_data = []
        
        for i, pdf_path in enumerate(product_pdfs[:5], 1):
            try:
                print(f"\n📦 PROCESSING PDF #{i}: {pdf_path.name}")
                print("-" * 60)
                
                # Process PDF
                result = processor.process_pdf(pdf_path)
                
                print(f"✅ Product Name: {result.product_name}")
                print(f"📄 Source File: {result.source_filename}")
                print(f"🔧 Extraction Method: {result.extraction_method}")
                print(f"🎯 Confidence Score: {result.confidence_score}")
                print(f"⏱️ Processing Time: {result.processing_time:.2f}s")
                
                # Show technical specs
                print(f"\n🔧 TECHNICAL SPECIFICATIONS:")
                if result.technical_specs:
                    for category, specs in result.technical_specs.items():
                        print(f"   📋 {category.upper()}:")
                        if isinstance(specs, dict):
                            for key, value in specs.items():
                                print(f"     • {key}: {value}")
                        else:
                            print(f"     • {specs}")
                else:
                    print("   ⚠️ No technical specifications extracted")
                
                # Show pricing info
                print(f"\n💰 PRICING INFORMATION:")
                if result.pricing_info:
                    for key, value in result.pricing_info.items():
                        print(f"   • {key}: {value}")
                else:
                    print("   ⚠️ No pricing information found")
                
                # Show tables
                print(f"\n📊 EXTRACTED TABLES ({len(result.tables_data)} found):")
                for j, table in enumerate(result.tables_data, 1):
                    print(f"   📋 Table {j} (Page {table.get('page', 'unknown')}):")
                    headers = table.get('headers', [])
                    print(f"     Headers: {headers}")
                    
                    table_rows = table.get('data', [])
                    print(f"     Data Rows: {len(table_rows)}")
                    
                    # Show first few rows
                    for row_idx, row in enumerate(table_rows[:3], 1):
                        print(f"       Row {row_idx}: {row}")
                        
                        # Add to CSV
                        csv_row = {
                            'Product': result.product_name,
                            'Source_File': result.source_filename,
                            'Confidence': result.confidence_score,
                            'Table_Number': j,
                            'Page': table.get('page', 'unknown'),
                            'Headers': '; '.join(headers) if headers else 'No headers',
                            'Row_Data': '; '.join([str(cell) for cell in row]) if row else 'Empty row'
                        }
                        csv_data.append(csv_row)
                
                # Show extracted text sample
                print(f"\n📄 EXTRACTED TEXT SAMPLE (first 800 chars):")
                text_sample = result.extracted_text[:800] if result.extracted_text else "No text extracted"
                print(text_sample)
                if len(result.extracted_text) > 800:
                    print("...[TRUNCATED]...")
                
                print("\n" + "=" * 70)
                
            except Exception as e:
                print(f"❌ Error processing {pdf_path.name}: {e}")
                continue
        
        # Save CSV
        if csv_data:
            csv_filename = '/app/real_pdf_tables_sample.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Product', 'Source_File', 'Confidence', 'Table_Number', 'Page', 'Headers', 'Row_Data']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"\n💾 CSV SAVED: {csv_filename}")
            print(f"📊 Total table rows exported: {len(csv_data)}")
        
        print(f"\n🎉 SAMPLE PROCESSING COMPLETE!")
        print("✅ Real AI-powered PDF extraction with Claude 3.5 Haiku")
        print("✅ Actual table data and technical specifications")
        print("✅ No simulations - 100% real processing")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")

if __name__ == "__main__":
    show_pdf_results() 