"""Tests del modulo de configuracion (``os.environ`` puro)."""

from __future__ import annotations

import dataclasses

import pytest

from bolsa_sim.config import (
    ConfiguracionSimulador,
    cargar_configuracion,
)


def test_configuracion_por_defecto(monkeypatch) -> None:
    for var in (
        "SIMULADOR_SEMILLA",
        "SIMULADOR_SESIONES",
        "SIMULADOR_EFECTIVO_INICIAL",
        "SIMULADOR_TICKERS",
    ):
        monkeypatch.delenv(var, raising=False)
    cfg = cargar_configuracion()
    assert isinstance(cfg, ConfiguracionSimulador)
    assert cfg.semilla == 42
    assert cfg.sesiones == 30
    assert cfg.efectivo_inicial == pytest.approx(10_000.0)
    assert "ACME" in cfg.tickers


def test_configuracion_valores_env(monkeypatch) -> None:
    monkeypatch.setenv("SIMULADOR_SEMILLA", "7")
    monkeypatch.setenv("SIMULADOR_SESIONES", "5")
    monkeypatch.setenv("SIMULADOR_EFECTIVO_INICIAL", "250.5")
    monkeypatch.setenv("SIMULADOR_TICKERS", "x,y , z")
    cfg = cargar_configuracion()
    assert cfg.semilla == 7
    assert cfg.sesiones == 5
    assert cfg.efectivo_inicial == pytest.approx(250.5)
    assert cfg.tickers == ("X", "Y", "Z")


@pytest.mark.parametrize(
    "var,valor",
    [
        ("SIMULADOR_SEMILLA", "no_numero"),
        ("SIMULADOR_SESIONES", "no_numero"),
        ("SIMULADOR_EFECTIVO_INICIAL", "no_numero"),
    ],
)
def test_configuracion_valores_invalidos(monkeypatch, var, valor) -> None:
    monkeypatch.setenv(var, valor)
    with pytest.raises(ValueError):
        cargar_configuracion()


def test_configuracion_es_inmutable() -> None:
    cfg = cargar_configuracion()
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        cfg.semilla = 99
