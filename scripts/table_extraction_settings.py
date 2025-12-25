"""
Configuración de parámetros para extracción de tablas con pdfplumber.
Proporciona valores por defecto y metadatos para la interfaz GUI.
"""
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class ParameterConfig:
    """Configuración de un parámetro de extracción."""
    name: str
    type: str  # 'choice', 'int', 'float', 'bool'
    default: Any
    description: str
    choices: List[Any] = field(default_factory=list)
    min_value: float = 0
    max_value: float = 100
    step: float = 1


# Definición de todos los parámetros de extracción
TABLE_EXTRACTION_PARAMETERS = [
    # Estrategias de detección
    ParameterConfig(
        name="vertical_strategy",
        type="choice",
        default="lines",
        description="Estrategia para detectar bordes verticales de tabla",
        choices=["lines", "lines_strict", "text", "explicit"]
    ),
    ParameterConfig(
        name="horizontal_strategy",
        type="choice",
        default="lines",
        description="Estrategia para detectar bordes horizontales de tabla",
        choices=["lines", "lines_strict", "text", "explicit"]
    ),

    # Tolerancias de ajuste (snap)
    ParameterConfig(
        name="snap_tolerance",
        type="int",
        default=3,
        description="Tolerancia general para ajustar bordes cercanos (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
    ParameterConfig(
        name="snap_x_tolerance",
        type="int",
        default=0,
        description="Tolerancia horizontal para ajustar bordes verticales (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
    ParameterConfig(
        name="snap_y_tolerance",
        type="int",
        default=0,
        description="Tolerancia vertical para ajustar bordes horizontales (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),

    # Tolerancias de unión (join)
    ParameterConfig(
        name="join_tolerance",
        type="int",
        default=3,
        description="Tolerancia general para unir bordes cercanos (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
    ParameterConfig(
        name="join_x_tolerance",
        type="int",
        default=0,
        description="Tolerancia horizontal para unir bordes (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
    ParameterConfig(
        name="join_y_tolerance",
        type="int",
        default=0,
        description="Tolerancia vertical para unir bordes (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),

    # Longitud mínima de bordes
    ParameterConfig(
        name="edge_min_length",
        type="int",
        default=3,
        description="Longitud mínima de borde para ser considerado (píxeles)",
        min_value=1,
        max_value=50,
        step=1
    ),

    # Palabras mínimas para estrategia 'text'
    ParameterConfig(
        name="min_words_vertical",
        type="int",
        default=3,
        description="Palabras mínimas para detectar borde vertical (estrategia 'text')",
        min_value=1,
        max_value=10,
        step=1
    ),
    ParameterConfig(
        name="min_words_horizontal",
        type="int",
        default=1,
        description="Palabras mínimas para detectar borde horizontal (estrategia 'text')",
        min_value=1,
        max_value=10,
        step=1
    ),

    # Tolerancias de intersección
    ParameterConfig(
        name="intersection_tolerance",
        type="int",
        default=3,
        description="Tolerancia general para detectar intersecciones (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
    ParameterConfig(
        name="intersection_x_tolerance",
        type="int",
        default=0,
        description="Tolerancia horizontal para intersecciones (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
    ParameterConfig(
        name="intersection_y_tolerance",
        type="int",
        default=0,
        description="Tolerancia vertical para intersecciones (píxeles)",
        min_value=0,
        max_value=20,
        step=1
    ),
]


class TableExtractionSettings:
    """Administrador de configuración de extracción de tablas."""

    def __init__(self):
        self.settings: Dict[str, Any] = self.get_default_settings()

    @staticmethod
    def get_default_settings() -> Dict[str, Any]:
        """Obtiene la configuración por defecto."""
        return {param.name: param.default for param in TABLE_EXTRACTION_PARAMETERS}

    def update(self, **kwargs):
        """Actualiza la configuración con nuevos valores."""
        for key, value in kwargs.items():
            if key in self.settings:
                self.settings[key] = value

    def reset_to_defaults(self):
        """Restaura todos los valores a sus valores por defecto."""
        self.settings = self.get_default_settings()

    def get_table_settings_dict(self) -> Dict[str, Any]:
        """
        Obtiene el diccionario de configuración para pasar a pdfplumber.
        Solo incluye valores que no son los por defecto.
        """
        defaults = self.get_default_settings()
        # Solo incluir valores que difieren del default
        return {
            key: value
            for key, value in self.settings.items()
            if value != defaults.get(key)
        }

    def get_full_table_settings_dict(self) -> Dict[str, Any]:
        """Obtiene el diccionario completo de configuración."""
        return self.settings.copy()

    def __repr__(self) -> str:
        """Representación en string de la configuración."""
        non_default = self.get_table_settings_dict()
        if not non_default:
            return "TableExtractionSettings(default)"
        return f"TableExtractionSettings({non_default})"


def get_parameter_by_name(name: str) -> ParameterConfig:
    """Obtiene la configuración de un parámetro por su nombre."""
    for param in TABLE_EXTRACTION_PARAMETERS:
        if param.name == name:
            return param
    raise ValueError(f"Parámetro desconocido: {name}")
