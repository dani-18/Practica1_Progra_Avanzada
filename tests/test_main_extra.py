"""Tests de los modos adicionales del entry point."""

from __future__ import annotations

import json

from bolsa_sim.__main__ import cli


def test_simular_desde_cli(capsys) -> None:
    assert cli(["--simulate", "--sessions", "5", "--strategy", "momentum"]) == 0
    salida = capsys.readouterr().out
    assert "[momentum]" in salida
    assert "rentabilidad" in salida


def test_paralelo_desde_cli(capsys) -> None:
    assert cli(["--parallel", "--sessions", "5"]) == 0
    salida = capsys.readouterr().out
    assert "Comparacion concurrente" in salida
    assert "comprar_mantener" in salida


def test_exportar_desde_cli(tmp_path) -> None:
    destino = tmp_path / "demo.json"
    assert cli(["--export", str(destino)]) == 0
    assert destino.exists()
    datos = json.loads(destino.read_text(encoding="utf-8"))
    assert datos["cartera"]["historial"]


def test_exportar_csv_desde_cli(tmp_path) -> None:
    destino = tmp_path / "demo.csv"
    assert cli(["--export", str(destino)]) == 0
    assert destino.exists()
    assert destino.read_text(encoding="utf-8").startswith("registro,")


def test_drift_en_simulacion(capsys) -> None:
    assert cli(["--simulate", "--sessions", "3", "--drift", "0.01"]) == 0
    assert "sesiones" in capsys.readouterr().out
