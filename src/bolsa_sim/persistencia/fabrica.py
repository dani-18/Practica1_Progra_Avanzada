"""Fabrica de repositorios (patron **Factory**).

Selecciona el backend de persistencia a partir de un nombre o de la
extension del fichero, de modo que CLI, GUI y tests no importen clases
concretas::

    repo = RepositorioFactory.crear("sqlite", "datos.sqlite")
    repo = RepositorioFactory.crear("memoria")
    repo = RepositorioFactory.desde_ruta("resultados.json")
"""

from __future__ import annotations

from pathlib import Path

from ..excepciones import ErrorPersistencia
from .repositorios import Repositorio, RepositorioJSON, RepositorioMemoria, RepositorioSQLite

BACKENDS: tuple[str, ...] = ("json", "memoria", "sqlite")

RUTAS_POR_DEFECTO: dict[str, str] = {
    "sqlite": "bolsa_sim.sqlite",
    "json": "bolsa_sim.json",
}


class RepositorioFactory:
    """Crea el repositorio adecuado segun el backend pedido."""

    @staticmethod
    def crear(backend: str = "sqlite", ruta: str | Path | None = None) -> Repositorio:
        clave = backend.strip().lower() if isinstance(backend, str) else ""
        if clave in ("memoria", "memory", "in-memory"):
            return RepositorioMemoria()
        if clave in ("sqlite", "sqlite3", "db"):
            return RepositorioSQLite(ruta or RUTAS_POR_DEFECTO["sqlite"])
        if clave == "json":
            return RepositorioJSON(ruta or RUTAS_POR_DEFECTO["json"])
        raise ErrorPersistencia(
            f"backend de persistencia desconocido: {backend!r} (validos: {BACKENDS})"
        )

    @staticmethod
    def desde_ruta(ruta: str | Path) -> Repositorio:
        """Infiere el backend por la extension (``.json`` o SQLite)."""
        destino = Path(ruta)
        if destino.suffix.lower() == ".json":
            return RepositorioJSON(destino)
        return RepositorioSQLite(destino)

    @staticmethod
    def backends_disponibles() -> tuple[str, ...]:
        return BACKENDS


__all__ = ["BACKENDS", "RUTAS_POR_DEFECTO", "RepositorioFactory"]
