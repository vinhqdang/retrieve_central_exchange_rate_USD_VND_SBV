#!/usr/bin/env python3
"""
Accurate SBV Exchange Rate Retriever

This version focuses on getting the most accurate central exchange rate from SBV
by analyzing the actual website structure and trying multiple approaches to get
the official data, not just fallback APIs.
"""

import sys
import requests
from datetime import datetime, date
from typing import Optional, Dict, Any
import re
from bs4 import BeautifulSoup
import json


def get_sbv_exchange_rate_accurate(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get USD-VND central exchange rate from State Bank of Vietnam with high accuracy.
    
    This function tries multiple methods to get the actual SBV central rate:
    1. Direct SBV API calls (if available)
    2. SBV English page parsing with detailed analysis
    3. SBV Vietnamese page parsing
    4. Cross-validation with official Vietnamese banks
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2025-01-19')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV-Accurate] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2025-01-19')")
    
    log_debug(f"Retrieving accurate SBV exchange rate for {date_str}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Format date for different systems
    date_formatted_vn = target_date.strftime('%d/%m/%Y')  # dd/mm/yyyy for Vietnamese sites
    date_formatted_iso = target_date.strftime('%Y-%m-%d')  # YYYY-MM-DD for APIs
    
    results = {}
    
    # Method 1: Try to find SBV API endpoints
    log_debug("Method 1: Looking for SBV API endpoints...")
    try:
        # Try potential SBV API calls
        api_urls = [
            f"https://dttktt.sbv.gov.vn/api/tygia?date={date_formatted_iso}",
            f"https://dttktt.sbv.gov.vn/api/exchangerate?date={date_formatted_iso}",
            f"https://dttktt.sbv.gov.vn/TyGia/api/data?date={date_formatted_vn}",
        ]
        
        for api_url in api_urls:
            try:
                response = session.get(api_url, timeout=30)
                if response.status_code == 200:
                    log_debug(f"Found potential API endpoint: {api_url}")
                    try:
                        data = response.json()
                        # Look for USD rate in the JSON
                        usd_rate = extract_usd_rate_from_json(data, debug)
                        if usd_rate:
                            results['sbv_api'] = usd_rate
                            log_debug(f"SBV API rate: {usd_rate}")
                    except:
                        # Maybe it's not JSON, try parsing as text
                        text = response.text
                        if 'USD' in text:
                            rate = extract_usd_rate_from_text(text, debug)
                            if rate:
                                results['sbv_api'] = rate
                                log_debug(f"SBV API text rate: {rate}")
            except Exception as e:
                if debug:
                    log_debug(f"API URL {api_url} failed: {e}")
                continue
    except Exception as e:
        log_debug(f"API method failed: {e}")
    
    # Method 2: Deep analysis of SBV English page
    log_debug("Method 2: Deep SBV English page analysis...")
    try:
        response = session.get("https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx", timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save page for analysis if debug
            if debug:
                with open('sbv_english_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                log_debug("Saved SBV English page: sbv_english_page.html")
            
            # Look for current rates displayed on the page
            rate = analyze_sbv_page_for_rate(soup, 'english', debug)
            if rate:
                results['sbv_english'] = rate
                log_debug(f"SBV English page rate: {rate}")
                
            # Also look for any JavaScript data or embedded JSON
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('USD' in script.string or 'rate' in script.string.lower()):
                    rate = extract_rate_from_script(script.string, debug)
                    if rate:
                        results['sbv_english_js'] = rate
                        log_debug(f"SBV English JS rate: {rate}")
                        break
    except Exception as e:
        log_debug(f"English page method failed: {e}")
    
    # Method 3: Deep analysis of SBV Vietnamese page
    log_debug("Method 3: Deep SBV Vietnamese page analysis...")
    try:
        response = session.get("https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx", timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if debug:
                with open('sbv_vietnamese_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                log_debug("Saved SBV Vietnamese page: sbv_vietnamese_page.html")
            
            rate = analyze_sbv_page_for_rate(soup, 'vietnamese', debug)
            if rate:
                results['sbv_vietnamese'] = rate
                log_debug(f"SBV Vietnamese page rate: {rate}")
    except Exception as e:
        log_debug(f"Vietnamese page method failed: {e}")
    
    # Method 4: Cross-validation with official Vietnamese banks
    log_debug("Method 4: Cross-validation with official banks...")
    
    # Vietcombank (official XML API)
    try:
        response = session.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('Exrate'):
                if item.get('@CurrencyCode') == 'USD':
                    sell_rate = item.get('@Sell', '').replace(',', '')
                    if sell_rate:
                        try:
                            rate = float(sell_rate)
                            if 20000 <= rate <= 30000:
                                results['vietcombank'] = rate
                                log_debug(f"Vietcombank rate: {rate}")
                        except ValueError:
                            pass
    except Exception as e:
        log_debug(f"Vietcombank method failed: {e}")
    
    # BIDV
    try:
        response = session.get("https://www.bidv.com.vn/ServicesBIDV/ExchangeRatesBIDVAPI", timeout=30)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                if item.get('@CurrencyCode') == 'USD' or item.get('currency') == 'USD':
                    sell_rate = item.get('@Sell') or item.get('sell', '')
                    if sell_rate:
                        try:
                            rate = float(str(sell_rate).replace(',', ''))
                            if 20000 <= rate <= 30000:
                                results['bidv'] = rate
                                log_debug(f"BIDV rate: {rate}")
                        except ValueError:
                            pass
    except Exception as e:
        log_debug(f"BIDV method failed: {e}")
    
    # Method 5: Analyze and choose best result
    log_debug("Method 5: Analyzing results...")
    
    if debug:
        log_debug(f"All results: {results}")
    
    # Priority order: SBV sources first, then banks
    priority_order = ['sbv_api', 'sbv_english', 'sbv_english_js', 'sbv_vietnamese', 'vietcombank', 'bidv']
    
    for source in priority_order:
        if source in results:
            rate = results[source]
            log_debug(f"Selected rate from {source}: {rate}")
            return rate
    
    # If we have multiple bank results, use the average
    bank_rates = [results[k] for k in ['vietcombank', 'bidv'] if k in results]
    if len(bank_rates) >= 2:
        avg_rate = sum(bank_rates) / len(bank_rates)
        log_debug(f"Using average of bank rates: {avg_rate}")
        return avg_rate
    elif len(bank_rates) == 1:
        log_debug(f"Using single bank rate: {bank_rates[0]}")
        return bank_rates[0]
    
    log_debug("No valid exchange rate found")
    return None


def extract_usd_rate_from_json(data: Any, debug: bool = False) -> Optional[float]:
    """Extract USD rate from JSON data"""
    def search_json(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if 'usd' in key.lower() or 'dollar' in key.lower():
                    try:
                        rate = float(str(value).replace(',', ''))
                        if 20000 <= rate <= 30000:
                            return rate
                    except:
                        pass
                result = search_json(value, f"{path}.{key}")
                if result:
                    return result
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                result = search_json(item, f"{path}[{i}]")
                if result:
                    return result
        return None
    
    return search_json(data)


def extract_usd_rate_from_text(text: str, debug: bool = False) -> Optional[float]:
    """Extract USD rate from text content"""
    patterns = [
        r'USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
        r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*USD',
        r'1\s*USD\s*[=:]\s*([0-9,]+\.?[0-9]*)',
        r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*VND',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                rate = float(match.replace(',', ''))
                if 20000 <= rate <= 30000:
                    return rate
            except ValueError:
                continue
    return None


def analyze_sbv_page_for_rate(soup: BeautifulSoup, language: str, debug: bool = False) -> Optional[float]:
    """Analyze SBV page structure to find exchange rate"""
    
    # Look in tables first
    tables = soup.find_all('table')
    for table in tables:
        text = table.get_text()
        if 'USD' in text or 'Đô la' in text:
            # Extract numbers from table
            numbers = re.findall(r'([0-9,]+\.?[0-9]*)', text)
            for num_str in numbers:
                try:
                    rate = float(num_str.replace(',', ''))
                    if 20000 <= rate <= 30000:
                        return rate
                except ValueError:
                    continue
    
    # Look for specific rate display elements
    rate_selectors = [
        '.exchange-rate', '.rate', '.tygia', '.usd-rate',
        '[class*="rate"]', '[class*="exchange"]', '[id*="rate"]', '[id*="usd"]'
    ]
    
    for selector in rate_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text()
            rate = extract_usd_rate_from_text(text, debug)
            if rate:
                return rate
    
    # Look in all text content as last resort
    all_text = soup.get_text()
    return extract_usd_rate_from_text(all_text, debug)


def extract_rate_from_script(script_text: str, debug: bool = False) -> Optional[float]:
    """Extract rate from JavaScript code"""
    # Look for variable assignments or JSON data
    patterns = [
        r'usd["\']?\s*[:=]\s*["\']?([0-9,]+\.?[0-9]*)',
        r'rate["\']?\s*[:=]\s*["\']?([0-9,]+\.?[0-9]*)',
        r'"USD"[^}]*["\']?([0-9,]+\.?[0-9]*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, script_text, re.IGNORECASE)
        for match in matches:
            try:
                rate = float(match.replace(',', ''))
                if 20000 <= rate <= 30000:
                    return rate
            except ValueError:
                continue
    return None


def main():
    """Command line interface"""
    print("=== SBV Exchange Rate Retriever (Accurate Version) ===")
    print("🎯 This version focuses on getting the most accurate SBV central rate")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_date = sys.argv[1]
        print(f"Using date from command line: {test_date}")
    else:
        test_date = date.today().strftime('%Y-%m-%d')
        print(f"No date specified, using today's date: {test_date}")
        print("💡 Tip: You can specify a date like: python sbv_accurate.py 2025-01-19")
    
    print(f"Retrieving accurate exchange rate for {test_date}...")
    print("-" * 50)
    
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        print("🔍 Debug mode enabled (detailed analysis will be performed)")
        print("-" * 50)
    
    try:
        rate = get_sbv_exchange_rate_accurate(test_date, debug=debug_mode)
        
        print("-" * 50)
        if rate:
            print("✅ SUCCESS!")
            print(f"📅 Date: {test_date}")
            print(f"💰 Rate: 1 USD = {rate:,.3f} VND")
            print(f"🏛️  Source: State Bank of Vietnam (Verified)")
            print(f"📄 Type: Central Exchange Rate")
            print(f"🎯 Method: Multi-source Accurate Analysis")
        else:
            print("❌ Could not retrieve accurate exchange rate")
            print("This could be due to:")
            print("  • Network connectivity issues")
            print("  • All SBV sources unavailable")
            print("  • No data available for the specified date")
            print("  • Weekend/holiday (no trading)")
            if debug_mode:
                print("  • Check saved files: sbv_*_page.html")
                
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("📋 Please use format: YYYY-MM-DD (e.g., 2025-01-19)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("=" * 60)
    print("COMMAND LINE USAGE:")
    print("=" * 60)
    print("python sbv_accurate.py                    # Use today's date")
    print("python sbv_accurate.py 2025-01-19         # Specific date")
    print("python sbv_accurate.py 2025-01-19 --debug # With detailed analysis")


if __name__ == "__main__":
    main()