"""Conexion SQLite, transacciones y versionado de esquema."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from importlib.resources import files
from pathlib import Path

from ..excepciones import ErrorPersistencia

ESQUEMA_VERSION = "1"
CLAVE_VERSION = "esquema_version"


def conectar(ruta: str | Path = ":memory:") -> sqlite3.Connection:
    """Abre una conexion SQLite configurada para el simulador.

    ``:memory:`` se usa en tests; para ficheros se activa WAL para permitir
    lecturas concurrentes mientras se escribe (util en la GUI).
    """
    destino = str(ruta)
    try:
        conexion = sqlite3.connect(destino, timeout=10.0, check_same_thread=False)
    except sqlite3.Error as exc:  # pragma: no cover - depende del sistema de ficheros
        raise ErrorPersistencia(f"no se pudo abrir {destino!r}: {exc}") from exc
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    if destino != ":memory:":
        with suppress(sqlite3.Error):  # pragma: no cover - sistemas de ficheros exoticos
            conexion.execute("PRAGMA journal_mode = WAL")
    return conexion


def _leer_esquema() -> str:
    return files("bolsa_sim.persistencia").joinpath("esquema.sql").read_text(encoding="utf-8")


def inicializar_esquema(conexion: sqlite3.Connection) -> None:
    """Crea las tablas si no existen y registra la version del esquema."""
    try:
        conexion.executescript(_leer_esquema())
        conexion.execute(
            "INSERT INTO meta (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (CLAVE_VERSION, ESQUEMA_VERSION),
        )
        conexion.commit()
    except sqlite3.Error as exc:
        conexion.rollback()
        raise ErrorPersistencia(f"no se pudo inicializar el esquema: {exc}") from exc


def version_esquema(conexion: sqlite3.Connection) -> str | None:
    try:
        fila = conexion.execute(
            "SELECT valor FROM meta WHERE clave = ?", (CLAVE_VERSION,)
        ).fetchone()
    except sqlite3.Error as exc:
        raise ErrorPersistencia(f"no se pudo leer la version del esquema: {exc}") from exc
    return None if fila is None else str(fila["valor"])


def verificar_esquema(conexion: sqlite3.Connection) -> None:
    version = version_esquema(conexion)
    if version is not None and version != ESQUEMA_VERSION:
        raise ErrorPersistencia(
            f"version de esquema incompatible: {version} (se esperaba {ESQUEMA_VERSION})"
        )


@contextmanager
def transaccion(conexion: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transaccion explicita: commit si todo va bien, rollback si falla."""
    try:
        yield conexion
        conexion.commit()
    except sqlite3.Error as exc:
        conexion.rollback()
        raise ErrorPersistencia(f"error de base de datos: {exc}") from exc


__all__ = [
    "CLAVE_VERSION",
    "ESQUEMA_VERSION",
    "conectar",
    "inicializar_esquema",
    "transaccion",
    "verificar_esquema",
    "version_esquema",
]
