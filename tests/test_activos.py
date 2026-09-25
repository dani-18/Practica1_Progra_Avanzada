"""Tests unitarios de ``bolsa_sim.activos``."""

from __future__ import annotations

import dataclasses

import pytest

from bolsa_sim.activos import (
    Activo,
    BarraDiaria,
    Posicion,
    TipoActivo,
    TipoOperacion,
    Transaccion,
)


# -------- Activo ------------------------------------------------------------
def test_activo_crea_atributos_basicos() -> None:
    act = Activo("ACME", "Acme Corp", 100.0)
    assert act.ticker == "ACME"
    assert act.nombre == "Acme Corp"
    assert act.precio == 100.0
    assert act.volatilidad == 0.2  # default


def test_activo_normaliza_ticker() -> None:
    act = Activo("  acme  ", "X", 1.0)
    assert act.ticker == "ACME"


@pytest.mark.parametrize("ticker", ["", "  ", "TICKER DEMASIADO_LARGO"])
def test_activo_rechaza_tickers_invalidos(ticker: str) -> None:
    with pytest.raises(ValueError):
        Activo(ticker, "X", 1.0)


@pytest.mark.parametrize("precio", [-1.0, 0.0, float("nan"), "no"])
def test_activo_rechaza_precios_invalidos(precio) -> None:
    with pytest.raises((ValueError, TypeError)):
        Activo("ACME", "X", precio)  # type: ignore[arg-type]


def test_activo_setter_valida() -> None:
    act = Activo("ACME", "X", 10.0)
    act.precio = 25.0
    assert act.precio == 25.0
    with pytest.raises(ValueError):
        act.precio = -1.0


def test_activo_aplicar_factor() -> None:
    act = Activo("ACME", "X", 100.0)
    nuevo = act.aplicar_factor(1.10)
    assert abs(nuevo - 110.0) < 1e-9
    with pytest.raises(ValueError):
        act.aplicar_factor(-1.0)


def test_activo_eq_y_hash_por_ticker() -> None:
    a = Activo("ACME", "X", 10.0)
    b = Activo("ACME", "Y distinto", 1.0)  # mismo ticker, distintos atributos
    c = Activo("GLOB", "X", 10.0)
    assert a == b
    assert hash(a) == hash(b)
    assert a != c
    # Usable como clave de un dict (demostracion de que es hashable).
    d = {a: "ok"}
    assert d[b] == "ok"


def test_activo_repr_no_ambiguo() -> None:
    s = repr(Activo("ACME", "X", 100.0))
    assert "ACME" in s and "100" in s


# -------- Posicion ----------------------------------------------------------
def test_posicion_cantidad_negativa() -> None:
    act = Activo("ACME", "X", 1.0)
    with pytest.raises(ValueError):
        Posicion(act, cantidad=-1)
    # Cantidad tipo invalido
    with pytest.raises(TypeError):
        Posicion(act, cantidad=1.5)  # type: ignore[arg-type]


def test_posicion_valor_con_precio() -> None:
    act = Activo("ACME", "X", 10.0)
    pos = Posicion(act, cantidad=3)
    assert pos.valor() == 30.0
    assert pos.valor(precio_referencia=12.5) == 37.5


# -------- Transaccion -------------------------------------------------------
def test_transaccion_inmutable() -> None:
    t = Transaccion(
        sesion=1,
        tipo=TipoOperacion.COMPRA,
        ticker="ACME",
        cantidad=2,
        precio_unitario=100.0,
        comision=1.0,
    )
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        t.cantidad = 99  # frozen dataclass


def test_transaccion_validacion() -> None:
    with pytest.raises(ValueError):
        Transaccion(
            sesion=-1, tipo=TipoOperacion.COMPRA, ticker="ACME", cantidad=1, precio_unitario=1.0
        )
    with pytest.raises(ValueError):
        Transaccion(
            sesion=1, tipo=TipoOperacion.COMPRA, ticker="ACME", cantidad=0, precio_unitario=1.0
        )
    with pytest.raises(ValueError):
        Transaccion(
            sesion=1, tipo=TipoOperacion.COMPRA, ticker="ACME", cantidad=1, precio_unitario=0.0
        )


def test_transaccion_importes() -> None:
    t = Transaccion(
        sesion=1,
        tipo=TipoOperacion.COMPRA,
        ticker="ACME",
        cantidad=10,
        precio_unitario=2.0,
        comision=0.5,
    )
    assert t.importe_bruto == pytest.approx(20.0)
    assert t.importe_neto == pytest.approx(20.5)


# -------- BarraDiaria -------------------------------------------------------
def test_barra_diaria_inmutable_y_hashable() -> None:
    b = BarraDiaria(sesion=1, apertura=1.0, cierre=2.0, maximo=2.5, minimo=0.5, volumen=100)
    with pytest.raises(AttributeError):
        b.cierre = 99  # NamedTuple: inmutable
    # Usable como clave (hashable, inmutable).
    d = {b: "ok"}
    assert d[b] == "ok"


# -------- TipoActivo / TipoOperacion ---------------------------------------
def test_enums_str() -> None:
    assert str(TipoActivo.ACCION) == "accion"
    assert str(TipoOperacion.COMPRA) == "compra"
