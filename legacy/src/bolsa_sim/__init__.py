"""Simulador de Bolsa y Carteras de Inversion (PRAC1, TPA).

Este paquete modela el dominio de un mercado con activos ficticios:
instrumentos financieros, posiciones, transacciones, evolucion del
mercado, estrategias y metricas. Implementa el **esqueleto** del
proyecto y la prueba de concepto ("hello flow") de la PRAC1.
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "dani-18 y colaboradores"
__license__ = "MIT"

# Orden pensado para evitar ciclos: activos no dependen de nadie;
# mercado depende de activos; cartera depende de ambos;
# simulacion depende de todo; estrategias depende de tipos duck-typing.
from .activos import (
    Activo,
    BarraDiaria,
    Posicion,
    TipoActivo,
    TipoOperacion,
    Transaccion,
)
from .cartera import Cartera
from .estrategias import AportePeriodico, CompraYMantiene, Orden
from .mercado import MercadoSimulado
from .metricas import drawdown_maximo, rentabilidad_total
from .simulacion import ResultadoSimulacion, Simulador

__all__ = [
    "Activo",
    "AportePeriodico",
    "BarraDiaria",
    "Cartera",
    "CompraYMantiene",
    "MercadoSimulado",
    "Orden",
    "Posicion",
    "ResultadoSimulacion",
    "Simulador",
    "TipoActivo",
    "TipoOperacion",
    "Transaccion",
    "__version__",
    "drawdown_maximo",
    "rentabilidad_total",
]
