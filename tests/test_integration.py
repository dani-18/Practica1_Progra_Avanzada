"""Tests de humo + integracion del modelo minimo (4 clases)."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.instrumento import InstrumentoBase
from bolsa_sim.mercado import Mercado


def test_hello_flow_4_clases() -> None:
    """El flujo basico exigido por la PRAC1, reducido a las 4 clases."""
    a = InstrumentoBase("ACME", "Acme Corp", "ACME", volatilidad=0.2, precio_base=100.0)
    b = InstrumentoBase("BONO10", "Bono 10a", "B10", volatilidad=0.05, precio_base=100.0)
    mercado = Mercado("Bolsa", {a.id: a, b.id: b}, semilla=42)
    cartera = Cartera("Dani", efectivo=1_000.0, comision=1.0)

    for _ in range(10):
        nuevos = mercado.avanzar_sesion(volumen=100)
        if cartera.efectivo > 200:
            cartera.invertir(
                mercado,
                a.id,
                1,
                precio=nuevos[a.id],
                fecha="s1",
            )

    assert mercado.sesion == 10
    assert mercado.volumen_total == 1000
    assert cartera.total_operaciones >= 1
    assert cartera.valor_total(mercado) > 0


def test_herencia_preparada() -> None:
    """Verifica que ``InstrumentoBase`` puede especializarse (PRAC2)."""
    # Solo se comprueba que la clase padre admite una subclase trivial
    # sin necesidad de reimplementar lo basico. Esto es solo un check
    # de "preparacion para la PRAC2": la subclase aqui creada NO
    # aparece en el paquete (es solo una muestra de la intencion).

    class Accion(InstrumentoBase):
        def __init__(self, id: str, nombre: str, simbolo: str, precio_base: float) -> None:
            super().__init__(id, nombre, simbolo, volatilidad=0.2, precio_base=precio_base)
            self.tipo = "accion"

    acc = Accion("ACME", "Acme Corp", "ACME", precio_base=100.0)
    assert acc.volatilidad == 0.2
    # La subclase hereda las properties con validacion:
    with pytest.raises(ValueError):
        acc.precio_base = -1.0
