"""
Script de debug para visualizar todas las tablas de un PDF.
Útil para entender la estructura de los datos extraídos por pdfplumber.

Uso:
    python scripts/debug_pdf_tables.py <ruta_al_pdf> [página] [tabla]
"""
import sys
import io
import pdfplumber
import argparse
from pathlib import Path
from typing import Optional, List, Any, Dict
from table_extraction_settings import TableExtractionSettings, TABLE_EXTRACTION_PARAMETERS

# Configurar encoding UTF-8 para la salida en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def analyze_table_detailed(table: List[List[Any]], table_idx: int, page_num: int):
    """
    Analiza una tabla específica con información detallada.

    Args:
        table: Tabla a analizar
        table_idx: Índice de la tabla
        page_num: Número de página
    """
    print(f"\n{'='*80}")
    print(f"ANÁLISIS DETALLADO - PÁGINA {page_num}, TABLA {table_idx}")
    print(f"{'='*80}\n")

    if not table:
        print("⚠ Tabla vacía\n")
        return

    # Estadísticas generales
    print(f"📊 ESTADÍSTICAS GENERALES")
    print(f"{'─'*80}")
    print(f"  Total de filas: {len(table)}")

    # Determinar número máximo de columnas
    max_cols = max(len(row) for row in table) if table else 0
    print(f"  Columnas máximas: {max_cols}")

    # Analizar consistencia de columnas
    col_counts = {}
    for row in table:
        cols = len(row)
        col_counts[cols] = col_counts.get(cols, 0) + 1

    print(f"\n  Distribución de columnas por fila:")
    for cols, count in sorted(col_counts.items()):
        percentage = (count / len(table)) * 100
        print(f"    {cols} columnas: {count} filas ({percentage:.1f}%)")

    # Análisis de densidad de datos
    print(f"\n📈 DENSIDAD DE DATOS")
    print(f"{'─'*80}")

    total_cells = sum(len(row) for row in table)
    empty_cells = sum(1 for row in table for cell in row if not cell or str(cell).strip() == '')
    filled_cells = total_cells - empty_cells

    if total_cells > 0:
        fill_percentage = (filled_cells / total_cells) * 100
        print(f"  Total de celdas: {total_cells}")
        print(f"  Celdas llenas: {filled_cells} ({fill_percentage:.1f}%)")
        print(f"  Celdas vacías: {empty_cells} ({100-fill_percentage:.1f}%)")

    # Análisis por columna
    print(f"\n📋 ANÁLISIS POR COLUMNA")
    print(f"{'─'*80}")

    for col_idx in range(max_cols):
        col_data = []
        for row in table:
            if col_idx < len(row):
                cell = row[col_idx]
                col_data.append(cell)

        filled = sum(1 for cell in col_data if cell and str(cell).strip())
        empty = len(col_data) - filled

        print(f"\n  Columna {col_idx}:")
        print(f"    Filas con datos: {filled}/{len(col_data)} ({(filled/len(col_data)*100):.1f}%)")

        # Mostrar muestra de valores únicos (primeros 5)
        unique_values = []
        for cell in col_data:
            if cell and str(cell).strip():
                val = str(cell).strip()
                if val not in unique_values:
                    unique_values.append(val)
                if len(unique_values) >= 5:
                    break

        if unique_values:
            print(f"    Muestra de valores:")
            for val in unique_values:
                # Truncar valores largos
                display_val = val[:50] + "..." if len(val) > 50 else val
                display_val = display_val.replace('\n', ' ⏎ ')
                print(f"      • {display_val}")

    # Detección de patrones
    print(f"\n🔍 DETECCIÓN DE PATRONES")
    print(f"{'─'*80}")

    # Identificar fila de encabezado
    header_rows = []
    for idx, row in enumerate(table[:3]):  # Revisar primeras 3 filas
        if row and any(keyword in str(row[0]).upper() for keyword in ['CONCEPTO', 'CLAVE', 'DESCRIPCION', 'EJERCICIO']):
            header_rows.append(idx)

    if header_rows:
        print(f"  Filas de encabezado detectadas: {header_rows}")
    else:
        print(f"  No se detectó fila de encabezado clara")

    # Identificar filas con patrones numéricos
    numeric_rows = []
    for idx, row in enumerate(table):
        if row and len(row) > 3:
            # Contar celdas que parecen números
            numeric_count = 0
            for cell in row[1:]:  # Excluir primera columna (concepto)
                cell_str = str(cell).strip() if cell else ""
                # Verificar si parece un número (puede tener puntos, comas)
                if cell_str and any(c.isdigit() for c in cell_str):
                    numeric_count += 1

            if numeric_count >= 3:  # Al menos 3 campos numéricos
                numeric_rows.append(idx)

    print(f"  Filas con datos numéricos: {len(numeric_rows)}")
    if numeric_rows and len(numeric_rows) <= 5:
        print(f"    Índices: {numeric_rows}")
    elif numeric_rows:
        print(f"    Primeras 5: {numeric_rows[:5]}")
        print(f"    Últimas 5: {numeric_rows[-5:]}")

    # Identificar filas de totales
    total_rows = []
    for idx, row in enumerate(table):
        if row and row[0] and 'TOTAL' in str(row[0]).upper():
            total_rows.append((idx, str(row[0]).strip()))

    if total_rows:
        print(f"\n  Filas de totales detectadas:")
        for idx, text in total_rows:
            print(f"    Fila {idx}: {text}")

    # Identificar filas parciales (solo concepto, sin datos)
    partial_rows = []
    for idx, row in enumerate(table):
        if row and len(row) >= 8:
            first_cell = str(row[0]).strip() if row[0] else ""
            numeric_cells = row[3:10] if len(row) > 9 else row[3:]

            if first_cell:
                all_numeric_empty = all(not str(cell).strip() for cell in numeric_cells)
                if all_numeric_empty:
                    partial_rows.append((idx, first_cell[:50]))

    if partial_rows:
        print(f"\n  Filas parciales (solo concepto): {len(partial_rows)}")
        if len(partial_rows) <= 5:
            for idx, text in partial_rows:
                print(f"    Fila {idx}: {text}")

    # Vista de datos completa
    print(f"\n📄 DATOS COMPLETOS")
    print(f"{'─'*80}\n")

    for row_idx, row in enumerate(table):
        num_cols = len(row) if row else 0
        empty_cells = sum(1 for cell in row if not cell or str(cell).strip() == '')
        non_empty_cells = num_cols - empty_cells

        # Determinar tipo de fila
        row_type = ""
        if row and row[0]:
            row_0_upper = str(row[0]).upper()
            if any(h in row_0_upper for h in ['CONCEPTO', 'CLAVE']):
                row_type = " 📋 HEADER"
            elif 'TOTAL' in row_0_upper:
                row_type = " 📊 TOTAL"
            elif row_idx in [pr[0] for pr in partial_rows]:
                row_type = " 🔴 PARCIAL"
            elif row_idx in numeric_rows:
                row_type = " ✅ DATOS"

        print(f"  Fila {row_idx:2d} [{num_cols} cols, {non_empty_cells} con datos]{row_type}")

        if row:
            for col_idx, cell in enumerate(row):
                cell_str = str(cell) if cell else ""

                # Mostrar celda vacía de forma especial
                if not cell_str.strip():
                    print(f"    [{col_idx:2d}] (vacío)")
                else:
                    # Si la celda contiene saltos de línea, mostrar el contenido completo en múltiples líneas
                    if '\n' in cell_str:
                        lines = cell_str.split('\n')
                        # Indicar tipo de dato
                        data_type = ""
                        if any(c.isdigit() for c in cell_str):
                            if ',' in cell_str or '.' in cell_str:
                                data_type = " [NUM/MULTILINE]"
                            else:
                                data_type = " [INT/MULTILINE]"
                        else:
                            data_type = " [MULTILINE]"

                        print(f"    [{col_idx:2d}] {data_type} ({len(lines)} líneas):")
                        for line_idx, line in enumerate(lines):
                            if line.strip():  # Solo mostrar líneas no vacías
                                # Truncar líneas individuales si son muy largas
                                if len(line) > 100:
                                    line_display = line[:97] + "..."
                                else:
                                    line_display = line
                                print(f"        L{line_idx}: {line_display}")
                    else:
                        # Para celdas sin saltos de línea, truncar si es muy largo
                        if len(cell_str) > 100:
                            cell_display = cell_str[:97] + "..."
                        else:
                            cell_display = cell_str

                        # Indicar tipo de dato
                        data_type = ""
                        if any(c.isdigit() for c in cell_str):
                            if ',' in cell_str or '.' in cell_str:
                                data_type = " [NUM]"
                            else:
                                data_type = " [INT]"
                        print(f"    [{col_idx:2d}] {cell_display}{data_type}")

        print()  # Línea en blanco entre filas

    print(f"{'='*80}\n")


