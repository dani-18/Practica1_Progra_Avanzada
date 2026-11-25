"""Simulador de Bolsa y Carteras de Inversion (PRAC1-PRAC4).

Paquete con el modelo de dominio, la jerarquia de instrumentos, las
metricas y la capa de persistencia.

Version 1.0.0: patrones Factory/Strategy, excepciones de dominio,
SQLite + JSON/CSV y GUI Tkinter.
"""

from __future__ import annotations

from .accion import Accion
from .bono import Bono
from .cartera import Cartera
from .etf import ETF
from .excepciones import (
    CarteraDesconocida,
    CarteraDuplicada,
    DatosInvalidos,
    ErrorBolsa,
    ErrorPersistencia,
    FondosInsuficientes,
    FormatoNoSoportado,
    InstrumentoDesconocido,
    InstrumentoDuplicado,
    OperacionInvalida,
    PosicionInsuficiente,
    TipoInstrumentoDesconocido,
)
from .fabrica import FabricaInstrumentos
from .gestor_carteras import GestorCarteras
from .instrumento import InstrumentoBase
from .logging_config import configurar_logging, obtener_logger
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

__all__ = [
    "ETF",
    "Accion",
    "Bono",
    "Cartera",
    "CarteraDesconocida",
    "CarteraDuplicada",
    "DatosInvalidos",
    "ErrorBolsa",
    "ErrorPersistencia",
    "FabricaInstrumentos",
    "FondosInsuficientes",
    "FormatoNoSoportado",
    "GestorCarteras",
    "InstrumentoBase",
    "InstrumentoDesconocido",
    "InstrumentoDuplicado",
    "Mercado",
    "MetricasInversion",
    "Operacion",
    "OperacionInvalida",
    "PosicionInsuficiente",
    "TipoInstrumentoDesconocido",
    "calcular_metricas",
    "configurar_logging",
    "max_drawdown",
    "metricas_cartera",
    "obtener_logger",
    "ratio_sharpe",
    "rentabilidad_anualizada",
    "rentabilidad_total",
    "volatilidad_anualizada",
]

__version__ = "1.0.0"
