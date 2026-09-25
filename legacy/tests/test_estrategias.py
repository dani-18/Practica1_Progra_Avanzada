"""Tests de las estrategias basicas."""

from __future__ import annotations

import dataclasses

import pytest

from bolsa_sim.activos import Activo
from bolsa_sim.cartera import Cartera
from bolsa_sim.estrategias import AportePeriodico, CompraYMantiene, Orden
from bolsa_sim.mercado import MercadoSimulado


@pytest.fixture
def mercado() -> MercadoSimulado:
    return MercadoSimulado(
        [Activo("ACME", "X", 100.0, volatilidad=0.2), Activo("GLOB", "Y", 50.0, volatilidad=0.2)],
        semilla=3,
    )


def test_compra_y_mantiene_una_vez(mercado: MercadoSimulado) -> None:
    c = Cartera(10_000.0)
    est = CompraYMantiene(("ACME",), cantidad_por_ticker=3)
    ordenes1 = est.generar_orden(c, mercado, 1)
    ordenes2 = est.generar_orden(c, mercado, 2)
    assert len(ordenes1) == 1
    assert ordenes2 == ()


def test_aporte_periodico_segun_cadencia(mercado: MercadoSimulado) -> None:
    c = Cartera(10_000.0)
    est = AportePeriodico("ACME", efectivo_por_sesion=500.0, cadencia=2)
    # sesion 0 => no opera
    assert est.generar_orden(c, mercado, 0) == ()
    # sesion 2 => opera
    ordenes = est.generar_orden(c, mercado, 2)
    assert len(ordenes) == 1
    assert ordenes[0].ticker == "ACME"


def test_orden_inmutable() -> None:
    o = Orden(tipo=type("T", (), {"value": "compra"})(), ticker="ACME", cantidad=1)
    # ``Orden`` es frozen dataclass.
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        o.cantidad = 99
