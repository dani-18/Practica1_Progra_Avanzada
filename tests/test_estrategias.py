"""Tests de las estrategias de inversion y su fabrica."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.estrategias import (
    ESTRATEGIAS,
    ComprarMantener,
    ContextoMercado,
    Decision,
    Momentum,
    Rebalanceo,
    crear_estrategia,
    estrategia_desde_pares,
    estrategias_disponibles,
)
from bolsa_sim.excepciones import (
    DatosInvalidos,
    EstrategiaDesconocida,
    InstrumentoDesconocido,
)
from bolsa_sim.instrumento import InstrumentoBase
from bolsa_sim.mercado import Mercado


def _contexto_tendencias() -> ContextoMercado:
    a = InstrumentoBase("AAA", "AAA", "AAA", 0.0, 100.0)
    b = InstrumentoBase("BBB", "BBB", "BBB", 0.0, 100.0)
    c = InstrumentoBase("CCC", "CCC", "CCC", 0.0, 100.0)
    mercado = Mercado("M", {i.id: i for i in (a, b, c)}, semilla=1)
    for precio in (110.0, 121.0):
        mercado.registrar_precio("AAA", precio)
    for precio in (90.0, 81.0):
        mercado.registrar_precio("BBB", precio)
    for precio in (100.0, 100.0):
        mercado.registrar_precio("CCC", precio)
    cartera = Cartera.desde_estado(
        "Dani",
        efectivo=500.0,
        comision=0.0,
        posiciones={"BBB": 1},
        historial=[],
        capital_inicial=1_000.0,
    )
    return ContextoMercado(mercado=mercado, cartera=cartera, sesion=2)


def test_decision_valida() -> None:
    decision = Decision("ACME", "compra", 2)
    assert decision.cantidad == 2
    assert "compra" in repr(decision)
    with pytest.raises(DatosInvalidos):
        Decision("", "compra", 1)
    with pytest.raises(DatosInvalidos):
        Decision("ACME", "otra", 1)  # type: ignore[arg-type]
    with pytest.raises(DatosInvalidos):
        Decision("ACME", "compra", 0)
    with pytest.raises(DatosInvalidos):
        Decision("ACME", "compra", True)  # type: ignore[arg-type]


def test_contexto_mercado() -> None:
    contexto = _contexto_tendencias()
    assert contexto.precio("AAA") == 121.0
    assert contexto.posicion("BBB") == 1
    assert contexto.momentum("AAA", 2) == pytest.approx(0.21)
    assert contexto.momentum("BBB", 2) == pytest.approx(-0.19)
    assert contexto.peso("BBB") > 0
    assert contexto.valor_total() > 0
    assert contexto.momentum("AAA", 10) is None
    assert contexto.momentum("AAA", 0) is None
    with pytest.raises(InstrumentoDesconocido):
        contexto.precio("NOPE")


def test_comprar_mantener_compra_una_vez() -> None:
    a = InstrumentoBase("AAA", "AAA", "AAA", 0.0, 100.0)
    b = InstrumentoBase("BBB", "BBB", "BBB", 0.0, 100.0)
    c = InstrumentoBase("CCC", "CCC", "CCC", 0.0, 100.0)
    mercado = Mercado("M", {i.id: i for i in (a, b, c)}, semilla=1)
    cartera = Cartera("Dani", efectivo=1_000.0)
    contexto = ContextoMercado(mercado=mercado, cartera=cartera, sesion=0)
    estrategia = ComprarMantener(fraccion=0.9)
    decisiones = estrategia.decidir(contexto)
    assert {d.instrumento_id for d in decisiones} == {"AAA", "BBB", "CCC"}
    contexto.cartera.invertir(contexto.mercado, "AAA", 1, 100.0, "s1")
    assert estrategia.decidir(contexto) == []


def test_comprar_mantener_mercado_vacio() -> None:
    mercado = Mercado("Vacio", {}, semilla=1)
    cartera = Cartera("Dani", efectivo=100.0)
    contexto = ContextoMercado(mercado, cartera, 0)
    assert ComprarMantener().decidir(contexto) == []


def test_comprar_mantener_parametros_invalidos() -> None:
    for fraccion in (0, -0.1, 1.1):
        with pytest.raises(DatosInvalidos):
            ComprarMantener(fraccion=fraccion)
    with pytest.raises(DatosInvalidos):
        ComprarMantener(fraccion=True)  # type: ignore[arg-type]


def test_momentum_vende_perdedores_y_compra_ganadores() -> None:
    contexto = _contexto_tendencias()
    decisiones = Momentum(ventana=2, fraccion=0.5, max_posiciones=1).decidir(contexto)
    ventas = [d for d in decisiones if d.tipo == "venta"]
    compras = [d for d in decisiones if d.tipo == "compra"]
    assert [(d.instrumento_id, d.cantidad) for d in ventas] == [("BBB", 1)]
    assert [d.instrumento_id for d in compras] == ["AAA"]


def test_momentum_sin_datos_o_sin_tendencia() -> None:
    mercado = mercado_demo()
    contexto = ContextoMercado(mercado, cartera_demo(), 0)
    assert Momentum(ventana=3).decidir(contexto) == []
    # Con todos los precios planos no hay impulso positivo.
    a = InstrumentoBase("A", "A", "A", 0.0, 100.0)
    plano = Mercado("P", {"A": a}, semilla=1)
    plano.registrar_precio("A", 100.0)
    plano.registrar_precio("A", 100.0)
    contexto_plano = ContextoMercado(plano, Cartera("D", efectivo=100.0), 2)
    assert Momentum(ventana=2).decidir(contexto_plano) == []


def test_momentum_parametros_invalidos() -> None:
    for kwargs in (
        {"ventana": 0},
        {"ventana": True},
        {"max_posiciones": 0},
        {"max_posiciones": True},
        {"fraccion": 0},
        {"umbral": "x"},
    ):
        with pytest.raises(DatosInvalidos):
            Momentum(**kwargs)  # type: ignore[arg-type]


def test_rebalanceo_compra_y_vende() -> None:
    contexto = _contexto_tendencias()
    contexto.cartera.desinvertir(contexto.mercado, "BBB", 1, 81.0, "s1")
    contexto = ContextoMercado(contexto.mercado, contexto.cartera, 2)
    decisiones = Rebalanceo(banda=0.01).decidir(contexto)
    assert any(d.tipo == "compra" for d in decisiones)

    cartera = Cartera("Dani", efectivo=1_000.0)
    cartera.comprar(contexto.mercado, "AAA", 6, precio=121.0, fecha="s1")
    contexto_skew = ContextoMercado(contexto.mercado, cartera, 2)
    decisiones_venta = Rebalanceo(banda=0.01).decidir(contexto_skew)
    assert any(d.tipo == "venta" and d.instrumento_id == "AAA" for d in decisiones_venta)


def test_rebalanceo_banda_alta_no_opera() -> None:
    contexto = _contexto_tendencias()
    assert Rebalanceo(banda=0.99).decidir(contexto) == []


def test_rebalanceo_pesos_personalizados_y_errores() -> None:
    contexto = _contexto_tendencias()
    estrategia = Rebalanceo(pesos={"AAA": 0.5, "BBB": 0.5})
    decisiones = estrategia.decidir(contexto)
    assert {d.instrumento_id for d in decisiones} <= {"AAA", "BBB"}
    with pytest.raises(DatosInvalidos):
        Rebalanceo(pesos={"AAA": 0.0}).decidir(contexto)
    with pytest.raises(DatosInvalidos):
        Rebalanceo(banda=-0.1)
    with pytest.raises(DatosInvalidos):
        Rebalanceo(banda=1.0)
    with pytest.raises(DatosInvalidos):
        Rebalanceo(banda=True)  # type: ignore[arg-type]
    with pytest.raises(InstrumentoDesconocido):
        Rebalanceo(pesos={"NOPE": 1.0}).decidir(contexto)


def test_rebalanceo_sin_instrumentos() -> None:
    contexto = ContextoMercado(Mercado("V", {}, semilla=1), Cartera("D", 100.0), 0)
    assert Rebalanceo().decidir(contexto) == []


def test_fabrica_de_estrategias() -> None:
    assert set(estrategias_disponibles()) == set(ESTRATEGIAS)
    assert isinstance(crear_estrategia("comprar_mantener"), ComprarMantener)
    assert isinstance(crear_estrategia("MOMENTUM", ventana=3), Momentum)
    assert isinstance(crear_estrategia("rebalanceo", banda=0.02), Rebalanceo)
    with pytest.raises(EstrategiaDesconocida):
        crear_estrategia("nope")
    with pytest.raises(EstrategiaDesconocida):
        crear_estrategia("")
    with pytest.raises(DatosInvalidos):
        crear_estrategia("momentum", parametro_raro=1)
    assert "Momentum" in repr(Momentum())


def test_estrategia_desde_pares() -> None:
    estrategia = estrategia_desde_pares("momentum", ["ventana=10", "fraccion=0.4"])
    assert isinstance(estrategia, Momentum)
    assert estrategia.ventana == 10
    assert estrategia.fraccion == pytest.approx(0.4)
    with pytest.raises(DatosInvalidos):
        estrategia_desde_pares("momentum", ["ventana"])
    with pytest.raises(DatosInvalidos):
        estrategia_desde_pares("momentum", ["=10"])
    with pytest.raises(DatosInvalidos):
        estrategia_desde_pares("momentum", ["ventana=abc"])