def debug_pdf_tables(pdf_path: str, page_number: Optional[int] = None, table_number: Optional[int] = None,
                     table_settings: Optional[Dict[str, Any]] = None):
    """
    Extrae y muestra todas las tablas de un PDF con formato detallado.

    Args:
        pdf_path: Ruta al archivo PDF
        page_number: Número de página específica a analizar (1-indexed). Si es None, analiza todas.
        table_number: Número de tabla específica a analizar (0-indexed). Requiere page_number. Si es None, analiza todas las tablas.
        table_settings: Diccionario con configuración para extract_tables(). Si es None, usa valores por defecto.
    """
    if table_settings is None:
        table_settings = {}
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"ERROR: Archivo no encontrado: {pdf_path}")
        return

    # Validar que si se especifica tabla, también se especifique página
    if table_number is not None and page_number is None:
        print("ERROR: Para analizar una tabla específica, debes especificar también el número de página.")
        print("Uso: python scripts/debug_pdf_tables.py <ruta_al_pdf> <página> <tabla>")
        return

    print(f"\n{'='*80}")
    print(f"ANÁLISIS DE PDF: {pdf_file.name}")
    print(f"{'='*80}\n")

    # Mostrar configuración de extracción si no es por defecto
    if table_settings:
        print(f"⚙️ Configuración de extracción personalizada:")
        for key, value in sorted(table_settings.items()):
            print(f"  {key}: {value}")
        print()

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        print(f"Total de páginas: {num_pages}")

        # Validar número de página si se especifica
        if page_number is not None:
            if page_number < 1 or page_number > num_pages:
                print(f"\nERROR: Página {page_number} fuera de rango. El PDF tiene {num_pages} página(s).")
                return

            if table_number is not None:
                print(f"Analizando página {page_number}, tabla {table_number} (modo detallado)\n")
            else:
                print(f"Analizando solo página: {page_number}\n")

            pages_to_process = [(page_number, pdf.pages[page_number - 1])]
        else:
            print(f"Analizando todas las páginas\n")
            pages_to_process = list(enumerate(pdf.pages, 1))

        for page_num, page in pages_to_process:
            print(f"\n{'─'*80}")
            print(f"PÁGINA {page_num}")
            print(f"{'─'*80}")

            # Extraer tablas con configuración personalizada
            tables = page.extract_tables(table_settings=table_settings)

            if not tables:
                print("  ⚠ No se encontraron tablas en esta página\n")
                continue

            print(f"  Tablas encontradas: {len(tables)}\n")

            # Si se especificó una tabla específica, validar y mostrar solo esa
            if table_number is not None:
                if table_number < 0 or table_number >= len(tables):
                    print(f"  ERROR: Tabla {table_number} fuera de rango. Esta página tiene {len(tables)} tabla(s) (índices 0-{len(tables)-1}).\n")
                    return

                # Mostrar análisis detallado de la tabla específica
                analyze_table_detailed(tables[table_number], table_number, page_num)
                continue

            # Modo normal: mostrar todas las tablas en resumen
            for table_idx, table in enumerate(tables):
                print(f"\n  {'┌'*40}")
                print(f"  TABLA {table_idx} - {len(table)} filas")
                print(f"  {'└'*40}\n")

                if not table:
                    print("    ⚠ Tabla vacía\n")
                    continue

                for row_idx, row in enumerate(table):
                    # Mostrar información sobre la fila
                    num_cols = len(row) if row else 0

                    # Contar celdas vacías
                    empty_cells = sum(1 for cell in row if not cell or str(cell).strip() == '')
                    non_empty_cells = num_cols - empty_cells

                    # Determinar si es fila parcial (solo concepto, sin datos)
                    is_partial = False
                    if row and len(row) >= 8:
                        first_cell = str(row[0]).strip() if row[0] else ""
                        numeric_cells = row[3:10] if len(row) > 9 else row[3:]
                        clave_cells = row[1:3] if len(row) > 2 else []

                        if first_cell:
                            all_numeric_empty = all(not str(cell).strip() for cell in numeric_cells)
                            all_clave_empty = all(not str(cell).strip() for cell in clave_cells)
                            is_partial = all_numeric_empty and all_clave_empty

                    # Mostrar encabezado de fila
                    row_status = ""
                    if is_partial:
                        row_status = " 🔴 PARCIAL"
                    elif row and any(h in str(row[0]).upper() for h in ['CONCEPTO', 'CLAVE']):
                        row_status = " 📋 HEADER"
                    elif row and 'TOTAL' in str(row[0]).upper() and 'EJERCICIO' in str(row[0]).upper():
                        row_status = " 📊 TOTAL"

                    print(f"    Fila {row_idx:2d} [{num_cols} cols, {non_empty_cells} con datos]{row_status}")

                    # Mostrar cada celda
                    if row:
                        for col_idx, cell in enumerate(row):
                            cell_str = str(cell) if cell else ""

                            # Truncar celdas muy largas
                            if len(cell_str) > 60:
                                cell_display = cell_str[:57] + "..."
                            else:
                                cell_display = cell_str

                            # Indicar si la celda tiene saltos de línea
                            newline_indicator = " ↵" if '\n' in cell_str else ""

                            # Mostrar celda vacía de forma especial
                            if not cell_str.strip():
                                print(f"      [{col_idx:2d}] (vacío)")
                            else:
                                # Reemplazar saltos de línea por símbolo para visualización
                                cell_display_clean = cell_display.replace('\n', ' ⏎ ')
                                print(f"      [{col_idx:2d}] {cell_display_clean}{newline_indicator}")

                    print()  # Línea en blanco entre filas

                print()  # Línea en blanco entre tablas

        print(f"\n{'='*80}")
        print("FIN DEL ANÁLISIS")
        print(f"{'='*80}\n")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Analiza y muestra tablas extraídas de un PDF usando pdfplumber.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Analizar todas las páginas
  python scripts/debug_pdf_tables.py data/ejemplo.pdf

  # Analizar solo la página 2
  python scripts/debug_pdf_tables.py data/ejemplo.pdf --page 2

  # Analizar la tabla 0 de la página 1 (modo detallado)
  python scripts/debug_pdf_tables.py data/ejemplo.pdf --page 1 --table 0

  # Usar configuración personalizada
  python scripts/debug_pdf_tables.py data/ejemplo.pdf --page 1 --table 0 \\
      --vertical-strategy text --snap-tolerance 5

  # Listar todos los parámetros disponibles
  python scripts/debug_pdf_tables.py --list-params
        """
    )

    parser.add_argument('pdf_path', nargs='?', help='Ruta al archivo PDF')
    parser.add_argument('--page', '-p', type=int, help='Número de página a analizar (1-indexed)')
    parser.add_argument('--table', '-t', type=int, help='Número de tabla a analizar (0-indexed, requiere --page)')
    parser.add_argument('--list-params', action='store_true', help='Listar todos los parámetros de extracción disponibles')

    # Agregar argumentos para cada parámetro de configuración
    settings_group = parser.add_argument_group('Parámetros de extracción de tablas')
    for param in TABLE_EXTRACTION_PARAMETERS:
        arg_name = f'--{param.name.replace("_", "-")}'

        if param.type == 'choice':
            settings_group.add_argument(
                arg_name,
                choices=param.choices,
                help=f'{param.description} (default: {param.default})'
            )
        elif param.type == 'bool':
            settings_group.add_argument(
                arg_name,
                action='store_true',
                help=f'{param.description} (default: {param.default})'
            )
        elif param.type in ['int', 'float']:
            arg_type = int if param.type == 'int' else float
            settings_group.add_argument(
                arg_name,
                type=arg_type,
                help=f'{param.description} (default: {param.default}, range: {param.min_value}-{param.max_value})'
            )

    args = parser.parse_args()

    # Si se solicita listar parámetros
    if args.list_params:
        print("\n" + "="*80)
        print("PARÁMETROS DE EXTRACCIÓN DE TABLAS DISPONIBLES")
        print("="*80 + "\n")

        for param in TABLE_EXTRACTION_PARAMETERS:
            print(f"📌 {param.name}")
            print(f"   Tipo: {param.type}")
            print(f"   Descripción: {param.description}")
            print(f"   Valor por defecto: {param.default}")

            if param.type == 'choice':
                print(f"   Opciones: {', '.join(str(c) for c in param.choices)}")
            elif param.type in ['int', 'float']:
                print(f"   Rango: {param.min_value} - {param.max_value} (paso: {param.step})")

            print()

        sys.exit(0)

    # Validar que se proporcione un PDF
    if not args.pdf_path:
        parser.print_help()
        sys.exit(1)

    # Construir diccionario de configuración con valores no-default
    table_settings = {}
    for param in TABLE_EXTRACTION_PARAMETERS:
        arg_value = getattr(args, param.name, None)
        if arg_value is not None:
            table_settings[param.name] = arg_value

    debug_pdf_tables(args.pdf_path, args.page, args.table, table_settings)


if __name__ == "__main__":
    main()
