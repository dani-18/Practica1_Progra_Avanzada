"""Servicio de persistencia: guarda y reconstruye el estado completo.

El servicio conoce el dominio (``Mercado``, ``Cartera``) y el repositorio,
pero el dominio no conoce ni SQLite ni JSON. Guarda instrumentos, cartera,
posiciones, historial y sesiones en una unica operacion logica; al cargar
reconstruye la jerarquia mediante ``FabricaInstrumentos``.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from ..cartera import Cartera
from ..excepciones import ErrorPersistencia
from ..fabrica import FabricaInstrumentos
from ..logging_config import obtener_logger
from ..mercado import Mercado
from .exportadores import exportar_resultados
from .repositorios import Repositorio

if TYPE_CHECKING:
    from ..instrumento import InstrumentoBase

log = obtener_logger(__name__)


class ServicioPersistencia:
    """Fachada de alto nivel sobre un ``Repositorio``."""

    def __init__(self, repositorio: Repositorio) -> None:
        self.repositorio = repositorio

    # ---- guardar ---------------------------------------------------------
    def guardar_estado(self, mercado: Mercado, cartera: Cartera) -> None:
        """Persiste una cartera y el mercado de forma idempotente."""
        self.guardar_carteras(mercado, [cartera])

    def guardar_carteras(self, mercado: Mercado, carteras: Iterable[Cartera]) -> None:
        """Persiste el mercado una vez y todas las carteras indicadas."""
        lista = list(carteras)
        if not lista:
            raise ErrorPersistencia("no hay carteras que guardar")

        self.repositorio.guardar_instrumentos(mercado.instrumentos.values())
        for cartera in lista:
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
        log.info(
            "estado guardado: mercado=%s instrumentos=%d carteras=%d operaciones=%d sesiones=%d",
            mercado.nombre,
            len(mercado.instrumentos),
            len(lista),
            sum(len(c.historial) for c in lista),
            len(mercado.sesiones),
        )

    # ---- cargar ----------------------------------------------------------
    def cargar_mercado(self, nombre: str, *, semilla: int | None = None) -> Mercado:
        datos = self.repositorio.listar_instrumentos()
        if not datos:
            log.error("no hay instrumentos guardados en el almacen (mercado=%s)", nombre)
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
        log.info(
            "mercado cargado: nombre=%s instrumentos=%d sesiones=%d",
            nombre,
            len(instrumentos),
            len(sesiones),
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
            log.error("cartera %r no existe en el almacen", propietario)
            raise ErrorPersistencia(f"cartera {propietario!r} no existe en el almacen")
        historial = self.repositorio.listar_operaciones(propietario)
        log.info(
            "cartera cargada: propietario=%s operaciones=%d posiciones=%d",
            propietario,
            len(historial),
            len(datos.get("posiciones", {})),
        )
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

    def cargar_carteras(
        self,
        nombre_mercado: str,
        propietarios: Iterable[str] | None = None,
        *,
        semilla: int | None = None,
    ) -> tuple[Mercado, list[Cartera]]:
        """Carga el mercado y todas las carteras (o solo las indicadas)."""
        mercado = self.cargar_mercado(nombre_mercado, semilla=semilla)
        nombres = list(propietarios) if propietarios is not None else self.listar_carteras()
        carteras = [self.cargar_cartera(nombre, mercado) for nombre in nombres]
        log.info(
            "estado cargado: mercado=%s carteras=%s",
            nombre_mercado,
            ", ".join(c.propietario for c in carteras) or "ninguna",
        )
        return mercado, carteras

    def cargar_estado(
        self,
        nombre_mercado: str,
        propietario: str,
        *,
        semilla: int | None = None,
    ) -> tuple[Mercado, Cartera]:
        mercado, carteras = self.cargar_carteras(nombre_mercado, [propietario], semilla=semilla)
        return mercado, carteras[0]

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
