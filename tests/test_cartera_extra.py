"""Tests adicionales de ``Cartera``: API estricta, curva y persistencia."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.excepciones import (
    DatosInvalidos,
    FondosInsuficientes,
    InstrumentoDesconocido,
    OperacionInvalida,
    PosicionInsuficiente,
)
from bolsa_sim.instrumento import InstrumentoBase
from bolsa_sim.mercado import Mercado
from bolsa_sim.operacion import Operacion


@pytest.fixture
def mercado() -> Mercado:
    a = InstrumentoBase("ACME", "Acme", "ACME", 0.2, 100.0)
    b = InstrumentoBase("GLOB", "Glob", "GLOB", 0.1, 50.0)
    return Mercado("M", {a.id: a, b.id: b}, semilla=1)


def test_compra_y_venta_estrictas(mercado: Mercado) -> None:
    cartera = Cartera("Dani", efectivo=1_000.0, comision=1.0)
    op = cartera.comprar(mercado, "acme", 2, fecha="s1")
    assert op.tipo == "compra"
    assert op.instrumento_id == "ACME"
    assert cartera.posicion("ACME") == 2
    venta = cartera.vender(mercado, "acme", 1, fecha="s2")
    assert venta.tipo == "venta"
    assert cartera.posicion("ACME") == 1


def test_compra_sin_fondos_lanza_excepcion(mercado: Mercado) -> None:
    cartera = Cartera("Dani", efectivo=10.0, comision=1.0)
    with pytest.raises(FondosInsuficientes):
        cartera.comprar(mercado, "ACME", 1)


def test_venta_sin_posicion_lanza_excepcion(mercado: Mercado) -> None:
    cartera = Cartera("Dani", efectivo=1_000.0)
    with pytest.raises(PosicionInsuficiente):
        cartera.vender(mercado, "ACME", 1, precio=100.0)


def test_errores_de_validacion(mercado: Mercado) -> None:
    cartera = Cartera("Dani", efectivo=1_000.0)
    with pytest.raises(InstrumentoDesconocido):
        cartera.invertir(mercado, "NOPE", 1, 10.0, "s1")
    with pytest.raises(OperacionInvalida):
        cartera.invertir(mercado, "ACME", True, 10.0, "s1")  # type: ignore[arg-type]
    with pytest.raises(DatosInvalidos):
        cartera.invertir(mercado, "ACME", 1, 0.0, "s1")
    with pytest.raises(DatosInvalidos):
        cartera.invertir(mercado, "ACME", 1, float("nan"), "s1")
    with pytest.raises(DatosInvalidos):
        cartera.invertir(mercado, "ACME", 1, "10", "s1")  # type: ignore[arg-type]


def test_valor_invertido_y_resumen(mercado: Mercado) -> None:
    cartera = Cartera("Dani", efectivo=1_000.0, comision=0.0)
    cartera.comprar(mercado, "ACME", 2, fecha="s1")
    mercado.avanzar_sesion()
    resumen = cartera.resumen(mercado)
    assert resumen["propietario"] == "Dani"
    assert resumen["posiciones"] == 1
    assert resumen["valor_invertido"] == pytest.approx(2 * mercado.precio_de("ACME"))
    assert resumen["valor_total"] == pytest.approx(cartera.valor_total(mercado))
    assert cartera.valor_invertido(mercado) > 0


def test_curva_de_valor(mercado: Mercado) -> None:
    cartera = Cartera("Dani", efectivo=500.0)
    assert cartera.capital_inicial == 500.0
    assert cartera.curva_valor == (500.0,)
    assert cartera.anotar_valor(510.0) == 510.0
    valor = cartera.anotar_valor(mercado=mercado)
    assert valor == 500.0
    assert cartera.curva_valor == (500.0, 510.0, 500.0)
    with pytest.raises(DatosInvalidos):
        cartera.anotar_valor(0.0)
    with pytest.raises(DatosInvalidos):
        cartera.anotar_valor()
    with pytest.raises(DatosInvalidos):
        cartera.anotar_valor(float("nan"))


def test_desde_estado_reconstruye_todo() -> None:
    historial = [
        Operacion("s1", "ACME", 2, 100.0, "compra"),
        Operacion("s2", "ACME", 1, 110.0, "venta"),
    ]
    cartera = Cartera.desde_estado(
        "Dani",
        efectivo=800.0,
        comision=1.0,
        posiciones={"ACME": 1},
        historial=historial,
        capital_inicial=1_000.0,
        curva=[1_000.0, 1_010.0],
    )
    assert cartera.posicion("ACME") == 1
    assert cartera.historial == tuple(historial)
    assert cartera.capital_inicial == 1_000.0
    assert cartera.curva_valor == (1_000.0, 1_010.0)


def test_desde_estado_ignora_cantidades_no_positivas() -> None:
    cartera = Cartera.desde_estado(
        "Dani",
        efectivo=0.0,
        comision=0.0,
        posiciones={"ACME": 0, "GLOB": -1},
        historial=[],
    )
    assert cartera.posiciones == ()


def test_repositorio_inyectado_guarda_operacion(mercado: Mercado) -> None:
    llamadas: list[str] = []

    class Repo:
        def guardar_cartera(self, cartera) -> None:
            llamadas.append("cartera")

        def guardar_posiciones(self, propietario, posiciones) -> None:
            llamadas.append("posiciones")

        def guardar_operacion(self, propietario, operacion) -> None:
            llamadas.append("operacion")

    cartera = Cartera("Dani", efectivo=1_000.0, repositorio=Repo())
    cartera.comprar(mercado, "ACME", 1, fecha="s1")
    assert llamadas == ["cartera", "posiciones", "operacion"]
    assert cartera.repositorio is not None
    cartera.repositorio = None
    assert cartera.repositorio is None


def test_propiedades_con_validacion() -> None:
    cartera = Cartera("Dani")
    with pytest.raises(TypeError):
        cartera.efectivo = "x"  # type: ignore[assignment]
    with pytest.raises(TypeError):
        cartera.comision = True  # type: ignore[assignment]
    with pytest.raises(ValueError):
        cartera.comision = -1.0
    assert cartera.posicion("noexiste") == 0


def test_mostrar_y_repr(capsys) -> None:
    cartera = Cartera("Dani", efectivo=100.0)
    cartera.mostrar()
    salida = capsys.readouterr().out
    assert "[Cartera]" in salida
    assert "Cartera(" in repr(cartera)


def test_capital_inicial_cero_sin_curva() -> None:
    cartera = Cartera("Dani", efectivo=0.0)
    assert cartera.capital_inicial == 0.0
    assert cartera.curva_valor == ()
