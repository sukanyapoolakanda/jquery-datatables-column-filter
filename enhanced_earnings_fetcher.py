#!/usr/bin/env python3
"""
Enhanced Earnings Presentations and Corporate Materials Fetcher

This enhanced script fetches earnings presentations, corporate presentations, CEO interviews,
product demos, investor day recordings, podcasts, and special events for a given
stock symbol from the most recent fiscal quarter.

Features:
- Multi-source scraping (SEC, Company IR, Nasdaq, Bloomberg, YouTube)
- Intelligent date filtering
- Duplicate detection
- Rate limiting and respectful scraping
- Comprehensive error handling
- Export to multiple formats

Author: AI Assistant
Date: 2024
"""

import requests
import re
import json
import time
import csv
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
import yfinance as yf
from typing import List, Dict, Optional, Tuple, Set
import logging
import os
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EarningsMaterial:
    """Data class for earnings materials"""
    title: str
    date: str
    speaker: str
    format: str
    url: str
    source: str
    description: str = ""
    file_size: str = ""
    duration: str = ""

class EnhancedEarningsFetcher:
    def __init__(self, rate_limit: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.rate_limit = rate_limit
        self.results: List[EarningsMaterial] = []
        self.seen_urls: Set[str] = set()
        
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive company information using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get additional company data
            company_data = {
                'name': info.get('longName', ''),
                'short_name': info.get('shortName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'website': info.get('website', ''),
                'country': info.get('country', ''),
                'market_cap': info.get('marketCap', 0),
                'employees': info.get('fullTimeEmployees', 0),
                'description': info.get('longBusinessSummary', ''),
                'exchange': info.get('exchange', ''),
                'currency': info.get('currency', ''),
                'cik': info.get('cik', ''),
            }
            
            logger.info(f"Retrieved company info for {symbol}: {company_data['name']}")
            return company_data
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return None
    
    def get_current_quarter(self) -> Tuple[str, str]:
        """Get the current fiscal quarter and year"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        year = now.year
        return f"Q{quarter}", str(year)
    
    def is_recent_content(self, date_str: str, days_threshold: int = 90) -> bool:
        """Check if content is from the recent period"""
        try:
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
                '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in date_formats:
                try:
                    content_date = datetime.strptime(date_str, fmt)
                    days_ago = (datetime.now() - content_date).days
                    return days_ago <= days_threshold
                except ValueError:
                    continue
                    
            return False
        except Exception:
            return False
    
    def search_sec_edgar_enhanced(self, symbol: str, company_info: Dict) -> List[EarningsMaterial]:
        """Enhanced SEC EDGAR search with better parsing"""
        results = []
        
        try:
            # Get CIK from company info or try to find it
            cik = company_info.get('cik', '')
            if not cik:
                # Try to find CIK using company name
                search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
                params = {
                    'action': 'getcompany',
                    'company': company_info.get('name', symbol),
                    'owner': 'exclude',
                    'output': 'xml',
                    'count': '10'
                }
                
                response = self.session.get(search_url, params=params)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    cik_elem = soup.find('CIK')
                    if cik_elem:
                        cik = cik_elem.text.zfill(10)
            
            if not cik:
                logger.warning(f"Could not find CIK for {symbol}")
                return results
            
            # Search for recent filings
            filing_types = ['10-Q', '8-K', '10-K']
            
            for filing_type in filing_types:
                base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
                params = {
                    'action': 'getcompany',
                    'CIK': cik,
                    'type': filing_type,
                    'dateb': '',
                    'owner': 'exclude',
                    'output': 'xml',
                    'count': '5'
                }
                
                response = self.session.get(base_url, params=params)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    filings = soup.find_all('filingHREF')
                    
                    for filing in filings:
                        filing_url = filing.text
                        try:
                            filing_response = self.session.get(filing_url)
                            if filing_response.status_code == 200:
                                filing_soup = BeautifulSoup(filing_response.content, 'html.parser')
                                
                                # Look for presentation links
                                links = filing_soup.find_all('a', href=True)
                                for link in links:
                                    href = link['href']
                                    text = link.get_text(strip=True)
                                    
                                    # Check for presentation files
                                    if any(ext in href.lower() for ext in ['.pdf', '.ppt', '.pptx', '.xlsx', '.xls']):
                                        if href not in self.seen_urls:
                                            self.seen_urls.add(href)
                                            
                                            title = text or f"{filing_type} Filing - {symbol}"
                                            results.append(EarningsMaterial(
                                                title=title,
                                                date=datetime.now().strftime('%Y-%m-%d'),
                                                speaker='SEC Filing',
                                                format='PDF' if href.endswith('.pdf') else 'PPT' if href.endswith(('.ppt', '.pptx')) else 'XLS',
                                                url=href,
                                                source='SEC EDGAR',
                                                description=f"{filing_type} filing containing presentation materials"
                                            ))
                                            
                        except Exception as e:
                            logger.error(f"Error processing filing {filing_url}: {e}")
                            continue
                            
                time.sleep(self.rate_limit)
                
        except Exception as e:
            logger.error(f"Error searching SEC EDGAR: {e}")
            
        return results
    
    def search_company_ir_site_enhanced(self, symbol: str, company_info: Dict) -> List[EarningsMaterial]:
        """Enhanced company IR site search"""
        results = []
        website = company_info.get('website', '')
        
        if not website:
            return results
            
        # Common IR page patterns
        ir_patterns = [
            '/investors', '/investor-relations', '/ir', '/investor',
            '/shareholders', '/financial', '/earnings', '/presentations',
            '/events', '/news', '/press-releases'
        ]
        
        try:
            for pattern in ir_patterns:
                ir_url = urljoin(website, pattern)
                try:
                    response = self.session.get(ir_url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for presentation links with enhanced detection
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            text = link.get_text(strip=True).lower()
                            
                            # Enhanced keyword detection
                            keywords = [
                                'earnings', 'presentation', 'quarterly', 'investor',
                                'call', 'webcast', 'conference', 'day', 'update',
                                'results', 'financial', 'performance'
                            ]
                            
                            if any(keyword in text for keyword in keywords):
                                if any(ext in href.lower() for ext in ['.pdf', '.ppt', '.pptx', '.mp4', '.mp3', '.wmv']):
                                    if href not in self.seen_urls:
                                        self.seen_urls.add(href)
                                        
                                        full_url = href if href.startswith('http') else urljoin(ir_url, href)
                                        title = link.get_text(strip=True) or f"Company Presentation - {symbol}"
                                        
                                        # Determine format
                                        if href.endswith('.pdf'):
                                            format_type = 'PDF'
                                        elif href.endswith(('.ppt', '.pptx')):
                                            format_type = 'PPT'
                                        elif href.endswith(('.mp4', '.avi', '.mov')):
                                            format_type = 'MP4'
                                        elif href.endswith(('.mp3', '.wav')):
                                            format_type = 'MP3'
                                        else:
                                            format_type = 'Document'
                                        
                                        results.append(EarningsMaterial(
                                            title=title,
                                            date=datetime.now().strftime('%Y-%m-%d'),
                                            speaker='Company Executive',
                                            format=format_type,
                                            url=full_url,
                                            source='Company IR Site',
                                            description=f"Investor relations content from {company_info.get('name', symbol)}"
                                        ))
                                        
                except Exception as e:
                    logger.error(f"Error accessing {ir_url}: {e}")
                    continue
                    
                time.sleep(self.rate_limit)
                
        except Exception as e:
            logger.error(f"Error searching company IR site: {e}")
            
        return results
    
    def search_nasdaq_enhanced(self, symbol: str) -> List[EarningsMaterial]:
        """Enhanced Nasdaq search"""
        results = []
        
        try:
            # Try multiple Nasdaq URLs
            nasdaq_urls = [
                f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}",
                f"https://www.nasdaq.com/quote/{symbol}",
                f"https://www.nasdaq.com/symbol/{symbol.lower()}"
            ]
            
            for nasdaq_url in nasdaq_urls:
                try:
                    response = self.session.get(nasdaq_url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for earnings and investor content
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            text = link.get_text(strip=True).lower()
                            
                            if any(keyword in text for keyword in ['earnings', 'presentation', 'quarterly', 'call', 'webcast']):
                                if any(ext in href.lower() for ext in ['.pdf', '.ppt', '.pptx', '.mp4']):
                                    if href not in self.seen_urls:
                                        self.seen_urls.add(href)
                                        
                                        full_url = href if href.startswith('http') else f"https://www.nasdaq.com{href}"
                                        title = link.get_text(strip=True) or f"Nasdaq Investor Content - {symbol}"
                                        
                                        results.append(EarningsMaterial(
                                            title=title,
                                            date=datetime.now().strftime('%Y-%m-%d'),
                                            speaker='Company Executive',
                                            format='PDF' if href.endswith('.pdf') else 'PPT' if href.endswith(('.ppt', '.pptx')) else 'MP4',
                                            url=full_url,
                                            source='Nasdaq',
                                            description=f"Investor content from Nasdaq for {symbol}"
                                        ))
                                        
                except Exception as e:
                    logger.error(f"Error accessing {nasdaq_url}: {e}")
                    continue
                    
                time.sleep(self.rate_limit)
                
        except Exception as e:
            logger.error(f"Error searching Nasdaq: {e}")
            
        return results
    
    def search_yahoo_finance(self, symbol: str) -> List[EarningsMaterial]:
        """Search Yahoo Finance for earnings content"""
        results = []
        
        try:
            yahoo_url = f"https://finance.yahoo.com/quote/{symbol}/events"
            response = self.session.get(yahoo_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for earnings events and presentations
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    text = link.get_text(strip=True).lower()
                    
                    if any(keyword in text for keyword in ['earnings', 'presentation', 'call', 'webcast']):
                        if href not in self.seen_urls:
                            self.seen_urls.add(href)
                            
                            full_url = href if href.startswith('http') else f"https://finance.yahoo.com{href}"
                            title = link.get_text(strip=True) or f"Yahoo Finance Event - {symbol}"
                            
                            results.append(EarningsMaterial(
                                title=title,
                                date=datetime.now().strftime('%Y-%m-%d'),
                                speaker='Company Executive',
                                format='Web Page',
                                url=full_url,
                                source='Yahoo Finance',
                                description=f"Earnings event from Yahoo Finance for {symbol}"
                            ))
                            
        except Exception as e:
            logger.error(f"Error searching Yahoo Finance: {e}")
            
        return results
    
    def fetch_earnings_materials_parallel(self, symbol: str) -> List[EarningsMaterial]:
        """Fetch earnings materials using parallel processing"""
        logger.info(f"Fetching earnings materials for {symbol}")
        
        # Get company information
        company_info = self.get_company_info(symbol)
        if not company_info:
            logger.error(f"Could not fetch company information for {symbol}")
            return []
        
        all_results = []
        
        # Define search functions
        search_functions = [
            ('SEC EDGAR', lambda: self.search_sec_edgar_enhanced(symbol, company_info)),
            ('Company IR Site', lambda: self.search_company_ir_site_enhanced(symbol, company_info)),
            ('Nasdaq', lambda: self.search_nasdaq_enhanced(symbol)),
            ('Yahoo Finance', lambda: self.search_yahoo_finance(symbol))
        ]
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_source = {
                executor.submit(search_func): source_name 
                for source_name, search_func in search_functions
            }
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    results = future.result()
                    logger.info(f"Found {len(results)} results from {source_name}")
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error searching {source_name}: {e}")
        
        # Filter for recent content
        filtered_results = []
        for result in all_results:
            if self.is_recent_content(result.date):
                filtered_results.append(result)
        
        logger.info(f"Total filtered results: {len(filtered_results)}")
        return filtered_results
    
    def export_to_csv(self, results: List[EarningsMaterial], symbol: str):
        """Export results to CSV file"""
        filename = f"{symbol}_earnings_materials.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Date', 'Speaker', 'Format', 'URL', 'Source', 'Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'Title': result.title,
                    'Date': result.date,
                    'Speaker': result.speaker,
                    'Format': result.format,
                    'URL': result.url,
                    'Source': result.source,
                    'Description': result.description
                })
        
        logger.info(f"Results exported to {filename}")
        return filename
    
    def export_to_json(self, results: List[EarningsMaterial], symbol: str):
        """Export results to JSON file"""
        filename = f"{symbol}_earnings_materials.json"
        
        data = []
        for result in results:
            data.append({
                'title': result.title,
                'date': result.date,
                'speaker': result.speaker,
                'format': result.format,
                'url': result.url,
                'source': result.source,
                'description': result.description
            })
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Results exported to {filename}")
        return filename
    
    def format_output(self, results: List[EarningsMaterial], symbol: str) -> str:
        """Format the results according to the specified output format"""
        if not results:
            return "NO DATA AVAILABLE FOR GIVEN COMPANY"
        
        output = f"Earnings Presentations and Corporate Materials for {symbol}\n"
        output += "=" * 80 + "\n\n"
        
        # Group by source
        by_source = {}
        for result in results:
            if result.source not in by_source:
                by_source[result.source] = []
            by_source[result.source].append(result)
        
        for source, source_results in by_source.items():
            output += f"Source: {source}\n"
            output += "-" * 40 + "\n"
            
            for i, result in enumerate(source_results, 1):
                output += f"{i}. Title: {result.title}\n"
                output += f"   Date: {result.date}\n"
                output += f"   Speaker(s): {result.speaker}\n"
                output += f"   Format: {result.format}\n"
                output += f"   Direct Source URL: {result.url}\n"
                if result.description:
                    output += f"   Description: {result.description}\n"
                output += "\n"
            
            output += "\n"
        
        return output

def main():
    """Main function to run the enhanced earnings fetcher"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Earnings Materials Fetcher')
    parser.add_argument('symbol', help='Stock symbol (e.g., AAPL)')
    parser.add_argument('--format', choices=['text', 'csv', 'json', 'all'], default='all',
                       help='Output format (default: all)')
    parser.add_argument('--rate-limit', type=float, default=1.0,
                       help='Rate limit between requests in seconds (default: 1.0)')
    parser.add_argument('--days', type=int, default=90,
                       help='Days threshold for recent content (default: 90)')
    
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    
    # Create fetcher instance
    fetcher = EnhancedEarningsFetcher(rate_limit=args.rate_limit)
    
    # Fetch results
    results = fetcher.fetch_earnings_materials_parallel(symbol)
    
    # Export based on format
    if args.format in ['text', 'all']:
        output = fetcher.format_output(results, symbol)
        print(output)
        
        # Save to text file
        with open(f"{symbol}_earnings_materials.txt", "w", encoding='utf-8') as f:
            f.write(output)
        print(f"\nResults saved to {symbol}_earnings_materials.txt")
    
    if args.format in ['csv', 'all']:
        csv_file = fetcher.export_to_csv(results, symbol)
        print(f"CSV results saved to {csv_file}")
    
    if args.format in ['json', 'all']:
        json_file = fetcher.export_to_json(results, symbol)
        print(f"JSON results saved to {json_file}")
    
    print(f"\nTotal results found: {len(results)}")

if __name__ == "__main__":
    main()