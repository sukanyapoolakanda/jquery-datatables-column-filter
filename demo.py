#!/usr/bin/env python3
"""
Demonstration script for the Earnings Presentations and Corporate Materials Fetcher

This script demonstrates how to use the earnings fetcher with a specific stock symbol
and shows the results in a user-friendly format.
"""

import sys
import os
from enhanced_earnings_fetcher import EnhancedEarningsFetcher

def main():
    """Main demonstration function"""
    
    print("🎯 Earnings Presentations and Corporate Materials Fetcher")
    print("=" * 60)
    print()
    
    # Get stock symbol from user or use default
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
    else:
        symbol = input("Enter stock symbol (e.g., AAPL, MSFT, GOOGL): ").upper()
    
    if not symbol:
        print("❌ No stock symbol provided. Exiting.")
        return
    
    print(f"🔍 Searching for earnings materials for {symbol}...")
    print()
    
    try:
        # Create fetcher instance with faster rate limiting for demo
        fetcher = EnhancedEarningsFetcher(rate_limit=0.5)
        
        # Get company information
        print("📊 Fetching company information...")
        company_info = fetcher.get_company_info(symbol)
        
        if company_info:
            print(f"✅ Company: {company_info.get('name', 'N/A')}")
            print(f"   Sector: {company_info.get('sector', 'N/A')}")
            print(f"   Industry: {company_info.get('industry', 'N/A')}")
            print(f"   Website: {company_info.get('website', 'N/A')}")
            print()
        else:
            print("❌ Could not fetch company information")
            return
        
        # Fetch earnings materials
        print("🔎 Searching for earnings materials...")
        print("   This may take a few minutes as we search multiple sources...")
        print()
        
        results = fetcher.fetch_earnings_materials_parallel(symbol)
        
        # Display results
        print("📋 Results Summary:")
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
            
            print()
            print("📄 Detailed Results:")
            print("-" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. 📄 {result.title}")
                print(f"   📅 Date: {result.date}")
                print(f"   🎤 Speaker: {result.speaker}")
                print(f"   📁 Format: {result.format}")
                print(f"   🔗 URL: {result.url}")
                print(f"   📍 Source: {result.source}")
                if result.description:
                    print(f"   📝 Description: {result.description}")
                print()
            
            # Export results
            print("💾 Exporting results...")
            
            # Export to text
            output = fetcher.format_output(results, symbol)
            with open(f"{symbol}_earnings_materials.txt", "w", encoding='utf-8') as f:
                f.write(output)
            print(f"   ✅ Text file: {symbol}_earnings_materials.txt")
            
            # Export to CSV
            csv_file = fetcher.export_to_csv(results, symbol)
            print(f"   ✅ CSV file: {csv_file}")
            
            # Export to JSON
            json_file = fetcher.export_to_json(results, symbol)
            print(f"   ✅ JSON file: {json_file}")
            
        else:
            print("❌ No earnings materials found for the recent period.")
            print()
            print("This could be because:")
            print("   • The company hasn't released recent earnings materials")
            print("   • The materials are not publicly available")
            print("   • Network issues prevented access to sources")
            print("   • The company doesn't have a public investor relations site")
            print()
            print("💡 Try:")
            print("   • Using a different stock symbol")
            print("   • Checking the company's investor relations website manually")
            print("   • Increasing the days threshold with --days parameter")
        
        print()
        print("🎉 Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()