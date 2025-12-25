# Liquidación OPAEF - Extractor de Datos

Aplicación de escritorio para procesar documentos de liquidación de la Diputación Provincial (formato OPAEF/MOD 2).

## Características

- Extracción precisa de registros de cobros por tributo
- Procesamiento de liquidaciones municipales
- Exportación a Excel con formato profesional
- Validación automática de totales
- Interfaz moderna y fácil de usar
- Portable - no requiere instalación

## Tipos de Datos Extraídos

### 1. Registros de Cobros (Página 1)
- IBI Rústica y Urbana
- Impuesto sobre Vehículos de Tracción Mecánica (IVTM)
- Multas de Tráfico/Circulación
- Importes: Voluntaria, Ejecutiva, Recargo
- Claves de Contabilidad y Recaudación

### 2. Resumen por Ejercicio
- Totales agrupados por año fiscal
- Cálculos de líquido
- Validación de sumas

### 3. Deducciones (Página 2)
- Tasas de recaudación
- Tasas tributarias (gestión censal, catastral)
- Multas y sanciones
- Anticipos desglosados por concepto
- Expedientes de ingresos indebidos

### 4. Devoluciones (Página 3)
- Expedientes de devolución individuales
- Resumen por concepto
- Intereses calculados

## Instalación

### Requisitos
- Python 3.8 o superior
- Windows 10/11 (puede adaptarse a Linux/Mac)

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar la Aplicación

```bash
python main.py
```

### Flujo de Trabajo

1. **Cargar PDF**: Haz clic en "Cargar PDF" y selecciona un documento de liquidación
2. **Revisar Datos**: Navega por las pestañas para ver los datos extraídos:
   - Registros de Cobros
   - Resumen por Ejercicio
   - Deducciones
   - Devoluciones
3. **Validar**: Haz clic en "Validar Datos" para verificar la integridad
4. **Exportar**: Haz clic en "Exportar a Excel" para guardar los datos

### Exportación a Excel

El archivo Excel generado contiene múltiples hojas:
- **Información**: Datos del documento
- **Registros de Cobros**: Tabla completa de tributos
- **Resumen por Ejercicio**: Totales por año
- **Deducciones**: Desglose completo
- **Anticipos**: Descuentos por concepto
- **Devoluciones**: Expedientes y resumen

## Estructura del Proyecto

```
liquidacion-opaef/
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── src/
│   ├── gui/               # Interfaz gráfica
│   │   └── main_window.py
│   ├── extractors/        # Extracción de PDF
│   │   └── pdf_extractor.py
│   ├── models/            # Modelos de datos
│   │   └── liquidation.py
│   ├── exporters/         # Exportación
│   │   └── excel_exporter.py
│   ├── validators/        # Validaciones (futuro)
│   └── utils/             # Utilidades
├── scripts/               # Herramientas de desarrollo
│   ├── debug_pdf_tables.py
│   └── debug_pdf_tables_gui.py
├── config/                # Configuraciones
└── tests/                 # Tests unitarios
```

## Creación de Ejecutable Portable

Para crear un archivo .exe portable:

```bash
pyinstaller --onefile --windowed --name="LiquidacionOPAEF" main.py
```

El ejecutable se generará en la carpeta `dist/`.

## Validaciones Implementadas

La aplicación implementa un sistema de validación de dos niveles para garantizar la integridad de los datos extraídos:

### Validación Global (Nivel Documento)

- **Verificación de sumas totales**: Compara la suma de TODOS los registros de cobros contra los totales documentados en el PDF
- **Validación de fórmula A LIQUIDAR**: Verifica que `A Liquidar = Líquido Total - Deducciones`
- **Tolerancia**: ±0.01€ (un céntimo) para evitar falsos positivos por redondeos

### Validación Por Año Fiscal (Nivel Ejercicio) ⭐ NUEVO

Para cada año fiscal presente en el documento, la aplicación valida que la suma de los registros individuales coincida con el "TOTAL EJERCICIO" documentado en el PDF:

- **Validación por ejercicio**: Para cada año (ej. 2024, 2025), suma los registros individuales y los compara contra el total documentado
- **Verificación exhaustiva**: Valida cada columna (Voluntaria, Ejecutiva, Recargo, Diputación Voluntaria, Diputación Ejecutiva, Diputación Recargo, Líquido)
- **Indicadores visuales en pestaña "Registros de Cobros"**:
  - ✓ **Marca verde**: Si el total calculado coincide con el total documentado (fondo verde claro)
  - ⚠ **Fila roja de advertencia**: Si hay discrepancia, se muestra una fila adicional "CALCULADO" con los valores calculados (fondo rojo claro)
- **Detección temprana de errores**: Permite identificar problemas de extracción específicos de un año sin necesidad de analizar todo el documento

#### Interpretación de Resultados

**Escenario 1: Validación Exitosa**
```
▸ EJERCICIO 2024 (15 registros)
[... registros individuales ...]
✓ TOTAL EJERCICIO 2024    [fondo verde claro]
  1,250.00  2,380.50  ...
```

**Escenario 2: Discrepancia Detectada**
```
▸ EJERCICIO 2024 (15 registros)
[... registros individuales ...]
TOTAL EJERCICIO 2024      [fondo gris - valor del PDF]
  1,250.00  2,380.50  ...
⚠ CALCULADO (discrepancia detectada)  [fondo rojo claro]
  1,245.30  2,380.50  ...  <- Valores calculados
```

