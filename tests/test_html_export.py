"""Test script for HTML export functionality."""
from src.extractors.pdf_extractor import extract_liquidation_pdf
from src.exporters.html_grouped_exporter import export_grouped_to_html
from src.models.grouping_config import GroupingConfig, ConceptGroup

# Test with the sample PDF (update path if needed)
pdf_path = "data/cargos/026_2025-0002_CR.PDF"

print(f"Testing HTML export with: {pdf_path}")
print("=" * 80)

try:
    # Extract document
    print("Extracting PDF...")
    doc = extract_liquidation_pdf(pdf_path)
    print(f"[OK] Extracted {doc.total_records} records")

    # Create a sample grouping configuration
    config = GroupingConfig()
    config.group_by_year = True
    config.group_by_concept = True
    config.group_by_custom = False

    # Extract concept names from records
    for record in doc.tribute_records:
        code = config.get_concept_code(record.clave_recaudacion)
        if code and code not in config.concept_names:
            config.concept_names[code] = record.concepto

    # Test 1: Export grouped by year and concept
    print("\nTest 1: Exporting grouped by year and concept...")
    output_path = "test_output_year_concept.html"
    export_grouped_to_html(
        doc,
        config,
        output_path,
        group_by_year=True,
        group_by_concept=True,
        group_by_custom=False
    )
    print(f"[OK] Exported to: {output_path}")

    # Test 2: Export with custom groups
    print("\nTest 2: Exporting with custom groups...")
    config.group_by_custom = True
    config.custom_groups = [
        ConceptGroup(
            name="IBI (Urbana + Rustica)",
            concept_codes=["208", "209"]  # Adjust based on actual codes in your PDF
        ),
        ConceptGroup(
            name="Tasas Varias",
            concept_codes=["100", "101"]  # Adjust based on actual codes
        )
    ]
    output_path_custom = "test_output_custom_groups.html"
    export_grouped_to_html(
        doc,
        config,
        output_path_custom,
        group_by_year=True,
        group_by_concept=True,
        group_by_custom=True
    )
    print(f"[OK] Exported to: {output_path_custom}")

    # Test 3: Export grouped only by concept (no year grouping)
    print("\nTest 3: Exporting grouped only by concept...")
    output_path_concept = "test_output_concept_only.html"
    export_grouped_to_html(
        doc,
        config,
        output_path_concept,
        group_by_year=False,
        group_by_concept=True,
        group_by_custom=False
    )
    print(f"[OK] Exported to: {output_path_concept}")

    print("\n" + "=" * 80)
    print("[OK] All tests completed successfully!")
    print("\nGenerated files:")
    print("  - test_output_year_concept.html")
    print("  - test_output_custom_groups.html")
    print("  - test_output_concept_only.html")
    print("\nOpen these files in a web browser to verify the output.")

except FileNotFoundError:
    print(f"\n[ERROR] PDF file not found: {pdf_path}")
    print("\nPlease update the 'pdf_path' variable in this script with the correct path to a liquidation PDF.")
except Exception as e:
    print(f"\n[ERROR] Error during export: {e}")
    import traceback
    traceback.print_exc()
