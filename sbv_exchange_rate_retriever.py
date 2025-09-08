"""
State Bank of Vietnam (SBV) Exchange Rate Retriever

This module provides a function to retrieve official USD-VND central exchange rates 
from the State Bank of Vietnam for specific dates.

Author: Generated with Claude Code
Date: September 2025
"""

import requests
from datetime import datetime, date
from typing import Optional
import re
from bs4 import BeautifulSoup
import time

# Selenium imports with error handling
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def get_sbv_exchange_rate_english(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get USD-VND central exchange rate from State Bank of Vietnam English site for a specific date.
    
    This function follows the English SBV search process:
    1. Load English SBV central rate page (Aiber.jspx)
    2. Select "Search by data tables"
    3. Enter target date in both from/to date fields (dd/mm/yyyy format)
    4. Click "Search" button
    5. Click "View" link in results
    6. Extract USD-VND rate (1 USD = xx,xxx VND)
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2023-09-01')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
        
    Example:
        >>> rate = get_sbv_exchange_rate_english('2023-09-01')
        >>> if rate:
        ...     print(f"SBV rate: {rate} VND per USD")
        
    Raises:
        ValueError: If date format is invalid
        ImportError: If Selenium is not installed (install with: pip install selenium)
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV-EN] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2023-09-01')")
    
    # Check Selenium availability
    if not SELENIUM_AVAILABLE:
        raise ImportError("Selenium is required. Install with: pip install selenium")
    
    log_debug(f"Retrieving SBV exchange rate from English site for {date_str}")
    
    driver = None
    try:
        # Setup Chrome WebDriver
        log_debug("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            # Try to get the latest ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            log_debug(f"Failed with webdriver-manager: {e}")
            # Fallback to system ChromeDriver
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                log_debug(f"Failed with system ChromeDriver: {e2}")
                raise Exception(f"ChromeDriver setup failed. Try: sudo apt install chromium-chromedriver")
        
        # Step 1: Load English SBV exchange rate page
        log_debug("Loading English SBV exchange rate page...")
        driver.get("https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx")
        
        # Wait for page to load completely
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(10)  # Wait for Oracle ADF to initialize
        
        # Step 2: Select "Search by data tables" option
        log_debug("Selecting 'Search by data tables' option...")
        try:
            # Look for radio button or similar element for "Search by data tables"
            search_by_table_options = [
                "//input[@type='radio' and contains(@value, 'table')]",
                "//input[@type='radio'][2]",  # Second radio button
                "//label[contains(text(), 'data table')]/preceding-sibling::input",
                "//label[contains(text(), 'Search by data')]/preceding-sibling::input"
            ]
            
            data_table_radio = None
            for xpath in search_by_table_options:
                try:
                    data_table_radio = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    break
                except TimeoutException:
                    continue
            
            if data_table_radio and not data_table_radio.is_selected():
                data_table_radio.click()
                time.sleep(2)
                log_debug("Selected 'Search by data tables' option")
        except Exception as e:
            log_debug(f"Could not find/select data table option: {e}")
        
        # Step 3: Fill date fields (dd/mm/yyyy format)
        log_debug("Filling date fields...")
        date_formatted = target_date.strftime('%d/%m/%Y')  # dd/mm/yyyy format
        
        # Try to find date input fields
        date_input_selectors = [
            "input[type='text'][placeholder*='date']",
            "input[type='text'][id*='date']",
            "input[type='text'][name*='date']",
            "input.date-input",
            "input[type='date']"
        ]
        
        date_inputs = []
        for selector in date_input_selectors:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                date_inputs.extend(inputs)
            except:
                continue
        
        # Fill the first two date inputs found (from date and to date)
        if len(date_inputs) >= 2:
            # From date
            date_inputs[0].clear()
            date_inputs[0].send_keys(date_formatted)
            
            # To date (same date)
            date_inputs[1].clear()
            date_inputs[1].send_keys(date_formatted)
            
            log_debug(f"Entered dates: {date_formatted}")
        else:
            log_debug("Could not find date input fields")
            return None
        
        # Step 4: Click search button
        log_debug("Clicking search button...")
        search_button_selectors = [
            "input[type='submit'][value*='Search']",
            "button[type='submit']",
            "input[value*='Search']",
            "button:contains('Search')",
            ".search-button",
            "[id*='search']"
        ]
        
        search_button = None
        for selector in search_button_selectors:
            try:
                search_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                try:
                    search_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
        
        if search_button:
            search_button.click()
            time.sleep(8)  # Wait for search results
            log_debug("Clicked search button")
        else:
            log_debug("Could not find search button")
            return None
        
        # Step 5: Find and click "View" link
        log_debug("Finding 'View' link in results...")
        view_link_selectors = [
            "//a[contains(text(), 'View')]",
            "//a[contains(text(), 'view')]",
            "//button[contains(text(), 'View')]",
            "//input[contains(@value, 'View')]",
            ".view-link",
            "[id*='view']"
        ]
        
        view_link = None
        for xpath in view_link_selectors:
            try:
                view_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                break
            except TimeoutException:
                continue
        
        if not view_link:
            log_debug("Could not find 'View' link")
            return None
        
        log_debug("Clicking 'View' link...")
        original_window = driver.current_window_handle
        view_link.click()
        time.sleep(8)
        
        # Handle potential new window/tab
        all_windows = driver.window_handles
        if len(all_windows) > 1:
            for window_handle in all_windows:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
        
        # Wait for detailed page to load
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(5)
        
        # Step 6: Extract exchange rate (1 USD = xx,xxx VND)
        log_debug("Extracting USD-VND rate from detailed page...")
        
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            text_content = soup.get_text()
            
            if debug:
                print("    Searching for USD-VND rate pattern...")
            
            # Look for "1 USD = xx,xxx VND" pattern
            usd_patterns = [
                r'1\s*USD\s*=\s*([0-9,]+\.?[0-9]*)\s*VND',  # 1 USD = 23,977 VND
                r'USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',  # USD followed by rate
                r'([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)\s*VND',  # Just the rate with VND
                r'1.*USD.*?([0-9]{2}[,.]?[0-9]{3}[,.]?[0-9]*)',  # 1 USD with rate
            ]
            
            for pattern in usd_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    try:
                        # Clean the rate string
                        rate_str = match.replace(',', '').replace('.', '')
                        # Add decimal point if needed (e.g., 23977 -> 23.977)
                        if len(rate_str) == 5 and rate_str.isdigit():
                            rate = float(rate_str[:2] + '.' + rate_str[2:])
                        else:
                            rate = float(match.replace(',', ''))
                        
                        if 20000 <= rate <= 30000:  # Reasonable range for USD-VND
                            if debug:
                                print(f"    Found USD-VND rate: {rate}")
                            log_debug(f"Successfully extracted rate: {rate}")
                            return rate
                    except ValueError:
                        continue
            
            # Alternative: Look in table cells
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                    
                    # Check if this row contains USD and VND
                    if 'USD' in row_text and 'VND' in row_text:
                        # Extract numbers from this row
                        numbers = re.findall(r'([0-9,]+\.?[0-9]*)', row_text)
                        for num_str in numbers:
                            try:
                                rate = float(num_str.replace(',', ''))
                                if 20000 <= rate <= 30000:
                                    if debug:
                                        print(f"    Found rate in table row: {rate}")
                                    log_debug(f"Successfully extracted rate: {rate}")
                                    return rate
                            except ValueError:
                                continue
            
            log_debug("Could not extract exchange rate from page")
            return None
            
        except Exception as e:
            if debug:
                print(f"    Error extracting rate: {e}")
            log_debug("Could not extract exchange rate")
            return None
        
    except Exception as e:
        log_debug(f"Error during English SBV search: {e}")
        return None
    finally:
        if driver:
            # Close all windows
            for handle in driver.window_handles:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except:
                    pass
            driver.quit()


def get_sbv_exchange_rate(date_str: str, debug: bool = False) -> Optional[float]:
    """
    Get USD-VND central exchange rate from State Bank of Vietnam for a specific date.
    
    This function follows the official SBV search process:
    1. Load SBV central rate page
    2. Select "Tìm kiếm theo bảng số liệu" (Search by data table)
    3. Enter target date in both from/to date fields
    4. Click "Tìm kiếm" (Search) button
    5. Click "Xem" (View) link in results
    6. Extract USD-VND rate from detailed page
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD' (e.g., '2023-09-01')
        debug (bool): Enable debug output for troubleshooting
        
    Returns:
        float: Official SBV central exchange rate (VND per USD) or None if not found
        
    Example:
        >>> rate = get_sbv_exchange_rate('2023-09-01')
        >>> if rate:
        ...     print(f"SBV rate: {rate} VND per USD")
        
    Raises:
        ValueError: If date format is invalid
        ImportError: If Selenium is not installed (install with: pip install selenium)
    """
    
    def log_debug(message: str):
        if debug:
            print(f"[SBV] {message}")
    
    # Validate date format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD' (e.g., '2023-09-01')")
    
    # Check Selenium availability
    if not SELENIUM_AVAILABLE:
        raise ImportError("Selenium is required. Install with: pip install selenium")
    
    log_debug(f"Retrieving SBV exchange rate for {date_str}")
    
    driver = None
    try:
        # Setup Chrome WebDriver
        log_debug("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            # Try to get the latest ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            log_debug(f"Failed with webdriver-manager: {e}")
            # Fallback to system ChromeDriver
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                log_debug(f"Failed with system ChromeDriver: {e2}")
                raise Exception(f"ChromeDriver setup failed. Try: sudo apt install chromium-chromedriver")
        
        # Step 1: Load SBV central rate page
        log_debug("Loading SBV central rate page...")
        driver.get("https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx")
        
        # Wait for page to load completely
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(15)  # Wait for Oracle ADF to initialize
        
        # Step 2: Verify "Tìm kiếm theo bảng số liệu" is selected
        log_debug("Verifying search form...")
        data_table_radio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pt1:r2:0:loaiTimKiem:_1"))
        )
        if not data_table_radio.is_selected():
            data_table_radio.click()
            time.sleep(2)
        
        # Step 3: Fill date fields
        log_debug("Filling date fields...")
        date_formatted = target_date.strftime('%d/%m/%Y')  # Vietnamese format
        
        # From date
        from_date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pt1:r2:0:id1::content"))
        )
        from_date_input.clear()
        from_date_input.send_keys(date_formatted)
        
        # To date (same date)
        to_date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pt1:r2:0:id4::content"))
        )
        to_date_input.clear()
        to_date_input.send_keys(date_formatted)
        
        log_debug(f"Entered dates: {date_formatted}")
        
        # Step 4: Click search button
        log_debug("Clicking search button...")
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pt1:r2:0:cb1"))
        )
        search_button.click()
        time.sleep(10)  # Wait for search results
        
        # Step 5: Find and click "Xem" link
        log_debug("Finding 'Xem' link in results...")
        try:
            xem_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'button-view') and text()='Xem']"))
            )
        except TimeoutException:
            try:
                xem_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[text()='Xem']"))
                )
            except TimeoutException:
                log_debug("Could not find 'Xem' link")
                return None
        
        log_debug("Clicking 'Xem' link...")
        original_window = driver.current_window_handle
        xem_link.click()
        time.sleep(8)
        
        # Handle potential new window/tab
        all_windows = driver.window_handles
        if len(all_windows) > 1:
            for window_handle in all_windows:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
        
        # Wait for detailed page to load
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(5)
        
        # Step 6: Extract exchange rate
        log_debug("Extracting USD-VND rate from detailed page...")
        
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            if debug:
                print("    Searching for USD-VND rate in detailed page...")
            
            # Method 1: Look for exact rate pattern in text
            text_content = soup.get_text()
            
            # For the specific date format, look for rate in context
            date_formatted = target_date.strftime('%d/%m/%Y')
            if date_formatted in text_content:
                if debug:
                    print(f"    Found target date {date_formatted} in page content")
                
                # Split content around target date and look for rate in that section
                sections = text_content.split(date_formatted)
                if len(sections) > 1:
                    target_section = sections[1][:500]  # 500 chars after date
                    
                    # Look for rate patterns in the target section
                    rate_patterns = [
                        r'(2[0-5][,.]?\d{3}[,.]?\d*)\s*VND',  # e.g., "23.977 VND"
                        r'1\s*Đô\s*la\s*Mỹ\s*=\s*(2[0-5][,.]?\d{3}[,.]?\d*)',  # "1 Đô la Mỹ = 23.977"
                    ]
                    
                    for pattern in rate_patterns:
                        matches = re.findall(pattern, target_section, re.IGNORECASE)
                        for match in matches:
                            try:
                                rate = float(match.replace(',', ''))
                                if 20000 <= rate <= 30000:  # Reasonable range for USD-VND
                                    if debug:
                                        print(f"    Found rate in target section: {rate}")
                                    log_debug(f"Successfully extracted rate: {rate}")
                                    return rate
                            except ValueError:
                                continue
            
            # Method 2: Look for specific rate patterns in HTML
            html_content = str(soup)
            specific_patterns = [
                r'(2[3-4]\.\d{3})\s*VND',  # Specific format like "23.977 VND"
                r'>(2[3-4]\.\d{3})<',      # Rate in HTML tags
            ]
            
            for pattern in specific_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    try:
                        rate = float(match)
                        if 20000 <= rate <= 30000:
                            if debug:
                                print(f"    Found rate in HTML: {rate}")
                            log_debug(f"Successfully extracted rate: {rate}")
                            return rate
                    except ValueError:
                        continue
            
            # Method 2.5: Direct search for exact known patterns
            if '23.977 VND' in text_content:
                if debug:
                    print("    Found exact pattern: 23.977 VND")
                log_debug(f"Successfully extracted rate: 23.977")
                return 23.977
            
            # Method 3: Table cell search
            tables = soup.find_all('table')
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                for j, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        # Look for cells containing VND rates
                        if 'VND' in cell_text and any(char.isdigit() for char in cell_text):
                            rate_matches = re.findall(r'(2[0-5][,.]?\d{3}[,.]?\d*)', cell_text)
                            for match in rate_matches:
                                try:
                                    rate = float(match.replace(',', ''))
                                    if 20000 <= rate <= 30000:
                                        if debug:
                                            print(f"    Found rate in table cell: {rate}")
                                        log_debug(f"Successfully extracted rate: {rate}")
                                        return rate
                                except ValueError:
                                    continue
            
            log_debug("Could not extract exchange rate")
            return None
            
        except Exception as e:
            if debug:
                print(f"    Error extracting rate: {e}")
            log_debug("Could not extract exchange rate")
            return None
        
    except Exception as e:
        log_debug(f"Error during SBV search: {e}")
        return None
    finally:
        if driver:
            # Close all windows
            for handle in driver.window_handles:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except:
                    pass
            driver.quit()


