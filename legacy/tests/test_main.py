"""Smoke tests del CLI ``python -m bolsa_sim``.

El modulo ``__main__`` no se cubre por las clases de dominio; estos
tests ejecutan el entry-point real para asegurar el contrato basico
(flag ``--version``, ``--memoria``, ``--demo`` y ``--sesiones``).
"""

from __future__ import annotations

import pytest

import bolsa_sim
from bolsa_sim.__main__ import _demo_hello_flow, _demo_memoria, cli


def test_version_retorna_0() -> None:
    assert cli(["--version"]) == 0


def test_memoria_retorna_0() -> None:
    assert _demo_memoria() == 0


def test_demo_hello_flow_5_sesiones() -> None:
    rc = _demo_hello_flow(sesiones=5, semilla=7)
    assert rc == 0


def test_cli_demo_con_sesiones_y_semilla() -> None:
    rc = cli(["--demo", "--sesiones", "3", "--semilla", "1"])
    assert rc == 0


def test_cli_inesperado_argumento() -> None:
    # argparse debe cortar el programa con SystemExit(2). Lo capturamos.
    with pytest.raises(SystemExit):
        cli(["--z"])


def test_imports_publicos() -> None:
    """El paquete expone la API documentada."""
    expected = {
        "Activo",
        "BarraDiaria",
        "Cartera",
        "MercadoSimulado",
        "Simulador",
        "ResultadoSimulacion",
        "CompraYMantiene",
        "AportePeriodico",
        "rentabilidad_total",
        "drawdown_maximo",
    }
    assert expected.issubset(set(bolsa_sim.__all__))
