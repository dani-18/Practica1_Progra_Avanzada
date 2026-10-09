"""Tests de humo + integracion del modelo minimo (4 clases)."""

from __future__ import annotations

import pytest

from bolsa_sim.accion import Accion
from bolsa_sim.bono import Bono
from bolsa_sim.cartera import Cartera
from bolsa_sim.etf import ETF
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


def test_jerarquia_polimorfica_prac2() -> None:
    """Las tres subclases conviven en un ``Mercado`` y responden distinto."""
    accion = Accion(
        "ACME", "Acme Corp", "ACME", 0.2, 120.0, sector="Tecnologia", dividendo_anual=1.8
    )
    bono = Bono(
        "BONO10",
        "Bono 10 anos",
        "B10",
        0.05,
        100.0,
        cupon_anual=0.04,
        valor_nominal=1_000.0,
    )
    etf = ETF("SPX", "ETF S&P 500", "SPX", 0.15, 400.0, indice="S&P 500", comision_gestion=0.002)
    mercado = Mercado("Bolsa", {i.id: i for i in (accion, bono, etf)}, semilla=7)

    # Todas son InstrumentoBase (relacion de herencia).
    assert all(isinstance(i, InstrumentoBase) for i in mercado.instrumentos.values())

    # Polimorfismo: mismo metodo, resultados distintos segun el tipo.
    assert accion.flujo_anual() == pytest.approx(1.8)
    assert bono.flujo_anual() == pytest.approx(40.0)
    assert etf.flujo_anual() == pytest.approx(0.0)

    # El mercado evoluciona los tres precios sin conocer su tipo concreto.
    nuevos = mercado.avanzar_sesion(volumen=30)
    assert set(nuevos) == {"ACME", "BONO10", "SPX"}
    assert mercado.sesion == 1
