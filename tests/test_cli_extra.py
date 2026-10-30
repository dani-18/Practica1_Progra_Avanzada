"""Tests de los comandos nuevos de la CLI."""

from __future__ import annotations

import json

import pytest

from bolsa_sim.cli import Shell, _sparkline
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.persistencia import RepositorioMemoria


@pytest.fixture
def shell() -> tuple[Shell, list[str]]:
    salida: list[str] = []
    sh = Shell(
        mercado_demo(),
        cartera_demo(),
        entrada=lambda _p: "quit",
        salida=salida.append,
    )
    return sh, salida


def _texto(salida: list[str]) -> str:
    return "\n".join(salida)


def test_metrics(shell) -> None:
    sh, salida = shell
    sh.ejecutar("metrics")
    texto = _texto(salida)
    assert "Capital inicial" in texto
    assert "rentabilidad" in texto
    assert "sharpe" in texto


def test_strategies_y_strategy(shell) -> None:
    sh, salida = shell
    sh.ejecutar("strategies")
    assert "comprar_mantener" in _texto(salida)
    sh.ejecutar("strategy momentum ventana=3")
    assert sh.estrategia.nombre == "momentum"
    sh.ejecutar("strategy")
    assert "Estrategia actual" in _texto(salida)
    sh.ejecutar("strategy nope")
    assert "Error:" in _texto(salida)


def test_simulate(shell) -> None:
    sh, salida = shell
    sh.ejecutar("simulate 5 momentum")
    texto = _texto(salida)
    assert "[momentum]" in texto
    assert "rentabilidad" in texto
    sh.ejecutar("simulate 3")
    assert "sesiones" in _texto(salida)
    sh.ejecutar("simulate 0")
    assert "sesiones debe ser un entero > 0" in _texto(salida)
    sh.ejecutar("simulate 5 nope")
    assert "Error:" in _texto(salida)


def test_parallel(shell) -> None:
    sh, salida = shell
    sh.ejecutar("parallel 5")
    texto = _texto(salida)
    assert "Comparacion en paralelo" in texto
    assert "momentum" in texto
    sh.ejecutar("parallel abc")
    assert "sesiones debe ser un entero > 0" in _texto(salida)
    sh.ejecutar("parallel 0")
    assert "sesiones debe ser un entero > 0" in _texto(salida)


def test_shock_y_chart(shell) -> None:
    sh, salida = shell
    sh.ejecutar("next")
    sh.ejecutar("shock -0.10")
    assert "Shock -10.00%" in _texto(salida)
    sh.ejecutar("chart acme")
    assert "ACME:" in _texto(salida)
    sh.ejecutar("shock")
    assert "Uso: shock" in _texto(salida)
    sh.ejecutar("shock abc")
    assert "variacion debe ser un numero" in _texto(salida)
    sh.ejecutar("shock -2")
    assert "Error:" in _texto(salida)
    sh.ejecutar("chart")
    assert "Uso: chart" in _texto(salida)
    sh.ejecutar("chart NOPE")
    assert "Error:" in _texto(salida)


def test_errores_de_instrumento(shell) -> None:
    sh, salida = shell
    sh.ejecutar("buy NOPE 1 10")
    assert "Error:" in _texto(salida)
    sh.ejecutar("price NOPE")
    assert "Instrumento desconocido" in _texto(salida)


def test_export_json_y_csv(shell, tmp_path) -> None:
    sh, salida = shell
    sh.ejecutar("buy acme 1")
    sh.ejecutar(f"export json {tmp_path / 'res'}")
    assert (tmp_path / "res.json").exists()
    sh.ejecutar(f"export csv {tmp_path / 'res.csv'}")
    assert (tmp_path / "res.csv").exists()
    sh.ejecutar("export")
    assert "Uso: export" in _texto(salida)
    sh.ejecutar(f"export pdf {tmp_path / 'res.pdf'}")
    assert "Error:" in _texto(salida)


def test_guardar_y_cargar_sqlite(shell, tmp_path) -> None:
    sh, salida = shell
    sh.ejecutar("buy acme 2")
    ruta = tmp_path / "estado.sqlite"
    sh.ejecutar(f"save {ruta}")
    assert ruta.exists()
    assert "Estado guardado" in _texto(salida)
    sh.ejecutar("save")  # reutiliza el repositorio ya abierto
    assert "Estado guardado" in _texto(salida)

    salida2: list[str] = []
    otro = Shell(mercado_demo(), cartera_demo("Otro", 500.0), salida=salida2.append)
    otro.ejecutar(f"load {ruta} Dani")
    assert otro.cartera.propietario == "Dani"
    assert otro.cartera.posicion("ACME") == 2
    assert otro.mercado.sesion == sh.mercado.sesion
    assert "Cargado" in _texto(salida2)
    sh.cerrar()
    otro.cerrar()


def test_guardar_y_cargar_json(shell, tmp_path) -> None:
    sh, _salida = shell
    sh.ejecutar("buy acme 1")
    ruta = tmp_path / "estado.json"
    sh.ejecutar(f"save {ruta}")
    assert ruta.exists()
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert "carteras" in datos
    otro_salida: list[str] = []
    otro = Shell(mercado_demo(), cartera_demo(), salida=otro_salida.append)
    otro.ejecutar(f"load {ruta} Dani")
    assert otro.cartera.posicion("ACME") == 1
    sh.cerrar()
    otro.cerrar()


def test_load_uso(shell) -> None:
    sh, salida = shell
    sh.ejecutar("load")
    assert "Uso: load" in _texto(salida)


def test_repositorio_inyectado_persiste_operaciones() -> None:
    repo = RepositorioMemoria()
    sh = Shell(mercado_demo(), cartera_demo(), repositorio=repo, salida=lambda _m: None)
    assert sh.servicio is not None
    sh.ejecutar("buy acme 1")
    assert len(repo.listar_operaciones("Dani")) == 1
    assert sh.cartera.repositorio is repo


def test_sparkline() -> None:
    assert _sparkline([]) == ""
    assert len(_sparkline([100.0, 100.0, 100.0])) == 3
    larga = _sparkline([float(i) for i in range(200)], ancho=20)
    assert len(larga) == 20
    assert set(_sparkline([1.0, 2.0])) <= set("▁▂▃▄▅▆▇█")
