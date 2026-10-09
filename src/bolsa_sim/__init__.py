"""Simulador de Bolsa y Carteras de Inversion (PRAC1-PRAC2).

Paquete con el modelo de dominio de referencia. ``InstrumentoBase`` es
la clase padre de la jerarquia de instrumentos que se concreta en PRAC2:
``Accion``, ``Bono`` y ``ETF``.
"""

from __future__ import annotations

from .accion import Accion
from .bono import Bono
from .cartera import Cartera
from .cli import Shell
from .etf import ETF
from .instrumento import InstrumentoBase
from .mercado import Mercado
from .operacion import Operacion

__all__ = [
    "ETF",
    "Accion",
    "Bono",
    "Cartera",
    "InstrumentoBase",
    "Mercado",
    "Operacion",
    "Shell",
]

__version__ = "0.4.0"
