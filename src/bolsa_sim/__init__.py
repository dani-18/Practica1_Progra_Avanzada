"""Simulador de Bolsa y Carteras de Inversion (PRAC1-PRAC4).

Paquete con el modelo de dominio, la jerarquia de instrumentos, las
estrategias de inversion, las metricas, la simulacion concurrente y la
capa de persistencia.

Version 1.0.0: patrones Strategy/Factory, excepciones de dominio,
SQLite + JSON/CSV, GUI Tkinter y concurrencia.
"""

from __future__ import annotations

from .accion import Accion
from .bono import Bono
from .cartera import Cartera
from .cli import Shell
from .concurrencia import (
    Escenario,
    ResultadoEscenario,
    comparar_estrategias,
    ejecutar_escenario,
    ejecutar_escenarios,
    escenarios_por_defecto,
)
from .estrategias import (
    ComprarMantener,
    ContextoMercado,
    Decision,
    EstrategiaInversion,
    Momentum,
    Rebalanceo,
    crear_estrategia,
    estrategias_disponibles,
)
from .etf import ETF
from .excepciones import (
    DatosInvalidos,
    ErrorBolsa,
    ErrorPersistencia,
    ErrorSimulacion,
    EstrategiaDesconocida,
    FondosInsuficientes,
    FormatoNoSoportado,
    InstrumentoDesconocido,
    InstrumentoDuplicado,
    OperacionInvalida,
    PosicionInsuficiente,
    TipoInstrumentoDesconocido,
)
from .fabrica import FabricaInstrumentos
from .instrumento import InstrumentoBase
from .mercado import Mercado
from .metricas import (
    MetricasInversion,
    calcular_metricas,
    max_drawdown,
    metricas_cartera,
    ratio_sharpe,
    rentabilidad_anualizada,
    rentabilidad_total,
    volatilidad_anualizada,
)
from .operacion import Operacion
from .simulacion import ResultadoSimulacion, Simulador, simular

__all__ = [
    "ETF",
    "Accion",
    "Bono",
    "Cartera",
    "ComprarMantener",
    "ContextoMercado",
    "DatosInvalidos",
    "Decision",
    "ErrorBolsa",
    "ErrorPersistencia",
    "ErrorSimulacion",
    "Escenario",
    "EstrategiaDesconocida",
    "EstrategiaInversion",
    "FabricaInstrumentos",
    "FondosInsuficientes",
    "FormatoNoSoportado",
    "InstrumentoBase",
    "InstrumentoDesconocido",
    "InstrumentoDuplicado",
    "Mercado",
    "MetricasInversion",
    "Momentum",
    "Operacion",
    "OperacionInvalida",
    "PosicionInsuficiente",
    "Rebalanceo",
    "ResultadoEscenario",
    "ResultadoSimulacion",
    "Shell",
    "Simulador",
    "TipoInstrumentoDesconocido",
    "calcular_metricas",
    "comparar_estrategias",
    "crear_estrategia",
    "ejecutar_escenario",
    "ejecutar_escenarios",
    "escenarios_por_defecto",
    "estrategias_disponibles",
    "max_drawdown",
    "metricas_cartera",
    "ratio_sharpe",
    "rentabilidad_anualizada",
    "rentabilidad_total",
    "simular",
    "volatilidad_anualizada",
]

__version__ = "1.0.0"