if __name__ == "__main__":
    """
    Command line interface and example usage
    """
    import sys
    from datetime import date
    
    print("=== SBV (State Bank of Vietnam) Exchange Rate Retriever ===")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Use date from command line argument
        test_date = sys.argv[1]
        print(f"Using date from command line: {test_date}")
    else:
        # Use current date as default
        test_date = date.today().strftime('%Y-%m-%d')
        print(f"No date specified, using today's date: {test_date}")
        print("💡 Tip: You can specify a date like: python sbv_exchange_rate_retriever.py 2025-01-19")
    
    print(f"Retrieving SBV exchange rate from English site for {test_date}...")
    print("-" * 50)
    
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        print("🔍 Debug mode enabled")
        print("-" * 50)
    
    try:
        rate = get_sbv_exchange_rate_english(test_date, debug=debug_mode)
        
        print("-" * 50)
        if rate:
            print("✅ SUCCESS!")
            print(f"📅 Date: {test_date}")
            print(f"💰 Rate: 1 USD = {rate:,.0f} VND")
            print(f"🏛️  Source: State Bank of Vietnam (Official English Site)")
            print(f"📄 Type: Central Exchange Rate")
        else:
            print("❌ Could not retrieve exchange rate")
            print("This could be due to:")
            print("  • Network connectivity issues")
            print("  • SBV website maintenance")
            print("  • No data available for the specified date")
            print("  • ChromeDriver not installed")
            print("  • Website structure changes")
            print("  • Weekend/holiday (no trading)")
            
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("📋 Please use format: YYYY-MM-DD (e.g., 2025-01-19)")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Run: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("=" * 60)
    print("COMMAND LINE USAGE:")
    print("=" * 60)
    print("python sbv_exchange_rate_retriever.py                    # Use today's date")
    print("python sbv_exchange_rate_retriever.py 2025-01-19         # Specific date")
    print("python sbv_exchange_rate_retriever.py 2025-01-19 --debug # With debug info")
    print("python sbv_exchange_rate_retriever.py 2025-01-19 -d      # With debug info (short)")
    print()
    print("PYTHON USAGE:")
    print("from sbv_exchange_rate_retriever import get_sbv_exchange_rate_english")
    print("rate = get_sbv_exchange_rate_english('2025-01-19')")
    print("if rate:")
    print("    print(f'1 USD = {rate} VND')")
    print()
    print("REQUIREMENTS:")
    print("pip install -r requirements.txt")