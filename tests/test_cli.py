"""Tests de la consola interactiva (``bolsa_sim.cli``)."""

from __future__ import annotations

import pytest

from bolsa_sim.cli import Shell
from bolsa_sim.demo import cartera_demo, mercado_demo


@pytest.fixture
def shell() -> tuple[Shell, list[str]]:
    """Shell con salida capturada y sin lectura real de teclado."""
    salida: list[str] = []
    sh = Shell(
        mercado_demo(),
        cartera_demo(),
        entrada=lambda _prompt: "",
        salida=salida.append,
    )
    return sh, salida


def _texto(salida: list[str]) -> str:
    return "\n".join(salida)


def test_help(shell) -> None:
    sh, salida = shell
    assert sh.ejecutar("help") is True
    assert "help" in _texto(salida)


def test_listar_instrumentos(shell) -> None:
    sh, salida = shell
    sh.ejecutar("list")
    out = _texto(salida)
    assert "ACME" in out
    assert "BONO10" in out
    assert "SP500" in out


def test_precio_actual(shell) -> None:
    sh, salida = shell
    sh.ejecutar("price acme")
    assert "ACME: 120.00 EUR" in _texto(salida)


def test_precio_instrumento_desconocido(shell) -> None:
    sh, salida = shell
    sh.ejecutar("price NOPE")
    assert "desconocido" in _texto(salida)


def test_uso_incorrecto_de_price(shell) -> None:
    sh, salida = shell
    sh.ejecutar("price")
    assert "Uso: price" in _texto(salida)


def test_compra(shell) -> None:
    sh, salida = shell
    sh.ejecutar("buy acme 2")
    assert dict(sh.cartera.posiciones)["ACME"] == 2
    # 2 * 120 + 1 de comision = 241
    assert sh.cartera.efectivo == pytest.approx(759.0)
    assert "Compra ejecutada" in _texto(salida)


def test_compra_sin_efectivo() -> None:
    salida: list[str] = []
    sh = Shell(mercado_demo(), cartera_demo(efectivo=10.0), salida=salida.append)
    sh.ejecutar("buy acme 1")
    assert sh.cartera.posiciones == ()
    assert "Efectivo insuficiente" in _texto(salida)


def test_compra_cantidad_invalida(shell) -> None:
    sh, salida = shell
    sh.ejecutar("buy acme 0")
    assert "cantidad debe ser un entero > 0" in _texto(salida)


def test_compra_precio_invalido(shell) -> None:
    sh, salida = shell
    sh.ejecutar("buy acme 1 abc")
    assert "precio debe ser un numero > 0" in _texto(salida)


def test_uso_incorrecto_de_buy(shell) -> None:
    sh, salida = shell
    sh.ejecutar("buy")
    assert "Uso: buy" in _texto(salida)


def test_venta(shell) -> None:
    sh, salida = shell
    sh.ejecutar("buy acme 2")
    sh.ejecutar("sell acme 1 130")
    assert dict(sh.cartera.posiciones)["ACME"] == 1
    # Tras comprar a 120 (efectivo 759) y vender 1 a 130 - 1 comision = +129.
    assert sh.cartera.efectivo == pytest.approx(888.0)
    assert "Venta ejecutada" in _texto(salida)


def test_venta_sin_posicion(shell) -> None:
    sh, salida = shell
    sh.ejecutar("sell acme 1")
    assert "No hay posicion suficiente" in _texto(salida)


def test_avanzar_sesion(shell) -> None:
    sh, salida = shell
    sh.ejecutar("next 50")
    assert sh.mercado.sesion == 1
    assert sh.mercado.volumen_total == 50
    assert "Sesion 1" in _texto(salida)


def test_avanzar_sesion_volumen_invalido(shell) -> None:
    sh, salida = shell
    sh.ejecutar("next abc")
    assert sh.mercado.sesion == 0
    assert "volumen debe ser un entero > 0" in _texto(salida)


def test_historial_vacio_y_con_operaciones(shell) -> None:
    sh, salida = shell
    sh.ejecutar("history")
    assert "Sin operaciones registradas." in _texto(salida)
    sh.ejecutar("buy acme 1")
    sh.ejecutar("history")
    assert "Operacion(" in _texto(salida)


def test_comando_desconocido(shell) -> None:
    sh, salida = shell
    assert sh.ejecutar("hazalgo") is True
    assert "Comando desconocido" in _texto(salida)


def test_linea_vacia_continua(shell) -> None:
    sh, _salida = shell
    assert sh.ejecutar("   ") is True


def test_quit_y_exit_detienen(shell) -> None:
    sh, _salida = shell
    assert sh.ejecutar("quit") is False
    assert sh.ejecutar("exit") is False


def test_market_imprime(capsys, shell) -> None:
    sh, _salida = shell
    sh.ejecutar("market")
    assert "[Mercado]" in capsys.readouterr().out


def test_portfolio_imprime(capsys, shell) -> None:
    sh, salida = shell
    sh.ejecutar("portfolio")
    out = capsys.readouterr().out
    assert "[Cartera]" in out
    assert "Valor liquidativo" in _texto(salida)


def test_run_termina_con_quit() -> None:
    entradas = iter(["list", "quit"])
    salida: list[str] = []
    sh = Shell(
        mercado_demo(), cartera_demo(), entrada=lambda _p: next(entradas), salida=salida.append
    )
    sh.run()
    assert "Hasta luego." in _texto(salida)


def test_run_termina_con_eof() -> None:
    salida: list[str] = []

    def entrada(_prompt: str) -> str:
        raise EOFError

    sh = Shell(mercado_demo(), cartera_demo(), entrada=entrada, salida=salida.append)
    sh.run()
    assert "Hasta luego." in _texto(salida)
