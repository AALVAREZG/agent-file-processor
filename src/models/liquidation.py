"""
Data models for liquidation documents (Documentos de Liquidación).
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Dict
from datetime import date


@dataclass
class TributeRecord:
    """
    Represents a single tribute charge record (cobro) from the main table.
    """
    concepto: str  # Concept (IBI RUSTICA, MULTAS TRAFICO, etc.)
    clave_contabilidad: str  # Accounting code
    clave_recaudacion: str  # Collection code
    voluntaria: Decimal  # Voluntary amount
    ejecutiva: Decimal  # Executive amount
    recargo: Decimal  # Surcharge
    diputacion_voluntaria: Decimal  # Provincial voluntary
    diputacion_ejecutiva: Decimal  # Provincial executive
    diputacion_recargo: Decimal  # Provincial surcharge
    liquido: Decimal  # Net amount
    ejercicio: int  # Fiscal year

    def __post_init__(self):
        """Convert string amounts to Decimal if needed."""
        for field_name in ['voluntaria', 'ejecutiva', 'recargo',
                           'diputacion_voluntaria', 'diputacion_ejecutiva',
                           'diputacion_recargo', 'liquido']:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                setattr(self, field_name, Decimal(str(value)))

    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount (should equal liquido)."""
        return (self.voluntaria + self.ejecutiva + self.recargo +
                self.diputacion_voluntaria + self.diputacion_ejecutiva +
                self.diputacion_recargo)


@dataclass
class ExerciseSummary:
    """
    Summary of amounts by fiscal year (exercise).
    """
    ejercicio: int
    voluntaria: Decimal
    ejecutiva: Decimal
    recargo: Decimal
    diputacion_voluntaria: Decimal
    diputacion_ejecutiva: Decimal
    diputacion_recargo: Decimal
    liquido: Decimal
    records: List[TributeRecord] = field(default_factory=list)


@dataclass
class ExerciseValidationResult:
    """
    Validation result for a specific fiscal year.
    Contains comparison between calculated totals and documented summary.
    """
    ejercicio: int
    is_valid: bool
    # Calculated values (from summing tribute records)
    calc_voluntaria: Decimal
    calc_ejecutiva: Decimal
    calc_recargo: Decimal
    calc_dip_voluntaria: Decimal
    calc_dip_ejecutiva: Decimal
    calc_dip_recargo: Decimal
    calc_liquido: Decimal
    # Documented values (from ExerciseSummary)
    doc_voluntaria: Decimal
    doc_ejecutiva: Decimal
    doc_recargo: Decimal
    doc_dip_voluntaria: Decimal
    doc_dip_ejecutiva: Decimal
    doc_dip_recargo: Decimal
    doc_liquido: Decimal
    # Error messages if validation fails
    errors: List[str] = field(default_factory=list)


@dataclass
class DeductionDetail:
    """
    Detailed deductions section from page 2.
    """
    # Recaudación (Collection)
    tasa_voluntaria: Decimal = Decimal('0')
    tasa_ejecutiva: Decimal = Decimal('0')
    tasa_ejecutiva_sin_recargo: Decimal = Decimal('0')
    tasa_baja_organo_gestor_deleg: Decimal = Decimal('0')

    # Tributaria (Tax)
    tasa_gestion_tributaria: Decimal = Decimal('0')
    tasa_gestion_censal: Decimal = Decimal('0')
    tasa_gestion_catastral: Decimal = Decimal('0')

    # Multas/Sanciones (Fines/Sanctions)
    tasa_sancion_tributaria: Decimal = Decimal('0')
    tasa_sancion_recaudacion: Decimal = Decimal('0')
    tasa_sancion_inspeccion: Decimal = Decimal('0')
    tasa_multas_trafico: Decimal = Decimal('0')

    # Otras deducciones (Other deductions)
    gastos_repercutidos: Decimal = Decimal('0')
    anticipos: Decimal = Decimal('0')
    intereses_por_anticipo: Decimal = Decimal('0')
    expedientes_compensacion: Decimal = Decimal('0')
    expedientes_ingresos_indebidos: Decimal = Decimal('0')

    @property
    def total_deducciones(self) -> Decimal:
        """Calculate total deductions."""
        return sum([
            self.tasa_voluntaria, self.tasa_ejecutiva,
            self.tasa_ejecutiva_sin_recargo, self.tasa_baja_organo_gestor_deleg,
            self.tasa_gestion_tributaria, self.tasa_gestion_censal,
            self.tasa_gestion_catastral, self.tasa_sancion_tributaria,
            self.tasa_sancion_recaudacion, self.tasa_sancion_inspeccion,
            self.tasa_multas_trafico, self.gastos_repercutidos,
            self.anticipos, self.intereses_por_anticipo,
            self.expedientes_compensacion, self.expedientes_ingresos_indebidos
        ])


