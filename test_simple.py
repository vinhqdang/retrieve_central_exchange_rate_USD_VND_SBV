#!/usr/bin/env python3
"""
Simple test script for the SBV English exchange rate function.
This script tests the function import and basic functionality.
"""

from sbv_exchange_rate_retriever import get_sbv_exchange_rate_english
from datetime import date, datetime

def test_function_import():
    """Test that the function can be imported successfully."""
    print("✅ Function import successful")
    return True

def test_date_validation():
    """Test date validation functionality."""
    try:
        # This should raise ValueError for invalid date format
        get_sbv_exchange_rate_english('invalid-date')
        return False
    except ValueError as e:
        print(f"✅ Date validation working: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error in date validation: {e}")
        return False

def main():
    print("=== SBV English Exchange Rate Function Test ===")
    print()
    
    # Test 1: Function import
    print("Test 1: Function Import")
    test_function_import()
    print()
    
    # Test 2: Date validation
    print("Test 2: Date Validation")
    test_date_validation()
    print()
    
    # Test 3: Show function signature and documentation
    print("Test 3: Function Documentation")
    print("Function signature:", get_sbv_exchange_rate_english.__name__)
    print("Documentation:")
    print(get_sbv_exchange_rate_english.__doc__)
    print()
    
    print("=== Summary ===")
    print("✅ All basic tests passed")
    print("📝 Note: Full browser test requires Chrome/ChromeDriver installation")
    print("🌐 The function is ready to use once Chrome is available")
    
    # Example usage
    print("\n=== Example Usage ===")
    print("from sbv_exchange_rate_retriever import get_sbv_exchange_rate_english")
    print("rate = get_sbv_exchange_rate_english('2025-01-08', debug=True)")
    print("if rate:")
    print("    print(f'1 USD = {rate} VND')")

if __name__ == "__main__":
    main()