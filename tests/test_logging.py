"""Tests de la configuracion de logging (stdlib) y su integracion en el CLI."""

from __future__ import annotations

import logging

import pytest

from bolsa_sim.__main__ import cli
from bolsa_sim.logging_config import (
    LOGGER_RAIZ,
    configurar_logging,
    obtener_logger,
)


@pytest.fixture(autouse=True)
def _limpiar_logging():
    yield
    logger = logging.getLogger(LOGGER_RAIZ)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True
    logger.addHandler(logging.NullHandler())


def test_configurar_logging_es_idempotente() -> None:
    logger = configurar_logging("INFO")
    primero = len(logger.handlers)
    configurar_logging("DEBUG")
    assert len(logger.handlers) == primero
    assert logger.level == logging.DEBUG


def test_configurar_logging_escribe_en_fichero(tmp_path) -> None:
    ruta = tmp_path / "logs" / "bolsa.log"
    configurar_logging("INFO", ruta, consola=False)
    obtener_logger("prueba").info("mensaje de prueba")
    contenido = ruta.read_text(encoding="utf-8")
    assert "mensaje de prueba" in contenido
    assert "bolsa_sim.prueba" in contenido


def test_configurar_logging_nivel_invalido() -> None:
    with pytest.raises(ValueError):
        configurar_logging("nivel-que-no-existe")


def test_configurar_logging_usa_variable_de_entorno(monkeypatch) -> None:
    monkeypatch.setenv("BOLSA_LOG_LEVEL", "ERROR")
    logger = configurar_logging(consola=False)
    assert logger.level == logging.ERROR


def test_obtener_logger_cuelga_del_paquete() -> None:
    assert obtener_logger().name == LOGGER_RAIZ
    assert obtener_logger("bolsa_sim.cli").name == "bolsa_sim.cli"
    assert obtener_logger("modulo").name == "bolsa_sim.modulo"


def test_cli_guarda_log_en_fichero(tmp_path) -> None:
    ruta = tmp_path / "cli.log"
    assert cli(["--simulate", "--sessions", "3", "--log-file", str(ruta)]) == 0
    contenido = ruta.read_text(encoding="utf-8")
    assert "simulacion iniciada" in contenido
    assert "simulacion completada" in contenido
