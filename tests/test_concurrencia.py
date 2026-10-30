"""Tests de la ejecucion concurrente de escenarios."""

from __future__ import annotations

import pytest

from bolsa_sim.concurrencia import (
    Escenario,
    ResultadoEscenario,
    comparar_estrategias,
    ejecutar_escenario,
    ejecutar_escenarios,
    escenarios_por_defecto,
)
from bolsa_sim.excepciones import DatosInvalidos, EstrategiaDesconocida


def test_escenario_valida() -> None:
    escenario = Escenario("base", semilla=1, sesiones=5)
    assert escenario.nombre == "base"
    with pytest.raises(DatosInvalidos):
        Escenario("")
    with pytest.raises(DatosInvalidos):
        Escenario("x", semilla=True)  # type: ignore[arg-type]
    with pytest.raises(DatosInvalidos):
        Escenario("x", sesiones=0)
    with pytest.raises(DatosInvalidos):
        Escenario("x", sesiones=True)  # type: ignore[arg-type]


def test_ejecutar_escenario() -> None:
    escenario = Escenario("mom", estrategia="momentum", semilla=5, sesiones=10)
    resultado = ejecutar_escenario(escenario)
    assert isinstance(resultado, ResultadoEscenario)
    assert resultado.escenario is escenario
    assert resultado.resultado.sesiones == 10
    datos = resultado.a_dict()
    assert datos["escenario"]["semilla"] == 5
    assert datos["resultado"]["estrategia"] == "momentum"


def test_ejecutar_escenarios_conserva_orden_y_determinismo() -> None:
    escenarios = [
        Escenario("a", estrategia="comprar_mantener", semilla=7, sesiones=8),
        Escenario("b", estrategia="momentum", semilla=7, sesiones=8),
        Escenario("c", estrategia="rebalanceo", semilla=7, sesiones=8),
    ]
    resultados = ejecutar_escenarios(escenarios, max_workers=2)
    assert [r.escenario.nombre for r in resultados] == ["a", "b", "c"]
    otra_vez = ejecutar_escenarios(escenarios, max_workers=2)
    assert [r.resultado.curva for r in resultados] == [r.resultado.curva for r in otra_vez]


def test_ejecutar_escenarios_validacion() -> None:
    with pytest.raises(DatosInvalidos):
        ejecutar_escenarios([])
    escenario = Escenario("x", sesiones=2)
    with pytest.raises(DatosInvalidos):
        ejecutar_escenarios([escenario], max_workers=0)
    with pytest.raises(DatosInvalidos):
        ejecutar_escenarios([escenario], max_workers=True)  # type: ignore[arg-type]


def test_estrategia_desconocida() -> None:
    with pytest.raises(EstrategiaDesconocida):
        ejecutar_escenario(Escenario("x", estrategia="nope", sesiones=2))


def test_escenarios_por_defecto() -> None:
    escenarios = escenarios_por_defecto(semillas=(1, 2), sesiones=3)
    assert len(escenarios) == 6
    assert {e.semilla for e in escenarios} == {1, 2}
    assert all(e.sesiones == 3 for e in escenarios)
    with pytest.raises(DatosInvalidos):
        escenarios_por_defecto(semillas=())


def test_comparar_estrategias() -> None:
    resultados = comparar_estrategias(semilla=4, sesiones=5)
    assert len(resultados) == 3
    assert {r.escenario.estrategia for r in resultados} == {
        "comprar_mantener",
        "momentum",
        "rebalanceo",
    }
