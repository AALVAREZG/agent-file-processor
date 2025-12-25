"""Test script for HTML export functionality with mock data."""
from decimal import Decimal
from datetime import date
from src.exporters.html_grouped_exporter import export_grouped_to_html
from src.models.liquidation import LiquidationDocument, TributeRecord
from src.models.grouping_config import GroupingConfig, ConceptGroup

print("Testing HTML export with mock data")
print("=" * 80)

# Create mock tribute records
records = [
    # Year 2023
    TributeRecord(
        concepto="IBI RUSTICA",
        clave_contabilidad="11300",
        clave_recaudacion="026/2023/20/100/208",
        voluntaria=Decimal("1500.50"),
        ejecutiva=Decimal("200.00"),
        recargo=Decimal("50.00"),
        diputacion_voluntaria=Decimal("150.00"),
        diputacion_ejecutiva=Decimal("20.00"),
        diputacion_recargo=Decimal("5.00"),
        liquido=Decimal("1595.50"),
        ejercicio=2023
    ),
    TributeRecord(
        concepto="IBI URBANA",
        clave_contabilidad="11310",
        clave_recaudacion="026/2023/20/100/209",
        voluntaria=Decimal("2000.00"),
        ejecutiva=Decimal("300.00"),
        recargo=Decimal("75.00"),
        diputacion_voluntaria=Decimal("200.00"),
        diputacion_ejecutiva=Decimal("30.00"),
        diputacion_recargo=Decimal("7.50"),
        liquido=Decimal("2112.50"),
        ejercicio=2023
    ),
    # Year 2024
    TributeRecord(
        concepto="IBI RUSTICA",
        clave_contabilidad="11300",
        clave_recaudacion="026/2024/20/100/208",
        voluntaria=Decimal("1600.00"),
        ejecutiva=Decimal("220.00"),
        recargo=Decimal("55.00"),
        diputacion_voluntaria=Decimal("160.00"),
        diputacion_ejecutiva=Decimal("22.00"),
        diputacion_recargo=Decimal("5.50"),
        liquido=Decimal("1702.50"),
        ejercicio=2024
    ),
    TributeRecord(
        concepto="IBI URBANA",
        clave_contabilidad="11310",
        clave_recaudacion="026/2024/20/100/209",
        voluntaria=Decimal("2100.00"),
        ejecutiva=Decimal("320.00"),
        recargo=Decimal("80.00"),
        diputacion_voluntaria=Decimal("210.00"),
        diputacion_ejecutiva=Decimal("32.00"),
        diputacion_recargo=Decimal("8.00"),
        liquido=Decimal("2230.00"),
        ejercicio=2024
    ),
    TributeRecord(
        concepto="TASA BASURAS",
        clave_contabilidad="39200",
        clave_recaudacion="026/2024/20/100/100",
        voluntaria=Decimal("800.00"),
        ejecutiva=Decimal("100.00"),
        recargo=Decimal("25.00"),
        diputacion_voluntaria=Decimal("80.00"),
        diputacion_ejecutiva=Decimal("10.00"),
        diputacion_recargo=Decimal("2.50"),
        liquido=Decimal("842.50"),
        ejercicio=2024
    ),
]

# Create mock document
doc = LiquidationDocument(
    ejercicio=2024,
    mandamiento_pago="MP-2024-001",
    fecha_mandamiento=date(2024, 12, 15),
    numero_liquidacion="LIQ-2024-12345",
    entidad="AYUNTAMIENTO DE EJEMPLO",
    codigo_entidad="026",
    tribute_records=records,
    total_voluntaria=sum(r.voluntaria for r in records),
    total_ejecutiva=sum(r.ejecutiva for r in records),
    total_recargo=sum(r.recargo for r in records),
    total_diputacion_voluntaria=sum(r.diputacion_voluntaria for r in records),
    total_diputacion_ejecutiva=sum(r.diputacion_ejecutiva for r in records),
    total_diputacion_recargo=sum(r.diputacion_recargo for r in records),
    total_liquido=sum(r.liquido for r in records),
    deductions=None,
    a_liquidar=sum(r.liquido for r in records)
)

# Create grouping configuration
config = GroupingConfig()
config.concept_names = {
    "208": "IBI RUSTICA",
    "209": "IBI URBANA",
    "100": "TASA BASURAS"
}

try:
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
    config.custom_groups = [
        ConceptGroup(
            name="IBI (Urbana + Rustica)",
            concept_codes=["208", "209"]
        ),
        ConceptGroup(
            name="Tasas",
            concept_codes=["100"]
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
    print("\nExpected output:")
    print("  - Tables should be organized by year")
    print("  - Each group should have texto SICAL and importe liquido rows")
    print("  - Copy buttons should work when clicked")
    print("  - Footer rows should show totals per year")

except Exception as e:
    print(f"\n[ERROR] Error during export: {e}")
    import traceback
    traceback.print_exc()
