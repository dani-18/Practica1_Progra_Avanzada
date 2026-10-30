"""Tests de las metricas financieras."""

from __future__ import annotations

import math

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.excepciones import DatosInvalidos
from bolsa_sim.metricas import (
    MetricasInversion,
    calcular_metricas,
    max_drawdown,
    metricas_cartera,
    ratio_sharpe,
    ratio_sortino,
    rentabilidad_anualizada,
    rentabilidad_total,
    rentabilidades,
    volatilidad_anualizada,
)

SERIE = [100.0, 110.0, 105.0, 120.0]


def test_rentabilidades() -> None:
    retornos = rentabilidades(SERIE)
    assert len(retornos) == 3
    assert retornos[0] == pytest.approx(0.10)
    assert retornos[1] == pytest.approx(-0.0454545, rel=1e-5)
    assert rentabilidades([100.0]) == []


def test_rentabilidad_total_y_anualizada() -> None:
    assert rentabilidad_total(SERIE) == pytest.approx(0.20)
    assert rentabilidad_total([100.0]) == 0.0
    anual = rentabilidad_anualizada(SERIE, sesiones_por_anio=252)
    assert anual == pytest.approx(1.2 ** (252 / 3) - 1)
    assert rentabilidad_anualizada([100.0]) == 0.0


def test_volatilidad_anualizada() -> None:
    vol = volatilidad_anualizada(SERIE)
    assert vol > 0
    assert volatilidad_anualizada([100.0]) == 0.0
    assert volatilidad_anualizada([100.0, 101.0]) == 0.0


def test_max_drawdown() -> None:
    # 110 -> 105 es una caida del 4.545 %.
    assert max_drawdown(SERIE) == pytest.approx(1 - 105 / 110)
    assert max_drawdown([100.0, 110.0, 120.0]) == 0.0
    assert max_drawdown([100.0]) == 0.0


def test_sharpe_y_sortino() -> None:
    sharpe = ratio_sharpe(SERIE, tasa_libre_anual=0.02)
    sortino = ratio_sortino(SERIE, tasa_libre_anual=0.02)
    assert math.isfinite(sharpe)
    assert math.isfinite(sortino)
    assert ratio_sharpe([100.0, 100.0, 100.0]) == 0.0
    assert ratio_sortino([100.0, 100.0, 100.0]) == 0.0
    assert ratio_sharpe([100.0]) == 0.0
    assert ratio_sortino([100.0]) == 0.0


def test_calcular_metricas_y_formato() -> None:
    metricas = calcular_metricas(SERIE)
    assert isinstance(metricas, MetricasInversion)
    assert metricas.valor_inicial == 100.0
    assert metricas.valor_final == 120.0
    assert metricas.num_periodos == 3
    datos = metricas.a_dict()
    assert datos["rentabilidad_total"] == pytest.approx(0.20)
    texto = str(metricas)
    assert "rentabilidad" in texto
    assert "sharpe" in texto


@pytest.mark.parametrize(
    "serie",
    [[], [100.0, 0.0], [100.0, -1.0], [100.0, float("nan")], [100.0, float("inf")]],
)
def test_series_invalidas(serie) -> None:
    with pytest.raises(DatosInvalidos):
        rentabilidades(serie)


def test_tipo_de_serie_invalido() -> None:
    with pytest.raises(DatosInvalidos):
        rentabilidad_total("100,110")  # type: ignore[arg-type]


def test_metricas_cartera_con_curva() -> None:
    cartera = Cartera("Dani", efectivo=1_000.0)
    mercado = mercado_demo(deriva=0.0)
    cartera.anotar_valor(1_000.0)
    cartera.anotar_valor(1_100.0)
    cartera.anotar_valor(1_050.0)
    metricas = metricas_cartera(cartera, mercado)
    assert metricas.valor_inicial == 1_000.0
    assert metricas.valor_final == 1_050.0
    assert metricas.rentabilidad_total == pytest.approx(0.05)


def test_metricas_cartera_sin_curva_usa_capital_y_valor_actual() -> None:
    mercado = mercado_demo()
    cartera = cartera_demo(efectivo=1_000.0)
    cartera.invertir(mercado, "ACME", 2, mercado.precio_de("ACME"), "s0000")
    metricas = metricas_cartera(cartera, mercado)
    assert metricas.valor_inicial == pytest.approx(1_000.0)
    assert metricas.valor_final == pytest.approx(cartera.valor_total(mercado))
    assert metricas.num_periodos == 1
