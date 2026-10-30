"""Servicio de persistencia: guarda y reconstruye el estado completo.

El servicio conoce el dominio (``Mercado``, ``Cartera``) y el repositorio,
pero el dominio no conoce ni SQLite ni JSON. Guarda instrumentos, cartera,
posiciones, historial y sesiones en una unica operacion logica; al cargar
reconstruye la jerarquia mediante ``FabricaInstrumentos``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..cartera import Cartera
from ..excepciones import ErrorPersistencia
from ..fabrica import FabricaInstrumentos
from ..mercado import Mercado
from .exportadores import exportar_resultados
from .repositorios import Repositorio

if TYPE_CHECKING:
    from ..instrumento import InstrumentoBase


class ServicioPersistencia:
    """Fachada de alto nivel sobre un ``Repositorio``."""

    def __init__(self, repositorio: Repositorio) -> None:
        self.repositorio = repositorio

    # ---- guardar ---------------------------------------------------------
    def guardar_estado(self, mercado: Mercado, cartera: Cartera) -> None:
        """Persiste el estado completo de forma idempotente."""
        self.repositorio.guardar_instrumentos(mercado.instrumentos.values())
        self.repositorio.guardar_cartera(cartera)
        self.repositorio.guardar_posiciones(cartera.propietario, dict(cartera.posiciones))
        self.repositorio.sincronizar_operaciones(cartera.propietario, cartera.historial)
        for sesion in mercado.sesiones:
            self.repositorio.guardar_sesion(
                mercado.nombre,
                int(sesion["numero"]),
                int(sesion["volumen"]),
                dict(sesion["precios"]),
            )

    # ---- cargar ----------------------------------------------------------
    def cargar_mercado(self, nombre: str, *, semilla: int | None = None) -> Mercado:
        datos = self.repositorio.listar_instrumentos()
        if not datos:
            raise ErrorPersistencia("no hay instrumentos guardados en el almacen")
        fabrica = FabricaInstrumentos.por_defecto()
        instrumentos: list[InstrumentoBase] = [fabrica.desde_dict(d) for d in datos]
        mercado = Mercado(
            nombre,
            {inst.id: inst for inst in instrumentos},
            semilla=semilla,
        )
        sesiones = self.repositorio.listar_sesiones(nombre)
        if sesiones:
            ultima = sesiones[-1]
            series: dict[str, list[float]] = {}
            for sesion in sesiones:
                for tid, precio in sesion["precios"].items():
                    series.setdefault(tid, []).append(float(precio))
            mercado.restaurar_estado(
                int(ultima["numero"]),
                sum(int(s["volumen"]) for s in sesiones),
                dict(ultima["precios"]),
                series=series,
                sesiones=sesiones,
            )
        return mercado

    def cargar_cartera(
        self,
        propietario: str,
        mercado: Mercado | None = None,
        *,
        con_repositorio: bool = False,
    ) -> Cartera:
        datos = self.repositorio.cargar_cartera(propietario)
        if datos is None:
            raise ErrorPersistencia(f"cartera {propietario!r} no existe en el almacen")
        historial = self.repositorio.listar_operaciones(propietario)
        return Cartera.desde_estado(
            propietario=propietario,
            efectivo=float(datos["efectivo"]),
            comision=float(datos["comision"]),
            posiciones=dict(datos.get("posiciones", {})),
            historial=historial,
            capital_inicial=float(datos.get("capital_inicial", datos["efectivo"])),
            curva=list(datos.get("curva_valor", [])),
            repositorio=self.repositorio if con_repositorio else None,
        )

    def cargar_estado(
        self,
        nombre_mercado: str,
        propietario: str,
        *,
        semilla: int | None = None,
    ) -> tuple[Mercado, Cartera]:
        mercado = self.cargar_mercado(nombre_mercado, semilla=semilla)
        cartera = self.cargar_cartera(propietario, mercado)
        return mercado, cartera

    # ---- utilidades ------------------------------------------------------
    def listar_carteras(self) -> list[str]:
        return self.repositorio.listar_carteras()

    def exportar(
        self,
        mercado: Mercado,
        cartera: Cartera,
        ruta: str | Path,
        formato: str = "json",
    ) -> Path:
        return exportar_resultados(mercado, cartera, ruta, formato)

    def cerrar(self) -> None:
        self.repositorio.cerrar()


__all__ = ["ServicioPersistencia"]
