"""Repositorios de persistencia: interfaz comun y backends (Strategy).

La interfaz :class:`Repositorio` define el contrato que consumen el dominio
y los servicios. Hay tres implementaciones intercambiables:

* :class:`RepositorioMemoria` - rapida, usada en tests y simulaciones.
* :class:`RepositorioSQLite` - almacen principal (stdlib ``sqlite3``).
* :class:`RepositorioJSON` - fichero JSON, util para compartir resultados.

El libro de operaciones es *append-only*: ``guardar_operacion`` solo inserta
y ``sincronizar_operaciones`` verifica que el prefijo guardado coincide antes
de anadir las nuevas. Nunca se reescribe una operacion existente.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..cartera import Cartera
from ..excepciones import ErrorPersistencia
from ..fabrica import instrumento_a_dict
from ..instrumento import InstrumentoBase
from ..operacion import Operacion
from .db import conectar, inicializar_esquema, transaccion

#: Campos comunes que no se guardan en la columna ``detalle``.
_CAMPOS_BASE = {"tipo", "id", "nombre", "simbolo", "volatilidad", "precio_base"}


def _operacion_a_dict(op: Operacion) -> dict[str, Any]:
    return asdict(op)


def _dict_a_operacion(datos: Mapping[str, Any]) -> Operacion:
    return Operacion(
        fecha=str(datos["fecha"]),
        instrumento_id=str(datos["instrumento_id"]),
        cantidad=int(datos["cantidad"]),
        precio_ejecucion=float(datos["precio_ejecucion"]),
        tipo=str(datos["tipo"]),
    )


def _instrumento_a_filas(inst: InstrumentoBase) -> tuple[Any, ...]:
    datos = instrumento_a_dict(inst)
    detalle = {k: v for k, v in datos.items() if k not in _CAMPOS_BASE}
    return (
        datos["id"],
        datos["nombre"],
        datos["simbolo"],
        datos["tipo"],
        datos["volatilidad"],
        datos["precio_base"],
        json.dumps(detalle, ensure_ascii=False),
    )


def _fila_a_dict(fila: Mapping[str, Any]) -> dict[str, Any]:
    datos = {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "simbolo": fila["simbolo"],
        "tipo": fila["tipo"],
        "volatilidad": fila["volatilidad"],
        "precio_base": fila["precio_base"],
    }
    detalle = fila["detalle"]
    if detalle:
        try:
            datos.update(json.loads(detalle))
        except json.JSONDecodeError as exc:  # pragma: no cover - datos corruptos
            raise ErrorPersistencia(f"detalle de instrumento corrupto: {exc}") from exc
    return datos


class Repositorio(ABC):
    """Contrato de almacenamiento que consume el dominio."""

    # ---- instrumentos ----------------------------------------------------
    @abstractmethod
    def guardar_instrumentos(self, instrumentos: Iterable[InstrumentoBase]) -> None: ...

    @abstractmethod
    def listar_instrumentos(self) -> list[dict[str, Any]]: ...

    # ---- carteras --------------------------------------------------------
    @abstractmethod
    def guardar_cartera(self, cartera: Cartera) -> None: ...

    @abstractmethod
    def cargar_cartera(self, propietario: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def listar_carteras(self) -> list[str]: ...

    @abstractmethod
    def guardar_posiciones(self, propietario: str, posiciones: Mapping[str, int]) -> None: ...

    # ---- libro de operaciones (append-only) ------------------------------
    @abstractmethod
    def guardar_operacion(self, propietario: str, operacion: Operacion) -> None: ...

    @abstractmethod
    def listar_operaciones(self, propietario: str) -> list[Operacion]: ...

    def sincronizar_operaciones(self, propietario: str, historial: Iterable[Operacion]) -> int:
        """Anade solo las operaciones nuevas, comprobando el prefijo existente.

        Devuelve cuantas operaciones se han anadido. Si el historial en
        memoria no es una extension del guardado se lanza ``ErrorPersistencia``
        para no perder ni reescribir el libro.
        """
        nuevas = list(historial)
        existentes = self.listar_operaciones(propietario)
        if len(existentes) > len(nuevas) or existentes != nuevas[: len(existentes)]:
            raise ErrorPersistencia(
                "el historial en memoria no es una extension del libro persistido"
            )
        anadidas = 0
        for op in nuevas[len(existentes) :]:
            self.guardar_operacion(propietario, op)
            anadidas += 1
        return anadidas

    # ---- sesiones de mercado --------------------------------------------
    @abstractmethod
    def guardar_sesion(
        self,
        mercado: str,
        numero: int,
        volumen: int,
        precios: Mapping[str, float],
    ) -> None: ...

    @abstractmethod
    def listar_sesiones(self, mercado: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def cerrar(self) -> None:
        """Libera recursos (no-op salvo en backends con fichero)."""


class RepositorioMemoria(Repositorio):
    """Backend en memoria, seguro para usarse desde varios hilos."""

    def __init__(self) -> None:
        self._instrumentos: dict[str, dict[str, Any]] = {}
        self._carteras: dict[str, dict[str, Any]] = {}
        self._sesiones: dict[str, dict[int, dict[str, Any]]] = {}
        self._lock = threading.RLock()

    # ---- estado serializable --------------------------------------------
    def estado(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(
                {
                    "instrumentos": self._instrumentos,
                    "carteras": self._carteras,
                    "sesiones": self._sesiones,
                }
            )

    def cargar_estado(self, estado: Mapping[str, Any]) -> None:
        with self._lock:
            self._instrumentos = copy.deepcopy(dict(estado.get("instrumentos", {})))
            self._carteras = copy.deepcopy(dict(estado.get("carteras", {})))
            sesiones: dict[str, dict[int, dict[str, Any]]] = {}
            for mercado, por_numero in dict(estado.get("sesiones", {})).items():
                sesiones[str(mercado)] = {
                    int(numero): copy.deepcopy(datos) for numero, datos in dict(por_numero).items()
                }
            self._sesiones = sesiones

    def _persistir(self) -> None:
        """Hook para backends con fichero (no-op en memoria)."""

    # ---- instrumentos ----------------------------------------------------
    def guardar_instrumentos(self, instrumentos: Iterable[InstrumentoBase]) -> None:
        with self._lock:
            for inst in instrumentos:
                self._instrumentos[inst.id] = instrumento_a_dict(inst)
            self._persistir()

    def listar_instrumentos(self) -> list[dict[str, Any]]:
        with self._lock:
            return [copy.deepcopy(self._instrumentos[tid]) for tid in sorted(self._instrumentos)]

    # ---- carteras --------------------------------------------------------
    def guardar_cartera(self, cartera: Cartera) -> None:
        with self._lock:
            actual = self._carteras.setdefault(
                cartera.propietario,
                {"posiciones": {}, "operaciones": []},
            )
            actual.update(
                {
                    "propietario": cartera.propietario,
                    "efectivo": cartera.efectivo,
                    "comision": cartera.comision,
                    "capital_inicial": cartera.capital_inicial,
                    "curva_valor": list(cartera.curva_valor),
                }
            )
            self._persistir()

    def cargar_cartera(self, propietario: str) -> dict[str, Any] | None:
        with self._lock:
            datos = self._carteras.get(propietario)
            return None if datos is None else copy.deepcopy(datos)

    def listar_carteras(self) -> list[str]:
        with self._lock:
            return sorted(self._carteras)

    def guardar_posiciones(self, propietario: str, posiciones: Mapping[str, int]) -> None:
        with self._lock:
            datos = self._carteras.setdefault(
                propietario,
                {
                    "propietario": propietario,
                    "efectivo": 0.0,
                    "comision": 0.0,
                    "capital_inicial": 0.0,
                    "curva_valor": [],
                    "operaciones": [],
                },
            )
            datos["posiciones"] = {
                str(tid): int(cantidad) for tid, cantidad in posiciones.items() if cantidad > 0
            }
            self._persistir()

    # ---- operaciones -----------------------------------------------------
    def guardar_operacion(self, propietario: str, operacion: Operacion) -> None:
        with self._lock:
            datos = self._carteras.setdefault(
                propietario,
                {
                    "propietario": propietario,
                    "efectivo": 0.0,
                    "comision": 0.0,
                    "capital_inicial": 0.0,
                    "curva_valor": [],
                    "posiciones": {},
                    "operaciones": [],
                },
            )
            datos.setdefault("operaciones", []).append(_operacion_a_dict(operacion))
            self._persistir()

    def listar_operaciones(self, propietario: str) -> list[Operacion]:
        with self._lock:
            datos = self._carteras.get(propietario, {})
            return [_dict_a_operacion(op) for op in datos.get("operaciones", [])]

    # ---- sesiones ---------------------------------------------------------
    def guardar_sesion(
        self,
        mercado: str,
        numero: int,
        volumen: int,
        precios: Mapping[str, float],
    ) -> None:
        with self._lock:
            self._sesiones.setdefault(mercado, {})[int(numero)] = {
                "numero": int(numero),
                "volumen": int(volumen),
                "precios": {str(tid): float(p) for tid, p in precios.items()},
            }
            self._persistir()

    def listar_sesiones(self, mercado: str) -> list[dict[str, Any]]:
        with self._lock:
            por_numero = self._sesiones.get(mercado, {})
            return [copy.deepcopy(por_numero[n]) for n in sorted(por_numero)]

    def cerrar(self) -> None:
        """El backend en memoria no necesita liberar recursos."""


class RepositorioSQLite(Repositorio):
    """Backend principal sobre SQLite (biblioteca estandar)."""

    def __init__(self, ruta: str | Path = ":memory:") -> None:
        self.ruta = str(ruta)
        self._conexion = conectar(ruta)
        inicializar_esquema(self._conexion)

    @property
    def conexion(self) -> sqlite3.Connection:
        return self._conexion

    # ---- instrumentos ----------------------------------------------------
    def guardar_instrumentos(self, instrumentos: Iterable[InstrumentoBase]) -> None:
        with transaccion(self._conexion) as conn:
            for inst in instrumentos:
                conn.execute(
                    "INSERT INTO instrumento "
                    "(id, nombre, simbolo, tipo, volatilidad, precio_base, detalle) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET "
                    "nombre=excluded.nombre, simbolo=excluded.simbolo, tipo=excluded.tipo, "
                    "volatilidad=excluded.volatilidad, precio_base=excluded.precio_base, "
                    "detalle=excluded.detalle",
                    _instrumento_a_filas(inst),
                )

    def listar_instrumentos(self) -> list[dict[str, Any]]:
        try:
            filas = self._conexion.execute(
                "SELECT id, nombre, simbolo, tipo, volatilidad, precio_base, detalle "
                "FROM instrumento ORDER BY id"
            ).fetchall()
        except sqlite3.Error as exc:
            raise ErrorPersistencia(f"no se pudieron leer instrumentos: {exc}") from exc
        return [_fila_a_dict(fila) for fila in filas]

    # ---- carteras --------------------------------------------------------
    def guardar_cartera(self, cartera: Cartera) -> None:
        curva = json.dumps(list(cartera.curva_valor))
        with transaccion(self._conexion) as conn:
            conn.execute(
                "INSERT INTO cartera "
                "(propietario, efectivo, comision, capital_inicial, curva_valor) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(propietario) DO UPDATE SET "
                "efectivo=excluded.efectivo, comision=excluded.comision, "
                "capital_inicial=excluded.capital_inicial, curva_valor=excluded.curva_valor",
                (
                    cartera.propietario,
                    cartera.efectivo,
                    cartera.comision,
                    cartera.capital_inicial,
                    curva,
                ),
            )

    def _id_cartera(self, propietario: str) -> int:
        fila = self._conexion.execute(
            "SELECT id FROM cartera WHERE propietario = ?", (propietario,)
        ).fetchone()
        if fila is None:
            raise ErrorPersistencia(f"cartera {propietario!r} no existe en el almacen")
        return int(fila["id"])

    def cargar_cartera(self, propietario: str) -> dict[str, Any] | None:
        fila = self._conexion.execute(
            "SELECT id, propietario, efectivo, comision, capital_inicial, curva_valor "
            "FROM cartera WHERE propietario = ?",
            (propietario,),
        ).fetchone()
        if fila is None:
            return None
        try:
            curva = json.loads(fila["curva_valor"])
        except json.JSONDecodeError:
            curva = []
        posiciones = {
            str(p["instrumento_id"]): int(p["cantidad"])
            for p in self._conexion.execute(
                "SELECT instrumento_id, cantidad FROM posicion WHERE cartera_id = ?",
                (fila["id"],),
            )
        }
        return {
            "propietario": fila["propietario"],
            "efectivo": float(fila["efectivo"]),
            "comision": float(fila["comision"]),
            "capital_inicial": float(fila["capital_inicial"]),
            "curva_valor": curva,
            "posiciones": posiciones,
        }

    def listar_carteras(self) -> list[str]:
        return [
            str(fila["propietario"])
            for fila in self._conexion.execute(
                "SELECT propietario FROM cartera ORDER BY propietario"
            )
        ]

    def guardar_posiciones(self, propietario: str, posiciones: Mapping[str, int]) -> None:
        with transaccion(self._conexion) as conn:
            cartera_id = self._id_cartera(propietario)
            conn.execute("DELETE FROM posicion WHERE cartera_id = ?", (cartera_id,))
            conn.executemany(
                "INSERT INTO posicion (cartera_id, instrumento_id, cantidad) VALUES (?, ?, ?)",
                [
                    (cartera_id, str(tid), int(cantidad))
                    for tid, cantidad in posiciones.items()
                    if cantidad > 0
                ],
            )

    # ---- operaciones -----------------------------------------------------
    def guardar_operacion(self, propietario: str, operacion: Operacion) -> None:
        with transaccion(self._conexion) as conn:
            cartera_id = self._id_cartera(propietario)
            conn.execute(
                "INSERT INTO operacion "
                "(cartera_id, fecha, instrumento_id, cantidad, precio_ejecucion, tipo) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    cartera_id,
                    operacion.fecha,
                    operacion.instrumento_id,
                    operacion.cantidad,
                    operacion.precio_ejecucion,
                    operacion.tipo,
                ),
            )

    def listar_operaciones(self, propietario: str) -> list[Operacion]:
        filas = self._conexion.execute(
            "SELECT o.fecha, o.instrumento_id, o.cantidad, o.precio_ejecucion, o.tipo "
            "FROM operacion o JOIN cartera c ON c.id = o.cartera_id "
            "WHERE c.propietario = ? ORDER BY o.id",
            (propietario,),
        ).fetchall()
        return [_dict_a_operacion(dict(fila)) for fila in filas]

    # ---- sesiones --------------------------------------------------------
    def guardar_sesion(
        self,
        mercado: str,
        numero: int,
        volumen: int,
        precios: Mapping[str, float],
    ) -> None:
        with transaccion(self._conexion) as conn:
            conn.execute(
                "INSERT INTO sesion (mercado, numero, volumen) VALUES (?, ?, ?) "
                "ON CONFLICT(mercado, numero) DO UPDATE SET volumen=excluded.volumen",
                (mercado, int(numero), int(volumen)),
            )
            fila = conn.execute(
                "SELECT id FROM sesion WHERE mercado = ? AND numero = ?",
                (mercado, int(numero)),
            ).fetchone()
            sesion_id = int(fila["id"])
            conn.execute("DELETE FROM precio_sesion WHERE sesion_id = ?", (sesion_id,))
            conn.executemany(
                "INSERT INTO precio_sesion (sesion_id, instrumento_id, precio) "
                "VALUES (?, ?, ?)",
                [(sesion_id, str(tid), float(p)) for tid, p in precios.items()],
            )

    def listar_sesiones(self, mercado: str) -> list[dict[str, Any]]:
        sesiones = self._conexion.execute(
            "SELECT id, numero, volumen FROM sesion WHERE mercado = ? ORDER BY numero",
            (mercado,),
        ).fetchall()
        resultado: list[dict[str, Any]] = []
        for fila in sesiones:
            precios = {
                str(p["instrumento_id"]): float(p["precio"])
                for p in self._conexion.execute(
                    "SELECT instrumento_id, precio FROM precio_sesion WHERE sesion_id = ?",
                    (fila["id"],),
                )
            }
            resultado.append(
                {
                    "numero": int(fila["numero"]),
                    "volumen": int(fila["volumen"]),
                    "precios": precios,
                }
            )
        return resultado

    def cerrar(self) -> None:
        self._conexion.close()


class RepositorioJSON(RepositorioMemoria):
    """Backend en memoria que vuelca el estado completo a un fichero JSON."""

    def __init__(self, ruta: str | Path) -> None:
        super().__init__()
        self.ruta = Path(ruta)
        if self.ruta.exists():
            self._cargar()

    def _cargar(self) -> None:
        try:
            estado = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ErrorPersistencia(f"no se pudo cargar {self.ruta}: {exc}") from exc
        if not isinstance(estado, dict):
            raise ErrorPersistencia(f"{self.ruta} no contiene un estado valido")
        self.cargar_estado(estado)

    def _persistir(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(
            json.dumps(self.estado(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def cerrar(self) -> None:
        self._persistir()


__all__ = [
    "Repositorio",
    "RepositorioJSON",
    "RepositorioMemoria",
    "RepositorioSQLite",
]
