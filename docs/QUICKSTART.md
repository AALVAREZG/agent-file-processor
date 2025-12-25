# Quick Start Guide - Liquidación OPAEF

## Instalación Rápida

### 1. Activar entorno virtual

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Verificar instalación

```bash
python test_extraction.py
```

### 3. Ejecutar aplicación

```bash
python main.py
```

## Uso Básico

### Cargar un PDF

1. Inicia la aplicación con `python main.py`
2. Haz clic en **"Cargar PDF"**
3. Selecciona un archivo PDF de liquidación
4. La aplicación extraerá automáticamente todos los datos

### Ver los datos extraídos

Navega por las pestañas:

- **Registros de Cobros**: Tabla completa de tributos
- **Resumen por Ejercicio**: Totales por año fiscal
- **Deducciones**: Tasas, anticipos, y deducciones
- **Devoluciones**: Expedientes de devolución

### Exportar a Excel

1. Con un PDF cargado, haz clic en **"Exportar a Excel"**
2. Elige ubicación y nombre del archivo
3. Se generará un archivo .xlsx con múltiples hojas

### Validar datos

1. Haz clic en **"Validar Datos"**
2. La aplicación verificará que los totales coincidan
3. Se mostrarán advertencias si hay discrepancias

## Datos Extraídos

### Tributos Capturados

- **IBI Rústica**: Impuesto sobre Bienes Inmuebles rústicos
- **IBI Urbana**: Impuesto sobre Bienes Inmuebles urbanos
- **IVTM**: Impuesto sobre Vehículos de Tracción Mecánica
- **Multas**: Multas de tráfico y circulación
- **Cánones**: Cánones y tasas municipales
- **Otros**: IAE, BICE, tasas diversas

### Campos por Registro

- Concepto (tipo de tributo)
- Clave de Contabilidad
- Clave de Recaudación
- Importes:
  - Voluntaria
  - Ejecutiva
  - Recargo
  - Diputación (voluntaria, ejecutiva, recargo)
  - Líquido (total)

### Deducciones Extraídas

- Tasas de recaudación (voluntaria, ejecutiva)
- Tasas de gestión (tributaria, censal, catastral)
- Multas y sanciones
- Anticipos desglosados por concepto
- Expedientes de compensación
- Expedientes de ingresos indebidos

### Devoluciones

- Número de expediente
- Número de resolución
- Importes (total, entidad, diputación, intereses)
- Resumen por concepto

## Solución de Problemas

### Error: "No module named 'pdfplumber'"

```bash
pip install -r requirements.txt
```

### Error: "Failed to extract PDF"

- Verifica que el archivo sea un PDF válido
- Asegúrate de que el PDF tenga el formato OPAEF (MOD 2)
- Revisa que el PDF no esté protegido o encriptado

### Validación muestra advertencias

Es normal ver algunas advertencias de validación debido a:
- Diferencias de redondeo
- Totales de ejercicio no capturados correctamente en versión inicial
- La extracción de registros individuales sigue siendo precisa

### GUI no se muestra

Asegúrate de tener instalado customtkinter:

```bash
pip install customtkinter
```

## Próximos Pasos

Una vez familiarizado con la aplicación:

1. **Procesa múltiples archivos** para análisis comparativo
2. **Exporta a Excel** y usa fórmulas para análisis adicional
3. **Revisa las claves contables** para categorizar correctamente
4. **Contacta al equipo** para solicitar funcionalidades adicionales

## Comandos Útiles

```bash
# Activar venv
venv\Scripts\activate

# Ejecutar tests
python test_extraction.py

# Ejecutar aplicación
python main.py

# Crear ejecutable portable
pyinstaller --onefile --windowed --name="LiquidacionOPAEF" main.py
```

## Soporte

Para reportar problemas o solicitar funcionalidades, contacta al equipo de desarrollo.
