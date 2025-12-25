"""Test extraction with the new multiple-record splitting logic."""
from src.extractors.pdf_extractor import extract_liquidation_pdf

pdf_path = "026_2025_0015_00000506_CML.PDF"

print(f"Testing extraction: {pdf_path}")
print("=" * 100)

try:
    doc = extract_liquidation_pdf(pdf_path)

    print(f"\nTotal records extracted: {doc.total_records}")
    print(f"\nLooking for the problematic MULTAS records...")
    print("=" * 100)

    # Find all MULTAS records for 2025
    multas_2025 = [r for r in doc.tribute_records if r.ejercicio == 2025 and 'MULTAS' in r.concepto.upper()]

    print(f"\nFound {len(multas_2025)} MULTAS records for year 2025:")
    print("-" * 100)

    for idx, record in enumerate(multas_2025, 1):
        print(f"\n{idx}. {record.concepto}")
        print(f"   Clave Contabilidad: {record.clave_contabilidad}")
        print(f"   Clave Recaudación: {record.clave_recaudacion}")
        print(f"   Voluntaria: {record.voluntaria:,.2f}")
        print(f"   Ejecutiva: {record.ejecutiva:,.2f}")
        print(f"   Recargo: {record.recargo:,.2f}")
        print(f"   Líquido: {record.liquido:,.2f}")

    # Check specifically for the two that were merged
    print("\n" + "=" * 100)
    print("CHECKING FOR SPECIFIC RECORDS:")
    print("=" * 100)

    target_claves = ['2025/M/0000731', '2025/M/0000903']
    for clave in target_claves:
        found = [r for r in doc.tribute_records if r.clave_contabilidad == clave]
        if found:
            print(f"\n[OK] FOUND: {clave}")
            for r in found:
                print(f"  - Concepto: {r.concepto}")
                print(f"  - Clave Recaudacion: {r.clave_recaudacion}")
                print(f"  - Liquido: {r.liquido:,.2f}")
        else:
            print(f"\n[MISSING] NOT FOUND: {clave}")

    print("\n" + "=" * 100)
    print("DOCUMENT TOTALS:")
    print("=" * 100)
    print(f"Total Voluntaria: {doc.total_voluntaria:,.2f}")
    print(f"Total Ejecutiva: {doc.total_ejecutiva:,.2f}")
    print(f"Total Recargo: {doc.total_recargo:,.2f}")
    print(f"Total Líquido: {doc.total_liquido:,.2f}")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
