"""Capa de persistencia: SQLite, memoria, JSON y exportadores.

API publica::

    from bolsa_sim.persistencia import RepositorioFactory, ServicioPersistencia

    repo = RepositorioFactory.crear("sqlite", "datos.sqlite")
    servicio = ServicioPersistencia(repo)
    servicio.guardar_estado(mercado, cartera)
    mercado, cartera = servicio.cargar_estado(mercado.nombre, cartera.propietario)
"""

from __future__ import annotations

from .db import conectar, inicializar_esquema, transaccion, version_esquema
from .exportadores import (
    Exportador,
    ExportadorCSV,
    ExportadorJSON,
    crear_exportador,
    datos_exportacion,
    exportar_resultados,
    exportar_simulacion,
)
from .fabrica import RepositorioFactory
from .repositorios import (
    Repositorio,
    RepositorioJSON,
    RepositorioMemoria,
    RepositorioSQLite,
)
from .servicio import ServicioPersistencia

__all__ = [
    "Exportador",
    "ExportadorCSV",
    "ExportadorJSON",
    "Repositorio",
    "RepositorioFactory",
    "RepositorioJSON",
    "RepositorioMemoria",
    "RepositorioSQLite",
    "ServicioPersistencia",
    "conectar",
    "crear_exportador",
    "datos_exportacion",
    "exportar_resultados",
    "exportar_simulacion",
    "inicializar_esquema",
    "transaccion",
    "version_esquema",
]
