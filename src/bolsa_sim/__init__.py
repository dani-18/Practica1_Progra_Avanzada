"""Simulador de Bolsa y Carteras de Inversion (PRAC1, version minima).

Paquete con el modelo de dominio reducido a 4 clases de referencia.
``InstrumentoBase`` queda preparada como clase padre para la jerarquia
que se anadira en PRAC2 (p.ej. ``Accion(InstrumentoBase)``,
``Bono(InstrumentoBase)``, ``ETF(InstrumentoBase)``).
"""

from __future__ import annotations

from .cartera import Cartera
from .instrumento import InstrumentoBase
from .mercado import Mercado
from .operacion import Operacion

__all__ = [
    "Cartera",
    "InstrumentoBase",
    "Mercado",
    "Operacion",
]

__version__ = "0.2.0"
