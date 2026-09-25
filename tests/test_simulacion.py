"""Smoke test de ``Simulador`` (mini-integracion para PRAC1)."""

from __future__ import annotations

import dataclasses

import pytest

from bolsa_sim.activos import Activo
from bolsa_sim.cartera import Cartera
from bolsa_sim.estrategias import AportePeriodico, CompraYMantiene
from bolsa_sim.mercado import MercadoSimulado
from bolsa_sim.simulacion import ResultadoSimulacion, Simulador


@pytest.fixture
def mercado_basico() -> MercadoSimulado:
    activos = [
        Activo("ACME", "X", 100.0, volatilidad=0.3),
        Activo("GLOB", "Y", 50.0, volatilidad=0.4),
    ]
    return MercadoSimulado(activos, semilla=11)


def test_simulador_devuelve_resultado(mercado_basico: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=10_000.0)
    estrategia = CompraYMantiene(tuple(mercado_basico.tickers), cantidad_por_ticker=2)
    sim = Simulador(mercado_basico, c, estrategia)
    r = sim.ejecutar(sesiones=5)
    assert isinstance(r, ResultadoSimulacion)
    assert r.sesiones_ejecutadas == 5
    assert r.operaciones_ejecutadas >= 1


def test_simulador_con_dca(mercado_basico: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=2_000.0)
    estrategia = AportePeriodico("ACME", efectivo_por_sesion=100.0, cadencia=3)
    sim = Simulador(mercado_basico, c, estrategia)
    r = sim.ejecutar(sesiones=7)
    # Al menos una compra (cadencia 3 -> sesiones 3 y 6 plausibles).
    assert r.operaciones_ejecutadas >= 1
    assert c.posiciones  # hay al menos una posicion


def test_resultado_es_inmutable() -> None:
    r = ResultadoSimulacion(
        sesiones_ejecutadas=0,
        efectivo_inicial=1000.0,
        efectivo_final=1000.0,
        valor_inicial=1000.0,
        valor_final=1000.0,
        operaciones_ejecutadas=0,
    )
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        r.sesiones_ejecutadas = 99  # frozen dataclass
