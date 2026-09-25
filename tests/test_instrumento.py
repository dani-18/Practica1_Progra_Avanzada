"""Tests de ``InstrumentoBase``."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from bolsa_sim.instrumento import InstrumentoBase


def test_instrumento_basico() -> None:
    inst = InstrumentoBase(
        id="acme",
        nombre="Acme Corp",
        simbolo="acme",
        volatilidad=0.3,
        precio_base=100.0,
    )
    assert inst.id == "ACME"  # normaliza a mayusculas
    assert inst.simbolo == "ACME"
    assert inst.nombre == "Acme Corp"
    assert inst.precio_base == 100.0


def test_instrumento_property_volatilidad_setter_valida() -> None:
    inst = InstrumentoBase("X", "X", "X", volatilidad=0.1, precio_base=10.0)
    inst.volatilidad = 0.5
    assert inst.volatilidad == 0.5
    with pytest.raises(ValueError):
        inst.volatilidad = -0.1
    with pytest.raises(ValueError):
        inst.volatilidad = 10.0
    with pytest.raises(TypeError):
        inst.volatilidad = "no"  # type: ignore[assignment]


def test_instrumento_property_precio_setter_valida() -> None:
    inst = InstrumentoBase("X", "X", "X", volatilidad=0.1, precio_base=10.0)
    inst.precio_base = 250.0
    assert inst.precio_base == 250.0
    with pytest.raises(ValueError):
        inst.precio_base = 0.0
    with pytest.raises(ValueError):
        inst.precio_base = -1.0


def test_instrumento_aplicar_factor() -> None:
    inst = InstrumentoBase("X", "X", "X", volatilidad=0.2, precio_base=100.0)
    nuevo = inst.aplicar_factor(1.10)
    assert pytest.approx(110.0) == nuevo


def test_instrumento_aplicar_factor_rechaza_factor_invalido() -> None:
    inst = InstrumentoBase("X", "X", "X", volatilidad=0.2, precio_base=100.0)
    with pytest.raises(ValueError):
        inst.aplicar_factor(0.0)


def test_instrumento_mostrar_imprime() -> None:
    inst = InstrumentoBase("ACME", "Acme", "ACME", 0.2, 100.0)
    buf = io.StringIO()
    with redirect_stdout(buf):
        inst.mostrar()
    out = buf.getvalue()
    assert "[InstrumentoBase]" in out
    assert "ACME" in out


def test_instrumento_eq_por_id() -> None:
    a = InstrumentoBase("ACME", "X", "X", 0.1, 1.0)
    b = InstrumentoBase("ACME", "Y", "Z", 0.5, 999.0)
    assert a == b


def test_instrumento_validacion_inicial() -> None:
    with pytest.raises(ValueError):
        InstrumentoBase("", "X", "X", 0.1, 1.0)
    with pytest.raises(ValueError):
        InstrumentoBase("X", "", "X", 0.1, 1.0)
    with pytest.raises(ValueError):
        InstrumentoBase("X", "X", "", 0.1, 1.0)
    with pytest.raises(ValueError):
        InstrumentoBase("X", "X", "X", -0.1, 1.0)
    with pytest.raises(ValueError):
        InstrumentoBase("X", "X", "X", 0.1, 0.0)
