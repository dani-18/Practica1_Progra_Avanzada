"""Tests unitarios de ``bolsa_sim.cartera``."""

from __future__ import annotations

import pytest

from bolsa_sim.activos import Activo
from bolsa_sim.cartera import Cartera
from bolsa_sim.mercado import MercadoSimulado


@pytest.fixture
def mercado() -> MercadoSimulado:
    activos = [
        Activo("ACME", "Acme Corp", 100.0),
        Activo("GLOB", "Global", 50.0),
    ]
    return MercadoSimulado(activos, semilla=7)


def test_cartera_crea_con_efectivo() -> None:
    c = Cartera(efectivo_inicial=500.0)
    assert c.efectivo == 500.0
    assert c.posiciones == ()
    assert c.transacciones == ()


@pytest.mark.parametrize("valor", [-1.0, float("nan"), "x"])
def test_cartera_rechaza_efectivo_invalido(valor) -> None:
    with pytest.raises((ValueError, TypeError)):
        Cartera(efectivo_inicial=valor)  # type: ignore[arg-type]


def test_cartera_compra_y_vender_basico(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=10_000.0)
    ok = c.comprar(mercado, "ACME", cantidad=5)
    assert ok is True
    # Comision por defecto = 1.0 => descuenta 5*100 + 1
    assert c.efectivo == pytest.approx(10_000 - 501.0)
    pos = c.posiciones[0]
    assert pos.ticker == "ACME" and pos.cantidad == 5

    # Venta parcial
    assert c.vender(mercado, "ACME", cantidad=2) is True
    pos = c.posiciones[0]
    assert pos.cantidad == 3


def test_cartera_fondos_insuficientes_no_falla(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=100.0)
    # 5 * 100 + 1 comision = 501: no llega.
    assert c.comprar(mercado, "ACME", cantidad=5) is False
    assert c.efectivo == 100.0
    assert c.posiciones == ()


def test_cartera_vender_sin_posicion(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=1000.0)
    assert c.vender(mercado, "GLOB", cantidad=1) is False


def test_cartera_cantidad_invalida(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=1000.0)
    with pytest.raises(ValueError):
        c.comprar(mercado, "ACME", cantidad=0)
    with pytest.raises(TypeError):
        c.comprar(mercado, "ACME", cantidad=1.5)  # type: ignore[arg-type]


def test_cartera_valor_total(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=10_000.0)
    c.comprar(mercado, "ACME", cantidad=5)
    c.comprar(mercado, "GLOB", cantidad=10)
    esperado = c.efectivo + 5 * 100.0 + 10 * 50.0
    assert c.valor_total(mercado) == pytest.approx(esperado)


def test_cartera_inversion_vs_valor(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=10_000.0)
    assert c.inversion() == 0.0
    c.comprar(mercado, "ACME", cantidad=3)
    assert c.inversion() == pytest.approx(3 * 100.0)
    # Valor total: efectivo + posiciones
    assert c.valor_total(mercado) == pytest.approx(c.efectivo + c.inversion())


def test_cartera_transacciones_crecen(mercado: MercadoSimulado) -> None:
    c = Cartera(efectivo_inicial=10_000.0)
    assert c.total_transacciones == 0
    c.comprar(mercado, "ACME", cantidad=2)
    c.vender(mercado, "ACME", cantidad=1)
    assert c.total_transacciones == 2
    assert len(c.transacciones) == 2
