"""
GUI para el análisis de tablas en PDFs.
Proporciona una interfaz gráfica para visualizar y analizar tablas extraídas de documentos PDF.

Uso:
    python scripts/debug_pdf_tables_gui.py
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import pdfplumber
from pathlib import Path
import sys
import io
from contextlib import redirect_stdout
from typing import Optional

# Importar las funciones del script original
from debug_pdf_tables import analyze_table_detailed
from table_extraction_settings import (
    TableExtractionSettings,
    TABLE_EXTRACTION_PARAMETERS,
    ParameterConfig
)


class PDFTableDebugger(tk.Tk):
    """Aplicación GUI para análisis de tablas PDF."""

    def __init__(self):
        super().__init__()

        self.title("Debug de Tablas PDF - Liquidación OPAEF")
        self.geometry("1000x700")

        # Variables
        self.pdf_path = tk.StringVar()
        self.page_var = tk.StringVar(value="Todas")
        self.table_var = tk.StringVar(value="Todas")
        self.current_pdf = None
        self.num_pages = 0
        self.tables_in_page = {}

        # Settings de extracción de tablas
        self.extraction_settings = TableExtractionSettings()
        self.settings_widgets = {}  # Almacenar referencias a widgets de settings

        self._create_widgets()
        self._layout_widgets()
        self._update_settings_visibility()

    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""

        # Frame superior - Selección de archivo
        self.file_frame = ttk.LabelFrame(self, text="Archivo PDF", padding=10)

        self.path_entry = ttk.Entry(self.file_frame, textvariable=self.pdf_path, width=60, state='readonly')
        self.browse_btn = ttk.Button(self.file_frame, text="Examinar...", command=self._browse_file)

        # Frame de opciones
        self.options_frame = ttk.LabelFrame(self, text="Opciones de Análisis", padding=10)

        # Página
        ttk.Label(self.options_frame, text="Página:").grid(row=0, column=0, sticky='w', padx=5)
        self.page_combo = ttk.Combobox(self.options_frame, textvariable=self.page_var, width=15, state='readonly')
        self.page_combo['values'] = ['Todas']
        self.page_combo.bind('<<ComboboxSelected>>', self._on_page_selected)

        # Tabla
        ttk.Label(self.options_frame, text="Tabla:").grid(row=0, column=2, sticky='w', padx=5)
        self.table_combo = ttk.Combobox(self.options_frame, textvariable=self.table_var, width=15, state='readonly')
        self.table_combo['values'] = ['Todas']

        # Botones de acción
        self.action_frame = ttk.Frame(self.options_frame)
        self.analyze_btn = ttk.Button(self.action_frame, text="Analizar", command=self._analyze, state='disabled')
        self.export_btn = ttk.Button(self.action_frame, text="Exportar Resultado", command=self._export_result, state='disabled')
        self.clear_btn = ttk.Button(self.action_frame, text="Limpiar", command=self._clear_output)

        # Frame de configuración de extracción (solo visible para tabla específica)
        self.settings_frame = ttk.LabelFrame(self, text="⚙️ Configuración de Extracción de Tablas", padding=10)
        self._create_settings_widgets()

        # Frame de resultados
        self.results_frame = ttk.LabelFrame(self, text="Resultados del Análisis", padding=10)

        # Área de texto con scroll
        self.output_text = scrolledtext.ScrolledText(
            self.results_frame,
            wrap=tk.WORD,
            font=('Courier New', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )

        # Barra de estado
        self.status_bar = ttk.Label(self, text="Listo", relief=tk.SUNKEN, anchor=tk.W)

    def _create_settings_widgets(self):
        """Crea los widgets de configuración de extracción."""
        # Crear notebook con pestañas para organizar los parámetros
        self.settings_notebook = ttk.Notebook(self.settings_frame)

        # Organizar parámetros por categoría
        categories = {
            "Estrategias": ["vertical_strategy", "horizontal_strategy"],
            "Tolerancias Snap": ["snap_tolerance", "snap_x_tolerance", "snap_y_tolerance"],
            "Tolerancias Join": ["join_tolerance", "join_x_tolerance", "join_y_tolerance"],
            "Tolerancias Intersección": ["intersection_tolerance", "intersection_x_tolerance", "intersection_y_tolerance"],
            "Otros": ["edge_min_length", "min_words_vertical", "min_words_horizontal"]
        }

        for category, param_names in categories.items():
            frame = ttk.Frame(self.settings_notebook, padding=10)
            self.settings_notebook.add(frame, text=category)

            row = 0
            for param_name in param_names:
                param = next(p for p in TABLE_EXTRACTION_PARAMETERS if p.name == param_name)
                self._create_setting_control(frame, param, row)
                row += 1

        # Botón para restaurar defaults
        self.restore_btn = ttk.Button(
            self.settings_frame,
            text="🔄 Restaurar Valores por Defecto",
            command=self._restore_defaults
        )

    def _create_setting_control(self, parent: ttk.Frame, param: ParameterConfig, row: int):
        """Crea un control para un parámetro específico."""
        # Label
        label = ttk.Label(parent, text=f"{param.name.replace('_', ' ').title()}:")
        label.grid(row=row, column=0, sticky='w', padx=5, pady=5)

        # Tooltip con descripción
        tooltip_btn = ttk.Label(parent, text="ℹ️", foreground="blue", cursor="hand2")
        tooltip_btn.grid(row=row, column=1, padx=2)
        self._create_tooltip(tooltip_btn, param.description)

        if param.type == 'choice':
            # Combobox para opciones
            var = tk.StringVar(value=str(param.default))
            combo = ttk.Combobox(parent, textvariable=var, values=param.choices, width=15, state='readonly')
            combo.grid(row=row, column=2, sticky='ew', padx=5)
            combo.bind('<<ComboboxSelected>>', lambda e, p=param.name: self._on_setting_changed(p))
            self.settings_widgets[param.name] = ('choice', var, combo)

        elif param.type == 'bool':
            # Checkbox para booleanos
            var = tk.BooleanVar(value=param.default)
            check = ttk.Checkbutton(parent, variable=var, command=lambda p=param.name: self._on_setting_changed(p))
            check.grid(row=row, column=2, sticky='w', padx=5)
            self.settings_widgets[param.name] = ('bool', var, check)

        elif param.type in ['int', 'float']:
            # Frame para slider + spinbox
            control_frame = ttk.Frame(parent)
            control_frame.grid(row=row, column=2, sticky='ew', padx=5)
            control_frame.columnconfigure(0, weight=1)

            var = tk.DoubleVar(value=param.default) if param.type == 'float' else tk.IntVar(value=param.default)

            # Slider
            slider = ttk.Scale(
                control_frame,
                from_=param.min_value,
                to=param.max_value,
                orient='horizontal',
                variable=var,
                command=lambda v, p=param.name: self._on_setting_changed(p)
            )
            slider.grid(row=0, column=0, sticky='ew', padx=(0, 5))

            # Spinbox para valores precisos
            spinbox = ttk.Spinbox(
                control_frame,
                from_=param.min_value,
                to=param.max_value,
                increment=param.step,
                textvariable=var,
                width=8,
                command=lambda p=param.name: self._on_setting_changed(p)
            )
            spinbox.grid(row=0, column=1)

            self.settings_widgets[param.name] = ('numeric', var, (slider, spinbox))

        # Mostrar valor por defecto
        default_label = ttk.Label(parent, text=f"(default: {param.default})", font=('TkDefaultFont', 8), foreground='gray')
        default_label.grid(row=row, column=3, sticky='w', padx=5)

        parent.columnconfigure(2, weight=1)

    def _create_tooltip(self, widget, text):
        """Crea un tooltip simple para un widget."""
        def on_enter(event):
            self.status_bar.config(text=text)

        def on_leave(event):
            self.status_bar.config(text="Listo")

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _on_setting_changed(self, param_name: str):
        """Callback cuando cambia un setting."""
        if param_name in self.settings_widgets:
            widget_type, var, widget = self.settings_widgets[param_name]
            value = var.get()

            # Actualizar el objeto de configuración
            self.extraction_settings.update(**{param_name: value})

            # Mostrar en status bar
            self.status_bar.config(text=f"Parámetro actualizado: {param_name} = {value}")

    def _restore_defaults(self):
        """Restaura todos los parámetros a sus valores por defecto."""
        self.extraction_settings.reset_to_defaults()

        # Actualizar todos los widgets
        for param in TABLE_EXTRACTION_PARAMETERS:
            if param.name in self.settings_widgets:
                widget_type, var, widget = self.settings_widgets[param.name]
                var.set(param.default)

        self.status_bar.config(text="Valores restaurados a configuración por defecto")
        messagebox.showinfo("Valores Restaurados", "Todos los parámetros han sido restaurados a sus valores por defecto.")

    def _layout_widgets(self):
        """Organiza los widgets en la ventana."""

        # Frame de archivo
        self.file_frame.pack(fill='x', padx=10, pady=5)
        self.path_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.browse_btn.pack(side='right')

        # Frame de opciones
        self.options_frame.pack(fill='x', padx=10, pady=5)
        self.page_combo.grid(row=0, column=1, padx=5)
        self.table_combo.grid(row=0, column=3, padx=5)
        self.table_combo.bind('<<ComboboxSelected>>', self._on_table_selection_changed)

        self.action_frame.grid(row=0, column=4, padx=20)
        self.analyze_btn.pack(side='left', padx=2)
        self.export_btn.pack(side='left', padx=2)
        self.clear_btn.pack(side='left', padx=2)

        # Frame de configuración (no visible por defecto)
        # Se mostrará solo cuando se seleccione una tabla específica
        self.settings_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        self.restore_btn.pack(pady=5)

        # Frame de resultados
        self.results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.output_text.pack(fill='both', expand=True)

        # Barra de estado
        self.status_bar.pack(fill='x', side='bottom')

    def _browse_file(self):
        """Abre el diálogo de selección de archivo."""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )

        if filename:
            self.pdf_path.set(filename)
            self._load_pdf_info(filename)

    def _load_pdf_info(self, pdf_path: str):
        """Carga información del PDF y actualiza los combos."""
        try:
            self.current_pdf = pdfplumber.open(pdf_path)
            self.num_pages = len(self.current_pdf.pages)

            # Actualizar combo de páginas
            pages = ['Todas'] + [str(i) for i in range(1, self.num_pages + 1)]
            self.page_combo['values'] = pages
            self.page_var.set('Todas')

            # Escanear tablas por página
            self.tables_in_page = {}
            for i, page in enumerate(self.current_pdf.pages, 1):
                tables = page.extract_tables()
                self.tables_in_page[i] = len(tables)

            # Resetear combo de tablas
            self.table_combo['values'] = ['Todas']
            self.table_var.set('Todas')

            # Habilitar botón de análisis
            self.analyze_btn['state'] = 'normal'

            # Actualizar estado
            total_tables = sum(self.tables_in_page.values())
            self.status_bar.config(text=f"PDF cargado: {self.num_pages} página(s), {total_tables} tabla(s) encontrada(s)")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el PDF:\n{str(e)}")
            self.status_bar.config(text="Error al cargar PDF")

    def _on_page_selected(self, event=None):
        """Actualiza el combo de tablas según la página seleccionada."""
        page_str = self.page_var.get()

        if page_str == 'Todas':
            self.table_combo['values'] = ['Todas']
            self.table_var.set('Todas')
        else:
            try:
                page_num = int(page_str)
                num_tables = self.tables_in_page.get(page_num, 0)

                if num_tables > 0:
                    tables = ['Todas'] + [str(i) for i in range(num_tables)]
                    self.table_combo['values'] = tables
                    self.table_var.set('Todas')
                    self.status_bar.config(text=f"Página {page_num}: {num_tables} tabla(s)")
                else:
                    self.table_combo['values'] = ['Todas']
                    self.table_var.set('Todas')
                    self.status_bar.config(text=f"Página {page_num}: No se encontraron tablas")

            except ValueError:
                pass

        # Actualizar visibilidad de settings
        self._update_settings_visibility()

    def _on_table_selection_changed(self, event=None):
        """Callback cuando cambia la selección de tabla."""
        self._update_settings_visibility()

    def _update_settings_visibility(self):
        """Muestra u oculta el panel de configuración según la selección."""
        page_str = self.page_var.get()
        table_str = self.table_var.get()

        # Solo mostrar settings cuando se selecciona una página específica Y una tabla específica
        show_settings = (page_str != 'Todas' and table_str != 'Todas')

        if show_settings:
            # Mostrar el frame de settings
            if not self.settings_frame.winfo_ismapped():
                self.settings_frame.pack(fill='x', padx=10, pady=5, before=self.results_frame)
        else:
            # Ocultar el frame de settings
            if self.settings_frame.winfo_ismapped():
                self.settings_frame.pack_forget()

    def _analyze(self):
        """Realiza el análisis según las opciones seleccionadas."""
        if not self.current_pdf:
            messagebox.showwarning("Advertencia", "Debe cargar un archivo PDF primero")
            return

        self._clear_output()

        page_str = self.page_var.get()
        table_str = self.table_var.get()

        page_number = None if page_str == 'Todas' else int(page_str)
        table_number = None if table_str == 'Todas' else int(table_str)

        # Redirigir stdout para capturar la salida
        output_buffer = io.StringIO()

        try:
            with redirect_stdout(output_buffer):
                self._run_analysis(page_number, table_number)

            # Mostrar resultado
            result = output_buffer.getvalue()
            self.output_text.insert('1.0', result)
            self.export_btn['state'] = 'normal'

            # Actualizar estado
            mode = "detallado" if table_number is not None else "resumen"
            self.status_bar.config(text=f"Análisis completado - Modo: {mode}")

        except Exception as e:
            error_msg = f"ERROR: {str(e)}\n"
            self.output_text.insert('1.0', error_msg)
            self.status_bar.config(text="Error durante el análisis")
            messagebox.showerror("Error", f"Error durante el análisis:\n{str(e)}")

    def _run_analysis(self, page_number: Optional[int], table_number: Optional[int]):
        """Ejecuta el análisis de tablas."""
        pdf_path = self.pdf_path.get()
        pdf_file = Path(pdf_path)

        print(f"{'='*80}")
        print(f"ANÁLISIS DE PDF: {pdf_file.name}")
        print(f"{'='*80}\n")

        num_pages = len(self.current_pdf.pages)
        print(f"Total de páginas: {num_pages}")

        # Obtener configuración de extracción
        table_settings = self.extraction_settings.get_table_settings_dict()

        # Mostrar configuración si no es por defecto
        if table_settings:
            print(f"\n⚙️ Configuración de extracción personalizada:")
            for key, value in sorted(table_settings.items()):
                print(f"  {key}: {value}")
            print()

        if page_number is not None:
            if table_number is not None:
                print(f"Analizando página {page_number}, tabla {table_number} (modo detallado)\n")
            else:
                print(f"Analizando solo página: {page_number}\n")

            pages_to_process = [(page_number, self.current_pdf.pages[page_number - 1])]
        else:
            print(f"Analizando todas las páginas\n")
            pages_to_process = list(enumerate(self.current_pdf.pages, 1))

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

            if table_number is not None:
                if table_number < 0 or table_number >= len(tables):
                    print(f"  ERROR: Tabla {table_number} fuera de rango. Esta página tiene {len(tables)} tabla(s) (índices 0-{len(tables)-1}).\n")
                    return

                analyze_table_detailed(tables[table_number], table_number, page_num)
                continue

            # Modo resumen
            for table_idx, table in enumerate(tables):
                print(f"\n  {'┌'*40}")
                print(f"  TABLA {table_idx} - {len(table)} filas")
                print(f"  {'└'*40}\n")

                if not table:
                    print("    ⚠ Tabla vacía\n")
                    continue

                # Mostrar solo primeras filas en modo resumen
                max_rows_summary = 5
                for row_idx, row in enumerate(table[:max_rows_summary]):
                    num_cols = len(row) if row else 0
                    empty_cells = sum(1 for cell in row if not cell or str(cell).strip() == '')
                    non_empty_cells = num_cols - empty_cells

                    print(f"    Fila {row_idx:2d} [{num_cols} cols, {non_empty_cells} con datos]")

                    if row:
                        for col_idx, cell in enumerate(row):
                            cell_str = str(cell) if cell else ""
                            if len(cell_str) > 50:
                                cell_display = cell_str[:47] + "..."
                            else:
                                cell_display = cell_str

                            if not cell_str.strip():
                                print(f"      [{col_idx:2d}] (vacío)")
                            else:
                                cell_display_clean = cell_display.replace('\n', ' ⏎ ')
                                print(f"      [{col_idx:2d}] {cell_display_clean}")

                    print()

                if len(table) > max_rows_summary:
                    print(f"    ... y {len(table) - max_rows_summary} fila(s) más\n")
                    print(f"    💡 Para análisis detallado, selecciona esta tabla específicamente\n")

                print()

        print(f"\n{'='*80}")
        print("FIN DEL ANÁLISIS")
        print(f"{'='*80}\n")

    def _export_result(self):
        """Exporta los resultados a un archivo de texto."""
        content = self.output_text.get('1.0', tk.END)

        if not content.strip():
            messagebox.showwarning("Advertencia", "No hay resultados para exportar")
            return

        filename = filedialog.asksaveasfilename(
            title="Guardar resultados",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Éxito", f"Resultados exportados a:\n{filename}")
                self.status_bar.config(text=f"Resultados exportados: {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar:\n{str(e)}")

    def _clear_output(self):
        """Limpia el área de resultados."""
        self.output_text.delete('1.0', tk.END)
        self.export_btn['state'] = 'disabled'

    def destroy(self):
        """Limpia recursos al cerrar."""
        if self.current_pdf:
            self.current_pdf.close()
        super().destroy()


def main():
    """Función principal."""
    app = PDFTableDebugger()
    app.mainloop()


if __name__ == "__main__":
    main()