@dataclass
class AdvanceBreakdown:
    """
    Breakdown of advances by concept (Desglose Descuentos Anticipos).
    """
    ejercicio: int
    urbana: Decimal
    rustica: Decimal
    vehiculos: Decimal
    bice: Decimal
    iae: Decimal
    tasas: Decimal
    ejecutiva: Decimal

    @property
    def total(self) -> Decimal:
        """Total advances."""
        return (self.urbana + self.rustica + self.vehiculos +
                self.bice + self.iae + self.tasas + self.ejecutiva)


@dataclass
class RefundRecord:
    """
    Individual refund record (Expediente de Devolución).
    """
    num_expte: str  # File number
    num_resolucion: str  # Resolution number
    num_solic: int  # Request number
    total_devolucion: Decimal  # Total refund
    entidad: Decimal  # Entity amount
    diputacion: Decimal  # Provincial amount
    intereses: Decimal  # Interest
    comp_trib: Decimal  # Tax compensation
    a_deducir: Decimal  # To deduct


@dataclass
class RefundSummary:
    """
    Summary of refunds by concept.
    """
    concepto: str  # Concept name
    total_devolucion: Decimal
    entidad: Decimal
    diputacion: Decimal
    intereses: Decimal


@dataclass
class LiquidationDocument:
    """
    Complete liquidation document with all sections.
    """
    # Header information
    ejercicio: int
    mandamiento_pago: str  # Payment mandate
    fecha_mandamiento: date  # Mandate date
    numero_liquidacion: str  # Liquidation number
    entidad: str  # Entity (municipality)
    codigo_entidad: str  # Entity code

    # Main records
    tribute_records: List[TributeRecord] = field(default_factory=list)

    # Summaries by exercise
    exercise_summaries: List[ExerciseSummary] = field(default_factory=list)

    # Totals from page 2
    total_voluntaria: Decimal = Decimal('0')
    total_ejecutiva: Decimal = Decimal('0')
    total_recargo: Decimal = Decimal('0')
    total_diputacion_voluntaria: Decimal = Decimal('0')
    total_diputacion_ejecutiva: Decimal = Decimal('0')
    total_diputacion_recargo: Decimal = Decimal('0')
    total_liquido: Decimal = Decimal('0')

    # Deductions
    deductions: Optional[DeductionDetail] = None

    # Advances breakdown
    advance_breakdown: List[AdvanceBreakdown] = field(default_factory=list)

    # Refunds
    refund_records: List[RefundRecord] = field(default_factory=list)
    refund_summaries: List[RefundSummary] = field(default_factory=list)

    # Final amount
    a_liquidar: Decimal = Decimal('0')  # Amount to settle

    # Verification
    codigo_verificacion: Optional[str] = None
    firmado_por: Optional[str] = None
    fecha_firma: Optional[date] = None

    def validate_totals(self) -> List[str]:
        """
        Validate that totals match the sum of records.
        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Calculate sum from records
        calc_voluntaria = sum(r.voluntaria for r in self.tribute_records)
        calc_ejecutiva = sum(r.ejecutiva for r in self.tribute_records)
        calc_recargo = sum(r.recargo for r in self.tribute_records)
        calc_liquido = sum(r.liquido for r in self.tribute_records)

        tolerance = Decimal('0.01')  # Allow 1 cent tolerance for rounding

        if abs(calc_voluntaria - self.total_voluntaria) > tolerance:
            errors.append(f"Voluntaria mismatch: calculated {calc_voluntaria} vs documented {self.total_voluntaria}")

        if abs(calc_ejecutiva - self.total_ejecutiva) > tolerance:
            errors.append(f"Ejecutiva mismatch: calculated {calc_ejecutiva} vs documented {self.total_ejecutiva}")

        if abs(calc_recargo - self.total_recargo) > tolerance:
            errors.append(f"Recargo mismatch: calculated {calc_recargo} vs documented {self.total_recargo}")

        if abs(calc_liquido - self.total_liquido) > tolerance:
            errors.append(f"Liquido mismatch: calculated {calc_liquido} vs documented {self.total_liquido}")

        # Validate A LIQUIDAR formula if deductions exist
        if self.deductions:
            expected_liquidar = self.total_liquido - self.deductions.total_deducciones
            if abs(expected_liquidar - self.a_liquidar) > tolerance:
                errors.append(f"A Liquidar mismatch: expected {expected_liquidar} vs documented {self.a_liquidar}")

        return errors

    def validate_exercise_summaries(self) -> Dict[int, 'ExerciseValidationResult']:
        """
        Validate that per-year totals match their exercise summaries.

        Returns:
            Dictionary mapping ejercicio (year) to ExerciseValidationResult
        """
        from src.models.liquidation import ExerciseValidationResult

        results = {}
        tolerance = Decimal('0.01')  # Allow 1 cent tolerance for rounding

        for summary in self.exercise_summaries:
            ejercicio = summary.ejercicio
            year_records = self.get_records_by_year(ejercicio)

            # Calculate totals from tribute records for this year
            calc_voluntaria = sum(r.voluntaria for r in year_records)
            calc_ejecutiva = sum(r.ejecutiva for r in year_records)
            calc_recargo = sum(r.recargo for r in year_records)
            calc_dip_voluntaria = sum(r.diputacion_voluntaria for r in year_records)
            calc_dip_ejecutiva = sum(r.diputacion_ejecutiva for r in year_records)
            calc_dip_recargo = sum(r.diputacion_recargo for r in year_records)
            calc_liquido = sum(r.liquido for r in year_records)

            # Check for discrepancies
            errors = []
            is_valid = True

            if abs(calc_voluntaria - summary.voluntaria) > tolerance:
                errors.append(f"Voluntaria: calculado {calc_voluntaria} vs documentado {summary.voluntaria}")
                is_valid = False

            if abs(calc_ejecutiva - summary.ejecutiva) > tolerance:
                errors.append(f"Ejecutiva: calculado {calc_ejecutiva} vs documentado {summary.ejecutiva}")
                is_valid = False

            if abs(calc_recargo - summary.recargo) > tolerance:
                errors.append(f"Recargo: calculado {calc_recargo} vs documentado {summary.recargo}")
                is_valid = False

            if abs(calc_dip_voluntaria - summary.diputacion_voluntaria) > tolerance:
                errors.append(f"Dip. Voluntaria: calculado {calc_dip_voluntaria} vs documentado {summary.diputacion_voluntaria}")
                is_valid = False

            if abs(calc_dip_ejecutiva - summary.diputacion_ejecutiva) > tolerance:
                errors.append(f"Dip. Ejecutiva: calculado {calc_dip_ejecutiva} vs documentado {summary.diputacion_ejecutiva}")
                is_valid = False

            if abs(calc_dip_recargo - summary.diputacion_recargo) > tolerance:
                errors.append(f"Dip. Recargo: calculado {calc_dip_recargo} vs documentado {summary.diputacion_recargo}")
                is_valid = False

            if abs(calc_liquido - summary.liquido) > tolerance:
                errors.append(f"Líquido: calculado {calc_liquido} vs documentado {summary.liquido}")
                is_valid = False

            # Create validation result
            result = ExerciseValidationResult(
                ejercicio=ejercicio,
                is_valid=is_valid,
                calc_voluntaria=calc_voluntaria,
                calc_ejecutiva=calc_ejecutiva,
                calc_recargo=calc_recargo,
                calc_dip_voluntaria=calc_dip_voluntaria,
                calc_dip_ejecutiva=calc_dip_ejecutiva,
                calc_dip_recargo=calc_dip_recargo,
                calc_liquido=calc_liquido,
                doc_voluntaria=summary.voluntaria,
                doc_ejecutiva=summary.ejecutiva,
                doc_recargo=summary.recargo,
                doc_dip_voluntaria=summary.diputacion_voluntaria,
                doc_dip_ejecutiva=summary.diputacion_ejecutiva,
                doc_dip_recargo=summary.diputacion_recargo,
                doc_liquido=summary.liquido,
                errors=errors
            )

            results[ejercicio] = result

        return results

    def get_records_by_concept(self, concepto: str) -> List[TributeRecord]:
        """Get all records for a specific concept."""
        return [r for r in self.tribute_records if r.concepto == concepto]

    def get_records_by_year(self, ejercicio: int) -> List[TributeRecord]:
        """Get all records for a specific fiscal year."""
        return [r for r in self.tribute_records if r.ejercicio == ejercicio]

    @property
    def total_records(self) -> int:
        """Total number of tribute records."""
        return len(self.tribute_records)

    @property
    def total_refunds(self) -> Decimal:
        """Total amount of refunds."""
        return sum(r.total_devolucion for r in self.refund_records)

    @property
    def has_exercise_validation_errors(self) -> bool:
        """Check if any exercise summary has validation errors."""
        validation_results = self.validate_exercise_summaries()
        return any(not result.is_valid for result in validation_results.values())
