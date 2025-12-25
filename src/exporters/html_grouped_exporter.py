"""
HTML Exporter for Grouped Concept Records
Exports liquidation data grouped by concept to a standalone HTML page
"""

from typing import List, Dict, Tuple, Set
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from ..models.liquidation import LiquidationDocument, TributeRecord
from ..models.grouping_config import GroupingConfig


class HTMLGroupedExporter:
    """Exports grouped concept records to HTML format"""

    def __init__(self, document: LiquidationDocument, grouping_config: GroupingConfig):
        """
        Initialize the HTML exporter

        Args:
            document: LiquidationDocument with all records
            grouping_config: GroupingConfig with concept and custom group definitions
        """
        self.document = document
        self.grouping_config = grouping_config

    def export_grouped_concepts(
        self,
        output_path: str,
        group_by_year: bool = True,
        group_by_concept: bool = True,
        group_by_custom: bool = False
    ) -> None:
        """
        Export grouped concept records to HTML

        Args:
            output_path: Path where to save the HTML file
            group_by_year: Whether to group by year
            group_by_concept: Whether to group by concept
            group_by_custom: Whether to apply custom grouping
        """
        # Organize data according to grouping settings
        grouped_data = self._organize_data(group_by_year, group_by_concept, group_by_custom)

        # Generate HTML content
        html_content = self._generate_html(grouped_data, group_by_year, group_by_concept, group_by_custom)

        # Write to file
        output_file = Path(output_path)
        output_file.write_text(html_content, encoding='utf-8')

    def _organize_data(
        self,
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> Dict:
        """
        Organize records according to grouping configuration

        Returns:
            Dictionary with organized data structure
        """
        if group_by_year:
            # Group by year first
            years_data = {}
            for year in sorted(set(r.ejercicio for r in self.document.tribute_records)):
                year_records = [r for r in self.document.tribute_records if r.ejercicio == year]
                years_data[year] = self._organize_records(year_records, group_by_concept, group_by_custom)
            return years_data
        else:
            # All records together
            return {None: self._organize_records(self.document.tribute_records, group_by_concept, group_by_custom)}

    def _organize_records(
        self,
        records: List[TributeRecord],
        group_by_concept: bool,
        group_by_custom: bool
    ) -> List[Dict]:
        """
        Organize a list of records into groups

        Returns:
            List of group dictionaries with name, records, and totals
        """
        if not group_by_concept and not group_by_custom:
            # Return all records as one group
            return [{
                'name': 'Todos los conceptos',
                'records': records,
                'liquido': sum(r.liquido for r in records)
            }]

        groups = []

        if group_by_concept and not group_by_custom:
            # Group by concept only
            concept_groups = {}
            for record in records:
                concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                concept_name = self.grouping_config.concept_names.get(concept_code, concept_code)

                if concept_name not in concept_groups:
                    concept_groups[concept_name] = []
                concept_groups[concept_name].append(record)

            for concept_name, concept_records in sorted(concept_groups.items()):
                groups.append({
                    'name': concept_name,
                    'records': concept_records,
                    'liquido': sum(r.liquido for r in concept_records)
                })

        elif group_by_custom:
            # Apply custom grouping
            if group_by_concept:
                # First group by concept, then apply custom groups
                concept_groups = {}
                for record in records:
                    concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                    if concept_code not in concept_groups:
                        concept_groups[concept_code] = []
                    concept_groups[concept_code].append(record)

                # Apply custom groups to concepts
                used_concepts = set()
                for custom_group in self.grouping_config.custom_groups:
                    group_records = []
                    for concept_code in custom_group.concept_codes:
                        if concept_code in concept_groups:
                            group_records.extend(concept_groups[concept_code])
                            used_concepts.add(concept_code)

                    if group_records:
                        groups.append({
                            'name': custom_group.name,
                            'records': group_records,
                            'liquido': sum(r.liquido for r in group_records)
                        })

                # Add ungrouped concepts
                for concept_code, concept_records in sorted(concept_groups.items()):
                    if concept_code not in used_concepts:
                        concept_name = self.grouping_config.concept_names.get(concept_code, concept_code)
                        groups.append({
                            'name': concept_name,
                            'records': concept_records,
                            'liquido': sum(r.liquido for r in concept_records)
                        })
            else:
                # Apply custom groups directly to records
                used_records = set()
                for custom_group in self.grouping_config.custom_groups:
                    group_records = []
                    for record in records:
                        concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                        if concept_code in custom_group.concept_codes:
                            group_records.append(record)
                            used_records.add(id(record))

                    if group_records:
                        groups.append({
                            'name': custom_group.name,
                            'records': group_records,
                            'liquido': sum(r.liquido for r in group_records)
                        })

                # Add ungrouped records
                ungrouped_records = [r for r in records if id(r) not in used_records]
                if ungrouped_records:
                    groups.append({
                        'name': 'Sin agrupar',
                        'records': ungrouped_records,
                        'liquido': sum(r.liquido for r in ungrouped_records)
                    })

        return groups

    def _collect_unique_claves(self, records: List[TributeRecord]) -> Tuple[str, str]:
        """
        Collect unique clave_recaudacion and clave_contabilidad from records

        Returns:
            Tuple of (claves_recaudacion_str, claves_contabilidad_str)
        """
        claves_recaudacion = sorted(set(r.clave_recaudacion for r in records))
        claves_contabilidad = sorted(set(r.clave_contabilidad for r in records))

        return ' '.join(claves_recaudacion), ' '.join(claves_contabilidad)

    def _build_texto_sical(self, group_name: str, records: List[TributeRecord]) -> str:
        """
        Build the texto SICAL string for a group

        Format: OPAEF. REGULARIZACION COBROS LIQ. {num} MTO. PAGO {mto} {claves_rec} {claves_cont}
        """
        claves_rec, claves_cont = self._collect_unique_claves(records)

        return (
            f"OPAEF. REGULARIZACION COBROS LIQ. {self.document.numero_liquidacion} "
            f"MTO. PAGO {self.document.mandamiento_pago} {claves_rec} {claves_cont}"
        )

    def _format_decimal(self, value: Decimal) -> str:
        """Format decimal value as currency string"""
        return f"{value:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')

    def _generate_html(
        self,
        grouped_data: Dict,
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> str:
        """Generate complete HTML document"""

        # Build the HTML content
        html_parts = [
            self._html_header(),
            self._html_document_info(),
        ]

        # Generate tables for each year (or single table if not grouped by year)
        for year, groups in grouped_data.items():
            html_parts.append(self._html_year_table(year, groups))

        html_parts.append(self._html_footer())

        return '\n'.join(html_parts)

    def _html_header(self) -> str:
        """Generate HTML header with CSS and JavaScript"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Liquidación OPAEF - Agrupación por Conceptos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #2E3440;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }

        .header {
            background: linear-gradient(135deg, #366092 0%, #3A5F7D 100%);
            color: white;
            padding: 25px;
            border-radius: 8px 8px 0 0;
            margin: -30px -30px 30px -30px;
        }

        .header h1 {
            font-size: 24px;
            margin-bottom: 15px;
        }

        .doc-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #EEF3F7;
            border-radius: 6px;
        }

        .doc-info-item {
            display: flex;
            flex-direction: column;
        }

        .doc-info-label {
            font-weight: bold;
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .doc-info-value {
            font-size: 16px;
            color: #2E3440;
        }

        .year-section {
            margin-bottom: 40px;
        }

        .year-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .year-header {
            background: linear-gradient(135deg, #3A5F7D 0%, #366092 100%);
            color: white;
            text-align: left;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
        }

        .year-table tbody tr {
            border-bottom: 1px solid #d0d0d0;
        }

        .year-table td {
            padding: 12px 15px;
            vertical-align: middle;
        }

        .label-cell {
            font-weight: bold;
            background-color: #D6E4F0;
            color: #2E3440;
            width: 150px;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }

        .value-cell {
            background-color: white;
        }

        .group-separator {
            height: 20px;
            background-color: #f5f5f5;
        }

        .footer-row {
            background: linear-gradient(135deg, #D9E1F2 0%, #D6E4F0 100%);
            font-weight: bold;
            font-size: 16px;
        }

        .footer-row td {
            padding: 15px 20px;
        }

        .copy-btn {
            background-color: #366092;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
            transition: all 0.2s;
        }

        .copy-btn:hover {
            background-color: #2a4d75;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .copy-btn:active {
            transform: translateY(0);
        }

        .copy-btn.copied {
            background-color: #2E7D32;
        }

        .copy-btn.copied::after {
            content: " ✓";
        }

        .texto-sical {
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #2E3440;
            word-break: break-word;
        }

        .amount {
            font-weight: bold;
            color: #2E7D32;
            font-size: 15px;
            text-align: right;
        }

        @media print {
            body {
                background-color: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                padding: 0;
            }

            .copy-btn {
                display: none;
            }

            .year-section {
                page-break-inside: avoid;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }

            .header {
                margin: -15px -15px 20px -15px;
                padding: 15px;
            }

            .doc-info {
                grid-template-columns: 1fr;
            }

            .year-table td {
                font-size: 12px;
                padding: 8px 10px;
            }

            .texto-sical {
                font-size: 11px;
            }
        }
    </style>
    <script>
        function copyToClipboard(text, buttonId) {
            navigator.clipboard.writeText(text).then(function() {
                // Visual feedback
                const button = document.getElementById(buttonId);
                button.classList.add('copied');
                button.textContent = 'Copiado';

                setTimeout(function() {
                    button.classList.remove('copied');
                    button.textContent = 'Copiar';
                }, 2000);
            }).catch(function(err) {
                console.error('Error al copiar: ', err);
                alert('No se pudo copiar al portapapeles');
            });
        }
    </script>
</head>
<body>
    <div class="container">
'''

    def _html_document_info(self) -> str:
        """Generate document information section"""
        fecha_str = self.document.fecha_mandamiento.strftime('%d/%m/%Y') if self.document.fecha_mandamiento else 'N/A'

        return f'''
        <div class="header">
            <h1>Liquidación OPAEF - Agrupación por Conceptos</h1>
        </div>

        <div class="doc-info">
            <div class="doc-info-item">
                <div class="doc-info-label">Entidad</div>
                <div class="doc-info-value">{self.document.entidad} ({self.document.codigo_entidad})</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Nº Liquidación</div>
                <div class="doc-info-value">{self.document.numero_liquidacion}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Mandamiento de Pago</div>
                <div class="doc-info-value">{self.document.mandamiento_pago}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Fecha Mandamiento</div>
                <div class="doc-info-value">{fecha_str}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Ejercicio</div>
                <div class="doc-info-value">{self.document.ejercicio}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Fecha Exportación</div>
                <div class="doc-info-value">{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
        </div>
'''

    def _html_year_table(self, year: int, groups: List[Dict]) -> str:
        """Generate HTML table for a year's groups"""
        year_label = f"Ejercicio {year}" if year else "Todos los ejercicios"

        # Calculate total for footer
        total_liquido = sum(g['liquido'] for g in groups)

        html_parts = [f'''
        <div class="year-section">
            <table class="year-table">
                <thead>
                    <tr>
                        <th colspan="2" class="year-header">{year_label}</th>
                    </tr>
                </thead>
                <tbody>
''']

        # Generate rows for each group
        for idx, group in enumerate(groups):
            group_id = f"group_{year}_{idx}"
            texto_sical = self._build_texto_sical(group['name'], group['records'])
            liquido_formatted = self._format_decimal(group['liquido'])

            # Row 1: Grupo and Texto SICAL
            html_parts.append(f'''
                    <tr>
                        <td class="label-cell">Grupo</td>
                        <td class="value-cell"><strong>{group['name']}</strong></td>
                    </tr>
                    <tr>
                        <td class="label-cell">Texto SICAL</td>
                        <td class="value-cell">
                            <span class="texto-sical">{texto_sical}</span>
                            <button class="copy-btn" id="btn_sical_{group_id}" onclick="copyToClipboard('{self._escape_js(texto_sical)}', 'btn_sical_{group_id}')">Copiar</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="label-cell">Aplicación</td>
                        <td class="value-cell">{group['name']}</td>
                    </tr>
                    <tr>
                        <td class="label-cell">Importe Líquido</td>
                        <td class="value-cell">
                            <span class="amount">{liquido_formatted}</span>
                            <button class="copy-btn" id="btn_amount_{group_id}" onclick="copyToClipboard('{group['liquido']}', 'btn_amount_{group_id}')">Copiar</button>
                        </td>
                    </tr>
''')

            # Add separator between groups (except after last group)
            if idx < len(groups) - 1:
                html_parts.append('                    <tr><td colspan="2" class="group-separator"></td></tr>\n')

        # Footer with total
        html_parts.append(f'''
                    <tr class="footer-row">
                        <td>TOTAL {year_label.upper()}</td>
                        <td class="amount">{self._format_decimal(total_liquido)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
''')

        return ''.join(html_parts)

    def _html_footer(self) -> str:
        """Generate HTML footer"""
        return '''
    </div>
</body>
</html>
'''

    def _escape_js(self, text: str) -> str:
        """Escape text for use in JavaScript string"""
        return text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def export_grouped_to_html(
    document: LiquidationDocument,
    grouping_config: GroupingConfig,
    output_path: str,
    group_by_year: bool = True,
    group_by_concept: bool = True,
    group_by_custom: bool = False
) -> None:
    """
    Convenience function to export grouped concepts to HTML

    Args:
        document: LiquidationDocument with all records
        grouping_config: GroupingConfig with concept and custom group definitions
        output_path: Path where to save the HTML file
        group_by_year: Whether to group by year
        group_by_concept: Whether to group by concept
        group_by_custom: Whether to apply custom grouping
    """
    exporter = HTMLGroupedExporter(document, grouping_config)
    exporter.export_grouped_concepts(output_path, group_by_year, group_by_concept, group_by_custom)
