"""Tests unitarios de ``bolsa_sim.mercado``."""

from __future__ import annotations

import pytest

from bolsa_sim.activos import Activo
from bolsa_sim.mercado import MercadoSimulado


def test_mercado_rechaza_tickers_duplicados() -> None:
    a = Activo("ACME", "X", 1.0)
    b = Activo("ACME", "Y", 2.0)
    with pytest.raises(ValueError):
        MercadoSimulado([a, b])


def test_mercado_rechaza_otros_objetos() -> None:
    with pytest.raises(TypeError):
        MercadoSimulado(["no_es_un_activo"])  # type: ignore[list-item]


def test_mercado_avanzar_sesion_devuelve_dict() -> None:
    a = Activo("ACME", "X", 100.0)
    m = MercadoSimulado([a], semilla=1)
    m.avanzar_sesion()  # poblar la barra
    cambios = m.avanzar_sesion()
    assert "ACME" in cambios
    assert cambios["ACME"] > 0


def test_mercado_historial_es_tupla_inmutable() -> None:
    a = Activo("ACME", "X", 100.0)
    m = MercadoSimulado([a], semilla=1)
    m.simular(3)
    hist = m.historial_de("ACME")
    assert isinstance(hist, tuple)
    assert len(hist) == 3
    # Las NamedTuple no admiten setattr.
    with pytest.raises(AttributeError):
        hist[0].cierre = 0.0


def test_mercado_sesiones_invalidas() -> None:
    a = Activo("ACME", "X", 100.0)
    m = MercadoSimulado([a], semilla=1)
    with pytest.raises(ValueError):
        m.simular(-1)
    with pytest.raises(TypeError):
        m.simular(1.5)  # type: ignore[arg-type]


def test_mercado_semilla_reproducible() -> None:
    a1 = Activo("ACME", "X", 100.0)
    a2 = Activo("ACME", "X", 100.0)
    m1 = MercadoSimulado([a1], semilla=123)
    m2 = MercadoSimulado([a2], semilla=123)
    m1.simular(20)
    m2.simular(20)
    assert m1.precio_de("ACME") == pytest.approx(m2.precio_de("ACME"))


def test_mercado_no_puede_registrar_duplicado() -> None:
    a = Activo("ACME", "X", 1.0)
    with pytest.raises(ValueError):
        MercadoSimulado([a, Activo("ACME", "X2", 2.0)])


def test_mercado_simular_sesiones_actualiza_sesion_actual() -> None:
    a = Activo("ACME", "X", 100.0)
    m = MercadoSimulado([a], semilla=1)
    assert m.sesion_actual == 0
    m.simular(10)
    assert m.sesion_actual == 10
