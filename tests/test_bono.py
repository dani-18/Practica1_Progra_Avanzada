"""Tests de ``Bono`` (subclase de ``InstrumentoBase``)."""

from __future__ import annotations

import pytest

from bolsa_sim.bono import Bono
from bolsa_sim.instrumento import InstrumentoBase


def test_bono_crea_con_defaults() -> None:
    b = Bono("b10", "Bono 10 anos", "b10", volatilidad=0.05, precio_base=100.0)
    assert b.id == "B10"
    assert b.tipo == "bono"
    assert b.cupon_anual == pytest.approx(0.04)
    assert b.valor_nominal == pytest.approx(1_000.0)
    assert b.vencimiento == 10


def test_bono_es_instrumento_base() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0)
    assert isinstance(b, InstrumentoBase)


def test_bono_hereda_validacion_de_la_base() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0)
    with pytest.raises(ValueError):
        b.precio_base = 0.0


def test_bono_cupon_valida() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0)
    b.cupon_anual = 0.07
    assert b.cupon_anual == pytest.approx(0.07)
    with pytest.raises(ValueError):
        b.cupon_anual = -0.01
    with pytest.raises(ValueError):
        b.cupon_anual = 1.5
    with pytest.raises(TypeError):
        b.cupon_anual = "no"  # type: ignore[assignment]


def test_bono_valor_nominal_valida() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0)
    with pytest.raises(ValueError):
        b.valor_nominal = 0.0
    with pytest.raises(TypeError):
        b.valor_nominal = "no"  # type: ignore[assignment]


def test_bono_vencimiento_valida() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0)
    b.vencimiento = 30
    assert b.vencimiento == 30
    with pytest.raises(ValueError):
        b.vencimiento = 0
    with pytest.raises(ValueError):
        b.vencimiento = 1.5  # type: ignore[assignment]


def test_bono_flujo_y_rendimiento() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0, cupon_anual=0.05, valor_nominal=1_000.0)
    assert b.cupon_anual_eur() == pytest.approx(50.0)
    assert b.flujo_anual() == pytest.approx(50.0)
    assert b.rendimiento_actual(1_000.0) == pytest.approx(0.05)
    with pytest.raises(ValueError):
        b.rendimiento_actual(0.0)


def test_bono_mostrar(capsys) -> None:
    b = Bono("B10", "Bono 10 anos", "B10", 0.05, 100.0)
    b.mostrar()
    out = capsys.readouterr().out
    assert "[Bono]" in out
    assert "cupon_anual" in out
    assert "vencimiento=10a" in out


def test_bono_repr() -> None:
    b = Bono("B10", "Bono", "B10", 0.05, 100.0)
    assert repr(b).startswith("Bono(")
