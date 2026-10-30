"""Tests adicionales de ``Mercado``: historial, shocks y deriva."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.excepciones import (
    DatosInvalidos,
    InstrumentoDesconocido,
    InstrumentoDuplicado,
)
from bolsa_sim.instrumento import InstrumentoBase
from bolsa_sim.mercado import Mercado


def _mercado(**kwargs) -> Mercado:
    a = InstrumentoBase("ACME", "Acme", "ACME", volatilidad=0.2, precio_base=100.0)
    b = InstrumentoBase("GLOB", "Glob", "GLOB", volatilidad=0.1, precio_base=50.0)
    return Mercado("Continuo", {a.id: a, b.id: b}, semilla=42, **kwargs)


def test_historial_inicial_y_tras_sesiones() -> None:
    mercado = _mercado()
    assert mercado.historial_precios("ACME") == (100.0,)
    mercado.avanzar_sesion(10)
    assert len(mercado.historial_precios("ACME")) == 2
    mercado.avanzar_sesiones(2, volumen=5)
    assert len(mercado.historial_precios("ACME")) == 4
    assert mercado.sesion == 3
    assert mercado.volumen_total == 20
    assert set(mercado.series) == {"ACME", "GLOB"}
    assert mercado.precios_actuales()["ACME"] == mercado.precio_de("ACME")


def test_rendimientos() -> None:
    mercado = _mercado()
    assert mercado.rendimiento_sesion("ACME") is None
    mercado.avanzar_sesion()
    assert mercado.rendimiento_sesion("ACME") is not None
    assert mercado.rendimiento_desde_inicio("ACME") == pytest.approx(
        mercado.precio_de("ACME") / 100.0 - 1
    )


def test_deriva_positiva_con_volatilidad_cero() -> None:
    a = InstrumentoBase("X", "X", "X", volatilidad=0.0, precio_base=100.0)
    mercado = Mercado("M", {"X": a}, semilla=1, deriva=0.01)
    mercado.avanzar_sesiones(10)
    assert mercado.precio_de("X") == pytest.approx(100.0 * 1.01**10)


def test_deriva_invalida() -> None:
    with pytest.raises(DatosInvalidos):
        _mercado(deriva=2.0)
    with pytest.raises(DatosInvalidos):
        _mercado(deriva=float("nan"))
    with pytest.raises(TypeError):
        _mercado(deriva="0.1")  # type: ignore[arg-type]


def test_shock_global() -> None:
    mercado = _mercado()
    nuevos = mercado.aplicar_shock(-0.10)
    assert nuevos["ACME"] == pytest.approx(90.0)
    assert nuevos["GLOB"] == pytest.approx(45.0)
    assert len(mercado.historial_precios("ACME")) == 2
    assert mercado.sesion == 0
    assert mercado.deriva == 0.0


def test_shock_invalido() -> None:
    mercado = _mercado()
    with pytest.raises(DatosInvalidos):
        mercado.aplicar_shock(-1.0)
    with pytest.raises(DatosInvalidos):
        mercado.aplicar_shock(float("nan"))
    with pytest.raises(TypeError):
        mercado.aplicar_shock("x")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        mercado.aplicar_shock(True)  # type: ignore[arg-type]


def test_registrar_precio() -> None:
    mercado = _mercado()
    assert mercado.registrar_precio("ACME", 105.0) == 105.0
    assert mercado.precio_de("ACME") == 105.0
    assert mercado.historial_precios("ACME") == (100.0, 105.0)
    with pytest.raises(InstrumentoDesconocido):
        mercado.registrar_precio("NOPE", 1.0)
    with pytest.raises(DatosInvalidos):
        mercado.registrar_precio("ACME", 0.0)
    with pytest.raises(TypeError):
        mercado.registrar_precio("ACME", "1")  # type: ignore[arg-type]


def test_avanzar_sesiones_invalido() -> None:
    mercado = _mercado()
    with pytest.raises(DatosInvalidos):
        mercado.avanzar_sesiones(0)
    with pytest.raises(DatosInvalidos):
        mercado.avanzar_sesiones(True)  # type: ignore[arg-type]


def test_registrar_duplicado_y_desconocido() -> None:
    mercado = _mercado()
    with pytest.raises(InstrumentoDuplicado):
        mercado.registrar(InstrumentoBase("ACME", "Otro", "A", 0.1, 1.0))
    with pytest.raises(InstrumentoDesconocido):
        mercado.precio_de("NOPE")
    with pytest.raises(InstrumentoDesconocido):
        mercado.historial_precios("NOPE")


def test_repositorio_inyectado_guarda_sesion() -> None:
    llamadas: list[tuple] = []

    class Repo:
        def guardar_sesion(self, nombre, numero, volumen, precios) -> None:
            llamadas.append((nombre, numero, volumen, dict(precios)))

    mercado = _mercado(repositorio=Repo())
    mercado.avanzar_sesion(7)
    assert len(llamadas) == 1
    assert llamadas[0][0] == "Continuo"
    assert llamadas[0][1] == 1
    assert llamadas[0][2] == 7
    assert set(llamadas[0][3]) == {"ACME", "GLOB"}


def test_repositorio_setter() -> None:
    mercado = _mercado()
    repo = object()
    mercado.repositorio = repo
    assert mercado.repositorio is repo
    mercado.repositorio = None
    assert mercado.repositorio is None


def test_restaurar_estado_con_historial_y_sesiones() -> None:
    mercado = _mercado()
    sesiones = [
        {"numero": 1, "volumen": 10, "precios": {"ACME": 101.0, "GLOB": 51.0}},
        {"numero": 2, "volumen": 20, "precios": {"ACME": 102.0, "GLOB": 52.0}},
    ]
    mercado.restaurar_estado(
        2,
        30,
        {"ACME": 102.0, "GLOB": 52.0},
        series={"ACME": [100.0, 101.0, 102.0]},
        sesiones=sesiones,
    )
    assert mercado.sesion == 2
    assert mercado.volumen_total == 30
    assert mercado.historial_precios("ACME") == (100.0, 101.0, 102.0)
    assert mercado.sesiones[1]["numero"] == 2
    assert mercado.sesiones[1]["precios"]["GLOB"] == 52.0


def test_sesiones_son_copias_inmutables() -> None:
    mercado = _mercado()
    mercado.avanzar_sesion()
    snapshots = mercado.sesiones
    snapshots[0]["precios"]["ACME"] = 1.0
    assert mercado.precios_actuales()["ACME"] != 1.0


def test_mostrar_incluye_deriva(capsys) -> None:
    _mercado(deriva=0.001).mostrar()
    salida = capsys.readouterr().out
    assert "deriva=" in salida
    assert "Continuo" in salida


def test_repr() -> None:
    assert "Mercado(" in repr(_mercado())


def test_liquidar_sin_posiciones() -> None:
    mercado = _mercado()
    cartera = Cartera("Dani", efectivo=100.0)
    assert mercado.liquidar(cartera) == 0.0
