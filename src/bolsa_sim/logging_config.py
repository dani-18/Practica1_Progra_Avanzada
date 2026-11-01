"""Configuracion de logging del simulador (biblioteca estandar).

La biblioteca **no** instala handlers al importarse: solo crea loggers con
``obtener_logger``. La aplicacion (``python -m bolsa_sim``, CLI o GUI) decide
el nivel y los destinos con :func:`configurar_logging`. Asi el paquete puede
usarse como biblioteca sin efectos secundarios sobre el logging global.

Uso::

    from bolsa_sim.logging_config import configurar_logging, obtener_logger

    configurar_logging("INFO", archivo="bolsa.log")
    log = obtener_logger(__name__)
    log.info("estado guardado")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

#: Logger raiz del paquete. Todos los loggers internos cuelgan de el.
LOGGER_RAIZ = "bolsa_sim"

#: Formato comun (fecha, nivel, modulo y mensaje).
FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FECHA = "%Y-%m-%d %H:%M:%S"

#: Marca propia para poder retirar solo los handlers instalados por nosotros.
_MARCA_HANDLER = "_bolsa_sim_handler"

#: Variable de entorno para fijar el nivel sin tocar codigo.
VARIABLE_NIVEL = "BOLSA_LOG_LEVEL"

#: Sin handlers, la biblioteca no debe escribir en stderr (lo decide la app).
logging.getLogger(LOGGER_RAIZ).addHandler(logging.NullHandler())


def _normalizar_nivel(nivel: int | str) -> int:
    """Convierte ``"INFO"``/``"debug"``/``20`` en el entero de ``logging``."""
    if isinstance(nivel, bool):
        raise TypeError("el nivel de logging debe ser un entero o una cadena")
    if isinstance(nivel, int):
        return nivel
    if not isinstance(nivel, str):
        raise TypeError("el nivel de logging debe ser un entero o una cadena")
    valor = logging.getLevelName(nivel.strip().upper())
    if not isinstance(valor, int):
        raise ValueError(f"nivel de logging desconocido: {nivel!r}")
    return valor


def _quitar_handlers_propios(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, _MARCA_HANDLER, False):
            logger.removeHandler(handler)
            handler.close()


def configurar_logging(
    nivel: int | str | None = None,
    archivo: str | Path | None = None,
    *,
    consola: bool = True,
    propagar: bool = False,
) -> logging.Logger:
    """Configura el logger ``bolsa_sim`` de forma idempotente.

    Args:
        nivel: nivel de logging (por defecto ``BOLSA_LOG_LEVEL`` o ``INFO``).
        archivo: ruta opcional de un fichero de log (se crea si no existe).
        consola: si ``True`` anade un handler a ``stderr``.
        propagar: si ``True`` deja que los records lleguen al logger raiz.

    Returns:
        El logger raiz del paquete, listo para usar.
    """
    logger = logging.getLogger(LOGGER_RAIZ)
    if nivel is None:
        nivel = os.getenv(VARIABLE_NIVEL) or "INFO"
    logger.setLevel(_normalizar_nivel(nivel))
    logger.propagate = propagar
    _quitar_handlers_propios(logger)

    formatter = logging.Formatter(FORMATO, datefmt=FECHA)
    if consola:
        handler_consola = logging.StreamHandler()
        handler_consola.setFormatter(formatter)
        setattr(handler_consola, _MARCA_HANDLER, True)
        logger.addHandler(handler_consola)

    if archivo is not None:
        ruta = Path(archivo).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        handler_fichero = logging.FileHandler(ruta, encoding="utf-8")
        handler_fichero.setFormatter(formatter)
        setattr(handler_fichero, _MARCA_HANDLER, True)
        logger.addHandler(handler_fichero)

    logger.debug(
        "logging configurado: nivel=%s archivo=%s consola=%s",
        logging.getLevelName(logger.level),
        archivo,
        consola,
    )
    return logger


def obtener_logger(nombre: str | None = None) -> logging.Logger:
    """Devuelve un logger bajo ``bolsa_sim`` (``__name__`` por convencion)."""
    if not nombre:
        return logging.getLogger(LOGGER_RAIZ)
    if nombre == LOGGER_RAIZ or nombre.startswith(f"{LOGGER_RAIZ}."):
        return logging.getLogger(nombre)
    return logging.getLogger(f"{LOGGER_RAIZ}.{nombre}")


__all__ = [
    "FORMATO",
    "LOGGER_RAIZ",
    "VARIABLE_NIVEL",
    "configurar_logging",
    "obtener_logger",
]
