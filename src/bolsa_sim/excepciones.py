"""Excepciones de dominio del simulador.

Todas heredan de :class:`ErrorBolsa`, de modo que la interfaz (CLI o GUI)
puede capturar cualquier error esperado del negocio con un unico ``except``.
Ademas, cada excepcion hereda de la excepcion builtin mas afin (``ValueError``,
``KeyError``...) para no romper el contrato de la biblioteca estandar ni los
tests escritos antes de introducir esta jerarquia.

Ejemplo::

    try:
        mercado.precio_de("NOPE")
    except InstrumentoDesconocido:
        ...  # tambien se puede capturar como KeyError
"""

from __future__ import annotations


class ErrorBolsa(Exception):
    """Error base de cualquier regla de negocio del simulador."""


class DatosInvalidos(ErrorBolsa, ValueError):
    """Un dato de entrada no cumple el contrato del dominio."""


class OperacionInvalida(ErrorBolsa, ValueError):
    """La operacion solicitada no es valida (cantidad, precio...)."""


class FondosInsuficientes(OperacionInvalida):
    """El efectivo de la cartera no cubre el coste de la compra."""


class PosicionInsuficiente(OperacionInvalida):
    """La cartera no tiene unidades suficientes para vender."""


class InstrumentoDesconocido(ErrorBolsa, KeyError):
    """El identificador no corresponde a ningun instrumento del mercado."""


class InstrumentoDuplicado(ErrorBolsa, ValueError):
    """Ya existe un instrumento con ese identificador."""


class CarteraDuplicada(ErrorBolsa, ValueError):
    """Ya existe una cartera con ese propietario."""


class CarteraDesconocida(ErrorBolsa, KeyError):
    """No existe una cartera con ese propietario."""


class TipoInstrumentoDesconocido(ErrorBolsa, ValueError):
    """La fabrica no conoce el tipo de instrumento solicitado."""


class EstrategiaDesconocida(ErrorBolsa, ValueError):
    """La fabrica no conoce la estrategia de inversion solicitada."""


class FormatoNoSoportado(ErrorBolsa, ValueError):
    """No existe un exportador para el formato pedido."""


class ErrorPersistencia(ErrorBolsa, RuntimeError):
    """Fallo al leer o escribir en el almacen de datos."""


class ErrorSimulacion(ErrorBolsa, RuntimeError):
    """La simulacion no pudo completarse."""


__all__ = [
    "CarteraDesconocida",
    "CarteraDuplicada",
    "DatosInvalidos",
    "ErrorBolsa",
    "ErrorPersistencia",
    "ErrorSimulacion",
    "EstrategiaDesconocida",
    "FondosInsuficientes",
    "FormatoNoSoportado",
    "InstrumentoDesconocido",
    "InstrumentoDuplicado",
    "OperacionInvalida",
    "PosicionInsuficiente",
    "TipoInstrumentoDesconocido",
]
