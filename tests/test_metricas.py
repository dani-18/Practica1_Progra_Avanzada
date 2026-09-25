"""Tests minimos de las metricas (evolutivos en PRAC4)."""

from __future__ import annotations

import math

import pytest

from bolsa_sim.metricas import drawdown_maximo, rentabilidad_total


def test_rentabilidad_total_porcentaje() -> None:
    assert rentabilidad_total(100.0, 150.0) == pytest.approx(50.0)
    assert rentabilidad_total(100.0, 50.0) == pytest.approx(-50.0)
    assert abs(rentabilidad_total(100.0, 100.0)) < 1e-9


def test_rentabilidad_total_en_ratio() -> None:
    assert rentabilidad_total(100.0, 110.0, como_porcentaje=False) == pytest.approx(0.1)


def test_rentabilidad_total_invalido() -> None:
    with pytest.raises(ValueError):
        rentabilidad_total(float("nan"), 1.0)
    with pytest.raises(ValueError):
        rentabilidad_total(1.0, float("inf"))


def test_drawdown_maximo_serie_simple() -> None:
    # Pico en 100, valle en 60 => drawdown = -0.4
    assert drawdown_maximo([100.0, 90.0, 60.0, 70.0, 100.0]) == pytest.approx(-0.4)


def test_drawdown_maximo_serie_plana() -> None:
    assert drawdown_maximo([10.0, 10.0, 10.0]) == 0.0


def test_drawdown_maximo_serie_vacia() -> None:
    assert drawdown_maximo([]) == 0.0


def test_drawdown_maximo_ignora_no_finitos() -> None:
    assert math.isfinite(drawdown_maximo([100.0, float("nan"), 80.0]))
