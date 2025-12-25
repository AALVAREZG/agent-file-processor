# Claude Development Instructions

## Python Environment

This project uses a custom Python virtual environment located at `venv/`.

### Important: Always use the project's virtual environment

When running Python commands, tests, or the application, **always use the virtual environment's Python interpreter**:

```bash
# Windows
venv\Scripts\python.exe <command>

# Linux/Mac
venv/bin/python <command>
```

### Installing dependencies

```bash
# Windows
venv\Scripts\python.exe -m pip install -r requirements.txt

# Linux/Mac
venv/bin/python -m pip install -r requirements.txt
```

### Running the application

```bash
# Windows
venv\Scripts\python.exe main.py

# Linux/Mac
venv/bin/python main.py
```

## Project Structure

- `src/` - Source code
  - `gui/` - GUI components (CustomTkinter)
  - `models/` - Data models and configuration
  - `extractors/` - PDF extraction logic
  - `exporters/` - Export functionality
  - `utils/` - Utility functions and configuration management
- `main.py` - Application entry point
- `requirements.txt` - Python dependencies

## Configuration

The application stores user configuration in `~/.liquidacion-opaef/`:
- `grouping_config.json` - Grouping criteria configuration
- `appearance_config.json` - Font and appearance settings
- `extraction_config.json` - PDF table extraction parameters

## Key Features

1. **PDF Extraction**: Extracts liquidation data from PDF documents with configurable extraction strategies
2. **Grouped Visualization**: Customizable grouping by year, concept, and custom groups
3. **Configuration Management**: Persistent configuration across sessions
4. **Excel Export**: Export data to Excel format
5. **Two-Level Validation**: Document-level and per-year validation system

## Validation Architecture

The application implements a comprehensive validation system to ensure data integrity:

### Data Models

**Location**: `src/models/liquidation.py`

#### `ExerciseSummary` (lines 44-57)
Represents the "TOTAL EJERCICIO" row extracted from the PDF for a specific fiscal year.

```python
@dataclass
class ExerciseSummary:
    ejercicio: int  # Fiscal year
    voluntaria: Decimal
    ejecutiva: Decimal
    recargo: Decimal
    diputacion_voluntaria: Decimal
    diputacion_ejecutiva: Decimal
    diputacion_recargo: Decimal
    liquido: Decimal
    records: List[TributeRecord]  # Not populated during extraction
```

#### `ExerciseValidationResult` (lines 60-85)
Contains the comparison between calculated totals (from summing individual records) and documented totals (from ExerciseSummary).

```python
@dataclass
class ExerciseValidationResult:
    ejercicio: int
    is_valid: bool
    # Calculated values (sum of tribute records)
    calc_voluntaria: Decimal
    calc_ejecutiva: Decimal
    calc_recargo: Decimal
    ...
    # Documented values (from PDF's TOTAL EJERCICIO row)
    doc_voluntaria: Decimal
    doc_ejecutiva: Decimal
    doc_recargo: Decimal
    ...
    errors: List[str]  # Detailed error messages if validation fails
```

### Validation Methods

**Location**: `src/models/liquidation.py`

#### `validate_totals()` (lines 231-260)
**Document-level validation**
- Sums ALL tribute records across all years
- Compares against document totals (`total_voluntaria`, `total_ejecutiva`, etc.)
- Validates A LIQUIDAR formula: `total_liquido - deductions = a_liquidar`
- Returns: `List[str]` of error messages (empty if valid)

#### `validate_exercise_summaries()` (lines 262-342)
**Per-year validation** ⭐ NEW
- For each ExerciseSummary:
  1. Gets all tribute records for that year using `get_records_by_year()`
  2. Calculates sums for each column
  3. Compares calculated vs documented values
  4. Creates ExerciseValidationResult with detailed comparison
- Returns: `Dict[int, ExerciseValidationResult]` mapping year to validation result
- Tolerance: ±0.01€ (one cent) for rounding errors

#### `has_exercise_validation_errors` (property, lines 362-366)
Convenience property that returns `True` if ANY exercise has validation errors.

### GUI Display Implementation

**Location**: `src/gui/main_window.py`

#### Visual Indicators (lines 805-822)
The Cobros tab uses color-coded tags to display validation status:

```python
# Tag configurations
"year_subtotal_valid"  -> Green background (#E8F5E9) with green text (#2E7D32)
"validation_error"     -> Red background (#FFE6E6) with red text (#C62828)
"year_subtotal"        -> Gray background (default, for when validation not available)
```

#### Display Logic (lines 874-926)
For each year's data:

1. **Calculate year totals** from individual records
2. **Get validation result** from `validate_exercise_summaries()`
3. **Display "TOTAL EJERCICIO" row**:
   - If valid: Show with green background and ✓ checkmark
   - If invalid: Show with gray background (documented values from PDF)
4. **If validation failed**: Add red "CALCULADO" row showing calculated values for comparison

### How to Modify Validation Rules

#### Adding New Validations

1. **Add validation logic** to `LiquidationDocument.validate_exercise_summaries()`:
   ```python
   # Example: Add validation for a new field
   if abs(calc_new_field - summary.new_field) > tolerance:
       errors.append(f"New Field: calculado {calc_new_field} vs documentado {summary.new_field}")
       is_valid = False
   ```

2. **Update ExerciseValidationResult** dataclass to include new fields:
   ```python
   @dataclass
   class ExerciseValidationResult:
       # ... existing fields ...
       calc_new_field: Decimal
       doc_new_field: Decimal
   ```

3. **Update GUI display** in `_display_cobros()` to show new field in validation rows

#### Changing Tolerance

Modify the `tolerance` variable in both validation methods:
```python
tolerance = Decimal('0.05')  # Change from 0.01 to 0.05 euros
```

#### Customizing Visual Indicators

Edit tag configurations in `_display_cobros()`:
```python
self.cobros_table.tag_configure("year_subtotal_valid",
    background="#YOUR_COLOR",  # Change colors
    foreground="#YOUR_TEXT_COLOR",
    font=(font_family, font_size, "bold"))
```

### Testing Validation

**Location**: `tests/integration/test_summary.py` (existing test script)

The test script demonstrates:
- Loading a PDF
- Extracting data
- Running validation
- Displaying results

To add validation testing:
```python
# Get validation results
validation_results = doc.validate_exercise_summaries()

# Check specific year
if 2024 in validation_results:
    result = validation_results[2024]
    assert result.is_valid, f"Year 2024 validation failed: {result.errors}"
```

### Debugging Validation Issues

1. **Check extraction**: Use `scripts/debug_pdf_tables.py` to verify table structure
2. **Inspect ExerciseSummary**: Print `doc.exercise_summaries` to see what was extracted
3. **Check individual records**: Filter by year using `doc.get_records_by_year(2024)`
4. **Run validation**: Call `doc.validate_exercise_summaries()` and inspect errors
5. **Compare values**: Look at both `calc_*` and `doc_*` fields in validation result

### PDF Extraction Configuration

**Location**: `src/models/grouping_config.py` (PDFExtractionConfig)

The extraction strategy can affect validation results. Available configurations:
- `horizontal_strategy`: "lines" (default) or "lines_strict"
- Configurable via GUI sidebar under "Extracción PDF"
- Stored in `~/.liquidacion-opaef/extraction_config.json`

If validation consistently fails, try changing the extraction strategy to see if it improves table detection.
