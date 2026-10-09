"""Tests de ``ETF`` (subclase de ``InstrumentoBase``)."""

from __future__ import annotations

import pytest

from bolsa_sim.etf import ETF
from bolsa_sim.instrumento import InstrumentoBase


def test_etf_crea_con_defaults() -> None:
    e = ETF("spx", "ETF S&P 500", "spx", volatilidad=0.15, precio_base=400.0)
    assert e.id == "SPX"
    assert e.tipo == "etf"
    assert e.indice == "General"
    assert e.comision_gestion == 0.0


def test_etf_es_instrumento_base() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0)
    assert isinstance(e, InstrumentoBase)


def test_etf_hereda_validacion_de_la_base() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0)
    with pytest.raises(ValueError):
        e.volatilidad = -1.0


def test_etf_indice_valida() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0)
    e.indice = "  S&P 500  "
    assert e.indice == "S&P 500"
    with pytest.raises(ValueError):
        e.indice = ""


def test_etf_comision_valida() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0)
    e.comision_gestion = 0.002
    assert e.comision_gestion == pytest.approx(0.002)
    with pytest.raises(ValueError):
        e.comision_gestion = -0.001
    with pytest.raises(TypeError):
        e.comision_gestion = "no"  # type: ignore[assignment]


def test_etf_hereda_flujo_anual_cero() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0)
    assert e.flujo_anual() == 0.0


def test_etf_coste_anual() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0, comision_gestion=0.005)
    assert e.coste_anual(10_000.0) == pytest.approx(50.0)
    with pytest.raises(TypeError):
        e.coste_anual("no")  # type: ignore[arg-type]


def test_etf_mostrar(capsys) -> None:
    e = ETF("SPX", "ETF S&P 500", "SPX", 0.15, 400.0, indice="S&P 500")
    e.mostrar()
    out = capsys.readouterr().out
    assert "[ETF]" in out
    assert "S&P 500" in out


def test_etf_repr() -> None:
    e = ETF("SPX", "ETF", "SPX", 0.15, 400.0)
    assert repr(e).startswith("ETF(")
