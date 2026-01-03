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
    concepto: str  # Concept (BREVE - IBI RUSTICA, MULTAS TRAFICO, etc.)
    clave_c: str  # Accounting code (CLAVE C)
    clave_r: str  # Collection code (CLAVE R)
    cargo: Decimal  # Total charge (CARGO)
    datas_total: Decimal  # Datas amount
    voluntaria_total: Decimal  # Voluntary amount
    ejecutiva_total: Decimal  # Executive amount
    pendiente_total: Decimal  # Pending amount
    ejercicio: int  # Fiscal year

    def __post_init__(self):
        """Convert string amounts to Decimal if needed."""
        for field_name in ['cargo', 'datas_total', 'voluntaria_total',
                           'ejecutiva_total', 'pendiente_total']:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                setattr(self, field_name, Decimal(str(value)))

    @property
    def total_amount(self) -> Decimal:
        """Calculate total collected (datas + voluntaria + ejecutiva)."""
        return self.datas_total + self.voluntaria_total + self.ejecutiva_total


@dataclass
class ExerciseSummary:
    """
    Summary of amounts by fiscal year (exercise).
    """
    ejercicio: int
    cargo: Decimal
    datas_total: Decimal
    voluntaria_total: Decimal
    ejecutiva_total: Decimal
    pendiente_total: Decimal
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
    calc_cargo: Decimal
    calc_datas: Decimal
    calc_voluntaria: Decimal
    calc_ejecutiva: Decimal
    calc_pendiente: Decimal
    # Documented values (from ExerciseSummary)
    doc_cargo: Decimal
    doc_datas: Decimal
    doc_voluntaria: Decimal
    doc_ejecutiva: Decimal
    doc_pendiente: Decimal
    # Error messages if validation fails
    errors: List[str] = field(default_factory=list)


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

    # Totals
    total_cargo: Decimal = Decimal('0')
    total_datas: Decimal = Decimal('0')
    total_voluntaria: Decimal = Decimal('0')
    total_ejecutiva: Decimal = Decimal('0')
    total_pendiente: Decimal = Decimal('0')

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
        calc_cargo = sum(r.cargo for r in self.tribute_records)
        calc_datas = sum(r.datas_total for r in self.tribute_records)
        calc_voluntaria = sum(r.voluntaria_total for r in self.tribute_records)
        calc_ejecutiva = sum(r.ejecutiva_total for r in self.tribute_records)
        calc_pendiente = sum(r.pendiente_total for r in self.tribute_records)

        tolerance = Decimal('0.01')  # Allow 1 cent tolerance for rounding

        if abs(calc_cargo - self.total_cargo) > tolerance:
            errors.append(f"Cargo mismatch: calculated {calc_cargo} vs documented {self.total_cargo}")

        if abs(calc_datas - self.total_datas) > tolerance:
            errors.append(f"Datas mismatch: calculated {calc_datas} vs documented {self.total_datas}")

        if abs(calc_voluntaria - self.total_voluntaria) > tolerance:
            errors.append(f"Voluntaria mismatch: calculated {calc_voluntaria} vs documented {self.total_voluntaria}")

        if abs(calc_ejecutiva - self.total_ejecutiva) > tolerance:
            errors.append(f"Ejecutiva mismatch: calculated {calc_ejecutiva} vs documented {self.total_ejecutiva}")

        if abs(calc_pendiente - self.total_pendiente) > tolerance:
            errors.append(f"Pendiente mismatch: calculated {calc_pendiente} vs documented {self.total_pendiente}")

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
            calc_cargo = sum(r.cargo for r in year_records)
            calc_datas = sum(r.datas_total for r in year_records)
            calc_voluntaria = sum(r.voluntaria_total for r in year_records)
            calc_ejecutiva = sum(r.ejecutiva_total for r in year_records)
            calc_pendiente = sum(r.pendiente_total for r in year_records)

            # Check for discrepancies
            errors = []
            is_valid = True

            if abs(calc_cargo - summary.cargo) > tolerance:
                errors.append(f"Cargo: calculado {calc_cargo} vs documentado {summary.cargo}")
                is_valid = False

            if abs(calc_datas - summary.datas_total) > tolerance:
                errors.append(f"Datas: calculado {calc_datas} vs documentado {summary.datas_total}")
                is_valid = False

            if abs(calc_voluntaria - summary.voluntaria_total) > tolerance:
                errors.append(f"Voluntaria: calculado {calc_voluntaria} vs documentado {summary.voluntaria_total}")
                is_valid = False

            if abs(calc_ejecutiva - summary.ejecutiva_total) > tolerance:
                errors.append(f"Ejecutiva: calculado {calc_ejecutiva} vs documentado {summary.ejecutiva_total}")
                is_valid = False

            if abs(calc_pendiente - summary.pendiente_total) > tolerance:
                errors.append(f"Pendiente: calculado {calc_pendiente} vs documentado {summary.pendiente_total}")
                is_valid = False

            # Create validation result
            result = ExerciseValidationResult(
                ejercicio=ejercicio,
                is_valid=is_valid,
                calc_cargo=calc_cargo,
                calc_datas=calc_datas,
                calc_voluntaria=calc_voluntaria,
                calc_ejecutiva=calc_ejecutiva,
                calc_pendiente=calc_pendiente,
                doc_cargo=summary.cargo,
                doc_datas=summary.datas_total,
                doc_voluntaria=summary.voluntaria_total,
                doc_ejecutiva=summary.ejecutiva_total,
                doc_pendiente=summary.pendiente_total,
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
    def has_exercise_validation_errors(self) -> bool:
        """Check if any exercise summary has validation errors."""
        validation_results = self.validate_exercise_summaries()
        return any(not result.is_valid for result in validation_results.values())
