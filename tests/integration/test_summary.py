"""Test script to verify summary calculations."""
from src.extractors.pdf_extractor import extract_liquidation_pdf
from decimal import Decimal

# Test with the multi-page PDF
pdf_path = "026_2025_0016_00000623_CML.PDF"

print(f"Testing: {pdf_path}")
print("=" * 80)

# Extract document
doc = extract_liquidation_pdf(pdf_path)

print(f"\nTotal records: {doc.total_records}")
print(f"\nDocument totals (from PDF):")
print(f"  Total Voluntaria: {doc.total_voluntaria:,.2f}")
print(f"  Total Ejecutiva: {doc.total_ejecutiva:,.2f}")
print(f"  Total Recargo: {doc.total_recargo:,.2f}")
print(f"  Total Líquido: {doc.total_liquido:,.2f}")

# Calculate totals from records
calc_voluntaria = sum(r.voluntaria for r in doc.tribute_records)
calc_ejecutiva = sum(r.ejecutiva for r in doc.tribute_records)
calc_recargo = sum(r.recargo for r in doc.tribute_records)
calc_liquido = sum(r.liquido for r in doc.tribute_records)

print(f"\nCalculated totals (from summing records):")
print(f"  Total Voluntaria: {calc_voluntaria:,.2f}")
print(f"  Total Ejecutiva: {calc_ejecutiva:,.2f}")
print(f"  Total Recargo: {calc_recargo:,.2f}")
print(f"  Total Líquido: {calc_liquido:,.2f}")

# Show difference
print(f"\nDifference (PDF - Calculated):")
print(f"  Voluntaria: {doc.total_voluntaria - calc_voluntaria:,.2f}")
print(f"  Ejecutiva: {doc.total_ejecutiva - calc_ejecutiva:,.2f}")
print(f"  Recargo: {doc.total_recargo - calc_recargo:,.2f}")
print(f"  Líquido: {doc.total_liquido - calc_liquido:,.2f}")

# Group by year and show summary
print(f"\n{'='*80}")
print("SUMMARY BY YEAR:")
print(f"{'='*80}")

exercises = {}
for record in doc.tribute_records:
    if record.ejercicio not in exercises:
        exercises[record.ejercicio] = []
    exercises[record.ejercicio].append(record)

print(f"\n{'Year':<8} {'Count':<8} {'Voluntaria':>15} {'Ejecutiva':>15} {'Recargo':>12} {'Líquido':>15}")
print("-" * 80)

for ejercicio in sorted(exercises.keys()):
    records = exercises[ejercicio]
    vol = sum(r.voluntaria for r in records)
    ejec = sum(r.ejecutiva for r in records)
    rec = sum(r.recargo for r in records)
    liq = sum(r.liquido for r in records)

    print(f"{ejercicio:<8} {len(records):<8} {vol:>15,.2f} {ejec:>15,.2f} {rec:>12,.2f} {liq:>15,.2f}")

print("-" * 80)
print(f"{'TOTAL':<8} {doc.total_records:<8} {calc_voluntaria:>15,.2f} {calc_ejecutiva:>15,.2f} {calc_recargo:>12,.2f} {calc_liquido:>15,.2f}")

# Show exercise summaries from PDF
if doc.exercise_summaries:
    print(f"\n{'='*80}")
    print("EXERCISE SUMMARIES FROM PDF:")
    print(f"{'='*80}")
    print(f"\n{'Year':<8} {'Voluntaria':>15} {'Ejecutiva':>15} {'Recargo':>12} {'Líquido':>15}")
    print("-" * 80)
    for summary in doc.exercise_summaries:
        print(f"{summary.ejercicio:<8} {summary.voluntaria:>15,.2f} {summary.ejecutiva:>15,.2f} {summary.recargo:>12,.2f} {summary.liquido:>15,.2f}")

print(f"\n{'='*80}")
print("Validation errors:")
errors = doc.validate_totals()
if errors:
    for error in errors:
        print(f"  - {error}")
else:
    print("  No errors! Totals match.")
