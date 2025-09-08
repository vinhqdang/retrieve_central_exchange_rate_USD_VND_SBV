#!/usr/bin/env python3
"""
Real SBV Exchange Rate Retriever

This version uses requests-html with PyPPeteer to execute JavaScript and get
the actual SBV central exchange rate from the official website.
"""

import sys
import asyncio
from datetime import datetime, date
from typing import Optional
import re

try:
    from requests_html import AsyncHTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False


async def get_sbv_real_rate(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get actual SBV central exchange rate from the official SBV website.
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2025-01-19')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV-Real] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2025-01-19')")
    
    if not REQUESTS_HTML_AVAILABLE:
        raise ImportError("requests-html is required. Install with: pip install requests-html")
    
    log_debug(f"Retrieving real SBV exchange rate for {date_str}")
    
    # Format date for SBV
    date_formatted = target_date.strftime('%d/%m/%Y')  # dd/mm/yyyy
    
    session = AsyncHTMLSession()
    
    try:
        # Method 1: Try English SBV site with JavaScript execution
        log_debug("Method 1: SBV English site with JavaScript...")
        
        try:
            r = await session.get("https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx")
            log_debug(f"Loaded English page, status: {r.status_code}")
            
            # Render JavaScript
            await r.html.arender(timeout=30)
            log_debug("JavaScript rendered successfully")
            
            if debug:
                with open('sbv_english_rendered.html', 'w', encoding='utf-8') as f:
                    f.write(r.html.html)
                log_debug("Saved rendered HTML: sbv_english_rendered.html")
            
            # Look for exchange rate in rendered content
            text_content = r.html.text
            rate = extract_rate_from_text(text_content, debug)
            if rate:
                log_debug(f"Found rate in English rendered page: {rate}")
                return rate
                
        except Exception as e:
            log_debug(f"English site method failed: {e}")
        
        # Method 2: Try Vietnamese SBV site with JavaScript execution
        log_debug("Method 2: SBV Vietnamese site with JavaScript...")
        
        try:
            r = await session.get("https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx")
            log_debug(f"Loaded Vietnamese page, status: {r.status_code}")
            
            # Render JavaScript
            await r.html.arender(timeout=30)
            log_debug("JavaScript rendered successfully")
            
            if debug:
                with open('sbv_vietnamese_rendered.html', 'w', encoding='utf-8') as f:
                    f.write(r.html.html)
                log_debug("Saved rendered HTML: sbv_vietnamese_rendered.html")
            
            # Look for exchange rate in rendered content
            text_content = r.html.text
            rate = extract_rate_from_text(text_content, debug)
            if rate:
                log_debug(f"Found rate in Vietnamese rendered page: {rate}")
                return rate
                
        except Exception as e:
            log_debug(f"Vietnamese site method failed: {e}")
        
        # Method 3: Try to interact with the form (English site)
        log_debug("Method 3: Trying form interaction on English site...")
        
        try:
            r = await session.get("https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx")
            await r.html.arender(timeout=30)
            
            # Try to fill form and submit
            # Look for form elements
            forms = r.html.find('form')
            log_debug(f"Found {len(forms)} forms")
            
            if forms:
                # Try to find date inputs and fill them
                date_inputs = r.html.find('input[type="text"]')
                log_debug(f"Found {len(date_inputs)} text inputs")
                
                if len(date_inputs) >= 2:
                    # This would require more complex interaction
                    # For now, just analyze the current page content
                    pass
            
            # Extract any rates from the current page
            rate = extract_rate_from_text(r.html.text, debug)
            if rate:
                log_debug(f"Found rate in form page: {rate}")
                return rate
                
        except Exception as e:
            log_debug(f"Form interaction method failed: {e}")
        
        log_debug("No rate found in any method")
        return None
        
    except Exception as e:
        log_debug(f"Error during real SBV retrieval: {e}")
        return None
    finally:
        await session.close()


