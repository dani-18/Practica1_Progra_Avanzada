"""Tests de ``Mercado``."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.instrumento import InstrumentoBase
from bolsa_sim.mercado import Mercado


@pytest.fixture
def mercado() -> Mercado:
    a = InstrumentoBase("ACME", "Acme", "ACME", volatilidad=0.2, precio_base=100.0)
    b = InstrumentoBase("GLOB", "Glob", "GLOB", volatilidad=0.3, precio_base=50.0)
    return Mercado("Continuo", {a.id: a, b.id: b}, semilla=42)


def test_mercado_crea(mercado: Mercado) -> None:
    assert mercado.nombre == "Continuo"
    assert mercado.semilla == 42
    assert mercado.sesion == 0
    assert mercado.volumen_total == 0
    assert mercado.ids == ("ACME", "GLOB")


def test_mercado_property_sesion_valida(mercado: Mercado) -> None:
    mercado.sesion = 5
    assert mercado.sesion == 5
    with pytest.raises(ValueError):
        mercado.sesion = -1


def test_mercado_property_volumen_valida(mercado: Mercado) -> None:
    mercado.volumen_total = 100
    assert mercado.volumen_total == 100
    with pytest.raises(ValueError):
        mercado.volumen_total = -1


def test_mercado_avanzar_sesion(mercado: Mercado) -> None:
    nuevos = mercado.avanzar_sesion(volumen=10)
    assert "ACME" in nuevos and "GLOB" in nuevos
    assert mercado.sesion == 1
    assert mercado.volumen_total == 10
    mercado.avanzar_sesion(volumen=10)
    assert mercado.sesion == 2
    assert mercado.volumen_total == 20


def test_mercado_precio_de_instrumento_inexistente(mercado: Mercado) -> None:
    with pytest.raises(KeyError):
        mercado.precio_de("XX")


def test_mercado_registrar_duplicado(mercado: Mercado) -> None:
    x = InstrumentoBase("ACME", "Otro", "ACME", 0.1, 1.0)
    with pytest.raises(ValueError):
        mercado.registrar(x)


def test_mercado_semilla_reproducible() -> None:
    a1 = InstrumentoBase("X", "X", "X", 0.4, 100.0)
    a2 = InstrumentoBase("X", "X", "X", 0.4, 100.0)
    m1 = Mercado("M", {a1.id: a1}, semilla=99)
    m2 = Mercado("M", {a2.id: a2}, semilla=99)
    m1.avanzar_sesion(1)
    m2.avanzar_sesion(1)
    assert m1.instrumentos["X"].precio_base == m2.instrumentos["X"].precio_base


def test_mercado_liquidar_cartera(mercado: Mercado) -> None:
    c = Cartera("Dani", efectivo=1000.0, comision=0.5)
    c.invertir(mercado, "ACME", 3, precio=100.0, fecha="s1")
    ingreso = mercado.liquidar(c)
    # Solo opera sobre posiciones existentes; la venta a precio actual
    # registra Operacion con cantidad=3 y tipo venta.
    assert c.posiciones == ()
    assert c.total_operaciones == 2  # 1 compra + 1 venta de la liquidacion
    assert ingreso > 0


def test_mercado_mostrar(capsys, mercado: Mercado) -> None:
    mercado.mostrar()
    out = capsys.readouterr().out
    assert "[Mercado]" in out
    assert "Continuo" in out


def test_mercado_nombre_vacio() -> None:
    with pytest.raises(ValueError):
        Mercado("", {}, semilla=None)


def test_mercado_semilla_invalida() -> None:
    with pytest.raises(TypeError):
        Mercado("M", {}, semilla=1.5)  # type: ignore[arg-type]
