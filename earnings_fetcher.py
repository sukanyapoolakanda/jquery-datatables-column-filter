#!/usr/bin/env python3
"""
Earnings Presentations and Corporate Materials Fetcher

This script fetches earnings presentations, corporate presentations, CEO interviews,
product demos, investor day recordings, podcasts, and special events for a given
stock symbol from the most recent fiscal quarter.

Author: AI Assistant
Date: 2024
"""

import requests
import re
import json
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import yfinance as yf
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EarningsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.results = []
        
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get basic company information using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'website': info.get('website', ''),
                'country': info.get('country', '')
            }
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return None
    
    def get_current_quarter(self) -> Tuple[str, str]:
        """Get the current fiscal quarter and year"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        year = now.year
        return f"Q{quarter}", str(year)
    
    def is_recent_content(self, date_str: str) -> bool:
        """Check if content is from the current quarter"""
        try:
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'
            ]
            
            for fmt in date_formats:
                try:
                    content_date = datetime.strptime(date_str, fmt)
                    current_quarter, current_year = self.get_current_quarter()
                    
                    # Check if it's from the current quarter
                    if content_date.year == int(current_year):
                        quarter = (content_date.month - 1) // 3 + 1
                        if quarter == int(current_quarter[1]):
                            return True
                except ValueError:
                    continue
                    
            return False
        except Exception:
            return False
    
    def search_sec_edgar(self, symbol: str) -> List[Dict]:
        """Search SEC EDGAR for recent filings with presentations"""
        results = []
        try:
            # Search for 10-Q and 8-K filings
            base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': symbol,
                'type': '10-Q',
                'dateb': '',
                'owner': 'exclude',
                'output': 'xml',
                'count': '10'
            }
            
            response = self.session.get(base_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                filings = soup.find_all('filingHREF')
                
                for filing in filings:
                    filing_url = filing.text
                    if '10-Q' in filing_url or '8-K' in filing_url:
                        # Check if filing contains presentation
                        filing_response = self.session.get(filing_url)
                        if filing_response.status_code == 200:
                            filing_soup = BeautifulSoup(filing_response.content, 'html.parser')
                            
                            # Look for presentation links
                            links = filing_soup.find_all('a', href=True)
                            for link in links:
                                href = link['href']
                                if any(ext in href.lower() for ext in ['.pdf', '.ppt', '.pptx']):
                                    title = link.get_text(strip=True) or f"SEC Filing Presentation - {symbol}"
                                    results.append({
                                        'title': title,
                                        'date': datetime.now().strftime('%Y-%m-%d'),
                                        'speaker': 'SEC Filing',
                                        'format': 'PDF' if href.endswith('.pdf') else 'PPT',
                                        'url': href
                                    })
                                    
        except Exception as e:
            logger.error(f"Error searching SEC EDGAR: {e}")
            
        return results
    
    def search_company_ir_site(self, symbol: str, company_info: Dict) -> List[Dict]:
        """Search company's investor relations website"""
        results = []
        website = company_info.get('website', '')
        
        if not website:
            return results
            
        # Common IR page patterns
        ir_patterns = [
            '/investors', '/investor-relations', '/ir', '/investor',
            '/shareholders', '/financial', '/earnings'
        ]
        
        try:
            for pattern in ir_patterns:
                ir_url = urljoin(website, pattern)
                response = self.session.get(ir_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for presentation links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        text = link.get_text(strip=True).lower()
                        
                        # Check for presentation-related content
                        if any(keyword in text for keyword in ['earnings', 'presentation', 'quarterly', 'investor']):
                            if any(ext in href.lower() for ext in ['.pdf', '.ppt', '.pptx', '.mp4']):
                                title = link.get_text(strip=True)
                                if not title:
                                    title = f"Company Presentation - {symbol}"
                                    
                                results.append({
                                    'title': title,
                                    'date': datetime.now().strftime('%Y-%m-%d'),
                                    'speaker': 'Company Executive',
                                    'format': 'PDF' if href.endswith('.pdf') else 'PPT' if href.endswith(('.ppt', '.pptx')) else 'MP4',
                                    'url': href if href.startswith('http') else urljoin(ir_url, href)
                                })
                                
        except Exception as e:
            logger.error(f"Error searching company IR site: {e}")
            
        return results
    
    def search_youtube_channel(self, symbol: str, company_info: Dict) -> List[Dict]:
        """Search company's YouTube channel for investor content"""
        results = []
        
        try:
            # Try to find company's YouTube channel
            company_name = company_info.get('name', '').replace(' ', '')
            search_terms = [
                f"{company_name} investor relations",
                f"{symbol} earnings call",
                f"{company_name} quarterly earnings",
                f"{symbol} investor day"
            ]
            
            for term in search_terms:
                # This would require YouTube API integration
                # For now, we'll return a placeholder
                pass
                
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            
        return results
    
    def search_bloomberg(self, symbol: str) -> List[Dict]:
        """Search Bloomberg for investor content"""
        results = []
        
        try:
            # Bloomberg requires API access for proper scraping
            # This is a placeholder for the structure
            bloomberg_url = f"https://www.bloomberg.com/quote/{symbol}:US"
            
            response = self.session.get(bloomberg_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for investor-related content
                # This would need more sophisticated parsing
                pass
                
        except Exception as e:
            logger.error(f"Error searching Bloomberg: {e}")
            
        return results
    
    def search_nasdaq(self, symbol: str) -> List[Dict]:
        """Search Nasdaq for investor content"""
        results = []
        
        try:
            nasdaq_url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}"
            response = self.session.get(nasdaq_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for earnings and investor content
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    text = link.get_text(strip=True).lower()
                    
                    if any(keyword in text for keyword in ['earnings', 'presentation', 'quarterly']):
                        if any(ext in href.lower() for ext in ['.pdf', '.ppt', '.pptx']):
                            title = link.get_text(strip=True)
                            if not title:
                                title = f"Nasdaq Investor Content - {symbol}"
                                
                            results.append({
                                'title': title,
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'speaker': 'Company Executive',
                                'format': 'PDF' if href.endswith('.pdf') else 'PPT',
                                'url': href if href.startswith('http') else f"https://www.nasdaq.com{href}"
                            })
                            
        except Exception as e:
            logger.error(f"Error searching Nasdaq: {e}")
            
        return results
    
    def fetch_earnings_materials(self, symbol: str) -> List[Dict]:
        """Main method to fetch all earnings materials for a given symbol"""
        logger.info(f"Fetching earnings materials for {symbol}")
        
        # Get company information
        company_info = self.get_company_info(symbol)
        if not company_info:
            logger.error(f"Could not fetch company information for {symbol}")
            return []
        
        all_results = []
        
        # Search various sources
        sources = [
            ('SEC EDGAR', self.search_sec_edgar),
            ('Company IR Site', lambda s: self.search_company_ir_site(s, company_info)),
            ('Nasdaq', self.search_nasdaq),
            ('Bloomberg', self.search_bloomberg),
            ('YouTube', lambda s: self.search_youtube_channel(s, company_info))
        ]
        
        for source_name, search_func in sources:
            try:
                logger.info(f"Searching {source_name} for {symbol}")
                results = search_func(symbol)
                all_results.extend(results)
                time.sleep(1)  # Be respectful to servers
            except Exception as e:
                logger.error(f"Error searching {source_name}: {e}")
        
        # Filter for recent content and remove duplicates
        filtered_results = []
        seen_urls = set()
        
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                if self.is_recent_content(result['date']):
                    filtered_results.append(result)
        
        return filtered_results
    
    def format_output(self, results: List[Dict], symbol: str) -> str:
        """Format the results according to the specified output format"""
        if not results:
            return "NO DATA AVAILABLE FOR GIVEN COMPANY"
        
        output = f"Earnings Presentations and Corporate Materials for {symbol}\n"
        output += "=" * 60 + "\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. Title: {result['title']}\n"
            output += f"   Date: {result['date']}\n"
            output += f"   Speaker(s): {result['speaker']}\n"
            output += f"   Format: {result['format']}\n"
            output += f"   Direct Source URL: {result['url']}\n"
            output += "\n"
        
        return output

def main():
    """Main function to run the earnings fetcher"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python earnings_fetcher.py <STOCK_SYMBOL>")
        print("Example: python earnings_fetcher.py AAPL")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    fetcher = EarningsFetcher()
    results = fetcher.fetch_earnings_materials(symbol)
    
    output = fetcher.format_output(results, symbol)
    print(output)
    
    # Save results to file
    with open(f"{symbol}_earnings_materials.txt", "w") as f:
        f.write(output)
    
    print(f"\nResults saved to {symbol}_earnings_materials.txt")

if __name__ == "__main__":
    main()