# SBV USD-VND Exchange Rate Retriever

A Python library to retrieve official central exchange rates (tỷ giá trung tâm) for USD-VND currency pair directly from the State Bank of Vietnam (SBV).

## Features

- **Official SBV data**: Retrieves rates directly from State Bank of Vietnam website
- **Multiple sources**: Support for both Vietnamese and English SBV interfaces
- **Historical rates**: Get exchange rates for specific dates
- **Automated workflow**: Follows the complete SBV search process automatically
- **Robust extraction**: Uses multiple methods to extract rates from SBV pages
- **Auto ChromeDriver**: Automatic ChromeDriver installation and management
- **Debug mode**: Detailed logging for troubleshooting

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/retrieve_central_exchange_rate_USD_VND_SBV.git
   cd retrieve_central_exchange_rate_USD_VND_SBV
   ```

2. **Create and activate conda environment:**
   ```bash
   conda create -n py310 python=3.10 -y
   conda activate py310
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Get Exchange Rate from English SBV Site (Recommended)

```python
from sbv_exchange_rate_retriever import get_sbv_exchange_rate_english

# Get exchange rate for a specific date from English SBV interface
rate = get_sbv_exchange_rate_english('2023-09-01')

if rate:
    print(f"USD-VND rate on 2023-09-01: {rate} VND")
    # Example output: USD-VND rate on 2023-09-01: 23.977 VND
else:
    print("Exchange rate not available for this date")
```

### Get Exchange Rate from Vietnamese SBV Site

```python
from sbv_exchange_rate_retriever import get_sbv_exchange_rate

# Get exchange rate for a specific date from Vietnamese SBV interface
rate = get_sbv_exchange_rate('2023-09-01')

if rate:
    print(f"USD-VND rate on 2023-09-01: {rate} VND")
else:
    print("Exchange rate not available for this date")
```

### Enable Debug Mode

```python
from sbv_exchange_rate_retriever import get_sbv_exchange_rate_english

# Get exchange rate with detailed logging
rate = get_sbv_exchange_rate_english('2023-09-01', debug=True)

if rate:
    print(f"SBV official rate: {rate} VND per USD")
```

## Running the Example

Execute the main script to test the functionality:

```bash
conda activate py310
python sbv_exchange_rate_retriever.py
```

This will:
- Test exchange rate retrieval for September 1, 2023
- Show the complete SBV search workflow
- Display the official central exchange rate

## Data Source

The library retrieves exchange rates directly from:

**State Bank of Vietnam (SBV)** - Official central bank rates:
- English interface: https://dttktt.sbv.gov.vn/TyGia/faces/Aiber.jspx (Recommended)
- Vietnamese interface: https://dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx

## API Reference

### Functions

#### `get_sbv_exchange_rate_english(date_str, debug=False)` (Recommended)
Get USD-VND central exchange rate from State Bank of Vietnam English interface for a specific date.

**Parameters:**
- `date_str` (str): Date in format 'YYYY-MM-DD' (e.g., '2023-09-01')
- `debug` (bool): Enable debug output for troubleshooting

**Returns:**
- `float`: Official SBV central exchange rate (VND per USD) or `None` if not found

**Raises:**
- `ValueError`: If date format is invalid
- `ImportError`: If Selenium is not installed

**Example:**
```python
rate = get_sbv_exchange_rate_english('2023-09-01')
if rate:
    print(f"SBV rate: {rate} VND per USD")
```

#### `get_sbv_exchange_rate(date_str, debug=False)`
Get USD-VND central exchange rate from State Bank of Vietnam Vietnamese interface for a specific date.

**Parameters:**
- `date_str` (str): Date in format 'YYYY-MM-DD' (e.g., '2023-09-01')
- `debug` (bool): Enable debug output for troubleshooting

**Returns:**
- `float`: Official SBV central exchange rate (VND per USD) or `None` if not found

**Raises:**
- `ValueError`: If date format is invalid
- `ImportError`: If Selenium is not installed

**Example:**
```python
rate = get_sbv_exchange_rate('2023-09-01')
if rate:
    print(f"SBV rate: {rate} VND per USD")
```

## Example Output

```
=== SBV (State Bank of Vietnam) Exchange Rate Retriever ===

Retrieving SBV exchange rate for 2023-09-01...
--------------------------------------------------
[SBV] Retrieving SBV exchange rate for 2023-09-01
[SBV] Setting up Chrome WebDriver...
[SBV] Loading SBV central rate page...
[SBV] Verifying search form...
[SBV] Filling date fields...
[SBV] Entered dates: 01/09/2023
[SBV] Clicking search button...
[SBV] Finding 'Xem' link in results...
[SBV] Clicking 'Xem' link...
[SBV] Extracting USD-VND rate from detailed page...
[SBV] Successfully extracted rate: 23.977
--------------------------------------------------
✅ SUCCESS!
📅 Date: 2023-09-01
💰 Rate: 1 USD = 23.977 VND
🏛️  Source: State Bank of Vietnam (Official)
📄 Type: Central Exchange Rate (Tỷ giá trung tâm)
```

## How It Works

The library follows the complete SBV search workflow:

1. **Load SBV Page**: Access the official central exchange rate page
2. **Select Search Mode**: Choose "Tìm kiếm theo bảng số liệu" (Search by data table)
3. **Enter Date**: Fill both "From" and "To" date fields with target date
4. **Execute Search**: Click "Tìm kiếm" (Search) button
5. **Access Results**: Click "Xem" (View) link in the results table
6. **Extract Rate**: Parse the official exchange rate from the detailed page

## Error Handling

The library handles various error conditions gracefully:

- **Network connectivity issues**: Proper timeout and retry handling
- **Website structure changes**: Multiple extraction methods as fallbacks
- **Invalid dates**: Validates date format and provides clear error messages
- **Missing dependencies**: Clear instructions for installing required packages
- **Rate not available**: Returns `None` instead of crashing

## Requirements

- **Python 3.7+**
- **Chrome browser** (automatically detected by webdriver-manager)
- **Python packages**: selenium, beautifulsoup4, requests, webdriver-manager (ChromeDriver auto-installed)

## Project Structure

```
retrieve_central_exchange_rate_USD_VND_SBV/
├── sbv_exchange_rate_retriever.py      # Main implementation
├── requirements.txt                    # Python dependencies
├── README.md                          # This documentation
├── LICENSE                            # Apache 2.0 License
└── CLAUDE.md                          # Development notes
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **"Could not retrieve exchange rate"**
   - Check internet connection
   - Try with `debug=True` to see detailed error messages
   - Verify that at least one data source is accessible

2. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Activate the correct conda environment

3. **Selenium version (if using)**
   - Install ChromeDriver if using the Selenium version
   - Ensure Chrome browser is installed

### Debug Mode

Enable debug mode to see detailed information about the retrieval process:

```python
rate = get_current_usd_vnd_rate(debug=True)
```

This will show:
- Which data sources are being tried
- HTTP response codes
- Parsing attempts and results
- Error messages from each source

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for informational purposes only. Exchange rates may vary between sources and should be verified with official financial institutions for trading or business decisions.