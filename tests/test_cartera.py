"""Tests de ``Cartera``."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.instrumento import InstrumentoBase
from bolsa_sim.mercado import Mercado


@pytest.fixture
def mercado() -> Mercado:
    a = InstrumentoBase("ACME", "Acme", "ACME", volatilidad=0.2, precio_base=100.0)
    b = InstrumentoBase("GLOB", "Glob", "GLOB", volatilidad=0.3, precio_base=50.0)
    return Mercado("M", {a.id: a, b.id: b}, semilla=1)


def test_cartera_crea() -> None:
    c = Cartera("Dani", efectivo=100.0, comision=1.0)
    assert c.propietario == "Dani"
    assert c.efectivo == 100.0
    assert c.comision == 1.0
    assert c.posiciones == ()
    assert c.historial == ()
    assert c.total_operaciones == 0


def test_cartera_property_efectivo_valida() -> None:
    c = Cartera("Dani", efectivo=100.0)
    c.efectivo = 250.0
    assert c.efectivo == 250.0
    with pytest.raises(ValueError):
        c.efectivo = -1.0
    with pytest.raises(TypeError):
        c.efectivo = "no"  # type: ignore[assignment]


def test_cartera_property_comision_valida() -> None:
    c = Cartera("Dani", comision=1.0)
    c.comision = 5.0
    assert c.comision == 5.0
    with pytest.raises(ValueError):
        c.comision = -0.1


def test_cartera_invertir_y_desinvertir(mercado: Mercado) -> None:
    c = Cartera("Dani", efectivo=500.0, comision=1.0)
    op = c.invertir(mercado, "ACME", 2, precio=100.0, fecha="2026-09-25 10:00")
    assert op is not None
    # Coste: 2*100 + 1 comision = 201
    assert c.efectivo == pytest.approx(299.0)
    assert dict(c.posiciones).get("ACME") == 2
    assert c.total_operaciones == 1

    op2 = c.desinvertir(mercado, "ACME", 1, precio=110.0, fecha="2026-09-25 11:00")
    assert op2 is not None
    # Ingreso: 1*110 - 1 = 109
    assert c.efectivo == pytest.approx(408.0)
    assert dict(c.posiciones).get("ACME") == 1


def test_cartera_invertir_sin_fondos(mercado: Mercado) -> None:
    c = Cartera("Dani", efectivo=10.0, comision=1.0)
    op = c.invertir(mercado, "ACME", 1, precio=100.0, fecha="2026")
    assert op is None
    assert c.efectivo == 10.0
    assert c.posiciones == ()


def test_cartera_desinvertir_sin_posicion(mercado: Mercado) -> None:
    c = Cartera("Dani", efectivo=1000.0, comision=0.0)
    op = c.desinvertir(mercado, "GLOB", 1, precio=50.0, fecha="2026")
    assert op is None


def test_cartera_validacion_cantidad(mercado: Mercado) -> None:
    c = Cartera("Dani", efectivo=1000.0)
    with pytest.raises(ValueError):
        c.invertir(mercado, "ACME", 0, precio=100.0, fecha="2026")
    with pytest.raises(ValueError):
        c.desinvertir(mercado, "ACME", -1, precio=100.0, fecha="2026")


def test_cartera_mostrar(capsys) -> None:
    c = Cartera("Dani", efectivo=100.0)
    c.mostrar()
    out = capsys.readouterr().out
    assert "[Cartera]" in out
    assert "Dani" in out


def test_cartera_propietario_no_vacio() -> None:
    with pytest.raises(ValueError):
        Cartera("", efectivo=100.0)
    with pytest.raises(ValueError):
        Cartera("   ", efectivo=100.0)
