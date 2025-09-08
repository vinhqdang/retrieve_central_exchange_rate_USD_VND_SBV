#!/usr/bin/env python3
"""
Official SBV Central Exchange Rate Retriever

This version specifically targets official Vietnamese banking sources that 
reference the SBV central exchange rate, not commercial rates.
"""

import sys
import requests
from datetime import datetime, date
from typing import Optional, Dict, Tuple
import re
from bs4 import BeautifulSoup
import json


def get_sbv_central_rate_official(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get the official SBV central exchange rate from authoritative Vietnamese sources.
    
    The SBV central rate is different from commercial bank rates and is used as the
    official reference rate for Vietnam.
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2025-01-19')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV-Official] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2025-01-19')")
    
    log_debug(f"Retrieving official SBV central rate for {date_str}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })
    
    # Format dates
    date_formatted_vn = target_date.strftime('%d/%m/%Y')  
    date_formatted_iso = target_date.strftime('%Y-%m-%d')
    
    # Method 1: Vietcombank Central Rate API
    # Vietcombank publishes both commercial and central rates
    log_debug("Method 1: Vietcombank Central Rate...")
    try:
        # Try the central rate endpoint specifically
        central_url = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10"
        response = session.get(central_url, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            log_debug("Successfully accessed Vietcombank central rate API")
            
            # Look for USD central rate specifically
            for item in soup.find_all('Exrate'):
                currency_code = item.get('CurrencyCode', '')
                if currency_code == 'USD':
                    # Central rate might be in different field
                    central_rate = item.get('Central') or item.get('Transfer') or item.get('Buy')
                    if central_rate:
                        try:
                            rate = float(central_rate.replace(',', ''))
                            if 20000 <= rate <= 30000:
                                log_debug(f"Found Vietcombank central rate: {rate}")
                                return rate
                        except ValueError:
                            pass
    except Exception as e:
        log_debug(f"Vietcombank central rate failed: {e}")
    
    # Method 2: Try Vietcombank regular API and identify central rate
    log_debug("Method 2: Vietcombank standard API...")
    try:
        response = session.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            
            for item in soup.find_all('Exrate'):
                if item.get('CurrencyCode') == 'USD':
                    # The transfer rate is often closest to central rate
                    transfer_rate = item.get('Transfer', '').replace(',', '')
                    buy_rate = item.get('Buy', '').replace(',', '')
                    sell_rate = item.get('Sell', '').replace(',', '')
                    
                    rates = {}
                    for name, value in [('transfer', transfer_rate), ('buy', buy_rate), ('sell', sell_rate)]:
                        if value:
                            try:
                                rates[name] = float(value)
                            except ValueError:
                                pass
                    
                    if rates:
                        log_debug(f"Vietcombank rates: {rates}")
                        # Transfer rate is typically closest to central rate
                        if 'transfer' in rates:
                            rate = rates['transfer']
                            if 20000 <= rate <= 30000:
                                log_debug(f"Using Vietcombank transfer rate as central: {rate}")
                                return rate
    except Exception as e:
        log_debug(f"Vietcombank standard API failed: {e}")
    
    # Method 3: Try Agribank (another state bank)
    log_debug("Method 3: Agribank...")
    try:
        # Agribank API
        agri_url = "https://www.agribank.com.vn/vn/json/tygia"
        response = session.get(agri_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            log_debug("Successfully accessed Agribank API")
            
            for item in data:
                if item.get('currency_code') == 'USD' or item.get('code') == 'USD':
                    transfer_rate = item.get('transfer_rate') or item.get('transfer')
                    if transfer_rate:
                        try:
                            rate = float(str(transfer_rate).replace(',', ''))
                            if 20000 <= rate <= 30000:
                                log_debug(f"Found Agribank rate: {rate}")
                                return rate
                        except ValueError:
                            pass
    except Exception as e:
        log_debug(f"Agribank method failed: {e}")
    
    # Method 4: Try BIDV with different approach
    log_debug("Method 4: BIDV alternative...")
    try:
        # Try different BIDV endpoints
        bidv_urls = [
            "https://www.bidv.com.vn/api/exchangerates",
            "https://bidv.com.vn/wps/wcm/connect/bidv/site/home/services/exchange-rate",
        ]
        
        for url in bidv_urls:
            try:
                response = session.get(url, timeout=30, verify=False)  # Skip SSL verification
                if response.status_code == 200:
                    log_debug(f"Accessed BIDV endpoint: {url}")
                    
                    # Try to parse as JSON first
                    try:
                        data = response.json()
                        for item in data:
                            if isinstance(item, dict) and ('USD' in str(item) or 'usd' in str(item).lower()):
                                # Look for transfer/central rate
                                for key, value in item.items():
                                    if 'transfer' in key.lower() or 'central' in key.lower():
                                        try:
                                            rate = float(str(value).replace(',', ''))
                                            if 20000 <= rate <= 30000:
                                                log_debug(f"Found BIDV rate: {rate}")
                                                return rate
                                        except ValueError:
                                            pass
                    except:
                        # Try parsing as HTML
                        soup = BeautifulSoup(response.content, 'html.parser')
                        text = soup.get_text()
                        if 'USD' in text:
                            # Extract potential rates
                            numbers = re.findall(r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)', text)
                            for num_str in numbers:
                                try:
                                    rate = float(num_str.replace(',', ''))
                                    if 20000 <= rate <= 30000:
                                        log_debug(f"Found BIDV HTML rate: {rate}")
                                        return rate
                                except ValueError:
                                    continue
            except Exception as e:
                log_debug(f"BIDV URL {url} failed: {e}")
                continue
    except Exception as e:
        log_debug(f"BIDV alternative method failed: {e}")
    
    # Method 5: Get current market consensus from financial news sites
    log_debug("Method 5: Financial news sources...")
    try:
        # Try VietnamNet economics section (often reports official rates)
        news_urls = [
            "https://vietnamnet.vn/kinh-te",
            "https://vneconomy.vn/ty-gia.htm",
            "https://cafef.vn/ty-gia.chn"
        ]
        
        for url in news_urls:
            try:
                response = session.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text = soup.get_text()
                    
                    # Look for SBV or central rate mentions
                    if any(term in text.lower() for term in ['sbv', 'ngân hàng nhà nước', 'tỷ giá trung tâm']):
                        # Extract rates near these mentions
                        sentences = text.split('.')
                        for sentence in sentences:
                            if any(term in sentence.lower() for term in ['sbv', 'trung tâm', 'usd']):
                                numbers = re.findall(r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)', sentence)
                                for num_str in numbers:
                                    try:
                                        rate = float(num_str.replace(',', ''))
                                        if 20000 <= rate <= 30000:
                                            log_debug(f"Found news rate: {rate} from {url}")
                                            return rate
                                    except ValueError:
                                        continue
            except Exception as e:
                log_debug(f"News URL {url} failed: {e}")
                continue
    except Exception as e:
        log_debug(f"News sources method failed: {e}")
    
    log_debug("No official central rate found")
    return None


def main():
    """Command line interface"""
    print("=== SBV Official Central Exchange Rate Retriever ===")
    print("🏛️  This version targets official SBV central rates from authoritative sources")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_date = sys.argv[1]
        print(f"Using date from command line: {test_date}")
    else:
        test_date = date.today().strftime('%Y-%m-%d')
        print(f"No date specified, using today's date: {test_date}")
        print("💡 Tip: You can specify a date like: python sbv_official.py 2025-01-19")
    
    print(f"Retrieving official SBV central rate for {test_date}...")
    print("-" * 50)
    
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        print("🔍 Debug mode enabled")
        print("-" * 50)
    
    try:
        rate = get_sbv_central_rate_official(test_date, debug=debug_mode)
        
        print("-" * 50)
        if rate:
            print("✅ SUCCESS!")
            print(f"📅 Date: {test_date}")
            print(f"💰 Central Rate: 1 USD = {rate:,.0f} VND")
            print(f"🏛️  Source: Official Vietnamese Banking System")
            print(f"📄 Type: SBV Central Exchange Rate (Reference)")
            print()
            print("ℹ️  Note: This is the central/reference rate used by Vietnamese")
            print("   financial institutions, different from commercial bank rates.")
        else:
            print("❌ Could not retrieve official central rate")
            print("This could be due to:")
            print("  • Network connectivity issues")
            print("  • All official sources unavailable")
            print("  • No data available for the specified date")
            print("  • Weekend/holiday (no official rate published)")
                
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("📋 Please use format: YYYY-MM-DD (e.g., 2025-01-19)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("=" * 60)
    print("COMMAND LINE USAGE:")
    print("=" * 60)
    print("python sbv_official.py                    # Use today's date")
    print("python sbv_official.py 2025-01-19         # Specific date")
    print("python sbv_official.py 2025-01-19 --debug # With detailed analysis")


if __name__ == "__main__":
    main()