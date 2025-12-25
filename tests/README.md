# Tests

This directory contains all test files for the liquidacion-opaef project.

## Directory Structure

- **unit/** - Unit tests for individual components and functions
  - `test_extraction_direct.py` - Direct extraction unit tests
  - `test_page2.py` - Page 2 specific tests
  - `test_last_page.py` - Last page specific tests

- **integration/** - Integration tests with actual PDF files
  - `test_extraction.py` - Main extraction integration tests
  - `test_summary.py` - Summary extraction tests
  - `test_2025_extraction.py` - 2025 format extraction tests
  - `test_506_fix.py` - Specific fix verification for issue 506
  - `test_totals_debug.py` - Totals calculation debug tests

- **fixtures/** - Test data and fixtures
  - (Currently empty - can add sample PDFs or expected outputs here)

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run only unit tests:
```bash
pytest tests/unit/
```

Run only integration tests:
```bash
pytest tests/integration/
```

Run specific test file:
```bash
pytest tests/unit/test_extraction_direct.py
```
