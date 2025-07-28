#!/usr/bin/env python3
"""
Test script for the Earnings Presentations and Corporate Materials Fetcher

This script demonstrates the functionality of the earnings fetcher with a sample stock symbol.
"""

import sys
import os
from enhanced_earnings_fetcher import EnhancedEarningsFetcher

def test_earnings_fetcher():
    """Test the earnings fetcher with a sample stock symbol"""
    
    # Test with a well-known stock symbol
    test_symbol = "AAPL"  # Apple Inc.
    
    print(f"Testing Earnings Fetcher with symbol: {test_symbol}")
    print("=" * 60)
    
    try:
        # Create fetcher instance
        fetcher = EnhancedEarningsFetcher(rate_limit=1.0)
        
        # Get company information first
        print(f"\n1. Fetching company information for {test_symbol}...")
        company_info = fetcher.get_company_info(test_symbol)
        
        if company_info:
            print(f"   Company Name: {company_info.get('name', 'N/A')}")
            print(f"   Sector: {company_info.get('sector', 'N/A')}")
            print(f"   Industry: {company_info.get('industry', 'N/A')}")
            print(f"   Website: {company_info.get('website', 'N/A')}")
            print(f"   Country: {company_info.get('country', 'N/A')}")
        else:
            print("   Could not fetch company information")
            return
        
        # Fetch earnings materials
        print(f"\n2. Fetching earnings materials for {test_symbol}...")
        print("   This may take a few minutes as we search multiple sources...")
        
        results = fetcher.fetch_earnings_materials_parallel(test_symbol)
        
        print(f"\n3. Results Summary:")
        print(f"   Total materials found: {len(results)}")
        
        if results:
            # Group by source
            by_source = {}
            for result in results:
                if result.source not in by_source:
                    by_source[result.source] = []
                by_source[result.source].append(result)
            
            print(f"   Sources found: {len(by_source)}")
            for source, source_results in by_source.items():
                print(f"   - {source}: {len(source_results)} materials")
            
            # Show first few results
            print(f"\n4. Sample Results:")
            print("-" * 40)
            
            for i, result in enumerate(results[:3], 1):
                print(f"{i}. Title: {result.title}")
                print(f"   Date: {result.date}")
                print(f"   Speaker: {result.speaker}")
                print(f"   Format: {result.format}")
                print(f"   Source: {result.source}")
                print(f"   URL: {result.url}")
                if result.description:
                    print(f"   Description: {result.description}")
                print()
            
            # Export results
            print("5. Exporting results...")
            
            # Export to text
            output = fetcher.format_output(results, test_symbol)
            with open(f"{test_symbol}_test_results.txt", "w", encoding='utf-8') as f:
                f.write(output)
            print(f"   Text file: {test_symbol}_test_results.txt")
            
            # Export to CSV
            csv_file = fetcher.export_to_csv(results, test_symbol)
            print(f"   CSV file: {csv_file}")
            
            # Export to JSON
            json_file = fetcher.export_to_json(results, test_symbol)
            print(f"   JSON file: {json_file}")
            
        else:
            print("   No earnings materials found for the recent period.")
            print("   This could be because:")
            print("   - The company hasn't released recent earnings materials")
            print("   - The materials are not publicly available")
            print("   - Network issues prevented access to sources")
        
        print(f"\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_symbols():
    """Test with multiple stock symbols"""
    
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print("Testing with multiple symbols...")
    print("=" * 60)
    
    fetcher = EnhancedEarningsFetcher(rate_limit=1.0)
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        try:
            company_info = fetcher.get_company_info(symbol)
            if company_info:
                print(f"   Company: {company_info.get('name', 'N/A')}")
                
                # Quick test - just get a few results
                results = fetcher.fetch_earnings_materials_parallel(symbol)
                print(f"   Materials found: {len(results)}")
            else:
                print(f"   Could not fetch company info for {symbol}")
        except Exception as e:
            print(f"   Error testing {symbol}: {e}")

if __name__ == "__main__":
    print("Earnings Fetcher Test Script")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--multiple":
        test_multiple_symbols()
    else:
        test_earnings_fetcher()
    
    print("\nTest script completed!")