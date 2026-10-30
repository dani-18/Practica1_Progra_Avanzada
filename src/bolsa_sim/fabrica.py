"""Fabrica de instrumentos y (de)serializacion de la jerarquia.

Aplica el patron **Factory** al punto del dominio donde de verdad aporta:
reconstruir un ``Accion``, ``Bono`` o ``ETF`` a partir de datos externos
(JSON, SQLite, GUI...) sin que el llamador tenga que conocer las clases
concretas ni encadenar ``isinstance``.

La serializacion es simetrica::

    datos = instrumento_a_dict(accion)
    copia = FabricaInstrumentos.por_defecto().desde_dict(datos)
    assert copia == accion  # igualdad por id
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .accion import Accion
from .bono import Bono
from .etf import ETF
from .excepciones import DatosInvalidos, TipoInstrumentoDesconocido
from .instrumento import InstrumentoBase

#: Campos comunes a toda la jerarquia.
CAMPOS_COMUNES: tuple[str, ...] = ("id", "nombre", "simbolo", "volatilidad", "precio_base")

#: Campos propios de cada subclase.
CAMPOS_ESPECIFICOS: dict[str, tuple[str, ...]] = {
    "accion": ("sector", "dividendo_anual"),
    "bono": ("cupon_anual", "valor_nominal", "vencimiento"),
    "etf": ("indice", "comision_gestion"),
}


def instrumento_a_dict(instrumento: InstrumentoBase) -> dict[str, Any]:
    """Convierte un instrumento en un diccionario plano y serializable."""
    datos: dict[str, Any] = {
        "tipo": instrumento.tipo,
        "id": instrumento.id,
        "nombre": instrumento.nombre,
        "simbolo": instrumento.simbolo,
        "volatilidad": instrumento.volatilidad,
        "precio_base": instrumento.precio_base,
    }
    for campo in CAMPOS_ESPECIFICOS.get(instrumento.tipo, ()):
        datos[campo] = getattr(instrumento, campo)
    return datos


class FabricaInstrumentos:
    """Registro ``tipo -> clase`` con creacion desde diccionarios."""

    def __init__(self) -> None:
        self._tipos: dict[str, type[InstrumentoBase]] = {}

    def registrar(self, tipo: str, clase: type[InstrumentoBase]) -> None:
        if not isinstance(tipo, str) or not tipo.strip():
            raise DatosInvalidos("el tipo de instrumento no puede estar vacio")
        if not isinstance(clase, type) or not issubclass(clase, InstrumentoBase):
            raise DatosInvalidos(f"{clase!r} no es una subclase de InstrumentoBase")
        self._tipos[tipo.strip().lower()] = clase

    @property
    def tipos(self) -> tuple[str, ...]:
        return tuple(sorted(self._tipos))

    def crear(self, tipo: str, **datos: Any) -> InstrumentoBase:
        """Crea el instrumento concreto indicado por ``tipo``."""
        clave = tipo.strip().lower() if isinstance(tipo, str) else ""
        clase = self._tipos.get(clave)
        if clase is None:
            raise TipoInstrumentoDesconocido(
                f"tipo de instrumento desconocido: {tipo!r} (validos: {self.tipos})"
            )
        permitidos = set(CAMPOS_COMUNES) | set(CAMPOS_ESPECIFICOS.get(clave, ()))
        desconocidos = set(datos) - permitidos
        if desconocidos:
            raise DatosInvalidos(f"campos no validos para {clave!r}: {sorted(desconocidos)}")
        try:
            return clase(**datos)
        except TypeError as exc:  # faltan campos obligatorios
            raise DatosInvalidos(f"datos incompletos para {clave!r}: {exc}") from exc

    def desde_dict(self, datos: Mapping[str, Any]) -> InstrumentoBase:
        if not isinstance(datos, Mapping):
            raise DatosInvalidos("se esperaba un mapping con los datos del instrumento")
        copia = dict(datos)
        tipo = copia.pop("tipo", None)
        if tipo is None:
            raise DatosInvalidos("faltan el campo 'tipo' para crear el instrumento")
        return self.crear(tipo, **copia)

    @classmethod
    def por_defecto(cls) -> FabricaInstrumentos:
        """Fabrica con las tres subclases de la jerarquia registradas."""
        fabrica = cls()
        fabrica.registrar("accion", Accion)
        fabrica.registrar("bono", Bono)
        fabrica.registrar("etf", ETF)
        return fabrica


def instrumentos_a_dicts(instrumentos: Iterable[InstrumentoBase]) -> list[dict[str, Any]]:
    return [instrumento_a_dict(inst) for inst in instrumentos]


def guardar_instrumentos_json(instrumentos: Iterable[InstrumentoBase], ruta: str | Path) -> Path:
    """Escribe la jerarquia completa en un JSON legible."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(instrumentos_a_dicts(instrumentos), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destino


def cargar_instrumentos_json(ruta: str | Path) -> list[InstrumentoBase]:
    origen = Path(ruta)
    try:
        crudo = json.loads(origen.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatosInvalidos(f"no se pudo leer {origen}: {exc}") from exc
    if not isinstance(crudo, list):
        raise DatosInvalidos(f"{origen} debe contener una lista de instrumentos")
    fabrica = FabricaInstrumentos.por_defecto()
    return [fabrica.desde_dict(item) for item in crudo]


__all__ = [
    "CAMPOS_COMUNES",
    "CAMPOS_ESPECIFICOS",
    "FabricaInstrumentos",
    "cargar_instrumentos_json",
    "guardar_instrumentos_json",
    "instrumento_a_dict",
    "instrumentos_a_dicts",
]
