# Scripts de Utilidad

Este directorio contiene scripts auxiliares para debug y análisis.

## debug_pdf_tables.py

Script para visualizar todas las tablas extraídas de un PDF.

**Uso:**
```bash
python scripts/debug_pdf_tables.py <ruta_al_pdf> [página]
```

**Ejemplos:**
```bash
# Analizar todas las páginas del PDF
python scripts/debug_pdf_tables.py data/documentos/liquidacion_ejemplo.pdf

# Analizar solo la página 2
python scripts/debug_pdf_tables.py data/documentos/liquidacion_ejemplo.pdf 2

# Analizar la última página de un documento de 3 páginas
python scripts/debug_pdf_tables.py data/documentos/liquidacion_ejemplo.pdf 3
```

**Características:**
- Muestra todas las páginas y tablas del PDF
- Indica filas parciales (🔴 PARCIAL) que necesitan ser combinadas
- Marca headers (📋 HEADER) y totales (📊 TOTAL)
- Muestra el contenido de cada celda
- Indica celdas con saltos de línea (↵)
- Cuenta celdas vacías vs. con datos

**Output de ejemplo:**
```
================================================================================
ANÁLISIS DE PDF: liquidacion_ejemplo.pdf
================================================================================

Total de páginas: 3

────────────────────────────────────────────────────────────────────────────────
PÁGINA 1
────────────────────────────────────────────────────────────────────────────────
  Tablas encontradas: 1

  ┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌┌
  TABLA 0 - 15 filas
  └└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└└

    Fila  0 [10 cols, 9 con datos] 📋 HEADER
      [ 0] CONCEPTO
      [ 1] CLAVE CONTABILIDAD
      ...
```
