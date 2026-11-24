"""Tests de los modos adicionales del entry point."""

from __future__ import annotations

import json

import pytest

import bolsa_sim.__main__ as entrypoint
from bolsa_sim.__main__ import cli
from bolsa_sim.excepciones import DatosInvalidos


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


def test_error_de_dominio_devuelve_codigo_1(monkeypatch, tmp_path, capsys) -> None:
    def falla(*_args, **_kwargs):
        raise DatosInvalidos("fallo controlado")

    monkeypatch.setattr(entrypoint, "exportar_resultados", falla)
    assert cli(["--export", str(tmp_path / "demo.json")]) == 1
    assert "Error:" in capsys.readouterr().out


def test_verbose_y_quiet_son_excluyentes() -> None:
    with pytest.raises(SystemExit):
        cli(["--verbose", "--quiet"])
