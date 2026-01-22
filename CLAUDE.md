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
5. **HTML Grouped Export**: Professional HTML reports with print functionality ⭐ NEW
6. **Two-Level Validation**: Document-level and per-year validation system

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

## HTML Grouped Export Architecture ⭐ NEW

**Location**: `src/exporters/html_grouped_exporter.py`

The HTML grouped exporter generates standalone HTML reports with professional formatting and print functionality, designed for attaching to accounting documents by fiscal year.

### Core Components

#### 1. HTMLGroupedExporter Class

Main class responsible for generating HTML reports with grouping and formatting.

**Key Methods:**

- `export_grouped_concepts()` - Main export method that orchestrates the process
- `_organize_data()` - Organizes records according to grouping configuration
- `_organize_records()` - Groups records by concept and/or custom groups
- `_generate_html()` - Generates complete HTML document
- `_html_year_table()` - Generates table for each year with document header

#### 2. Code Compaction Algorithm

**Method**: `_compact_codes(codes: List[str]) -> str`

Intelligently compacts OPAEF codes for better readability.

**Algorithm:**

```python
# Input: List of codes
codes = [
    "026/2021/58/064/573",
    "026/2021/58/064/665",
    "026/2021/58/068/573",
    "2023/E/0000783",
    "2023/E/0000784"
]

# Processing:
1. Classify codes by pattern:
   - Five-part: "XXX/YYYY/ZZ/AAA/BBB" -> grouped by base (XXX/YYYY/ZZ)
   - E-codes: "YYYY/E/NNNNNNN" -> strip leading zeros

2. Group five-part codes:
   - Extract base: (026, 2021, 58)
   - Collect levels: {064, 068}
   - Collect suffixes: {573, 665}
   - Format: "026/2021/58/{064,068}/573,665"

3. Group E-codes:
   - Strip leading zeros: 0000783 -> 783
   - Sort numerically
   - Format: "2023/E/783,784"

# Output:
"026/2021/58/{064,068}/573,665 2023/E/783,784"
```

**Usage in Code:**
- Applied to both `clave_recaudacion` and `clave_contabilidad`
- Used in `_collect_unique_claves()` method
- Integrated into texto SICAL generation

#### 3. Partida Mapping System

**Dictionary**: `CORRESP_PARTIDAS` (class constant)

Maps OPAEF concept codes to local accounting partidas. Currently contains 44 mappings.

**Structure:**
```python
CORRESP_PARTIDAS = {
    'opaef_code': ['partida_local', 'description'],
    # Examples:
    '208': ['113', 'ibi urb'],      # IBI Urbana
    '501': ['115', 'ivtm'],          # IVTM
    '700': ['393', 'intereses'],     # Interest
}
```

**Method**: `_get_partidas_from_records(records: List[TributeRecord]) -> str`

Extracts unique partidas from a group of records.

**Process:**
1. For each record, extract concept code using `grouping_config.get_concept_code()`
2. Look up partida in `CORRESP_PARTIDAS`
3. Collect unique partidas in a set
4. Return sorted, comma-separated string

**Example Output:**
- Single partida: `"113"`
- Multiple partidas: `"10049, 300"`
- No mapping found: `"N/A"`

#### 4. Texto SICAL Generation

**Method**: `_build_texto_sical(ejercicio: int, group_name: str, records: List[TributeRecord]) -> str`

Generates the SICAL text for each group with enhanced format.

**Format:**
```
OPAEF. REGULARIZACION COBROS {ejercicio} - {group_name} LIQ. {num_liquidacion} MTO. PAGO {num_mandamiento} {compact_clave_rec} {compact_clave_cont}
```

**Example:**
```
OPAEF. REGULARIZACION COBROS 2024 - IBI_URBANA LIQ. 00000623 MTO. PAGO 2025/0016 026/2024/58/{064,068}/208 2024/E/783,784
```

**Key Features:**
- Includes fiscal year (ejercicio) at the beginning
- Includes group name for clarity
- Uses compacted codes for brevity
- Includes both recaudacion and contabilidad codes

