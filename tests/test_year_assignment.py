"""Test to check year assignment for records."""
import sys
import io
from pathlib import Path
from src.extractors.pdf_extractor import extract_liquidation_pdf

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Extract PDF
pdf_path = Path('data/samples/026_2025_0016_00000623_CML.PDF')
print(f"Extracting: {pdf_path.name}\n")

doc = extract_liquidation_pdf(str(pdf_path))

# Show how records are distributed by year
print("=" * 60)
print("RECORDS PER YEAR")
print("=" * 60)

for year in sorted(set(r.ejercicio for r in doc.tribute_records)):
    year_records = doc.get_records_by_year(year)
    print(f"\nYear {year}: {len(year_records)} records")

    if len(year_records) <= 3:
        for rec in year_records:
            print(f"  - {rec.concepto[:20]:20s} | {rec.clave_recaudacion:30s} | Liquido: {rec.liquido}")

    # Show sum
    total_liquido = sum(r.liquido for r in year_records)
    total_ejecutiva = sum(r.ejecutiva for r in year_records)
    total_recargo = sum(r.recargo for r in year_records)
    print(f"  SUM: Ejecutiva={total_ejecutiva:,.2f}, Recargo={total_recargo:,.2f}, Liquido={total_liquido:,.2f}")

print("\n" + "=" * 60)
print("EXERCISE SUMMARIES (from PDF)")
print("=" * 60)

for summary in sorted(doc.exercise_summaries, key=lambda s: s.ejercicio):
    print(f"\nYear {summary.ejercicio}:")
    print(f"  Ejecutiva: {summary.ejecutiva:,.2f}")
    print(f"  Recargo: {summary.recargo:,.2f}")
    print(f"  Liquido: {summary.liquido:,.2f}")

# Show a few sample records to understand the year field
print("\n" + "=" * 60)
print("SAMPLE RECORDS (first 10)")
print("=" * 60)
for i, rec in enumerate(doc.tribute_records[:10]):
    print(f"{i+1}. Ejercicio={rec.ejercicio} | Recaudacion={rec.clave_recaudacion} | Concepto={rec.concepto[:20]}")
