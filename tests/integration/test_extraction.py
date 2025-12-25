"""
Test script to verify PDF extraction functionality.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.pdf_extractor import extract_liquidation_pdf, PDFExtractionError


def test_extraction(pdf_path: str):
    """Test extraction of a single PDF file."""
    print(f"\n{'='*80}")
    print(f"Testing extraction of: {Path(pdf_path).name}")
    print(f"{'='*80}\n")

    try:
        doc = extract_liquidation_pdf(pdf_path)

        # Print document info
        print(f"[OK] Extraction successful!")
        print(f"\nDocument Information:")
        print(f"  Ejercicio: {doc.ejercicio}")
        print(f"  Mandamiento: {doc.mandamiento_pago}")
        print(f"  Fecha: {doc.fecha_mandamiento}")
        print(f"  Liquidación: {doc.numero_liquidacion}")
        print(f"  Entidad: {doc.entidad} ({doc.codigo_entidad})")

        # Print record counts
        print(f"\nExtracted Records:")
        print(f"  Total tribute records: {doc.total_records}")
        print(f"  Exercise summaries: {len(doc.exercise_summaries)}")
        print(f"  Refund records: {len(doc.refund_records)}")

        # Print totals
        print(f"\nTotals:")
        print(f"  Voluntaria:    {doc.total_voluntaria:>15,.2f}")
        print(f"  Ejecutiva:     {doc.total_ejecutiva:>15,.2f}")
        print(f"  Recargo:       {doc.total_recargo:>15,.2f}")
        print(f"  Líquido:       {doc.total_liquido:>15,.2f}")
        print(f"  A Liquidar:    {doc.a_liquidar:>15,.2f}")

        # Print sample records
        print(f"\nSample Records (first 5):")
        print(f"  {'Concepto':<30} {'Ejercicio':<10} {'Voluntaria':>12} {'Liquido':>12}")
        print(f"  {'-'*70}")
        for record in doc.tribute_records[:5]:
            print(f"  {record.concepto[:30]:<30} {record.ejercicio:<10} "
                  f"{record.voluntaria:>12,.2f} {record.liquido:>12,.2f}")

        # Validate
        print(f"\nValidation:")
        errors = doc.validate_totals()
        if errors:
            print(f"  [WARNING] Found {len(errors)} validation error(s):")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  [OK] All totals validate correctly!")

        return True

    except PDFExtractionError as e:
        print(f"[FAILED] Extraction failed: {e}")
        return False
    except Exception as e:
        print(f"[FAILED] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test extraction with all PDF files in the current directory."""
    current_dir = Path.cwd()
    pdf_files = list(current_dir.glob("*.pdf")) + list(current_dir.glob("*.PDF"))

    if not pdf_files:
        print("No PDF files found in current directory.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to test.")

    results = []
    for pdf_file in pdf_files:
        success = test_extraction(str(pdf_file))
        results.append((pdf_file.name, success))

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    successful = sum(1 for _, success in results if success)
    print(f"Total files tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    print("\nDetailed Results:")
    for filename, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"  {status} {filename}")


if __name__ == "__main__":
    main()
