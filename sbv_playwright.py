#!/usr/bin/env python3
"""
SBV Exchange Rate Retriever using Playwright

This version uses Playwright to properly interact with the SBV website,
following the exact process you described:
1. Load English SBV page
2. Select "Search by data tables"
3. Fill date fields (dd/mm/yyyy)
4. Click Search
5. Click View
6. Extract USD-VND rate

Playwright is more reliable than Selenium and handles modern JavaScript better.
"""

import sys
from datetime import datetime, date
from typing import Optional
import re
import asyncio

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


async def get_sbv_exchange_rate_playwright(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get USD-VND central exchange rate from State Bank of Vietnam English site using Playwright.
    
    This function follows the exact SBV English site workflow:
    1. Load https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx
    2. Select "Search by data tables"
    3. Enter target date in both from/to date fields (dd/mm/yyyy format)
    4. Click "Search" button
    5. Click "View" link in results
    6. Extract USD-VND rate (1 USD = xx,xxx VND)
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2025-01-19')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV-Playwright] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2025-01-19')")
    
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError("Playwright is required. Install with: pip install playwright && playwright install chromium")
    
    log_debug(f"Retrieving SBV exchange rate from English site for {date_str}")
    
    async with async_playwright() as playwright:
        try:
            # Launch browser
            log_debug("Launching Chromium browser...")
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create new page
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # Step 1: Load English SBV exchange rate page
            log_debug("Loading English SBV exchange rate page...")
            await page.goto("https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx", 
                          wait_until='networkidle', timeout=60000)
            
            # Wait for page to be fully loaded
            await page.wait_for_timeout(5000)
            log_debug("Page loaded successfully")
            
            # Take screenshot for debugging if needed
            if debug:
                await page.screenshot(path="sbv_page_loaded.png")
                log_debug("Screenshot saved: sbv_page_loaded.png")
            
            # Step 2: Look for and select "Search by data tables" option
            log_debug("Looking for 'Search by data tables' option...")
            
            # Try different selectors for the search by data tables radio button
            search_selectors = [
                'input[type="radio"][value*="table"]',
                'input[type="radio"][value*="data"]',
                'input[type="radio"]:nth-child(2)',  # Second radio button
                '[id*="table"][type="radio"]',
                '[id*="data"][type="radio"]'
            ]
            
            search_radio_found = False
            for selector in search_selectors:
                try:
                    radio_button = page.locator(selector).first
                    if await radio_button.count() > 0:
                        log_debug(f"Found search radio button with selector: {selector}")
                        await radio_button.click()
                        search_radio_found = True
                        await page.wait_for_timeout(2000)
                        break
                except Exception as e:
                    if debug:
                        log_debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not search_radio_found:
                log_debug("Could not find search by data tables option, continuing anyway...")
            
            # Step 3: Fill date fields
            log_debug("Looking for date input fields...")
            date_formatted = target_date.strftime('%d/%m/%Y')  # dd/mm/yyyy format
            
            # Try to find date input fields
            date_selectors = [
                'input[type="text"][placeholder*="date" i]',
                'input[type="text"][id*="date" i]',
                'input[type="text"][name*="date" i]',
                'input[type="date"]',
                'input.date-input',
                'input[id*="from"]',
                'input[id*="to"]'
            ]
            
            date_inputs = []
            for selector in date_selectors:
                try:
                    inputs = page.locator(selector)
                    count = await inputs.count()
                    for i in range(count):
                        date_inputs.append(inputs.nth(i))
                except:
                    continue
            
            if len(date_inputs) >= 2:
                log_debug(f"Found {len(date_inputs)} date input fields")
                
                # Fill from date
                await date_inputs[0].clear()
                await date_inputs[0].fill(date_formatted)
                
                # Fill to date (same date)
                await date_inputs[1].clear()
                await date_inputs[1].fill(date_formatted)
                
                log_debug(f"Entered dates: {date_formatted}")
                await page.wait_for_timeout(2000)
            else:
                log_debug("Could not find date input fields")
                # Try alternative approach - look for any text inputs
                all_inputs = page.locator('input[type="text"]')
                input_count = await all_inputs.count()
                log_debug(f"Found {input_count} text inputs total")
                
                if input_count >= 2:
                    # Fill first two text inputs assuming they are date fields
                    await all_inputs.nth(0).clear()
                    await all_inputs.nth(0).fill(date_formatted)
                    await all_inputs.nth(1).clear()
                    await all_inputs.nth(1).fill(date_formatted)
                    log_debug(f"Filled first two text inputs with: {date_formatted}")
                    await page.wait_for_timeout(2000)
            
            # Step 4: Click search button
            log_debug("Looking for search button...")
            search_button_selectors = [
                'input[type="submit"][value*="Search" i]',
                'button[type="submit"]',
                'input[value*="Search" i]',
                'button:has-text("Search")',
                'input[type="button"][value*="Search" i]',
                '[id*="search" i]',
                '[onclick*="search" i]'
            ]
            
            search_clicked = False
            for selector in search_button_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.count() > 0:
                        log_debug(f"Found search button with selector: {selector}")
                        await button.click()
                        search_clicked = True
                        await page.wait_for_timeout(5000)  # Wait for search results
                        break
                except Exception as e:
                    if debug:
                        log_debug(f"Search button selector {selector} failed: {e}")
                    continue
            
            if not search_clicked:
                log_debug("Could not find search button")
                return None
            
            # Take screenshot after search
            if debug:
                await page.screenshot(path="sbv_after_search.png")
                log_debug("Screenshot saved: sbv_after_search.png")
            
            # Step 5: Find and click "View" link
            log_debug("Looking for 'View' link in results...")
            view_selectors = [
                'a:has-text("View")',
                'a:has-text("view")',
                'button:has-text("View")',
                'input[value*="View" i]',
                '[onclick*="view" i]',
                'a[href*="view" i]'
            ]
            
            view_clicked = False
            for selector in view_selectors:
                try:
                    view_element = page.locator(selector).first
                    if await view_element.count() > 0:
                        log_debug(f"Found view link with selector: {selector}")
                        # Handle potential new page/popup
                        async with context.expect_page() as new_page_info:
                            await view_element.click()
                        
                        try:
                            new_page = await new_page_info.value
                            page = new_page  # Switch to new page
                            view_clicked = True
                            await page.wait_for_load_state('networkidle', timeout=30000)
                            break
                        except:
                            # If no new page, continue with current page
                            view_clicked = True
                            await page.wait_for_timeout(5000)
                            break
                except Exception as e:
                    if debug:
                        log_debug(f"View link selector {selector} failed: {e}")
                    continue
            
            if not view_clicked:
                log_debug("Could not find 'View' link")
                return None
            
            # Take screenshot of results page
            if debug:
                await page.screenshot(path="sbv_results_page.png")
                log_debug("Screenshot saved: sbv_results_page.png")
            
            # Step 6: Extract exchange rate
            log_debug("Extracting USD-VND rate from page...")
            
            try:
                # Get page content
                content = await page.content()
                text_content = await page.text_content('body')
                
                if debug:
                    with open('sbv_page_content.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    log_debug("Page content saved: sbv_page_content.html")
                
                # Look for USD-VND rate patterns in text
                if text_content:
                    usd_patterns = [
                        r'1\s*USD\s*=\s*([0-9,]+\.?[0-9]*)\s*VND',  # 1 USD = 23,977 VND
                        r'USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',  # USD followed by rate
                        r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*VND',  # Just rate with VND
                        r'1.*USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',  # 1 USD with rate
                        r'(\d{2}[,.]?\d{3}[,.]?\d{0,3})',  # Any 5-6 digit number (exchange rate range)
                    ]
                    
                    for pattern in usd_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        for match in matches:
                            try:
                                # Clean and convert rate
                                rate_str = match.replace(',', '').replace('.', '')
                                # Handle different formats
                                if len(rate_str) == 5 and rate_str.isdigit():
                                    # Format like 23977 -> 23.977
                                    rate = float(rate_str[:2] + '.' + rate_str[2:])
                                elif len(rate_str) == 6 and rate_str.isdigit():
                                    # Format like 239770 -> 23977.0
                                    rate = float(rate_str) / 10
                                else:
                                    rate = float(match.replace(',', ''))
                                
                                # Validate rate is in reasonable range for USD-VND
                                if 20000 <= rate <= 30000:
                                    log_debug(f"Found valid USD-VND rate: {rate}")
                                    return rate
                                elif debug:
                                    log_debug(f"Rate {rate} outside valid range")
                            except (ValueError, ZeroDivisionError):
                                continue
                
                # Also try to extract from table cells
                tables = page.locator('table')
                table_count = await tables.count()
                log_debug(f"Found {table_count} tables")
                
                for i in range(table_count):
                    table = tables.nth(i)
                    table_text = await table.text_content()
                    if table_text and ('USD' in table_text or 'VND' in table_text):
                        # Extract numbers from table
                        numbers = re.findall(r'([0-9,]+\.?[0-9]*)', table_text)
                        for num_str in numbers:
                            try:
                                rate = float(num_str.replace(',', ''))
                                if 20000 <= rate <= 30000:
                                    log_debug(f"Found rate in table: {rate}")
                                    return rate
                            except ValueError:
                                continue
                
                log_debug("Could not extract valid exchange rate from page")
                return None
                
            except Exception as e:
                log_debug(f"Error extracting rate: {e}")
                return None
            
        except Exception as e:
            log_debug(f"Error during Playwright scraping: {e}")
            return None
        finally:
            try:
                await browser.close()
            except:
                pass


def get_sbv_exchange_rate_sync(date_str: str, debug: bool = False) -> Optional[float]:
    """Synchronous wrapper for the async Playwright function"""
    return asyncio.run(get_sbv_exchange_rate_playwright(date_str, debug))


def main():
    """Command line interface"""
    print("=== SBV Exchange Rate Retriever (Playwright Version) ===")
    print("🎭 This version uses Playwright for reliable browser automation")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_date = sys.argv[1]
        print(f"Using date from command line: {test_date}")
    else:
        test_date = date.today().strftime('%Y-%m-%d')
        print(f"No date specified, using today's date: {test_date}")
        print("💡 Tip: You can specify a date like: python sbv_playwright.py 2025-01-19")
    
    print(f"Retrieving exchange rate for {test_date} using Playwright...")
    print("-" * 50)
    
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        print("🔍 Debug mode enabled (screenshots and logs will be saved)")
        print("-" * 50)
    
    try:
        rate = get_sbv_exchange_rate_sync(test_date, debug=debug_mode)
        
        print("-" * 50)
        if rate:
            print("✅ SUCCESS!")
            print(f"📅 Date: {test_date}")
            print(f"💰 Rate: 1 USD = {rate:,.3f} VND")
            print(f"🏛️  Source: State Bank of Vietnam (Official English Site)")
            print(f"📄 Type: Central Exchange Rate")
            print(f"🎭 Method: Playwright Browser Automation")
        else:
            print("❌ Could not retrieve exchange rate")
            print("This could be due to:")
            print("  • Network connectivity issues")
            print("  • SBV website maintenance or changes")
            print("  • No data available for the specified date")
            print("  • Weekend/holiday (no trading)")
            if debug_mode:
                print("  • Check screenshots: sbv_*.png and sbv_page_content.html")
                
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("📋 Please use format: YYYY-MM-DD (e.g., 2025-01-19)")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Run: pip install playwright && playwright install chromium")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("=" * 60)
    print("COMMAND LINE USAGE:")
    print("=" * 60)
    print("python sbv_playwright.py                    # Use today's date")
    print("python sbv_playwright.py 2025-01-19         # Specific date")
    print("python sbv_playwright.py 2025-01-19 --debug # With screenshots & logs")
    print("python sbv_playwright.py 2025-01-19 -d      # With debug (short)")


if __name__ == "__main__":
    main()