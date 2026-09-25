"""Tests de ``Operacion`` (inmutable)."""

from __future__ import annotations

import dataclasses

import pytest

from bolsa_sim.operacion import Operacion


def test_operacion_crea() -> None:
    o = Operacion(
        fecha="2026-09-25 10:00",
        instrumento_id="ACME",
        cantidad=2,
        precio_ejecucion=12.5,
        tipo="compra",
    )
    assert o.importe_bruto == 25.0
    assert o.signo == 1


def test_operacion_inmutable() -> None:
    o = Operacion("2026-09-25 10:00", "ACME", 2, 12.5, "compra")
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        o.cantidad = 9  # type: ignore[misc]


def test_operacion_validaciones() -> None:
    with pytest.raises(ValueError):
        Operacion(fecha="", instrumento_id="X", cantidad=1, precio_ejecucion=1.0, tipo="compra")
    with pytest.raises(ValueError):
        Operacion(fecha="2026", instrumento_id="", cantidad=1, precio_ejecucion=1.0, tipo="compra")
    with pytest.raises(ValueError):
        Operacion(
            fecha="2026", instrumento_id="X", cantidad=0, precio_ejecucion=1.0, tipo="compra"
        )
    with pytest.raises(ValueError):
        Operacion(
            fecha="2026", instrumento_id="X", cantidad=1, precio_ejecucion=0.0, tipo="compra"
        )
    with pytest.raises(ValueError):
        Operacion(fecha="2026", instrumento_id="X", cantidad=1, precio_ejecucion=1.0, tipo="otro")


def test_operacion_signo_y_mostrar(capsys) -> None:
    o = Operacion("2026-09-25 10:00", "ACME", 3, 12.0, "venta")
    assert o.signo == -1
    o.mostrar()
    out = capsys.readouterr().out
    assert "[Operacion]" in out
    assert "VENTA" in out