**¿Qué hacer si hay discrepancias?**
1. Verificar visualmente el PDF original - puede haber un error en el documento
2. Revisar si algún registro fue mal extraído o está duplicado
3. Comprobar la configuración de extracción de tablas (ver "Configuración de Extracción PDF" en la interfaz)
4. Utilizar las herramientas de depuración (`scripts/debug_pdf_tables.py`) para analizar la estructura del PDF

#### Ventajas de la Validación Por Año

- **Granularidad**: Detecta errores específicos de un año que podrían compensarse en el total global
- **Precisión**: Identifica exactamente qué ejercicio tiene problemas
- **Transparencia**: Muestra tanto el valor documentado como el calculado para facilitar la investigación
- **Automatización**: No requiere cálculos manuales por parte del usuario

## Próximas Características

Las siguientes funcionalidades se desarrollarán en fase 2:

- [ ] Procesamiento por lotes (múltiples PDFs)
- [ ] Agrupaciones personalizadas
- [ ] Generación de plantillas contables
- [ ] Análisis comparativo entre periodos
- [ ] Filtros y búsquedas avanzadas
- [ ] Exportación a otros formatos (CSV, JSON)
- [ ] Configuración de patrones contables
- [ ] Reportes personalizados

## Herramientas de Desarrollo

### Script de Debug de Tablas PDF

El script `debug_pdf_tables.py` es una herramienta crítica para analizar y optimizar la extracción de datos de documentos PDF. Permite visualizar la estructura exacta de las tablas tal como las detecta `pdfplumber`, facilitando la identificación de problemas y la mejora del rendimiento.

#### Características

- **Modo resumen**: Visualiza todas las tablas de todas las páginas
- **Modo página**: Analiza solo una página específica
- **Modo detallado**: Análisis profundo de una tabla específica con:
  - Estadísticas generales (filas, columnas, densidad de datos)
  - Análisis por columna (valores únicos, porcentaje de datos)
  - Detección automática de patrones (encabezados, totales, filas parciales)
  - Identificación de datos numéricos
  - Vista completa con tipado de datos

#### Uso

```bash
# Analizar todas las páginas del PDF (modo resumen)
python scripts/debug_pdf_tables.py data/ejemplo.pdf

# Analizar solo la página 2
python scripts/debug_pdf_tables.py data/ejemplo.pdf 2

# Analizar la tabla 0 de la página 1 (modo detallado)
python scripts/debug_pdf_tables.py data/ejemplo.pdf 1 0
```

#### Parámetros

- `<ruta_al_pdf>`: Ruta al archivo PDF a analizar (requerido)
- `[página]`: Número de página a analizar (1-indexed, opcional)
- `[tabla]`: Número de tabla a analizar (0-indexed, opcional, requiere página)

#### Salida del Modo Detallado

El modo detallado proporciona información exhaustiva:

1. **Estadísticas Generales**
   - Total de filas y columnas
   - Distribución de columnas por fila
   - Detección de inconsistencias estructurales

2. **Densidad de Datos**
   - Porcentaje de celdas llenas vs vacías
   - Total de celdas analizadas

3. **Análisis por Columna**
   - Porcentaje de filas con datos por columna
   - Muestra de valores únicos (primeros 5)
   - Identificación de patrones de datos

4. **Detección de Patrones**
   - Filas de encabezado (CONCEPTO, CLAVE, etc.)
   - Filas con datos numéricos
   - Filas de totales
   - Filas parciales (solo concepto sin datos)

5. **Vista Completa de Datos**
   - Cada celda con su contenido
   - Tipado automático ([NUM], [INT])
   - Indicadores de filas especiales (📋 HEADER, 📊 TOTAL, 🔴 PARCIAL, ✅ DATOS)

#### Utilidad para Optimización

Esta herramienta es esencial para:

- **Diagnosticar problemas de extracción**: Identificar por qué ciertos datos no se extraen correctamente
- **Optimizar parsers**: Entender la estructura real de las tablas para ajustar la lógica de extracción
- **Validar cambios**: Verificar que modificaciones en el código no afecten la detección de tablas
- **Documentar estructura**: Generar reportes de la estructura de datos de los PDFs

### Versión GUI del Script de Debug

Para una experiencia más visual e interactiva, también está disponible una interfaz gráfica:

```bash
python scripts/debug_pdf_tables_gui.py
```

#### Características de la GUI

- **Interfaz intuitiva**: Selección visual de archivo, página y tabla
- **Vista previa en tiempo real**: Resultados mostrados en un área de texto con sintaxis destacada
- **Exportación fácil**: Guarda los resultados en archivos de texto
- **Estadísticas automáticas**: Muestra el número de páginas y tablas detectadas
- **Modo oscuro**: Editor con tema oscuro para mejor legibilidad

La GUI proporciona las mismas capacidades de análisis que la versión CLI, pero con una experiencia más amigable para usuarios que prefieren interfaces gráficas.

## Soporte

Para reportar errores o solicitar funcionalidades, contacta al equipo de desarrollo.

## Notas Técnicas

### Precisión de Extracción

La aplicación utiliza `pdfplumber` para extraer tablas estructuradas del PDF. La precisión es crítica para datos contables, por lo que:

- Se utilizan tipos `Decimal` para evitar errores de redondeo
- Se validan automáticamente todos los totales
- Se mantiene la trazabilidad con claves de contabilidad

### Formato de Números

La aplicación maneja correctamente:
- Formato europeo: 1.234,56
- Separadores de miles
- Decimales con coma o punto

## Licencia

Uso interno - Todos los derechos reservados
