"""Quick test script for per-year validation."""
import sys
import io
from pathlib import Path
from src.extractors.pdf_extractor import extract_liquidation_pdf

# Fix Windows encoding for stdout
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Extract PDF
pdf_path = Path('data/samples/026_2025_0016_00000623_CML.PDF')
print(f"Extracting: {pdf_path.name}\n")

doc = extract_liquidation_pdf(str(pdf_path))

# Basic stats
print("="*60)
print("EXTRACTION RESULTS")
print("="*60)
print(f"Total records extracted: {doc.total_records}")
print(f"Exercise summaries found: {len(doc.exercise_summaries)}")
print(f"Years in document: {sorted(set(r.ejercicio for r in doc.tribute_records))}\n")

# Show exercise summaries
if doc.exercise_summaries:
    print("\nExercise Summaries:")
    for summary in sorted(doc.exercise_summaries, key=lambda s: s.ejercicio):
        print(f"  Year {summary.ejercicio}: Liquido = {summary.liquido:,.2f}")
else:
    print("\nWARNING: No exercise summaries found!")
    print("Validation cannot run without exercise summaries.\n")
    sys.exit(0)

# Validate per year
print("\n" + "="*60)
print("PER-YEAR VALIDATION")
print("="*60)

results = doc.validate_exercise_summaries()

if not results:
    print("\nNo validation results - no exercise summaries were extracted")
    sys.exit(0)

all_valid = True
for year in sorted(results.keys()):
    result = results[year]
    status = "VALID   [OK]" if result.is_valid else "INVALID [!!]"
    print(f"\nYear {year}: {status}")

    if result.is_valid:
        print(f"  Calculated liquido: {result.calc_liquido:,.2f}")
        print(f"  Documented liquido: {result.doc_liquido:,.2f}")
    else:
        all_valid = False
        print(f"  Errors found: {len(result.errors)}")
        for i, err in enumerate(result.errors[:5], 1):
            print(f"    {i}. {err}")

        if len(result.errors) > 5:
            print(f"    ... and {len(result.errors) - 5} more errors")

print("\n" + "="*60)
if all_valid:
    print("[OK] ALL YEARS VALIDATED SUCCESSFULLY")
else:
    print("[!!] SOME YEARS HAVE VALIDATION ERRORS")
print("="*60)