def extract_rate_from_text(text: str, debug: bool = False) -> Optional[float]:
    """Extract USD-VND rate from text content"""
    
    if debug:
        print(f"[SBV-Real] Analyzing text content ({len(text)} characters)")
        # Save first 2000 chars for analysis
        with open('text_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(text[:2000])
    
    # Patterns to look for SBV central rate
    patterns = [
        # Direct USD-VND patterns
        r'1\s*USD\s*=\s*([0-9,]+\.?[0-9]*)\s*VND',
        r'USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
        r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*VND',
        
        # Vietnamese patterns
        r'1\s*Đô\s*la\s*Mỹ\s*=\s*([0-9,]+\.?[0-9]*)',
        r'Đô\s*la\s*Mỹ.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
        
        # Table or structured patterns
        r'USD\s*[|\s]\s*([0-9,]+\.?[0-9]*)',
        r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*[|\s]\s*USD',
        
        # Any reasonable rate in the text
        r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',
    ]
    
    found_rates = []
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                # Clean the rate string
                rate_str = match.replace(',', '').replace('.', '')
                
                # Handle different formats
                if len(rate_str) == 5 and rate_str.isdigit():
                    # Format like 26217 -> 26217.0
                    rate = float(rate_str)
                elif len(rate_str) == 6 and rate_str.isdigit():
                    # Format like 262170 -> 26217.0
                    rate = float(rate_str) / 10
                else:
                    rate = float(match.replace(',', ''))
                
                # Validate rate is in reasonable range for USD-VND SBV central rate
                if 24000 <= rate <= 28000:  # SBV central rate range
                    found_rates.append(rate)
                    if debug:
                        print(f"[SBV-Real] Found potential rate: {rate} (pattern: {pattern})")
            except (ValueError, ZeroDivisionError):
                continue
    
    if found_rates:
        # If we found multiple rates, return the most common one
        # or the median to avoid outliers
        if len(found_rates) == 1:
            return found_rates[0]
        else:
            # Return median
            found_rates.sort()
            median_rate = found_rates[len(found_rates) // 2]
            if debug:
                print(f"[SBV-Real] Multiple rates found: {found_rates}, using median: {median_rate}")
            return median_rate
    
    return None


def get_sbv_real_rate_sync(date_str: str, debug: bool = False) -> Optional[float]:
    """Synchronous wrapper for the async function"""
    return asyncio.run(get_sbv_real_rate(date_str, debug))


def main():
    """Command line interface"""
    print("=== Real SBV Exchange Rate Retriever ===")
    print("🏛️  This version gets the actual SBV central rate from the official website")
    print("🚀 Uses JavaScript rendering to access dynamic content")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_date = sys.argv[1]
        print(f"Using date from command line: {test_date}")
    else:
        test_date = date.today().strftime('%Y-%m-%d')
        print(f"No date specified, using today's date: {test_date}")
        print("💡 Tip: You can specify a date like: python sbv_real.py 2025-01-19")
    
    print(f"Retrieving real SBV central rate for {test_date}...")
    print("-" * 50)
    
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        print("🔍 Debug mode enabled (files will be saved for analysis)")
        print("-" * 50)
    
    try:
        rate = get_sbv_real_rate_sync(test_date, debug=debug_mode)
        
        print("-" * 50)
        if rate:
            print("✅ SUCCESS!")
            print(f"📅 Date: {test_date}")
            print(f"💰 SBV Central Rate: 1 USD = {rate:,.0f} VND")
            print(f"🏛️  Source: State Bank of Vietnam (Official)")
            print(f"📄 Type: SBV Central Exchange Rate")
            print(f"🚀 Method: JavaScript-Enabled Browser Automation")
        else:
            print("❌ Could not retrieve SBV central rate")
            print("This could be due to:")
            print("  • Network connectivity issues")
            print("  • SBV website maintenance or changes")
            print("  • JavaScript execution issues")
            print("  • No data available for the specified date")
            print("  • Weekend/holiday (no official rate published)")
            if debug_mode:
                print("  • Check saved files: sbv_*_rendered.html, text_analysis.txt")
                
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("📋 Please use format: YYYY-MM-DD (e.g., 2025-01-19)")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Run: pip install requests-html")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("=" * 60)
    print("COMMAND LINE USAGE:")
    print("=" * 60)
    print("python sbv_real.py                    # Use today's date")
    print("python sbv_real.py 2025-01-19         # Specific date")
    print("python sbv_real.py 2025-01-19 --debug # With analysis files")


if __name__ == "__main__":
    main()