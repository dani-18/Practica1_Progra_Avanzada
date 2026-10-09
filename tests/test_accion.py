"""Tests de ``Accion`` (subclase de ``InstrumentoBase``)."""

from __future__ import annotations

import pytest

from bolsa_sim.accion import Accion
from bolsa_sim.instrumento import InstrumentoBase


def test_accion_crea_con_defaults() -> None:
    a = Accion("acme", "Acme Corp", "acme", volatilidad=0.2, precio_base=100.0)
    assert a.id == "ACME"  # normaliza a mayusculas (lo hace la base)
    assert a.tipo == "accion"
    assert a.sector == "General"
    assert a.dividendo_anual == 0.0


def test_accion_es_instrumento_base() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0)
    assert isinstance(a, InstrumentoBase)


def test_accion_hereda_validacion_de_la_base() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0)
    with pytest.raises(ValueError):
        a.precio_base = -1.0
    with pytest.raises(ValueError):
        a.volatilidad = 9.0


def test_accion_sector_valida() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0)
    a.sector = "  Tecnologia  "
    assert a.sector == "Tecnologia"
    with pytest.raises(ValueError):
        a.sector = "   "


def test_accion_dividendo_valida() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0)
    a.dividendo_anual = 1.5
    assert a.dividendo_anual == 1.5
    with pytest.raises(ValueError):
        a.dividendo_anual = -0.1
    with pytest.raises(TypeError):
        a.dividendo_anual = "no"  # type: ignore[assignment]


def test_accion_flujo_anual() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0, dividendo_anual=2.0)
    assert a.flujo_anual() == 2.0
    assert InstrumentoBase("X", "X", "X", 0.1, 1.0).flujo_anual() == 0.0


def test_accion_rentabilidad_por_dividendo() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0, dividendo_anual=5.0)
    assert a.rentabilidad_por_dividendo() == pytest.approx(0.05)
    assert a.rentabilidad_por_dividendo(50.0) == pytest.approx(0.10)
    with pytest.raises(ValueError):
        a.rentabilidad_por_dividendo(0.0)


def test_accion_mostrar(capsys) -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0, sector="Tecnologia", dividendo_anual=1.8)
    a.mostrar()
    out = capsys.readouterr().out
    assert "[Accion]" in out
    assert "Tecnologia" in out
    assert "dividendo_anual=1.80" in out


def test_accion_repr() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0)
    r = repr(a)
    assert r.startswith("Accion(")
    assert "ACME" in r


def test_accion_eq_por_id() -> None:
    a = Accion("ACME", "Acme", "ACME", 0.2, 100.0)
    b = Accion("ACME", "Otra", "OTR", 0.5, 999.0, sector="Energia")
    assert a == b
