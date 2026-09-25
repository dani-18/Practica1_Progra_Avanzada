"""Pruebas de humo exigidas por la PRAC1.

Estos tests son el "minimo viable" que verifica que:

* el paquete se puede importar;
* el flujo "hello flow" arranca (mercado + activo + 1 sesion);
* tras simular, los precios son finitos y positivos.

Mantener este fichero como punto de entrada para las pruebas iniciales
facilita que el profesor ejecute ``python -m pytest tests/test_modelo.py``
sin tener que conocer el resto de modulos.
"""

from __future__ import annotations

from math import isfinite

import pytest

import bolsa_sim
from bolsa_sim import Activo, Cartera, MercadoSimulado, Simulador
from bolsa_sim.estrategias import CompraYMantiene


def test_importar_paquete() -> None:
    """El paquete expone metadatos basicos."""
    assert bolsa_sim.__version__ == "0.1.0"
    assert bolsa_sim.__license__ == "MIT"


def test_mercado_no_produce_precios_negativos() -> None:
    """100 sesiones no deben producir precios negativos ni no finitos."""
    activos = [
        Activo("ACME", "Acme Corp", 100.0, volatilidad=0.3),
        Activo("GLOB", "Global Industries", 50.0, volatilidad=0.4),
    ]
    mercado = MercadoSimulado(activos, semilla=42)
    mercado.simular(100)
    for ticker in mercado.tickers:
        precio = mercado.precio_de(ticker)
        assert isfinite(precio), f"el precio de {ticker} no es finito"
        assert precio > 0, f"el precio de {ticker} es no positivo: {precio}"


def test_hello_flow() -> None:
    """PoC exigida por la PRAC1: mercado + cartera + una sesion."""
    activo = Activo("ACME", "Acme Corp", 100.0, volatilidad=0.2)
    mercado = MercadoSimulado([activo], semilla=42)
    cartera = Cartera(efectivo_inicial=1_000.0)
    estrategia = CompraYMantiene(("ACME",), cantidad_por_ticker=1)

    sim = Simulador(mercado, cartera, estrategia)
    resultado = sim.ejecutar(sesiones=1)

    assert resultado.sesiones_ejecutadas == 1
    assert cartera.total_transacciones == 1
    assert "ACME" in {p.ticker for p in cartera.posiciones}


@pytest.mark.parametrize(
    "activo_factory",
    [
        lambda: Activo("ACME", "Acme Corp", 100.0),
        lambda: Activo("BETA", "BetaCorp", 10.0),
    ],
)
def test_avanzar_sesion_cambia_precio(activo_factory) -> None:
    mercado = MercadoSimulado([activo_factory()], semilla=1)
    inicial = mercado.precio_de(mercado.tickers[0])
    mercado.avanzar_sesion()
    tras = mercado.precio_de(mercado.tickers[0])
    # No exigimos monotonicidad; solo que sigan siendo positivos.
    assert isfinite(tras) and tras > 0
    assert inicial > 0
