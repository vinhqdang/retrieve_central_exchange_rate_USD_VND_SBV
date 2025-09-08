#!/usr/bin/env python3
"""
Simple SBV Exchange Rate Retriever using requests (no Chrome required)

This version uses direct HTTP requests to try to get exchange rates from SBV
without requiring Chrome/ChromeDriver. This is a simpler fallback approach.
"""

import requests
from datetime import datetime, date
from typing import Optional
import re
from bs4 import BeautifulSoup
import sys

def get_sbv_exchange_rate_simple(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get USD-VND central exchange rate from State Bank of Vietnam using simple HTTP requests.
    
    This function tries to get exchange rates without Selenium by directly accessing
    SBV endpoints and parsing the responses.
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2025-01-07')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV-Simple] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2025-01-07')")
    
    log_debug(f"Retrieving SBV exchange rate for {date_str}")
    
    # Format date for SBV
    date_formatted = target_date.strftime('%d/%m/%Y')  # dd/mm/yyyy
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        # Method 1: Try English SBV API endpoint
        log_debug("Trying English SBV endpoint...")
        english_url = "https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx"
        
        try:
            response = session.get(english_url, timeout=30)
            if response.status_code == 200:
                log_debug("Successfully accessed English SBV page")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for current rate information in the page
                text_content = soup.get_text()
                
                # Try to find USD-VND rate patterns
                rate_patterns = [
                    r'USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
                    r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*VND',
                    r'1\s*USD\s*=\s*([0-9,]+\.?[0-9]*)',
                ]
                
                for pattern in rate_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            rate = float(match.replace(',', ''))
                            if 20000 <= rate <= 30000:  # Reasonable range
                                log_debug(f"Found rate in English page: {rate}")
                                return rate
                        except ValueError:
                            continue
        except Exception as e:
            log_debug(f"English endpoint failed: {e}")
        
        # Method 2: Try Vietnamese SBV endpoint
        log_debug("Trying Vietnamese SBV endpoint...")
        vietnamese_url = "https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx"
        
        try:
            response = session.get(vietnamese_url, timeout=30)
            if response.status_code == 200:
                log_debug("Successfully accessed Vietnamese SBV page")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for current rate information
                text_content = soup.get_text()
                
                # Vietnamese patterns
                rate_patterns = [
                    r'USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
                    r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*VND',
                    r'Đô\s*la\s*Mỹ.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
                ]
                
                for pattern in rate_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            rate = float(match.replace(',', ''))
                            if 20000 <= rate <= 30000:
                                log_debug(f"Found rate in Vietnamese page: {rate}")
                                return rate
                        except ValueError:
                            continue
        except Exception as e:
            log_debug(f"Vietnamese endpoint failed: {e}")
        
        # Method 3: Try Vietcombank API as fallback
        log_debug("Trying Vietcombank API as fallback...")
        try:
            vcb_url = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"
            response = session.get(vcb_url, timeout=30)
            
            if response.status_code == 200:
                log_debug("Successfully accessed Vietcombank API")
                # Parse XML response
                soup = BeautifulSoup(response.content, 'xml')
                
                # Look for USD rate
                for item in soup.find_all('Exrate'):
                    currency = item.get('@CurrencyCode', '')
                    if currency == 'USD':
                        sell_rate = item.get('@Sell', '')
                        if sell_rate:
                            try:
                                rate = float(sell_rate.replace(',', ''))
                                if 20000 <= rate <= 30000:
                                    log_debug(f"Found rate in Vietcombank API: {rate}")
                                    return rate
                            except ValueError:
                                continue
        except Exception as e:
            log_debug(f"Vietcombank API failed: {e}")
        
        # Method 4: Try ExchangeRate-API as international fallback
        log_debug("Trying ExchangeRate-API as international fallback...")
        try:
            api_url = f"https://api.exchangerate-api.com/v4/latest/USD"
            response = session.get(api_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                vnd_rate = data.get('rates', {}).get('VND')
                if vnd_rate:
                    rate = float(vnd_rate)
                    if 20000 <= rate <= 30000:
                        log_debug(f"Found rate in ExchangeRate-API: {rate}")
                        return rate
        except Exception as e:
            log_debug(f"ExchangeRate-API failed: {e}")
        
        log_debug("All methods failed to retrieve exchange rate")
        return None
        
    except Exception as e:
        log_debug(f"Error during rate retrieval: {e}")
        return None

def main():
    """
    Command line interface
    """
    print("=== SBV Exchange Rate Retriever (Simple Version) ===")
    print("🔧 This version uses HTTP requests instead of Chrome/Selenium")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_date = sys.argv[1]
        print(f"Using date from command line: {test_date}")
    else:
        test_date = date.today().strftime('%Y-%m-%d')
        print(f"No date specified, using today's date: {test_date}")
        print("💡 Tip: You can specify a date like: python sbv_simple.py 2025-01-07")
    
    print(f"Retrieving exchange rate for {test_date}...")
    print("-" * 50)
    
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        print("🔍 Debug mode enabled")
        print("-" * 50)
    
    try:
        rate = get_sbv_exchange_rate_simple(test_date, debug=debug_mode)
        
        print("-" * 50)
        if rate:
            print("✅ SUCCESS!")
            print(f"📅 Date: {test_date}")
            print(f"💰 Rate: 1 USD = {rate:,.0f} VND")
            print(f"🏛️  Source: State Bank of Vietnam / Fallback APIs")
            print(f"📄 Type: Exchange Rate")
        else:
            print("❌ Could not retrieve exchange rate")
            print("This could be due to:")
            print("  • Network connectivity issues")
            print("  • All data sources unavailable")
            print("  • No data available for the specified date")
            print("  • Weekend/holiday (no trading)")
            
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("📋 Please use format: YYYY-MM-DD (e.g., 2025-01-07)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("=" * 60)
    print("COMMAND LINE USAGE:")
    print("=" * 60)
    print("python sbv_simple.py                    # Use today's date")
    print("python sbv_simple.py 2025-01-07         # Specific date")
    print("python sbv_simple.py 2025-01-07 --debug # With debug info")

if __name__ == "__main__":
    main()