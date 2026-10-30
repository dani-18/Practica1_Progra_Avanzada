"""Exportacion de resultados a JSON y CSV (patron **Strategy**).

``ExportadorJSON`` y ``ExportadorCSV`` comparten la interfaz
``exportar(datos, ruta)``; ``crear_exportador`` elige la implementacion y
``exportar_resultados`` compone el diccionario de dominio. Anadir un nuevo
formato (por ejemplo PDF o XLSX) solo requiere otra subclase.
"""

from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..excepciones import FormatoNoSoportado
from ..fabrica import instrumento_a_dict
from ..metricas import metricas_cartera

if TYPE_CHECKING:
    from ..cartera import Cartera
    from ..mercado import Mercado
    from ..simulacion import ResultadoSimulacion

CABECERA_CSV: tuple[str, ...] = (
    "registro",
    "propietario",
    "instrumento_id",
    "cantidad",
    "precio",
    "importe",
    "tipo",
    "fecha",
    "clave",
    "valor",
)


def datos_exportacion(mercado: Mercado, cartera: Cartera) -> dict[str, Any]:
    """Foto completa y serializable de un mercado + cartera."""
    metricas = metricas_cartera(cartera, mercado)
    posiciones = [
        {
            "instrumento_id": tid,
            "cantidad": cantidad,
            "precio": mercado.precio_de(tid),
            "importe": cantidad * mercado.precio_de(tid),
        }
        for tid, cantidad in cartera.posiciones
    ]
    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mercado": {
            "nombre": mercado.nombre,
            "sesion": mercado.sesion,
            "volumen_total": mercado.volumen_total,
            "deriva": mercado.deriva,
            "instrumentos": [instrumento_a_dict(inst) for inst in mercado.instrumentos.values()],
            "sesiones": list(mercado.sesiones),
        },
        "cartera": {
            **cartera.resumen(mercado),
            "posiciones": posiciones,
            "historial": [asdict(op) for op in cartera.historial],
            "curva_valor": list(cartera.curva_valor),
        },
        "metricas": metricas.a_dict(),
    }


class Exportador(ABC):
    """Interfaz comun de los exportadores (Strategy)."""

    formato: str = "base"
    extension: str = "txt"

    @abstractmethod
    def exportar(self, datos: dict[str, Any], ruta: str | Path) -> Path: ...

    def _destino(self, ruta: str | Path) -> Path:
        destino = Path(ruta)
        if destino.is_dir():
            return destino / f"resultados_cartera.{self.extension}"
        if not destino.suffix:
            return destino.with_suffix(f".{self.extension}")
        return destino


class ExportadorJSON(Exportador):
    """Volcado completo en JSON (datos anidados y legibles)."""

    formato = "json"
    extension = "json"

    def exportar(self, datos: dict[str, Any], ruta: str | Path) -> Path:
        destino = self._destino(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return destino


class ExportadorCSV(Exportador):
    """Volcado tabular (una fila por resumen, posicion, operacion o precio)."""

    formato = "csv"
    extension = "csv"

    def exportar(self, datos: dict[str, Any], ruta: str | Path) -> Path:
        destino = self._destino(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        filas = list(self._filas(datos))
        with destino.open("w", newline="", encoding="utf-8") as fichero:
            escritor = csv.DictWriter(fichero, fieldnames=CABECERA_CSV, lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(filas)
        return destino

    def _filas(self, datos: dict[str, Any]) -> list[dict[str, Any]]:
        cartera = datos.get("cartera", {})
        propietario = cartera.get("propietario", "")
        filas: list[dict[str, Any]] = []

        for clave, valor in datos.get("metricas", {}).items():
            filas.append(
                {
                    "registro": "metrica",
                    "propietario": propietario,
                    "clave": clave,
                    "valor": valor,
                }
            )
        for clave in (
            "capital_inicial",
            "efectivo",
            "comision",
            "valor_invertido",
            "valor_total",
            "operaciones",
        ):
            filas.append(
                {
                    "registro": "resumen",
                    "propietario": propietario,
                    "clave": clave,
                    "valor": cartera.get(clave, ""),
                }
            )
        for posicion in cartera.get("posiciones", []):
            filas.append(
                {
                    "registro": "posicion",
                    "propietario": propietario,
                    "instrumento_id": posicion["instrumento_id"],
                    "cantidad": posicion["cantidad"],
                    "precio": posicion["precio"],
                    "importe": posicion["importe"],
                }
            )
        for op in cartera.get("historial", []):
            filas.append(
                {
                    "registro": "operacion",
                    "propietario": propietario,
                    "instrumento_id": op["instrumento_id"],
                    "cantidad": op["cantidad"],
                    "precio": op["precio_ejecucion"],
                    "importe": op["cantidad"] * op["precio_ejecucion"],
                    "tipo": op["tipo"],
                    "fecha": op["fecha"],
                }
            )
        for sesion in datos.get("mercado", {}).get("sesiones", []):
            for tid, precio in sesion.get("precios", {}).items():
                filas.append(
                    {
                        "registro": "precio_sesion",
                        "propietario": propietario,
                        "instrumento_id": tid,
                        "precio": precio,
                        "fecha": f"s{int(sesion['numero']):04d}",
                    }
                )
        return filas


#: Registro de exportadores disponibles.
EXPORTADORES: dict[str, type[Exportador]] = {
    ExportadorJSON.formato: ExportadorJSON,
    ExportadorCSV.formato: ExportadorCSV,
}


def formatos_disponibles() -> tuple[str, ...]:
    return tuple(sorted(EXPORTADORES))


def crear_exportador(formato: str) -> Exportador:
    if not isinstance(formato, str) or not formato.strip():
        raise FormatoNoSoportado("el formato no puede estar vacio")
    clase = EXPORTADORES.get(formato.strip().lower())
    if clase is None:
        raise FormatoNoSoportado(
            f"formato no soportado: {formato!r} (validos: {formatos_disponibles()})"
        )
    return clase()


def exportar_resultados(
    mercado: Mercado,
    cartera: Cartera,
    ruta: str | Path,
    formato: str = "json",
) -> Path:
    """Exporta cartera, operaciones, sesiones y metricas en ``formato``."""
    datos = datos_exportacion(mercado, cartera)
    return crear_exportador(formato).exportar(datos, ruta)


def exportar_simulacion(
    resultado: ResultadoSimulacion,
    ruta: str | Path,
) -> Path:
    """Exporta el resultado de una simulacion a JSON."""
    destino = Path(ruta)
    if not destino.suffix:
        destino = destino.with_suffix(".json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(resultado.a_dict(), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return destino


__all__ = [
    "CABECERA_CSV",
    "EXPORTADORES",
    "Exportador",
    "ExportadorCSV",
    "ExportadorJSON",
    "crear_exportador",
    "datos_exportacion",
    "exportar_resultados",
    "exportar_simulacion",
    "formatos_disponibles",
]
