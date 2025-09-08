#!/usr/bin/env python3
"""
Test Chrome/ChromeDriver setup
"""

import sys

def test_selenium_import():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        print("✅ Selenium import successful")
        return True
    except ImportError as e:
        print(f"❌ Selenium import failed: {e}")
        return False

def test_webdriver_manager():
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        print("✅ webdriver-manager import successful")
        return True
    except ImportError as e:
        print(f"❌ webdriver-manager import failed: {e}")
        return False

def test_chrome_setup():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        print("Testing Chrome setup...")
        
        # Setup options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Try webdriver-manager first
        try:
            print("Trying webdriver-manager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://www.google.com")
            print("✅ webdriver-manager setup successful")
            driver.quit()
            return True
        except Exception as e:
            print(f"⚠️ webdriver-manager failed: {e}")
            
        # Try system ChromeDriver
        try:
            print("Trying system ChromeDriver...")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://www.google.com")
            print("✅ System ChromeDriver setup successful")
            driver.quit()
            return True
        except Exception as e:
            print(f"❌ System ChromeDriver failed: {e}")
            
        return False
        
    except Exception as e:
        print(f"❌ Chrome setup test failed: {e}")
        return False

def main():
    print("=== Chrome/ChromeDriver Setup Test ===")
    print()
    
    # Test imports
    if not test_selenium_import():
        print("❌ Fix selenium installation first: pip install selenium")
        return
        
    if not test_webdriver_manager():
        print("❌ Fix webdriver-manager installation first: pip install webdriver-manager")
        return
    
    # Test Chrome setup
    if test_chrome_setup():
        print("\n🎉 Chrome setup is working! You can use the SBV script.")
    else:
        print("\n❌ Chrome setup failed. Try these solutions:")
        print("1. Install Chrome: sudo apt install google-chrome-stable")
        print("2. Install Chromium: sudo apt install chromium-browser")
        print("3. Install system ChromeDriver: sudo apt install chromium-chromedriver")
        print("4. Or try different Chrome options in the script")

if __name__ == "__main__":
    main()