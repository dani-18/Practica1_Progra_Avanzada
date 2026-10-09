"""Datos de ejemplo reutilizables por la demo y la CLI interactiva.

Centraliza la construccion del mercado y la cartera por defecto para que
``python -m bolsa_sim --demo`` y ``python -m bolsa_sim --cli`` compartan
exactamente el mismo escenario (una accion, un bono y un ETF).
"""

from __future__ import annotations

from .accion import Accion
from .bono import Bono
from .cartera import Cartera
from .etf import ETF
from .instrumento import InstrumentoBase
from .mercado import Mercado


def instrumentos_demo() -> list[InstrumentoBase]:
    """Devuelve la jerarquia Accion/Bono/ETF del escenario de ejemplo."""
    return [
        Accion(
            id="ACME",
            nombre="Acme Corp",
            simbolo="ACME",
            volatilidad=0.20,
            precio_base=120.0,
            sector="Tecnologia",
            dividendo_anual=1.80,
        ),
        Bono(
            id="BONO10",
            nombre="Bono 10 anos",
            simbolo="B10",
            volatilidad=0.05,
            precio_base=100.0,
            cupon_anual=0.04,
            valor_nominal=1_000.0,
            vencimiento=10,
        ),
        ETF(
            id="SP500",
            nombre="ETF S&P 500",
            simbolo="SPX",
            volatilidad=0.15,
            precio_base=400.0,
            indice="S&P 500",
            comision_gestion=0.002,
        ),
    ]


def mercado_demo(semilla: int | None = 42) -> Mercado:
    """Mercado de ejemplo con los tres instrumentos de la jerarquia."""
    return Mercado("Bolsa Continuo", {i.id: i for i in instrumentos_demo()}, semilla=semilla)


def cartera_demo(propietario: str = "Dani", efectivo: float = 1_000.0) -> Cartera:
    """Cartera de ejemplo con efectivo inicial y comision por operacion."""
    return Cartera(propietario=propietario, efectivo=efectivo, comision=1.0)
