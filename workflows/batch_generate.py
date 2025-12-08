#!/usr/bin/env python3
"""
Batch Generate Workflow
Generates multiple eindafrekeningen from a single Master Input Sheet.
"""

import sys
import os
import argparse
from typing import List, Dict, Any

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'Eindafrekening', 'src'))

from Eindafrekening.src.master_reader import MasterReader
from Eindafrekening.src.generate import generate_report
from Shared.database import Database

def batch_generate(input_file: str):
    print(f"🚀 Starting Batch Generation from {input_file}")
    print("=" * 60)
    
    # 1. Read Data
    reader = MasterReader(input_file)
    bookings = reader.read_all()
    
    if not bookings:
        print("⚠️  No bookings found in input file.")
        return

    print(f"📊 Found {len(bookings)} bookings to process.")
    
    # 2. Process each booking
    success_count = 0
    fail_count = 0
    
    for i, booking_data in enumerate(bookings, 1):
        client_name = booking_data['client'].name
        address = booking_data['object'].address
        
        print(f"\nProcessing {i}/{len(bookings)}: {client_name} @ {address}")
        print("-" * 40)
        
        try:
            # Call existing generation logic
            # output_dir defaults to Eindafrekening/output in generate_report if not specified
            # We pass the pre-structured 'data' dictionary
            
            result = generate_report(data=booking_data, skip_db_save=False)
            
            if result:
                print(f"   ✅ Success: {result['onepager']['pdf'] if result.get('onepager') and result['onepager'].get('is_pdf') else 'HTML generated'}")
                success_count += 1
            else:
                print(f"   ❌ Failed: Generator returned None")
                fail_count += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1

    # 3. Summary
    print("\n" + "=" * 60)
    print(f"🏁 Batch Complete")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed:     {fail_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Generate Eindafrekeningen")
    parser.add_argument("input_file", help="Path to Master Input Excel file")
    
    args = parser.parse_args()
    
    if os.path.exists(args.input_file):
        batch_generate(args.input_file)
    else:
        print(f"❌ Input file not found: {args.input_file}")