### HTML Structure and Styling

#### Screen View

```html
<div class="container">
  <div class="header">
    <h1>Liquidación OPAEF - Agrupación por Conceptos</h1>
    <button class="print-btn">🖨️ Imprimir</button>
  </div>

  <div class="doc-info">
    <!-- Document information grid (6 items) -->
  </div>

  <div class="year-section">
    <div class="print-year-header" style="display:none">
      <!-- Document info for print - hidden on screen -->
    </div>
    <table class="year-table">
      <!-- Year data -->
    </table>
  </div>
</div>
```

#### Print View

**CSS Media Query**: `@media print`

**Key Changes:**
1. **Hide screen elements:**
   - Main header and doc-info: `display: none`
   - Print button: `display: none`
   - Copy buttons: `display: none`

2. **Show print elements:**
   - `.print-year-header`: `display: block !important`
   - Contains document info specific to each year

3. **Page breaks:**
   - Each `.year-section`: `page-break-before: always`
   - Forces each year to start on new page

4. **Color preservation:**
   - All colored elements: `print-color-adjust: exact`
   - Ensures headers, labels, and backgrounds print correctly

5. **Layout optimization:**
   - `@page { margin: 1.5cm; size: A4; }`
   - Reduced padding and font sizes
   - Optimized for A4 paper

#### Per-Year Print Headers

Each year section includes a hidden header (lines 831-859 in `_html_year_table()`):

```html
<div class="print-year-header">
  <h2>Liquidación OPAEF - Agrupación por Conceptos</h2>
  <div class="print-doc-grid">
    <div class="print-doc-item">
      <div class="print-doc-label">Entidad</div>
      <div class="print-doc-value">{entidad} ({codigo})</div>
    </div>
    <!-- ... 5 more items including year-specific ejercicio ... -->
  </div>
</div>
```

**Key Feature**: The `ejercicio` field shows the specific year being printed, not the document's general year.

### JavaScript Functionality

**Functions:**

1. **`copyToClipboard(text, buttonId)`**
   - Copies text to clipboard using Navigator API
   - Provides visual feedback (button changes to "Copiado")
   - 2-second timeout before reverting

2. **`printReport()`**
   - Triggers browser print dialog
   - Called by print button
   - Simple wrapper around `window.print()`

### Usage Example

```python
from src.exporters.html_grouped_exporter import export_grouped_to_html
from src.models.liquidation import LiquidationDocument
from src.models.grouping_config import GroupingConfig

# Load document and config
document = LiquidationDocument.from_pdf(pdf_path)
grouping_config = GroupingConfig.load()

# Export with grouping options
export_grouped_to_html(
    document=document,
    grouping_config=grouping_config,
    output_path="output/liquidacion_agrupado.html",
    group_by_year=True,
    group_by_concept=True,
    group_by_custom=False
)
```

### Modifying the Partida Mapping

To add or modify partida mappings:

1. **Edit the CORRESP_PARTIDAS dictionary** (lines 20-64):
```python
CORRESP_PARTIDAS = {
    # ... existing mappings ...
    '999': ['999', 'new concept'],  # Add new mapping
}
```

2. **No code changes needed** - the `_get_partidas_from_records()` method automatically uses the updated dictionary

3. **Consider adding to both:**
   - Source code: `src/exporters/html_grouped_exporter.py`
   - Documentation: README.md (partida mapping table)

### Customizing Print Layout

To modify print layout, edit the `@media print` CSS block (lines 410-543):

**Example: Change page margins**
```css
@page {
    margin: 2cm;  /* Change from 1.5cm */
    size: A4;
}
```

**Example: Modify header colors**
```css
.print-year-header h2 {
    background: #FF0000 !important;  /* Change from blue */
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}
```

### Best Practices

1. **Always test print preview** after HTML generation changes
2. **Use `print-color-adjust: exact`** for all elements that need color preservation
3. **Include both screen and print views** for better UX
4. **Validate HTML** before deploying to ensure browser compatibility
5. **Keep file self-contained** - no external CSS/JS dependencies
