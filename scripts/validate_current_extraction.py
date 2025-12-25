"""
Validate the CURRENT extraction (your existing code) is accurate.

This will:
1. Run your actual extractor
2. Display the extracted totals
3. Compare with PDF page 2 totals (ground truth)
4. Show accuracy of current implementation
"""
from pathlib import Path
from src.extractors.pdf_extractor import LiquidationPDFExtractor
import sys


def validate_extraction(pdf_path: Path):
    """Validate extraction against ground truth from PDF."""
    print(f"\n{'='*100}")
    print(f"VALIDATING: {pdf_path.name}")
    print(f"{'='*100}\n")

    try:
        # Extract using YOUR current implementation
        extractor = LiquidationPDFExtractor(str(pdf_path))
        doc = extractor.extract()

        print("EXTRACTION RESULTS (Your Current Implementation):")
        print(f"{'-'*100}")

        print(f"\nHeader Info:")
        print(f"  Ejercicio: {doc.ejercicio}")
        print(f"  Mandamiento: {doc.mandamiento_pago}")
        print(f"  Liquidacion: {doc.numero_liquidacion}")
        print(f"  Entidad: {doc.entidad}")

        print(f"\nTribute Records Found: {len(doc.tribute_records)}")

        # Show first 5 records
        print(f"\nFirst 5 Records:")
        for i, rec in enumerate(doc.tribute_records[:5]):
            print(f"\n  {i+1}. {rec.concepto}")
            print(f"     Clave Contab: {rec.clave_contabilidad}")
            print(f"     Clave Recaud: {rec.clave_recaudacion}")
            print(f"     Voluntaria: {rec.voluntaria:,.2f}")
            print(f"     Ejecutiva: {rec.ejecutiva:,.2f}")
            print(f"     Liquido: {rec.liquido:,.2f}")

        print(f"\n{'-'*100}")
        print("TOTALS (from individual records)")
        print(f"{'-'*100}")

        # Calculate from records
        calc_voluntaria = sum(r.voluntaria for r in doc.tribute_records)
        calc_ejecutiva = sum(r.ejecutiva for r in doc.tribute_records)
        calc_recargo = sum(r.recargo for r in doc.tribute_records)
        calc_liquido = sum(r.liquido for r in doc.tribute_records)

        print(f"  Voluntaria (sum):  {calc_voluntaria:>15,.2f} EUR")
        print(f"  Ejecutiva (sum):   {calc_ejecutiva:>15,.2f} EUR")
        print(f"  Recargo (sum):     {calc_recargo:>15,.2f} EUR")
        print(f"  Liquido (sum):     {calc_liquido:>15,.2f} EUR")

        print(f"\n{'-'*100}")
        print("TOTALS (extracted from page 2)")
        print(f"{'-'*100}")

        print(f"  Voluntaria:        {doc.total_voluntaria:>15,.2f} EUR")
        print(f"  Ejecutiva:         {doc.total_ejecutiva:>15,.2f} EUR")
        print(f"  Recargo:           {doc.total_recargo:>15,.2f} EUR")
        print(f"  Liquido:           {doc.total_liquido:>15,.2f} EUR")
        print(f"  A Liquidar:        {doc.a_liquidar:>15,.2f} EUR")

        print(f"\n{'-'*100}")
        print("VALIDATION (Record Sum vs Page 2 Totals)")
        print(f"{'-'*100}")

        # Compare
        diff_vol = abs(calc_voluntaria - doc.total_voluntaria)
        diff_eje = abs(calc_ejecutiva - doc.total_ejecutiva)
        diff_rec = abs(calc_recargo - doc.total_recargo)
        diff_liq = abs(calc_liquido - doc.total_liquido)

        print(f"  Voluntaria diff:   {diff_vol:>15,.2f} EUR", end="")
        if diff_vol < 1:
            print(" [OK]")
        elif diff_vol < 100:
            print(" [WARNING - Small difference]")
        else:
            print(" [ERROR - Large difference!]")

        print(f"  Ejecutiva diff:    {diff_eje:>15,.2f} EUR", end="")
        if diff_eje < 1:
            print(" [OK]")
        elif diff_eje < 100:
            print(" [WARNING - Small difference]")
        else:
            print(" [ERROR - Large difference!]")

        print(f"  Recargo diff:      {diff_rec:>15,.2f} EUR", end="")
        if diff_rec < 1:
            print(" [OK]")
        elif diff_rec < 100:
            print(" [WARNING - Small difference]")
        else:
            print(" [ERROR - Large difference!]")

        print(f"  Liquido diff:      {diff_liq:>15,.2f} EUR", end="")
        if diff_liq < 1:
            print(" [OK]")
        elif diff_liq < 100:
            print(" [WARNING - Small difference]")
        else:
            print(" [ERROR - Large difference!]")

        # Exercise summaries
        if doc.exercise_summaries:
            print(f"\n{'-'*100}")
            print(f"EXERCISE SUMMARIES: {len(doc.exercise_summaries)}")
            print(f"{'-'*100}")
            for summary in doc.exercise_summaries:
                print(f"\n  Ejercicio {summary.ejercicio}:")
                print(f"    Voluntaria: {summary.voluntaria:>12,.2f}")
                print(f"    Ejecutiva:  {summary.ejecutiva:>12,.2f}")
                print(f"    Liquido:    {summary.liquido:>12,.2f}")

        # Deductions
        if doc.deductions:
            print(f"\n{'-'*100}")
            print("DEDUCTIONS")
            print(f"{'-'*100}")
            print(f"  Tasa Voluntaria:   {doc.deductions.tasa_voluntaria:>12,.2f}")
            print(f"  Tasa Ejecutiva:    {doc.deductions.tasa_ejecutiva:>12,.2f}")
            print(f"  Anticipos:         {doc.deductions.anticipos:>12,.2f}")

        print(f"\n{'='*100}")
        print("OVERALL STATUS")
        print(f"{'='*100}\n")

        max_diff = max(diff_vol, diff_eje, diff_rec, diff_liq)

        if max_diff < 1:
            print("  STATUS: EXCELLENT - Sums match page 2 totals perfectly")
            print("  Your current extraction is ACCURATE!")
        elif max_diff < 100:
            print("  STATUS: GOOD - Minor differences (likely rounding)")
            print("  Your current extraction is working well")
        else:
            print("  STATUS: NEEDS REVIEW - Significant differences detected")
            print("  Possible issues:")
            print("    - Missing records (not extracted)")
            print("    - Duplicate records (merged cells split incorrectly)")
            print("    - Exercise summary rows counted as records")

        return {
            'pdf': pdf_path.name,
            'record_count': len(doc.tribute_records),
            'max_diff': max_diff,
            'status': 'OK' if max_diff < 100 else 'REVIEW'
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'pdf': pdf_path.name,
            'error': str(e),
            'status': 'ERROR'
        }


def main():
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDFs found!")
        return

    print("="*100)
    print("CURRENT IMPLEMENTATION VALIDATION")
    print("="*100)
    print("\nThis validates YOUR EXISTING extraction code")
    print("by comparing record sums against page 2 totals (ground truth)")
    print()

    results = []

    for pdf_path in pdf_files:
        result = validate_extraction(pdf_path)
        results.append(result)
        print("\n" * 2)

    # Summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}\n")

    ok_count = sum(1 for r in results if r['status'] == 'OK')
    review_count = sum(1 for r in results if r['status'] == 'REVIEW')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"Total PDFs: {len(results)}")
    print(f"  OK:     {ok_count}")
    print(f"  REVIEW: {review_count}")
    print(f"  ERROR:  {error_count}")

    if ok_count == len(results):
        print("\nCONCLUSION: Your current implementation is working CORRECTLY!")
        print("The splitting logic is handling merged cells properly.")
    elif review_count > 0:
        print("\nCONCLUSION: Minor issues detected - review recommended")
    else:
        print("\nCONCLUSION: Errors detected - investigation needed")


if __name__ == "__main__":
    main()
