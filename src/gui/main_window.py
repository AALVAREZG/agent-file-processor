"""
Main GUI window for Liquidation OPAEF Application.

Built with CustomTkinter for a modern, professional appearance.
Uses ttk.Treeview for fancy table display with excellent readability.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from typing import Optional, List
import threading
from pathlib import Path

from src.models.liquidation import LiquidationDocument
from src.extractors.pdf_extractor import extract_liquidation_pdf, PDFExtractionError
from src.exporters.excel_exporter import export_to_excel
from src.exporters.html_grouped_exporter import export_grouped_to_html
from src.utils.config_manager import ConfigManager
from src.gui.config_dialog import ConfigDialog
from src.gui import info_messages
from src.gui.info_dialog import InfoDialog


# Configure CustomTkinter appearance
ctk.set_appearance_mode("light")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("Liquidación OPAEF - Extractor de Datos")
        self.geometry("1600x900")

        # Current loaded document
        self.current_document: Optional[LiquidationDocument] = None
        self.current_file_path: Optional[Path] = None

        # Display settings
        self.show_diputacion_columns = True  # Visible by default

        # Configuration manager
        self.config_manager = ConfigManager()

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left sidebar for controls
        self._create_sidebar()

        # Main content area
        self._create_main_area()

        # Status bar at bottom
        self._create_statusbar()

    def _create_sidebar(self):
        """Create left sidebar with controls."""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # App title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Liquidación OPAEF",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Extractor de Datos",
            font=ctk.CTkFont(size=12)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Load File button
        self.load_btn = ctk.CTkButton(
            self.sidebar,
            text="Cargar PDF",
            command=self._load_file,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.load_btn.grid(row=2, column=0, padx=20, pady=10)

        # Load Multiple Files button
        self.load_multiple_btn = ctk.CTkButton(
            self.sidebar,
            text="Cargar Múltiples PDFs",
            command=self._load_multiple_files,
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.load_multiple_btn.grid(row=3, column=0, padx=20, pady=10)

        # Separator
        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.grid(row=4, column=0, padx=20, pady=20, sticky="ew")

        # Export section label
        self.export_label = ctk.CTkLabel(
            self.sidebar,
            text="Exportar Datos",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.export_label.grid(row=5, column=0, padx=20, pady=(10, 5))

        # Export to Excel button
        self.export_excel_btn = ctk.CTkButton(
            self.sidebar,
            text="Exportar a Excel",
            command=self._export_to_excel,
            state="disabled",
            height=40
        )
        self.export_excel_btn.grid(row=6, column=0, padx=20, pady=10)

        # Validate button
        self.validate_btn = ctk.CTkButton(
            self.sidebar,
            text="Validar Datos",
            command=self._validate_data,
            state="disabled",
            height=40
        )
        self.validate_btn.grid(row=7, column=0, padx=20, pady=10)

        # Separator
        separator2 = ctk.CTkFrame(self.sidebar, height=2)
        separator2.grid(row=8, column=0, padx=20, pady=20, sticky="ew")

        # Configuration button
        self.config_btn = ctk.CTkButton(
            self.sidebar,
            text="⚙ Configuración",
            command=self._open_config_dialog,
            height=40,
            fg_color="gray40",
            hover_color="gray30"
        )
        self.config_btn.grid(row=8, column=0, padx=20, pady=(25, 10))

        # Validation panel (initially hidden)
        self._create_validation_panel()
        separator3 = ctk.CTkFrame(self.sidebar, height=2)
        separator3.grid(row=10, column=0, padx=20, pady=20, sticky="ew")

        # Display options section
        self.display_options_label = ctk.CTkLabel(
            self.sidebar,
            text="Opciones de Visualización",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.display_options_label.grid(row=11, column=0, padx=20, pady=(10, 5))

        # Toggle for Diputación columns
        self.diputacion_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Mostrar columnas Diputación",
            command=self._toggle_diputacion_columns,
            onvalue=True,
            offvalue=False
        )
        self.diputacion_switch.select()  # Set to ON by default
        self.diputacion_switch.grid(row=12, column=0, padx=20, pady=10, sticky="w")

        # PDF Extraction settings section
        self.extraction_settings_label = ctk.CTkLabel(
            self.sidebar,
            text="Extracción PDF",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.extraction_settings_label.grid(row=13, column=0, padx=20, pady=(20, 5))

        # Horizontal strategy selector
        self.horizontal_strategy_label = ctk.CTkLabel(
            self.sidebar,
            text="Estrategia Horizontal:",
            font=ctk.CTkFont(size=12)
        )
        self.horizontal_strategy_label.grid(row=14, column=0, padx=20, pady=(5, 0), sticky="w")

        self.horizontal_strategy_combo = ctk.CTkComboBox(
            self.sidebar,
            values=["lines", "lines_strict"],
            command=self._on_horizontal_strategy_changed,
            width=210
        )
        # Set current value from config
        current_strategy = self.config_manager.get_extraction_config().horizontal_strategy
        self.horizontal_strategy_combo.set(current_strategy)
        self.horizontal_strategy_combo.grid(row=15, column=0, padx=20, pady=(0, 10), sticky="w")

        # Appearance mode - disabled (using fixed light mode with custom palette)

    def _create_main_area(self):
        """Create main content area with tabs."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # File info section - modern compact card design
        self.info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.info_frame.grid_columnconfigure(0, weight=0)  # Mandamiento card
        self.info_frame.grid_columnconfigure(1, weight=0)  # Liquidación card
        self.info_frame.grid_columnconfigure(2, weight=0)  # Fecha card
        self.info_frame.grid_columnconfigure(3, weight=1)  # Spacer
        self.info_frame.grid_columnconfigure(4, weight=0)  # Entidad info

        # Card 1: Mandamiento de Pago
        mandamiento_card = ctk.CTkFrame(
            self.info_frame,
            fg_color=("#e8f4f8", "#1a4d5e"),
            corner_radius=8,
            border_width=1,
            border_color=("#b8dce8", "#2a6d7e")
        )
        mandamiento_card.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

        self.mandamiento_label = ctk.CTkLabel(
            mandamiento_card,
            text="Mandamiento",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=("#666666", "#aaaaaa")
        )
        self.mandamiento_label.pack(padx=12, pady=(8, 0), anchor="w")

        self.mandamiento_value_label = ctk.CTkLabel(
            mandamiento_card,
            text="—",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#4a9fd4")
        )
        self.mandamiento_value_label.pack(padx=12, pady=(0, 8), anchor="w")

        # Card 2: Número de Liquidación
        liquidacion_card = ctk.CTkFrame(
            self.info_frame,
            fg_color=("#f0e8f8", "#3d2d4d"),
            corner_radius=8,
            border_width=1,
            border_color=("#d0b8e8", "#5d4d6d")
        )
        liquidacion_card.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="w")

        self.liquidacion_label = ctk.CTkLabel(
            liquidacion_card,
            text="Nº Liquidación",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=("#666666", "#aaaaaa")
        )
        self.liquidacion_label.pack(padx=12, pady=(8, 0), anchor="w")

        self.liquidacion_value_label = ctk.CTkLabel(
            liquidacion_card,
            text="—",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#6b4a9f", "#9f7ad4")
        )
        self.liquidacion_value_label.pack(padx=12, pady=(0, 8), anchor="w")

        # Card 3: Fecha
        fecha_card = ctk.CTkFrame(
            self.info_frame,
            fg_color=("#e8f8f0", "#1d4d3d"),
            corner_radius=8,
            border_width=1,
            border_color=("#b8e8d0", "#2d6d5d")
        )
        fecha_card.grid(row=0, column=2, padx=(0, 8), pady=5, sticky="w")

        self.fecha_mandamiento_label = ctk.CTkLabel(
            fecha_card,
            text="Fecha",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=("#666666", "#aaaaaa")
        )
        self.fecha_mandamiento_label.pack(padx=12, pady=(8, 0), anchor="w")

        self.fecha_mandamiento_value_label = ctk.CTkLabel(
            fecha_card,
            text="—",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#2d7a4d", "#4dad6d")
        )
        self.fecha_mandamiento_value_label.pack(padx=12, pady=(0, 8), anchor="w")

        # Info section on the right (Entidad + Archivo)
        info_container = ctk.CTkFrame(
            self.info_frame,
            fg_color="transparent"
        )
        info_container.grid(row=0, column=4, padx=(0, 0), pady=5, sticky="e")

        self.entidad_info_label = ctk.CTkLabel(
            info_container,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#444444", "#bbbbbb"),
            anchor="e"
        )
        self.entidad_info_label.pack(anchor="e")

        self.file_value_label = ctk.CTkLabel(
            info_container,
            text="No hay archivo cargado",
            font=ctk.CTkFont(size=12),
            text_color=("#888888", "#888888"),
            anchor="e"
        )
        self.file_value_label.pack(anchor="e", pady=(4, 0))

        # Tabview for different data views
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.tabview.add("Registros de Cobros")
        self.tabview.add("Resumen por Ejercicio")
        self.tabview.add("Agrupación Personalizada")
        self.tabview.add("Deducciones")
        self.tabview.add("Devoluciones")

        # Configure each tab
        self._setup_cobros_tab()
        self._setup_resumen_tab()
        self._setup_grouped_tab()
        self._setup_deducciones_tab()
        self._setup_devoluciones_tab()

    def _setup_cobros_tab(self):
        """Setup the tribute records (cobros) tab with fancy table."""
        tab = self.tabview.tab("Registros de Cobros")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Create info button frame at top
        info_frame = ctk.CTkFrame(tab, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        # Add info button
        info_button = ctk.CTkButton(
            info_frame,
            text="ℹ️ Información",
            command=self._show_cobros_info,
            width=200,
            height=28,
            fg_color="#1976D2",
            hover_color="#1565C0"
        )
        info_button.pack(side="right", padx=5, pady=5)

        # Create frame for table and scrollbar
        table_frame = ctk.CTkFrame(tab)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview for table including diputación columns (visible by default)
        columns = ("ejercicio", "concepto", "clave_recaud", "clave_cont", "voluntaria", "ejecutiva", "recargo",
                   "dip_vol", "dip_ejec", "dip_rec", "liquido")
        self.cobros_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        # Define column headings
        self.cobros_table.heading("ejercicio", text="Ejercicio")
        self.cobros_table.heading("concepto", text="Concepto")
        self.cobros_table.heading("clave_recaud", text="Clave Recaudación")
        self.cobros_table.heading("clave_cont", text="Clave Contabilidad")
        self.cobros_table.heading("voluntaria", text="Voluntaria")
        self.cobros_table.heading("ejecutiva", text="Ejecutiva")
        self.cobros_table.heading("recargo", text="Recargo")
        self.cobros_table.heading("dip_vol", text="Dip.Vol")
        self.cobros_table.heading("dip_ejec", text="Dip.Ejec")
        self.cobros_table.heading("dip_rec", text="Dip.Rec")
        self.cobros_table.heading("liquido", text="Líquido")

        # Define column widths (diputación columns visible by default)
        self.cobros_table.column("ejercicio", width=80, minwidth=80, anchor="center", stretch=False)
        self.cobros_table.column("concepto", width=250, minwidth=250, anchor="w", stretch=False)
        self.cobros_table.column("clave_recaud", width=180, minwidth=180, anchor="center", stretch=False)
        self.cobros_table.column("clave_cont", width=180, minwidth=180, anchor="center", stretch=False)
        self.cobros_table.column("voluntaria", width=120, minwidth=120, anchor="e", stretch=False)
        self.cobros_table.column("ejecutiva", width=120, minwidth=120, anchor="e", stretch=False)
        self.cobros_table.column("recargo", width=100, minwidth=100, anchor="e", stretch=False)
        self.cobros_table.column("dip_vol", width=90, minwidth=90, anchor="e", stretch=False)  # Visible by default
        self.cobros_table.column("dip_ejec", width=90, minwidth=90, anchor="e", stretch=False)  # Visible by default
        self.cobros_table.column("dip_rec", width=90, minwidth=90, anchor="e", stretch=False)  # Visible by default
        self.cobros_table.column("liquido", width=120, minwidth=120, anchor="e", stretch=False)

        # Create scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.cobros_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.cobros_table.xview)
        self.cobros_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.cobros_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure alternating row colors for better readability
        self._configure_table_style()

    def _setup_resumen_tab(self):
        """Setup the summary by exercise tab with table."""
        tab = self.tabview.tab("Resumen por Ejercicio")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Create info button frame at top
        info_frame = ctk.CTkFrame(tab, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        # Add info button
        info_button = ctk.CTkButton(
            info_frame,
            text="ℹ️ Información sobre validación",
            command=self._show_resumen_info,
            width=200,
            height=28,
            fg_color="#1976D2",
            hover_color="#1565C0"
        )
        info_button.pack(side="right", padx=5, pady=5)

        # Create frame for table
        table_frame = ctk.CTkFrame(tab)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview
        columns = ("ejercicio", "voluntaria", "ejecutiva", "recargo", "dip_vol", "dip_ejec", "dip_rec", "liquido", "num_records")
        self.resumen_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Define headings
        self.resumen_table.heading("ejercicio", text="Ejercicio")
        self.resumen_table.heading("voluntaria", text="Voluntaria")
        self.resumen_table.heading("ejecutiva", text="Ejecutiva")
        self.resumen_table.heading("recargo", text="Recargo")
        self.resumen_table.heading("dip_vol", text="Dip. Vol.")
        self.resumen_table.heading("dip_ejec", text="Dip. Ejec.")
        self.resumen_table.heading("dip_rec", text="Dip. Rec.")
        self.resumen_table.heading("liquido", text="Líquido")
        self.resumen_table.heading("num_records", text="Registros")

        # Define column widths (diputación columns visible by default)
        self.resumen_table.column("ejercicio", width=200, minwidth=100, anchor="center", stretch=False)
        self.resumen_table.column("voluntaria", width=130, minwidth=130, anchor="e", stretch=False)
        self.resumen_table.column("ejecutiva", width=130, minwidth=130, anchor="e", stretch=False)
        self.resumen_table.column("recargo", width=120, minwidth=120, anchor="e", stretch=False)
        self.resumen_table.column("dip_vol", width=110, minwidth=100, anchor="e", stretch=False)  # Visible by default
        self.resumen_table.column("dip_ejec", width=110, minwidth=100, anchor="e", stretch=False)  # Visible by default
        self.resumen_table.column("dip_rec", width=110, minwidth=100, anchor="e", stretch=False)  # Visible by default
        self.resumen_table.column("liquido", width=140, minwidth=140, anchor="e", stretch=False)
        self.resumen_table.column("num_records", width=100, minwidth=100, anchor="center", stretch=False)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.resumen_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.resumen_table.xview)
        self.resumen_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid
        self.resumen_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def _setup_grouped_tab(self):
        """Setup the custom grouped records tab."""
        tab = self.tabview.tab("Agrupación Personalizada")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Info header with refresh button
        header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)

        info_label = ctk.CTkLabel(
            header_frame,
            text="Vista agrupada según configuración personalizada",
            font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray80")
        )
        info_label.grid(row=0, column=0, sticky="w")

        # Add info button
        info_button = ctk.CTkButton(
            header_frame,
            text="ℹ️ Información",
            command=self._show_agrupacion_info,
            width=140,
            height=28,
            fg_color="#1976D2",
            hover_color="#1565C0"
        )
        info_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="↻ Actualizar Vista",
            command=self._display_grouped_records,
            width=120,
            height=32
        )
        refresh_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        self.export_html_btn = ctk.CTkButton(
            header_frame,
            text="📄 Exportar a HTML",
            command=self._export_grouped_to_html,
            width=140,
            height=32,
            state="disabled"
        )
        self.export_html_btn.grid(row=0, column=3, sticky="e", padx=(10, 0))

        # Create frame for table
        table_frame = ctk.CTkFrame(tab)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview for grouped data (including diputación columns)
        columns = ("grupo", "concepto", "num_records", "voluntaria", "ejecutiva",
                   "recargo", "dip_vol", "dip_ejec", "dip_rec", "liquido")
        self.grouped_table = ttk.Treeview(
            table_frame, columns=columns, show="tree headings", height=20
        )

        # Define headings
        self.grouped_table.heading("#0", text="")
        self.grouped_table.heading("grupo", text="Grupo")
        self.grouped_table.heading("concepto", text="Concepto")
        self.grouped_table.heading("num_records", text="Registros")
        self.grouped_table.heading("voluntaria", text="Voluntaria")
        self.grouped_table.heading("ejecutiva", text="Ejecutiva")
        self.grouped_table.heading("recargo", text="Recargo")
        self.grouped_table.heading("dip_vol", text="Dip.Vol")
        self.grouped_table.heading("dip_ejec", text="Dip.Ejec")
        self.grouped_table.heading("dip_rec", text="Dip.Rec")
        self.grouped_table.heading("liquido", text="Líquido")

        # Define column widths (diputación columns visible by default)
        self.grouped_table.column("#0", width=30, minwidth=30, stretch=False)
        self.grouped_table.column("grupo", width=250, minwidth=200, anchor="w")
        self.grouped_table.column("concepto", width=200, minwidth=150, anchor="w")
        self.grouped_table.column("num_records", width=100, minwidth=80, anchor="center")
        self.grouped_table.column("voluntaria", width=130, minwidth=100, anchor="e")
        self.grouped_table.column("ejecutiva", width=130, minwidth=100, anchor="e")
        self.grouped_table.column("recargo", width=120, minwidth=100, anchor="e")
        self.grouped_table.column("dip_vol", width=120, minwidth=100, anchor="e", stretch=False)
        self.grouped_table.column("dip_ejec", width=120, minwidth=100, anchor="e", stretch=False)
        self.grouped_table.column("dip_rec", width=120, minwidth=100, anchor="e", stretch=False)
        self.grouped_table.column("liquido", width=140, minwidth=100, anchor="e")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.grouped_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.grouped_table.xview)
        self.grouped_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid
        self.grouped_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def _setup_deducciones_tab(self):
        """Setup the deductions tab with table."""
        tab = self.tabview.tab("Deducciones")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Create info button frame at top
        info_frame = ctk.CTkFrame(tab, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        # Add info button
        info_button = ctk.CTkButton(
            info_frame,
            text="ℹ️ Información",
            command=self._show_deducciones_info,
            width=200,
            height=28,
            fg_color="#1976D2",
            hover_color="#1565C0"
        )
        info_button.pack(side="right", padx=5, pady=5)

        # Create frame for table
        table_frame = ctk.CTkFrame(tab)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview
        columns = ("categoria", "importe")
        self.deducciones_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        # Define headings
        self.deducciones_table.heading("categoria", text="Categoría / Concepto")
        self.deducciones_table.heading("importe", text="Importe")

        # Define column widths
        self.deducciones_table.column("categoria", width=400, anchor="w")
        self.deducciones_table.column("importe", width=200, anchor="e")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.deducciones_table.yview)
        self.deducciones_table.configure(yscrollcommand=vsb.set)

        # Grid
        self.deducciones_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    def _setup_devoluciones_tab(self):
        """Setup the refunds tab with table."""
        tab = self.tabview.tab("Devoluciones")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Create info button frame at top
        info_frame = ctk.CTkFrame(tab, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        # Add info button
        info_button = ctk.CTkButton(
            info_frame,
            text="ℹ️ Información",
            command=self._show_devoluciones_info,
            width=200,
            height=28,
            fg_color="#1976D2",
            hover_color="#1565C0"
        )
        info_button.pack(side="right", padx=5, pady=5)

        # Create frame for table
        table_frame = ctk.CTkFrame(tab)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview
        columns = ("num_expte", "num_resolucion", "total_dev", "entidad", "diputacion", "intereses", "a_deducir")
        self.devoluciones_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Define headings
        self.devoluciones_table.heading("num_expte", text="Nº Expediente")
        self.devoluciones_table.heading("num_resolucion", text="Nº Resolución")
        self.devoluciones_table.heading("total_dev", text="Total Devolución")
        self.devoluciones_table.heading("entidad", text="Entidad")
        self.devoluciones_table.heading("diputacion", text="Diputación")
        self.devoluciones_table.heading("intereses", text="Intereses")
        self.devoluciones_table.heading("a_deducir", text="A Deducir")

        # Define column widths
        self.devoluciones_table.column("num_expte", width=130, anchor="center")
        self.devoluciones_table.column("num_resolucion", width=130, anchor="center")
        self.devoluciones_table.column("total_dev", width=140, anchor="e")
        self.devoluciones_table.column("entidad", width=140, anchor="e")
        self.devoluciones_table.column("diputacion", width=140, anchor="e")
        self.devoluciones_table.column("intereses", width=140, anchor="e")
        self.devoluciones_table.column("a_deducir", width=140, anchor="e")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.devoluciones_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.devoluciones_table.xview)
        self.devoluciones_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid
        self.devoluciones_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def _configure_table_style(self):
        """Configure ttk Treeview style with custom color palette."""
        style = ttk.Style()

        # Get appearance configuration
        appearance_config = self.config_manager.get_appearance_config()
        font_family = appearance_config.font_family
        font_size = appearance_config.font_size

        # Custom color palette (light mode only)
        bg_color = "#FFFFFF"        # Table background - white
        fg_color = "#2E3440"        # Row text - dark gray
        header_bg = "#3A5F7D"       # Header background - muted blue-gray
        header_fg = "#FFFFFF"       # Header text - white
        selected_bg = "#1F4E79"     # Selection - deep blue
        border_color = "#d0d0d0"    # Light gray borders

        style.theme_use("clam")

        # Configure Treeview with borders for clean grid appearance
        style.configure("Treeview",
                       background=bg_color,
                       foreground=fg_color,
                       rowheight=int(font_size * 2.8),  # Scale row height with font
                       fieldbackground=bg_color,
                       borderwidth=1,
                       bordercolor=border_color,
                       relief="solid",
                       font=(font_family, font_size))

        # Configure headers with custom palette
        style.configure("Treeview.Heading",
                       background=header_bg,
                       foreground=header_fg,
                       relief="flat",
                       borderwidth=1,
                       font=(font_family, font_size, "bold"),
                       padding=(10, 8))

        style.map("Treeview.Heading",
                 background=[("active", "#2d4a61")],  # Slightly darker on hover
                 relief=[("active", "flat")])

        style.map("Treeview",
                 background=[("selected", selected_bg)],
                 foreground=[("selected", "#FFFFFF")])

        # Configure for clean grid lines
        style.layout("Treeview", [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])

    def _create_statusbar(self):
        """Create status bar at bottom."""
        self.statusbar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.statusbar.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.statusbar,
            text="Listo",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=10, pady=5)

    def _create_validation_panel(self):
        """Create validation panel in sidebar showing totals comparison."""
        # Validation panel header
        self.validation_header = ctk.CTkLabel(
            self.sidebar,
            text="Validación de Totales",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.validation_header.grid(row=9, column=0, padx=20, pady=(10, 5))

        # Scrollable frame for validation details
        self.validation_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            height=200,
            label_text=""
        )
        self.validation_frame.grid(row=9, column=0, padx=20, pady=(35, 10), sticky="ew")
        self.validation_frame.grid_columnconfigure(0, weight=1)

        # Initially hide validation panel
        self.validation_frame.grid_remove()
        self.validation_header.grid_remove()

        # Storage for validation labels (to be populated when file is loaded)
        self.validation_labels = {}

    def _load_file(self):
        """Load a single PDF file."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )

        if file_path:
            self._process_file(file_path)

    def _load_multiple_files(self):
        """Load multiple PDF files."""
        file_paths = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )

        if file_paths:
            messagebox.showinfo(
                "Múltiples archivos",
                f"Se seleccionaron {len(file_paths)} archivos.\n"
                "Función de procesamiento por lotes próximamente disponible."
            )

    def _load_and_extract_pdf(self, file_path: Path):
        """Helper method to reload a PDF file."""
        self._process_file(str(file_path))

    def _process_file(self, file_path: str):
        """Process a PDF file and extract data."""
        self._set_status("Procesando archivo...")
        self.load_btn.configure(state="disabled")

        # Run extraction in background thread to keep UI responsive
        def extract_thread():
            try:
                # Get extraction settings from config
                extraction_config = self.config_manager.get_extraction_config()
                table_settings = extraction_config.get_table_settings()

                # Extract PDF with configured settings
                doc = extract_liquidation_pdf(file_path, table_settings=table_settings)

                # Update UI in main thread
                self.after(0, lambda: self._on_extraction_success(file_path, doc))

            except PDFExtractionError as e:
                self.after(0, lambda: self._on_extraction_error(str(e)))
            except Exception as e:
                self.after(0, lambda: self._on_extraction_error(f"Error inesperado: {str(e)}"))

        thread = threading.Thread(target=extract_thread, daemon=True)
        thread.start()

    def _on_extraction_success(self, file_path: str, doc: LiquidationDocument):
        """Handle successful extraction."""
        self.current_document = doc
        self.current_file_path = Path(file_path)

        # Update file info
        self.file_value_label.configure(text=self.current_file_path.name)

        # Update key document identifiers with emphasis
        self.mandamiento_value_label.configure(text=doc.mandamiento_pago)

        # Format fecha_mandamiento
        if doc.fecha_mandamiento:
            fecha_str = doc.fecha_mandamiento.strftime("%d/%m/%Y")
        else:
            fecha_str = "N/A"
        self.fecha_mandamiento_value_label.configure(text=fecha_str)

        self.liquidacion_value_label.configure(text=doc.numero_liquidacion)

        # Update entidad and record count
        self.entidad_info_label.configure(
            text=f"Entidad: {doc.entidad} | Total de registros: {doc.total_records}"
        )

        # Display data in tabs
        self._display_cobros()
        self._display_resumen()
        self._display_grouped_records()
        self._display_deducciones()
        self._display_devoluciones()

        # Update validation panel
        self._update_validation_panel()

        # Enable export buttons
        self.export_excel_btn.configure(state="normal")
        self.export_html_btn.configure(state="normal")
        self.validate_btn.configure(state="normal")

        self._set_status(f"Archivo cargado exitosamente: {doc.total_records} registros extraídos")
        self.load_btn.configure(state="normal")

    def _on_extraction_error(self, error_message: str):
        """Handle extraction error."""
        messagebox.showerror("Error de Extracción", f"Error al procesar el PDF:\n\n{error_message}")
        self._set_status("Error al cargar archivo")
        self.load_btn.configure(state="normal")

    def _display_cobros(self):
        """Display tribute records in the cobros table."""
        if not self.current_document:
            return

        # Clear existing data
        for item in self.cobros_table.get_children():
            self.cobros_table.delete(item)

        # Get appearance configuration for fonts
        appearance_config = self.config_manager.get_appearance_config()
        font_family = appearance_config.font_family
        font_size = appearance_config.font_size

        # Configure tags with custom color palette
        self.cobros_table.tag_configure("oddrow", background="#EEF3F7",
                                        foreground="#2E3440")  # Zebra row
        self.cobros_table.tag_configure("evenrow", background="#FFFFFF",
                                        foreground="#2E3440")
        self.cobros_table.tag_configure("year_header", background="#D6E4F0",
                                        foreground="#2E3440",
                                        font=(font_family, font_size + 1, "bold"))
        self.cobros_table.tag_configure("year_subtotal", background="#EEF3F7",
                                        foreground="#2E3440",
                                        font=(font_family, font_size, "bold"))
        self.cobros_table.tag_configure("year_subtotal_valid", background="#E8F5E9",
                                        foreground="#2E7D32",
                                        font=(font_family, font_size, "bold"))  # Light green for valid
        self.cobros_table.tag_configure("validation_error", background="#FFE6E6",
                                        foreground="#C62828",
                                        font=(font_family, font_size, "bold"))  # Light red for errors
        self.cobros_table.tag_configure("spacer", background="#FFFFFF")  # White spacer for separation

        # Get validation results for all years
        validation_results = self.current_document.validate_exercise_summaries()

        # Group by exercise
        exercises = {}
        for record in self.current_document.tribute_records:
            if record.ejercicio not in exercises:
                exercises[record.ejercicio] = []
            exercises[record.ejercicio].append(record)

        # Display by exercise
        row_num = 0
        for idx, ejercicio in enumerate(sorted(exercises.keys())):
            # Insert exercise header - clean format without === symbols
            # Put the text in the concepto column which is wider (250px)
            records_in_year = exercises[ejercicio]
            self.cobros_table.insert("", "end", values=(
                "",  # Empty ejercicio column
                f"▸ EJERCICIO {ejercicio} ({len(records_in_year)} registros)",  # Year label with count
                "", "", "", "", "", "", "", "", ""  # Empty columns including diputación
            ), tags=("year_header",))
            row_num += 1

            # Calculate year totals (including diputación columns)
            year_voluntaria = sum(r.voluntaria for r in records_in_year)
            year_ejecutiva = sum(r.ejecutiva for r in records_in_year)
            year_recargo = sum(r.recargo for r in records_in_year)
            year_dip_vol = sum(r.diputacion_voluntaria for r in records_in_year)
            year_dip_ejec = sum(r.diputacion_ejecutiva for r in records_in_year)
            year_dip_rec = sum(r.diputacion_recargo for r in records_in_year)
            year_liquido = sum(r.liquido for r in records_in_year)

            # Display records for this year
            for record in records_in_year:
                tag = "evenrow" if row_num % 2 == 0 else "oddrow"
                self.cobros_table.insert("", "end", values=(
                    record.ejercicio,
                    record.concepto,
                    record.clave_recaudacion,
                    record.clave_contabilidad,
                    f"{record.voluntaria:,.2f}",
                    f"{record.ejecutiva:,.2f}",
                    f"{record.recargo:,.2f}",
                    f"{record.diputacion_voluntaria:,.2f}",
                    f"{record.diputacion_ejecutiva:,.2f}",
                    f"{record.diputacion_recargo:,.2f}",
                    f"{record.liquido:,.2f}"
                ), tags=(tag,))
                row_num += 1

            # Check if we have validation results for this year
            validation = validation_results.get(ejercicio)

            if validation and validation.is_valid:
                # Validation passed - display subtotal with green checkmark
                subtotal_tag = "year_subtotal_valid"
                subtotal_label = f"  ✓ TOTAL EJERCICIO {ejercicio}"
            elif validation and not validation.is_valid:
                # Validation failed - display subtotal without checkmark
                subtotal_tag = "year_subtotal"
                subtotal_label = f"  TOTAL EJERCICIO {ejercicio}"
            else:
                # No validation data (shouldn't happen, but fallback)
                subtotal_tag = "year_subtotal"
                subtotal_label = f"  Subtotal {ejercicio}"

            # Insert subtotal row (documented values from PDF)
            self.cobros_table.insert("", "end", values=(
                "",
                subtotal_label,
                "",
                "",
                f"{year_voluntaria:,.2f}",
                f"{year_ejecutiva:,.2f}",
                f"{year_recargo:,.2f}",
                f"{year_dip_vol:,.2f}",
                f"{year_dip_ejec:,.2f}",
                f"{year_dip_rec:,.2f}",
                f"{year_liquido:,.2f}"
            ), tags=(subtotal_tag,))
            row_num += 1

            # If validation failed, show calculated row in red
            if validation and not validation.is_valid:
                self.cobros_table.insert("", "end", values=(
                    "",
                    f"  ⚠ CALCULADO (discrepancia detectada)",
                    "",
                    "",
                    f"{validation.calc_voluntaria:,.2f}",
                    f"{validation.calc_ejecutiva:,.2f}",
                    f"{validation.calc_recargo:,.2f}",
                    f"{validation.calc_dip_voluntaria:,.2f}",
                    f"{validation.calc_dip_ejecutiva:,.2f}",
                    f"{validation.calc_dip_recargo:,.2f}",
                    f"{validation.calc_liquido:,.2f}"
                ), tags=("validation_error",))
                row_num += 1

            # Add spacer row between year groups (except after last year)
            if idx < len(exercises) - 1:
                self.cobros_table.insert("", "end", values=("", "", "", "", "", "", "", "", "", "", ""), tags=("spacer",))
                row_num += 1

    def _display_resumen(self):
        """Display exercise summaries in table."""
        if not self.current_document:
            return

        # Clear existing data
        for item in self.resumen_table.get_children():
            self.resumen_table.delete(item)

        # Get appearance configuration for fonts
        appearance_config = self.config_manager.get_appearance_config()
        font_family = appearance_config.font_family
        font_size = appearance_config.font_size

        # Configure tags with custom color palette
        self.resumen_table.tag_configure("oddrow", background="#EEF3F7",
                                         foreground="#2E3440")  # Zebra row
        self.resumen_table.tag_configure("evenrow", background="#FFFFFF",
                                         foreground="#2E3440")
        self.resumen_table.tag_configure("total_calc", background="#E3F2FD",
                                         foreground="#1565C0",
                                         font=(font_family, font_size, "bold"))
        self.resumen_table.tag_configure("total_doc", background="#F5F5F5",
                                         foreground="#424242",
                                         font=(font_family, font_size, "bold"))
        self.resumen_table.tag_configure("validation_ok", background="#E8F5E9",
                                         foreground="#2E7D32",
                                         font=(font_family, font_size, "bold"))
        self.resumen_table.tag_configure("validation_error", background="#FFE6E6",
                                         foreground="#C62828",
                                         font=(font_family, font_size, "bold"))

        # Group records by exercise to get counts
        exercise_counts = {}
        for record in self.current_document.tribute_records:
            exercise_counts[record.ejercicio] = exercise_counts.get(record.ejercicio, 0) + 1

        # Calculate totals from all records (TOTAL CALCULADO)
        from decimal import Decimal
        calc_voluntaria = Decimal('0')
        calc_ejecutiva = Decimal('0')
        calc_recargo = Decimal('0')
        calc_dip_vol = Decimal('0')
        calc_dip_ejec = Decimal('0')
        calc_dip_rec = Decimal('0')
        calc_liquido = Decimal('0')

        # Display exercise summaries
        row_num = 0
        for ejercicio in sorted(exercise_counts.keys()):
            # Calculate totals for this exercise
            records = [r for r in self.current_document.tribute_records if r.ejercicio == ejercicio]
            voluntaria = sum(r.voluntaria for r in records)
            ejecutiva = sum(r.ejecutiva for r in records)
            recargo = sum(r.recargo for r in records)
            dip_vol = sum(r.diputacion_voluntaria for r in records)
            dip_ejec = sum(r.diputacion_ejecutiva for r in records)
            dip_rec = sum(r.diputacion_recargo for r in records)
            liquido = sum(r.liquido for r in records)

            # Accumulate for total calculated
            calc_voluntaria += voluntaria
            calc_ejecutiva += ejecutiva
            calc_recargo += recargo
            calc_dip_vol += dip_vol
            calc_dip_ejec += dip_ejec
            calc_dip_rec += dip_rec
            calc_liquido += liquido

            tag = "evenrow" if row_num % 2 == 0 else "oddrow"
            self.resumen_table.insert("", "end", values=(
                ejercicio,
                f"{voluntaria:,.2f}",
                f"{ejecutiva:,.2f}",
                f"{recargo:,.2f}",
                f"{dip_vol:,.2f}",
                f"{dip_ejec:,.2f}",
                f"{dip_rec:,.2f}",
                f"{liquido:,.2f}",
                exercise_counts[ejercicio]
            ), tags=(tag,))
            row_num += 1

        # Add TOTAL (Calculado) row - sum of all individual records
        doc = self.current_document
        self.resumen_table.insert("", "end", values=(
            "TOTAL (Calculado)",
            f"{calc_voluntaria:,.2f}",
            f"{calc_ejecutiva:,.2f}",
            f"{calc_recargo:,.2f}",
            f"{calc_dip_vol:,.2f}",
            f"{calc_dip_ejec:,.2f}",
            f"{calc_dip_rec:,.2f}",
            f"{calc_liquido:,.2f}",
            doc.total_records
        ), tags=("total_calc",))

        # Add TOTAL (Documento) row - extracted from PDF
        self.resumen_table.insert("", "end", values=(
            "TOTAL (Documento)",
            f"{doc.total_voluntaria:,.2f}",
            f"{doc.total_ejecutiva:,.2f}",
            f"{doc.total_recargo:,.2f}",
            f"{doc.total_diputacion_voluntaria:,.2f}",
            f"{doc.total_diputacion_ejecutiva:,.2f}",
            f"{doc.total_diputacion_recargo:,.2f}",
            f"{doc.total_liquido:,.2f}",
            doc.total_records
        ), tags=("total_doc",))

        # Add VALIDATION row - compare calculated vs document
        tolerance = Decimal('0.01')
        diff_voluntaria = calc_voluntaria - doc.total_voluntaria
        diff_ejecutiva = calc_ejecutiva - doc.total_ejecutiva
        diff_recargo = calc_recargo - doc.total_recargo
        diff_dip_vol = calc_dip_vol - doc.total_diputacion_voluntaria
        diff_dip_ejec = calc_dip_ejec - doc.total_diputacion_ejecutiva
        diff_dip_rec = calc_dip_rec - doc.total_diputacion_recargo
        diff_liquido = calc_liquido - doc.total_liquido

        # Check if all values match within tolerance
        is_valid = all(
            abs(diff) <= tolerance
            for diff in [diff_voluntaria, diff_ejecutiva, diff_recargo,
                        diff_dip_vol, diff_dip_ejec, diff_dip_rec, diff_liquido]
        )

        if is_valid:
            # All values match
            self.resumen_table.insert("", "end", values=(
                "✓ VALIDACIÓN CORRECTA",
                "", "", "", "", "", "", "", ""
            ), tags=("validation_ok",))
        else:
            # Show differences
            def format_diff(diff):
                if abs(diff) <= tolerance:
                    return "✓"
                else:
                    sign = "+" if diff > 0 else ""
                    return f"{sign}{diff:,.2f}"

            self.resumen_table.insert("", "end", values=(
                "⚠ DIFERENCIAS",
                format_diff(diff_voluntaria),
                format_diff(diff_ejecutiva),
                format_diff(diff_recargo),
                format_diff(diff_dip_vol),
                format_diff(diff_dip_ejec),
                format_diff(diff_dip_rec),
                format_diff(diff_liquido),
                ""
            ), tags=("validation_error",))

    def _show_cobros_info(self):
        """Show information dialog for Cobros tab."""
        InfoDialog(self, "Información - Registros de Cobros", info_messages.COBROS_INFO)

    def _show_resumen_info(self):
        """Show information dialog for Resumen por Ejercicio tab."""
        InfoDialog(self, "Información - Resumen por Ejercicio", info_messages.RESUMEN_INFO)

    def _show_agrupacion_info(self):
        """Show information dialog for Agrupación Personalizada tab."""
        InfoDialog(self, "Información - Agrupación Personalizada", info_messages.AGRUPACION_INFO)

    def _show_deducciones_info(self):
        """Show information dialog for Deducciones tab."""
        InfoDialog(self, "Información - Deducciones", info_messages.DEDUCCIONES_INFO)

    def _show_devoluciones_info(self):
        """Show information dialog for Devoluciones tab."""
        InfoDialog(self, "Información - Devoluciones", info_messages.DEVOLUCIONES_INFO)

    def _display_deducciones(self):
        """Display deductions in table."""
        if not self.current_document or not self.current_document.deductions:
            # Clear table
            for item in self.deducciones_table.get_children():
                self.deducciones_table.delete(item)
            self.deducciones_table.insert("", "end", values=("No hay datos de deducciones disponibles", ""))
            return

        # Clear existing data
        for item in self.deducciones_table.get_children():
            self.deducciones_table.delete(item)

        # Get appearance configuration for fonts
        appearance_config = self.config_manager.get_appearance_config()
        font_family = appearance_config.font_family
        font_size = appearance_config.font_size

        # Configure tags for clean hierarchy
        self.deducciones_table.tag_configure("category", background="#e3f2fd",
                                            font=(font_family, font_size, "bold"))
        self.deducciones_table.tag_configure("item", background="white")
        self.deducciones_table.tag_configure("total", background="#bbdefb",
                                            font=(font_family, font_size + 1, "bold"))

        ded = self.current_document.deductions

        # RECAUDACIÓN
        self.deducciones_table.insert("", "end", values=("RECAUDACIÓN", ""), tags=("category",))
        self.deducciones_table.insert("", "end", values=("  Tasa Voluntaria", f"{ded.tasa_voluntaria:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Ejecutiva", f"{ded.tasa_ejecutiva:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Ejecutiva Sin Recargo", f"{ded.tasa_ejecutiva_sin_recargo:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Baja Órgano Gestor Deleg.", f"{ded.tasa_baja_organo_gestor_deleg:,.2f}"), tags=("item",))

        # TRIBUTARIA
        self.deducciones_table.insert("", "end", values=("", ""))  # Spacer
        self.deducciones_table.insert("", "end", values=("TRIBUTARIA", ""), tags=("category",))
        self.deducciones_table.insert("", "end", values=("  Tasa Gestión Tributaria", f"{ded.tasa_gestion_tributaria:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Gestión Censal", f"{ded.tasa_gestion_censal:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Gestión Catastral", f"{ded.tasa_gestion_catastral:,.2f}"), tags=("item",))

        # MULTAS/SANCIONES
        self.deducciones_table.insert("", "end", values=("", ""))
        self.deducciones_table.insert("", "end", values=("MULTAS/SANCIONES", ""), tags=("category",))
        self.deducciones_table.insert("", "end", values=("  Tasa Sanción Tributaria", f"{ded.tasa_sancion_tributaria:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Sanción Recaudación", f"{ded.tasa_sancion_recaudacion:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Sanción Inspección", f"{ded.tasa_sancion_inspeccion:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Tasa Multas de Tráfico", f"{ded.tasa_multas_trafico:,.2f}"), tags=("item",))

        # OTRAS DEDUCCIONES
        self.deducciones_table.insert("", "end", values=("", ""))
        self.deducciones_table.insert("", "end", values=("OTRAS DEDUCCIONES", ""), tags=("category",))
        self.deducciones_table.insert("", "end", values=("  Gastos Repercutidos", f"{ded.gastos_repercutidos:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Anticipos", f"{ded.anticipos:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Intereses por Anticipo", f"{ded.intereses_por_anticipo:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Expedientes Compensación", f"{ded.expedientes_compensacion:,.2f}"), tags=("item",))
        self.deducciones_table.insert("", "end", values=("  Expedientes Ingresos Indebidos", f"{ded.expedientes_ingresos_indebidos:,.2f}"), tags=("item",))

        # TOTAL
        self.deducciones_table.insert("", "end", values=("", ""))
        self.deducciones_table.insert("", "end", values=("TOTAL DEDUCCIONES", f"{ded.total_deducciones:,.2f}"), tags=("total",))

    def _display_devoluciones(self):
        """Display refunds in table."""
        if not self.current_document or not self.current_document.refund_records:
            # Clear table
            for item in self.devoluciones_table.get_children():
                self.devoluciones_table.delete(item)
            self.devoluciones_table.insert("", "end", values=("No hay devoluciones", "", "", "", "", "", ""))
            return

        # Clear existing data
        for item in self.devoluciones_table.get_children():
            self.devoluciones_table.delete(item)

        # Configure tags with custom color palette
        self.devoluciones_table.tag_configure("oddrow", background="#EEF3F7",
                                              foreground="#2E3440")  # Zebra row
        self.devoluciones_table.tag_configure("evenrow", background="#FFFFFF",
                                              foreground="#2E3440")

        # Display refund records
        row_num = 0
        for refund in self.current_document.refund_records:
            tag = "evenrow" if row_num % 2 == 0 else "oddrow"
            self.devoluciones_table.insert("", "end", values=(
                refund.num_expte,
                refund.num_resolucion,
                f"{refund.total_devolucion:,.2f}",
                f"{refund.entidad:,.2f}",
                f"{refund.diputacion:,.2f}",
                f"{refund.intereses:,.2f}",
                f"{refund.a_deducir:,.2f}"
            ), tags=(tag,))
            row_num += 1

    def _export_to_excel(self):
        """Export current document to Excel."""
        if not self.current_document:
            return

        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile=f"liquidacion_{self.current_document.numero_liquidacion}.xlsx"
        )

        if file_path:
            try:
                self._set_status("Exportando a Excel...")
                export_to_excel(self.current_document, file_path)
                self._set_status(f"Exportado exitosamente a: {Path(file_path).name}")
                messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar:\n{str(e)}")
                self._set_status("Error al exportar")

    def _export_grouped_to_html(self):
        """Export grouped concept records to HTML."""
        if not self.current_document:
            messagebox.showwarning("Advertencia", "No hay documento cargado para exportar")
            return

        # Get current grouping configuration
        config = self.config_manager.get_grouping_config()

        # Check if any grouping is active
        if not config.group_by_year and not config.group_by_concept and not (config.group_by_custom and config.custom_groups):
            messagebox.showwarning(
                "Advertencia",
                "No hay criterios de agrupación activos.\n\n"
                "Por favor, configure al menos un criterio de agrupación antes de exportar."
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo HTML",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")],
            initialfile=f"liquidacion_{self.current_document.numero_liquidacion}_agrupado.html"
        )

        if file_path:
            try:
                self._set_status("Exportando a HTML...")
                # Update concept names before export
                self._update_concept_names(config)
                # Export with current grouping settings
                export_grouped_to_html(
                    self.current_document,
                    config,
                    file_path,
                    group_by_year=config.group_by_year,
                    group_by_concept=config.group_by_concept,
                    group_by_custom=config.group_by_custom
                )
                self._set_status(f"Exportado exitosamente a: {Path(file_path).name}")
                messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar a HTML:\n{str(e)}")
                self._set_status("Error al exportar")

    def _validate_data(self):
        """Validate current document data."""
        if not self.current_document:
            return

        errors = self.current_document.validate_totals()

        if not errors:
            messagebox.showinfo(
                "Validación Exitosa",
                "Todos los totales coinciden correctamente.\n\n"
                f"Total de registros: {self.current_document.total_records}\n"
                f"Líquido total: {self.current_document.total_liquido:.2f}"
            )
        else:
            error_text = "\n".join(f"- {error}" for error in errors)
            messagebox.showwarning(
                "Errores de Validación",
                f"Se encontraron {len(errors)} error(es):\n\n{error_text}"
            )

    def _toggle_diputacion_columns(self):
        """Toggle visibility of diputación columns in all tables."""
        self.show_diputacion_columns = self.diputacion_switch.get()

        if self.show_diputacion_columns:
            # Show columns with appropriate width in Cobros table
            self.cobros_table.column("dip_vol", width=90, minwidth=90, stretch=False)
            self.cobros_table.column("dip_ejec", width=90, minwidth=90, stretch=False)
            self.cobros_table.column("dip_rec", width=90, minwidth=90, stretch=False)

            # Show columns in Resumen table
            self.resumen_table.column("dip_vol", width=120, minwidth=120, stretch=False)
            self.resumen_table.column("dip_ejec", width=120, minwidth=120, stretch=False)
            self.resumen_table.column("dip_rec", width=120, minwidth=120, stretch=False)

            # Show columns in Grouped table
            self.grouped_table.column("dip_vol", width=120, minwidth=100, stretch=False)
            self.grouped_table.column("dip_ejec", width=120, minwidth=100, stretch=False)
            self.grouped_table.column("dip_rec", width=120, minwidth=100, stretch=False)
        else:
            # Hide columns in Cobros table
            self.cobros_table.column("dip_vol", width=0, minwidth=0, stretch=False)
            self.cobros_table.column("dip_ejec", width=0, minwidth=0, stretch=False)
            self.cobros_table.column("dip_rec", width=0, minwidth=0, stretch=False)

            # Hide columns in Resumen table
            self.resumen_table.column("dip_vol", width=0, minwidth=0, stretch=False)
            self.resumen_table.column("dip_ejec", width=0, minwidth=0, stretch=False)
            self.resumen_table.column("dip_rec", width=0, minwidth=0, stretch=False)

            # Hide columns in Grouped table
            self.grouped_table.column("dip_vol", width=0, minwidth=0, stretch=False)
            self.grouped_table.column("dip_ejec", width=0, minwidth=0, stretch=False)
            self.grouped_table.column("dip_rec", width=0, minwidth=0, stretch=False)

    def _on_horizontal_strategy_changed(self, choice):
        """Handle horizontal strategy selection change."""
        try:
            # Update configuration
            self.config_manager.update_extraction_config(horizontal_strategy=choice)
            self._set_status(f"Estrategia de extracción actualizada: {choice}")

            # If there's a loaded document, suggest reloading
            if self.current_document and self.current_file_path:
                response = messagebox.askyesno(
                    "Recargar PDF",
                    "La configuración de extracción ha cambiado.\n\n"
                    "¿Desea recargar el PDF actual con la nueva configuración?"
                )
                if response:
                    # Reload the current file
                    self._load_and_extract_pdf(self.current_file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar configuración:\n{str(e)}")
            self._set_status("Error al actualizar configuración")

    def _set_status(self, message: str):
        """Update status bar message."""
        self.status_label.configure(text=message)

    def _update_validation_panel(self):
        """Update validation panel with comparison data."""
        if not self.current_document:
            return

        from decimal import Decimal

        # Show validation panel
        self.validation_frame.grid()
        self.validation_header.grid()

        # Clear existing labels
        for widget in self.validation_frame.winfo_children():
            widget.destroy()

        # Calculate aggregates from extracted records
        calc_voluntaria = sum(r.voluntaria for r in self.current_document.tribute_records)
        calc_ejecutiva = sum(r.ejecutiva for r in self.current_document.tribute_records)
        calc_recargo = sum(r.recargo for r in self.current_document.tribute_records)
        calc_dip_vol = sum(r.diputacion_voluntaria for r in self.current_document.tribute_records)
        calc_dip_ejec = sum(r.diputacion_ejecutiva for r in self.current_document.tribute_records)
        calc_dip_rec = sum(r.diputacion_recargo for r in self.current_document.tribute_records)
        calc_liquido = sum(r.liquido for r in self.current_document.tribute_records)

        # Tolerance for comparison
        tolerance = Decimal('0.01')

        # Helper function to create validation row
        def create_validation_row(label_text: str, doc_value: Decimal, calc_value: Decimal, row: int):
            """Create a row showing validation comparison."""
            match = abs(doc_value - calc_value) <= tolerance
            icon = "✓" if match else "✗"
            color = ("#2d7a2d", "#4caf50") if match else ("#c41e3a", "#f44336")

            # Label
            label = ctk.CTkLabel(
                self.validation_frame,
                text=label_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                anchor="w"
            )
            label.grid(row=row, column=0, sticky="w", pady=2)

            # Document value
            doc_label = ctk.CTkLabel(
                self.validation_frame,
                text=f"{doc_value:,.2f}",
                font=ctk.CTkFont(size=9),
                anchor="e"
            )
            doc_label.grid(row=row, column=1, sticky="e", padx=(5, 2), pady=2)

            # Status icon
            status_label = ctk.CTkLabel(
                self.validation_frame,
                text=icon,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color,
                anchor="center"
            )
            status_label.grid(row=row, column=2, sticky="ew", padx=2, pady=2)

            # Calculated value
            calc_label = ctk.CTkLabel(
                self.validation_frame,
                text=f"{calc_value:,.2f}",
                font=ctk.CTkFont(size=9),
                text_color=color if not match else None,
                anchor="e"
            )
            calc_label.grid(row=row, column=3, sticky="e", padx=(2, 0), pady=2)

        # Configure columns
        self.validation_frame.grid_columnconfigure(0, weight=2)  # Label
        self.validation_frame.grid_columnconfigure(1, weight=1)  # Doc value
        self.validation_frame.grid_columnconfigure(2, weight=0)  # Icon
        self.validation_frame.grid_columnconfigure(3, weight=1)  # Calc value

        # Header row
        header_label = ctk.CTkLabel(
            self.validation_frame,
            text="Concepto",
            font=ctk.CTkFont(size=9, weight="bold"),
            anchor="w"
        )
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        doc_header = ctk.CTkLabel(
            self.validation_frame,
            text="PDF",
            font=ctk.CTkFont(size=9, weight="bold"),
            anchor="e"
        )
        doc_header.grid(row=0, column=1, sticky="e", padx=(5, 2), pady=(0, 5))

        calc_header = ctk.CTkLabel(
            self.validation_frame,
            text="Calculado",
            font=ctk.CTkFont(size=9, weight="bold"),
            anchor="e"
        )
        calc_header.grid(row=0, column=3, sticky="e", padx=(2, 0), pady=(0, 5))

        # Data rows
        row = 1
        create_validation_row("VOLUNTARIA", self.current_document.total_voluntaria, calc_voluntaria, row)
        row += 1
        create_validation_row("EJECUTIVA", self.current_document.total_ejecutiva, calc_ejecutiva, row)
        row += 1
        create_validation_row("RECARGO", self.current_document.total_recargo, calc_recargo, row)
        row += 1

        # Separator
        separator = ctk.CTkFrame(self.validation_frame, height=2, fg_color=("#d0d0d0", "#404040"))
        separator.grid(row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1

        create_validation_row("DIP. VOLUNT.", self.current_document.total_diputacion_voluntaria, calc_dip_vol, row)
        row += 1
        create_validation_row("DIP. EJECUT.", self.current_document.total_diputacion_ejecutiva, calc_dip_ejec, row)
        row += 1
        create_validation_row("DIP. RECARGO", self.current_document.total_diputacion_recargo, calc_dip_rec, row)
        row += 1

        # Separator
        separator2 = ctk.CTkFrame(self.validation_frame, height=2, fg_color=("#d0d0d0", "#404040"))
        separator2.grid(row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1

        create_validation_row("LÍQUIDO", self.current_document.total_liquido, calc_liquido, row)
        row += 1

        # Validate A LIQUIDAR if deductions exist
        if self.current_document.deductions:
            separator3 = ctk.CTkFrame(self.validation_frame, height=2, fg_color=("#d0d0d0", "#404040"))
            separator3.grid(row=row, column=0, columnspan=4, sticky="ew", pady=5)
            row += 1

            expected_liquidar = self.current_document.total_liquido - self.current_document.deductions.total_deducciones
            create_validation_row("A LIQUIDAR", self.current_document.a_liquidar, expected_liquidar, row)
            row += 1

            # Show deductions total
            deductions_label = ctk.CTkLabel(
                self.validation_frame,
                text=f"Total Deducciones: {self.current_document.deductions.total_deducciones:,.2f}",
                font=ctk.CTkFont(size=9),
                anchor="w",
                text_color=("#666666", "#999999")
            )
            deductions_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(5, 0))

    def _open_config_dialog(self):
        """Open configuration dialog."""
        grouping_config = self.config_manager.get_grouping_config()
        appearance_config = self.config_manager.get_appearance_config()

        # Update concept names from current document if available
        if self.current_document:
            self._update_concept_names(grouping_config)

        def on_save(updated_grouping_config, updated_appearance_config):
            """Save updated configurations."""
            self.config_manager.save_grouping_config(updated_grouping_config)
            self.config_manager.save_appearance_config(updated_appearance_config)

            # Refresh table styles with new font settings
            self._configure_table_style()

            # Refresh all views if document is loaded
            if self.current_document:
                self._display_cobros()
                self._display_resumen()
                self._display_grouped_records()
                self._display_deducciones()
                self._display_devoluciones()

        # Pass current records to dialog for concept selection
        current_records = self.current_document.tribute_records if self.current_document else []

        # Open dialog
        ConfigDialog(self, grouping_config, appearance_config, on_save, current_records)

    def _update_concept_names(self, config):
        """Update concept names in configuration from current document."""
        if not self.current_document:
            return

        # Extract unique concept codes and names from records
        for record in self.current_document.tribute_records:
            code = config.get_concept_code(record.clave_recaudacion)
            if code and code not in config.concept_names:
                # Use the concepto field as the name
                config.concept_names[code] = record.concepto

    def _display_grouped_records(self):
        """Display records grouped by configuration criteria."""
        if not self.current_document:
            # Clear table
            for item in self.grouped_table.get_children():
                self.grouped_table.delete(item)
            self.grouped_table.insert(
                "", "end",
                values=("No hay datos cargados", "", "", "", "", "", "", "", "", "")
            )
            return

        # Clear existing data
        for item in self.grouped_table.get_children():
            self.grouped_table.delete(item)

        # Get appearance configuration for fonts
        appearance_config = self.config_manager.get_appearance_config()
        font_family = appearance_config.font_family
        font_size = appearance_config.font_size

        # Configure tags for styling with custom color palette
        # Custom palette: Blue (years) + Green (groups) for harmonious hierarchy

        # Level 1: Year headers - soft steel blue
        self.grouped_table.tag_configure("year_header", background="#D6E4F0",
                                         foreground="#2E3440",
                                         font=(font_family, font_size + 1, "bold"))

        # Level 2: Custom group headers - soft mint green
        self.grouped_table.tag_configure("group_header", background="#DFF1E1",
                                         foreground="#2E3440",
                                         font=(font_family, font_size, "bold"))

        # Level 3: Concept headers - very light blue-gray (zebra color for consistency)
        self.grouped_table.tag_configure("concept_header", background="#EEF3F7",
                                         foreground="#2E3440",
                                         font=(font_family, font_size, "bold"))

        # Concepts within groups - white for contrast
        self.grouped_table.tag_configure("concept_in_group", background="#FFFFFF",
                                         foreground="#2E3440",
                                         font=(font_family, font_size))

        # Ungrouped concepts - light background
        self.grouped_table.tag_configure("concept_ungrouped", background="#F5F7FA",
                                         foreground="#2E3440",
                                         font=(font_family, font_size, "bold"))

        # Individual records within groups - white
        self.grouped_table.tag_configure("record_in_group", background="#FFFFFF",
                                         foreground="#2E3440")

        # Ungrouped records - zebra color
        self.grouped_table.tag_configure("record_ungrouped", background="#EEF3F7",
                                         foreground="#2E3440")

        # Alternating rows
        self.grouped_table.tag_configure("oddrow", background="#EEF3F7",
                                         foreground="#2E3440")
        self.grouped_table.tag_configure("evenrow", background="#FFFFFF",
                                         foreground="#2E3440")

        # Totals - deep blue with white text for contrast
        self.grouped_table.tag_configure("total", background="#1F4E79",
                                         foreground="#FFFFFF",
                                         font=(font_family, font_size + 1, "bold"))

        config = self.config_manager.get_grouping_config()
        self._update_concept_names(config)

        records = self.current_document.tribute_records

        # Check if any grouping is active
        if not config.group_by_year and not config.group_by_concept and not (config.group_by_custom and config.custom_groups):
            # No grouping - show message
            self.grouped_table.insert(
                "", "end",
                values=("No hay criterios de agrupación activos", "", "", "", "", "", "", "", "", "")
            )
        else:
            # Use hierarchical grouping logic
            self._build_hierarchical_grouping(records, config)

    def _build_hierarchical_grouping(self, records, config):
        """Build hierarchical grouping based on active dimensions."""
        from collections import defaultdict

        if config.group_by_year:
            # Level 1: Group by year
            years_data = defaultdict(list)
            for record in records:
                years_data[record.ejercicio].append(record)

            for ejercicio in sorted(years_data.keys()):
                year_records = years_data[ejercicio]

                # Calculate year totals (including diputación)
                year_voluntaria = sum(r.voluntaria for r in year_records)
                year_ejecutiva = sum(r.ejecutiva for r in year_records)
                year_recargo = sum(r.recargo for r in year_records)
                year_dip_vol = sum(r.diputacion_voluntaria for r in year_records)
                year_dip_ejec = sum(r.diputacion_ejecutiva for r in year_records)
                year_dip_rec = sum(r.diputacion_recargo for r in year_records)
                year_liquido = sum(r.liquido for r in year_records)

                # Insert year header as parent node
                year_node = self.grouped_table.insert(
                    "", "end",
                    text="▼",
                    values=(
                        f"EJERCICIO {ejercicio}",
                        "",
                        len(year_records),
                        f"{year_voluntaria:,.2f}",
                        f"{year_ejecutiva:,.2f}",
                        f"{year_recargo:,.2f}",
                        f"{year_dip_vol:,.2f}",
                        f"{year_dip_ejec:,.2f}",
                        f"{year_dip_rec:,.2f}",
                        f"{year_liquido:,.2f}"
                    ),
                    tags=("year_header",),
                    open=True
                )

                # Level 2 & 3: Add nested grouping within year
                self._add_nested_grouping(year_node, year_records, config)
        else:
            # No year grouping, start directly with concept/custom
            self._add_nested_grouping(None, records, config)

    def _add_nested_grouping(self, parent_node, records, config):
        """Add concept and/or custom group nesting under a parent node (or root if parent_node is None)."""
        from collections import defaultdict

        parent = parent_node if parent_node else ""

        if config.group_by_concept:
            # Level 2: Group by concept
            concepts_data = defaultdict(list)
            for record in records:
                code = config.get_concept_code(record.clave_recaudacion)
                concepts_data[code].append(record)

            if config.group_by_custom and config.custom_groups:
                # Level 3: Apply custom groups to concepts
                self._add_custom_grouped_concepts(parent, concepts_data, config)
            else:
                # Just show concepts individually
                self._add_concept_nodes(parent, concepts_data, config)
        else:
            # No concept grouping
            if config.group_by_custom and config.custom_groups:
                # Apply custom groups directly to records
                self._add_custom_groups_to_node_new(parent, records, config)
            else:
                # Show individual records
                self._add_individual_records(parent, records, config)

    def _add_custom_grouped_concepts(self, parent_node, concepts_data, config):
        """
        Group concepts into custom groups and show ungrouped concepts separately.

        Args:
            parent_node: Parent node ID (or "" for root)
            concepts_data: Dict[concept_code, List[records]]
            config: GroupingConfig
        """
        from collections import defaultdict

        # Map custom groups to their concept codes
        grouped_concepts = defaultdict(list)  # group_name -> [concept_codes]
        ungrouped_concepts = {}  # concept_code -> [records]

        for concept_code, concept_records in concepts_data.items():
            group_name = config.get_custom_group_for_concept(concept_code)

            if group_name:
                # This concept belongs to a custom group
                grouped_concepts[group_name].append((concept_code, concept_records))
            else:
                # Ungrouped concept
                ungrouped_concepts[concept_code] = concept_records

        # Display custom groups
        for group in config.custom_groups:
            if group.name in grouped_concepts:
                # Get all records for this group
                group_concept_items = grouped_concepts[group.name]
                all_group_records = []
                for _, concept_records in group_concept_items:
                    all_group_records.extend(concept_records)

                # Calculate group totals (including diputación)
                group_voluntaria = sum(r.voluntaria for r in all_group_records)
                group_ejecutiva = sum(r.ejecutiva for r in all_group_records)
                group_recargo = sum(r.recargo for r in all_group_records)
                group_dip_vol = sum(r.diputacion_voluntaria for r in all_group_records)
                group_dip_ejec = sum(r.diputacion_ejecutiva for r in all_group_records)
                group_dip_rec = sum(r.diputacion_recargo for r in all_group_records)
                group_liquido = sum(r.liquido for r in all_group_records)

                # Insert group header
                group_node = self.grouped_table.insert(
                    parent_node, "end",
                    text="  ▸",
                    values=(
                        f"GRUPO: {group.name}",
                        f"Conceptos: {', '.join(group.concept_codes)}",
                        len(all_group_records),
                        f"{group_voluntaria:,.2f}",
                        f"{group_ejecutiva:,.2f}",
                        f"{group_recargo:,.2f}",
                        f"{group_dip_vol:,.2f}",
                        f"{group_dip_ejec:,.2f}",
                        f"{group_dip_rec:,.2f}",
                        f"{group_liquido:,.2f}"
                    ),
                    tags=("group_header",),
                    open=True
                )

                # Show individual concepts within the group
                for concept_code, concept_records in sorted(group_concept_items, key=lambda x: x[0]):
                    concept_name = config.get_concept_name(concept_code)

                    # Calculate concept totals (including diputación)
                    concept_voluntaria = sum(r.voluntaria for r in concept_records)
                    concept_ejecutiva = sum(r.ejecutiva for r in concept_records)
                    concept_recargo = sum(r.recargo for r in concept_records)
                    concept_dip_vol = sum(r.diputacion_voluntaria for r in concept_records)
                    concept_dip_ejec = sum(r.diputacion_ejecutiva for r in concept_records)
                    concept_dip_rec = sum(r.diputacion_recargo for r in concept_records)
                    concept_liquido = sum(r.liquido for r in concept_records)

                    # Insert concept under group
                    self.grouped_table.insert(
                        group_node, "end",
                        text="",
                        values=(
                            "",
                            f"  {concept_name} ({concept_code})",
                            len(concept_records),
                            f"{concept_voluntaria:,.2f}",
                            f"{concept_ejecutiva:,.2f}",
                            f"{concept_recargo:,.2f}",
                            f"{concept_dip_vol:,.2f}",
                            f"{concept_dip_ejec:,.2f}",
                            f"{concept_dip_rec:,.2f}",
                            f"{concept_liquido:,.2f}"
                        ),
                        tags=("concept_in_group",)
                    )

        # Display ungrouped concepts
        if ungrouped_concepts:
            for concept_code in sorted(ungrouped_concepts.keys()):
                concept_records = ungrouped_concepts[concept_code]
                concept_name = config.get_concept_name(concept_code)

                # Calculate concept totals (including diputación)
                concept_voluntaria = sum(r.voluntaria for r in concept_records)
                concept_ejecutiva = sum(r.ejecutiva for r in concept_records)
                concept_recargo = sum(r.recargo for r in concept_records)
                concept_dip_vol = sum(r.diputacion_voluntaria for r in concept_records)
                concept_dip_ejec = sum(r.diputacion_ejecutiva for r in concept_records)
                concept_dip_rec = sum(r.diputacion_recargo for r in concept_records)
                concept_liquido = sum(r.liquido for r in concept_records)

                # Insert concept node
                self.grouped_table.insert(
                    parent_node, "end",
                    text="  ▸",
                    values=(
                        "",
                        f"{concept_name} ({concept_code})",
                        len(concept_records),
                        f"{concept_voluntaria:,.2f}",
                        f"{concept_ejecutiva:,.2f}",
                        f"{concept_recargo:,.2f}",
                        f"{concept_dip_vol:,.2f}",
                        f"{concept_dip_ejec:,.2f}",
                        f"{concept_dip_rec:,.2f}",
                        f"{concept_liquido:,.2f}"
                    ),
                    tags=("concept_ungrouped",)
                )

    def _add_concept_nodes(self, parent_node, concepts_data, config):
        """Display individual concept nodes without custom grouping."""
        for code in sorted(concepts_data.keys()):
            concept_records = concepts_data[code]
            concept_name = config.get_concept_name(code)

            # Calculate concept totals (including diputación)
            concept_voluntaria = sum(r.voluntaria for r in concept_records)
            concept_ejecutiva = sum(r.ejecutiva for r in concept_records)
            concept_recargo = sum(r.recargo for r in concept_records)
            concept_dip_vol = sum(r.diputacion_voluntaria for r in concept_records)
            concept_dip_ejec = sum(r.diputacion_ejecutiva for r in concept_records)
            concept_dip_rec = sum(r.diputacion_recargo for r in concept_records)
            concept_liquido = sum(r.liquido for r in concept_records)

            # Insert concept header
            self.grouped_table.insert(
                parent_node, "end",
                text="  ▸",
                values=(
                    "",
                    f"{concept_name} ({code})",
                    len(concept_records),
                    f"{concept_voluntaria:,.2f}",
                    f"{concept_ejecutiva:,.2f}",
                    f"{concept_recargo:,.2f}",
                    f"{concept_dip_vol:,.2f}",
                    f"{concept_dip_ejec:,.2f}",
                    f"{concept_dip_rec:,.2f}",
                    f"{concept_liquido:,.2f}"
                ),
                tags=("concept_header",)
            )

    def _add_custom_groups_to_node_new(self, parent_node, records, config):
        """Apply custom groups directly to records (when concept grouping is not active)."""
        from collections import defaultdict

        # Create groups
        grouped_records = defaultdict(list)
        ungrouped_records = []

        for record in records:
            code = config.get_concept_code(record.clave_recaudacion)
            group_name = config.get_custom_group_for_concept(code)

            if group_name:
                grouped_records[group_name].append(record)
            else:
                ungrouped_records.append(record)

        # Display custom groups
        for group in config.custom_groups:
            if group.name in grouped_records:
                group_records = grouped_records[group.name]

                # Calculate group totals (including diputación)
                group_voluntaria = sum(r.voluntaria for r in group_records)
                group_ejecutiva = sum(r.ejecutiva for r in group_records)
                group_recargo = sum(r.recargo for r in group_records)
                group_dip_vol = sum(r.diputacion_voluntaria for r in group_records)
                group_dip_ejec = sum(r.diputacion_ejecutiva for r in group_records)
                group_dip_rec = sum(r.diputacion_recargo for r in group_records)
                group_liquido = sum(r.liquido for r in group_records)

                # Insert group header
                group_node = self.grouped_table.insert(
                    parent_node, "end",
                    text="  ▸",
                    values=(
                        f"GRUPO: {group.name}",
                        f"Conceptos: {', '.join(group.concept_codes)}",
                        len(group_records),
                        f"{group_voluntaria:,.2f}",
                        f"{group_ejecutiva:,.2f}",
                        f"{group_recargo:,.2f}",
                        f"{group_dip_vol:,.2f}",
                        f"{group_dip_ejec:,.2f}",
                        f"{group_dip_rec:,.2f}",
                        f"{group_liquido:,.2f}"
                    ),
                    tags=("group_header",),
                    open=True
                )

                # Show records in group
                for record in group_records:
                    code = config.get_concept_code(record.clave_recaudacion)
                    concept_name = config.get_concept_name(code)

                    self.grouped_table.insert(
                        group_node, "end",
                        text="",
                        values=(
                            "",
                            f"  {concept_name} ({code}) - Ej. {record.ejercicio}",
                            "1",
                            f"{record.voluntaria:,.2f}",
                            f"{record.ejecutiva:,.2f}",
                            f"{record.recargo:,.2f}",
                            f"{record.diputacion_voluntaria:,.2f}",
                            f"{record.diputacion_ejecutiva:,.2f}",
                            f"{record.diputacion_recargo:,.2f}",
                            f"{record.liquido:,.2f}"
                        ),
                        tags=("record_in_group",)
                    )

        # Display ungrouped records
        if ungrouped_records:
            for record in ungrouped_records:
                code = config.get_concept_code(record.clave_recaudacion)
                concept_name = config.get_concept_name(code)

                self.grouped_table.insert(
                    parent_node, "end",
                    text="",
                    values=(
                        "",
                        f"{concept_name} ({code}) - Ej. {record.ejercicio}",
                        "1",
                        f"{record.voluntaria:,.2f}",
                        f"{record.ejecutiva:,.2f}",
                        f"{record.recargo:,.2f}",
                        f"{record.diputacion_voluntaria:,.2f}",
                        f"{record.diputacion_ejecutiva:,.2f}",
                        f"{record.diputacion_recargo:,.2f}",
                        f"{record.liquido:,.2f}"
                    ),
                    tags=("record_ungrouped",)
                )

    def _add_individual_records(self, parent_node, records, config):
        """Display individual records without any grouping."""
        row_num = 0
        for record in records:
            tag = "evenrow" if row_num % 2 == 0 else "oddrow"
            code = config.get_concept_code(record.clave_recaudacion)
            concept_name = config.get_concept_name(code)

            self.grouped_table.insert(
                parent_node, "end",
                text="",
                values=(
                    "",
                    f"{concept_name} ({code}) - Ej. {record.ejercicio}",
                    "1",
                    f"{record.voluntaria:,.2f}",
                    f"{record.ejecutiva:,.2f}",
                    f"{record.recargo:,.2f}",
                    f"{record.diputacion_voluntaria:,.2f}",
                    f"{record.diputacion_ejecutiva:,.2f}",
                    f"{record.diputacion_recargo:,.2f}",
                    f"{record.liquido:,.2f}"
                ),
                tags=(tag,)
            )
            row_num += 1

    def _display_grouped_by_year(self, records, config):
        """Display records grouped by year (and optionally by concept)."""
        from decimal import Decimal
        from collections import defaultdict

        # Group by year
        years_data = defaultdict(list)
        for record in records:
            years_data[record.ejercicio].append(record)

        row_num = 0
        for ejercicio in sorted(years_data.keys()):
            year_records = years_data[ejercicio]

            # Calculate year totals
            year_voluntaria = sum(r.voluntaria for r in year_records)
            year_ejecutiva = sum(r.ejecutiva for r in year_records)
            year_recargo = sum(r.recargo for r in year_records)
            year_liquido = sum(r.liquido for r in year_records)

            # Insert year header as parent node
            year_node = self.grouped_table.insert(
                "", "end",
                text="▼",
                values=(
                    f"EJERCICIO {ejercicio}",
                    "",
                    len(year_records),
                    f"{year_voluntaria:,.2f}",
                    f"{year_ejecutiva:,.2f}",
                    f"{year_recargo:,.2f}",
                    f"{year_liquido:,.2f}"
                ),
                tags=("year_header",),
                open=True
            )
            row_num += 1

            # If concept grouping is enabled, group within year
            if config.group_by_concept:
                self._add_concept_groups_to_node(
                    year_node, year_records, config, row_num
                )
            else:
                # Just show records
                for record in year_records:
                    tag = "evenrow" if row_num % 2 == 0 else "oddrow"
                    code = config.get_concept_code(record.clave_recaudacion)
                    concept_name = config.get_concept_name(code)

                    self.grouped_table.insert(
                        year_node, "end",
                        text="",
                        values=(
                            "",
                            f"{concept_name} ({code})",
                            "1",
                            f"{record.voluntaria:,.2f}",
                            f"{record.ejecutiva:,.2f}",
                            f"{record.recargo:,.2f}",
                            f"{record.liquido:,.2f}"
                        ),
                        tags=(tag,)
                    )
                    row_num += 1

    def _display_grouped_by_concept(self, records, config):
        """Display records grouped by concept."""
        from decimal import Decimal
        from collections import defaultdict

        # Group by concept code
        concepts_data = defaultdict(list)
        for record in records:
            code = config.get_concept_code(record.clave_recaudacion)
            concepts_data[code].append(record)

        row_num = 0
        for code in sorted(concepts_data.keys()):
            concept_records = concepts_data[code]
            concept_name = config.get_concept_name(code)

            # Calculate concept totals
            concept_voluntaria = sum(r.voluntaria for r in concept_records)
            concept_ejecutiva = sum(r.ejecutiva for r in concept_records)
            concept_recargo = sum(r.recargo for r in concept_records)
            concept_liquido = sum(r.liquido for r in concept_records)

            # Insert concept header as parent node
            concept_node = self.grouped_table.insert(
                "", "end",
                text="▼",
                values=(
                    f"CONCEPTO: {concept_name}",
                    f"Código: {code}",
                    len(concept_records),
                    f"{concept_voluntaria:,.2f}",
                    f"{concept_ejecutiva:,.2f}",
                    f"{concept_recargo:,.2f}",
                    f"{concept_liquido:,.2f}"
                ),
                tags=("concept_header",),
                open=True
            )
            row_num += 1

            # Show records under concept
            for record in concept_records:
                tag = "evenrow" if row_num % 2 == 0 else "oddrow"
                self.grouped_table.insert(
                    concept_node, "end",
                    text="",
                    values=(
                        "",
                        f"Ejercicio {record.ejercicio}",
                        "1",
                        f"{record.voluntaria:,.2f}",
                        f"{record.ejecutiva:,.2f}",
                        f"{record.recargo:,.2f}",
                        f"{record.liquido:,.2f}"
                    ),
                    tags=(tag,)
                )
                row_num += 1

    def _display_custom_groups(self, records, config):
        """Display records grouped by custom groups."""
        from decimal import Decimal
        from collections import defaultdict

        # Create groups
        grouped_records = defaultdict(list)
        ungrouped_records = []

        for record in records:
            code = config.get_concept_code(record.clave_recaudacion)
            group_name = config.get_custom_group_for_concept(code)

            if group_name:
                grouped_records[group_name].append(record)
            else:
                ungrouped_records.append(record)

        row_num = 0

        # Display custom groups
        for group in config.custom_groups:
            if group.name in grouped_records:
                group_records = grouped_records[group.name]

                # Calculate group totals
                group_voluntaria = sum(r.voluntaria for r in group_records)
                group_ejecutiva = sum(r.ejecutiva for r in group_records)
                group_recargo = sum(r.recargo for r in group_records)
                group_liquido = sum(r.liquido for r in group_records)

                # Insert group header
                group_node = self.grouped_table.insert(
                    "", "end",
                    text="▼",
                    values=(
                        f"GRUPO: {group.name}",
                        f"Conceptos: {', '.join(group.concept_codes)}",
                        len(group_records),
                        f"{group_voluntaria:,.2f}",
                        f"{group_ejecutiva:,.2f}",
                        f"{group_recargo:,.2f}",
                        f"{group_liquido:,.2f}"
                    ),
                    tags=("group_header",),
                    open=True
                )
                row_num += 1

                # Show records in group
                for record in group_records:
                    tag = "evenrow" if row_num % 2 == 0 else "oddrow"
                    code = config.get_concept_code(record.clave_recaudacion)
                    concept_name = config.get_concept_name(code)

                    self.grouped_table.insert(
                        group_node, "end",
                        text="",
                        values=(
                            "",
                            f"{concept_name} ({code}) - Ej. {record.ejercicio}",
                            "1",
                            f"{record.voluntaria:,.2f}",
                            f"{record.ejecutiva:,.2f}",
                            f"{record.recargo:,.2f}",
                            f"{record.liquido:,.2f}"
                        ),
                        tags=(tag,)
                    )
                    row_num += 1

        # Display ungrouped records
        if ungrouped_records:
            ungrouped_voluntaria = sum(r.voluntaria for r in ungrouped_records)
            ungrouped_ejecutiva = sum(r.ejecutiva for r in ungrouped_records)
            ungrouped_recargo = sum(r.recargo for r in ungrouped_records)
            ungrouped_liquido = sum(r.liquido for r in ungrouped_records)

            ungrouped_node = self.grouped_table.insert(
                "", "end",
                text="▼",
                values=(
                    "SIN AGRUPAR",
                    "",
                    len(ungrouped_records),
                    f"{ungrouped_voluntaria:,.2f}",
                    f"{ungrouped_ejecutiva:,.2f}",
                    f"{ungrouped_recargo:,.2f}",
                    f"{ungrouped_liquido:,.2f}"
                ),
                tags=("concept_header",),
                open=True
            )

            for record in ungrouped_records:
                tag = "evenrow" if row_num % 2 == 0 else "oddrow"
                code = config.get_concept_code(record.clave_recaudacion)
                concept_name = config.get_concept_name(code)

                self.grouped_table.insert(
                    ungrouped_node, "end",
                    text="",
                    values=(
                        "",
                        f"{concept_name} ({code}) - Ej. {record.ejercicio}",
                        "1",
                        f"{record.voluntaria:,.2f}",
                        f"{record.ejecutiva:,.2f}",
                        f"{record.recargo:,.2f}",
                        f"{record.liquido:,.2f}"
                    ),
                    tags=(tag,)
                )
                row_num += 1

    def _add_concept_groups_to_node(self, parent_node, records, config, start_row):
        """Add concept-grouped records to a parent node."""
        from collections import defaultdict

        # Group by concept
        concepts_data = defaultdict(list)
        for record in records:
            code = config.get_concept_code(record.clave_recaudacion)
            concepts_data[code].append(record)

        row_num = start_row
        for code in sorted(concepts_data.keys()):
            concept_records = concepts_data[code]
            concept_name = config.get_concept_name(code)

            # Calculate concept totals
            concept_voluntaria = sum(r.voluntaria for r in concept_records)
            concept_ejecutiva = sum(r.ejecutiva for r in concept_records)
            concept_recargo = sum(r.recargo for r in concept_records)
            concept_liquido = sum(r.liquido for r in concept_records)

            # Insert concept sub-header
            self.grouped_table.insert(
                parent_node, "end",
                text="  ▸",
                values=(
                    "",
                    f"{concept_name} ({code})",
                    len(concept_records),
                    f"{concept_voluntaria:,.2f}",
                    f"{concept_ejecutiva:,.2f}",
                    f"{concept_recargo:,.2f}",
                    f"{concept_liquido:,.2f}"
                ),
                tags=("concept_header",)
            )
            row_num += 1
