# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Environment Setup:**
```bash
conda activate py310
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**Run Main Function:**
```bash
python sbv_exchange_rate_final.py
```

**Test with Debug:**
```bash
python -c "from sbv_exchange_rate_final import get_current_usd_vnd_rate; print(get_current_usd_vnd_rate(debug=True))"
```

## Architecture

This project retrieves USD-VND central exchange rates from Vietnamese financial institutions with multiple fallback sources:

### Core Components

1. **sbv_exchange_rate_final.py** - Main production-ready implementation
   - Multi-source retrieval strategy
   - Robust error handling and fallbacks
   - Support for SBV, Vietcombank, Dong A Bank, and international APIs

2. **Alternative Implementations:**
   - `sbv_exchange_rate.py` - Original SBV-only version
   - `sbv_exchange_rate_improved.py` - Enhanced parsing with better error handling
   - `sbv_exchange_rate_selenium.py` - JavaScript-capable version using Selenium

### Data Sources (Priority Order)

1. **State Bank of Vietnam (SBV)** - Official source, requires manual parsing due to JavaScript
2. **Vietcombank API** - Reliable XML API endpoint
3. **Dong A Bank API** - JSON API endpoint
4. **ExchangeRate-API** - International fallback service

### Key Design Patterns

- **Fallback Strategy**: Each source is tried in sequence until one succeeds
- **Graceful Degradation**: Functions return `None` rather than throwing exceptions
- **Debug Mode**: Detailed logging available for troubleshooting
- **Date Validation**: Strict date format validation with clear error messages

## Development Notes

- Use conda environment `py310` for consistent Python 3.10 environment
- The SBV website requires JavaScript, making direct scraping challenging
- Vietcombank XML API is the most reliable Vietnamese source
- Historical data retrieval is limited due to API constraints
- All functions handle network errors gracefully and provide fallbacks