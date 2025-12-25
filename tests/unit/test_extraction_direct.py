"""Direct test of extraction function."""
from src.extractors.pdf_extractor import extract_liquidation_pdf

pdf_path = "026_2025_0016_00000623_CML.PDF"

# Extract document
print(f"Extracting from: {pdf_path}")
print("=" * 80)

try:
    doc = extract_liquidation_pdf(pdf_path)

    print(f"\nTotal records: {doc.total_records}")
    print(f"\nDocument totals (from PDF):")
    print(f"  Total Voluntaria: {doc.total_voluntaria:,.2f}")
    print(f"  Total Ejecutiva: {doc.total_ejecutiva:,.2f}")
    print(f"  Total Recargo: {doc.total_recargo:,.2f}")
    print(f"  Total Líquido: {doc.total_liquido:,.2f}")
    print(f"  A Liquidar: {doc.a_liquidar:,.2f}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
