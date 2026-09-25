"""Configuracion del simulador leida del entorno.

No se usa ``python-dotenv`` (lo prohibe el enunciado: PRAC1 es solo
biblioteca estandar). Para cargar ``.env`` desde Bash/Zsh::

    set -a; source .env; set +a

o desde PowerShell (divide la linea en dos para PowerShell < 7)::

    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#].+?)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }

El resto del paquete solo necesita :func:`cargar_configuracion`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _leer_float(nombre: str, por_defecto: float) -> float:
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        return por_defecto
    try:
        return float(valor)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un numero, recibido {valor!r}") from exc


def _leer_int(nombre: str, por_defecto: int) -> int:
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        return por_defecto
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un entero, recibido {valor!r}") from exc


def _leer_int_opcional(nombre: str, por_defecto: int | None) -> int | None:
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        return por_defecto
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un entero, recibido {valor!r}") from exc


def _leer_lista(nombre: str, por_defecto: list[str]) -> list[str]:
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        return list(por_defecto)
    return [t.strip().upper() for t in valor.split(",") if t.strip()]


@dataclass(frozen=True, slots=True)
class ConfiguracionSimulador:
    """Snapshot inmutable de los parametros de la simulacion."""

    semilla: int | None
    sesiones: int
    efectivo_inicial: float
    tickers: tuple[str, ...]


def cargar_configuracion() -> ConfiguracionSimulador:
    """Lee las variables ``SIMULADOR_*`` del entorno y devuelve la configuracion."""
    tickers = tuple(
        _leer_lista(
            "SIMULADOR_TICKERS",
            ["ACME", "GLOB", "OILX", "TECH", "BONO10"],
        )
    )
    return ConfiguracionSimulador(
        semilla=_leer_int_opcional("SIMULADOR_SEMILLA", 42),
        sesiones=_leer_int("SIMULADOR_SESIONES", 30),
        efectivo_inicial=_leer_float("SIMULADOR_EFECTIVO_INICIAL", 10_000.0),
        tickers=tickers,
    )
