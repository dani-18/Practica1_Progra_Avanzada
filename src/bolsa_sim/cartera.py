"""``Cartera``: composicion por asociacion con ``Operacion`` y un ``Mercado``.

Atributos (5):

* ``propietario`` (str): nombre del titular, no vacio.
* ``efectivo`` (float ``>= 0``): dinero disponible en EUR.
* ``_inversiones`` (dict ``{instrumento_id: cantidad}``): estado
  abierto por instrumento (interno, mutable a proposito).
* ``comision`` (float ``>= 0``): comision por operacion.
* ``_historial`` (list ``[Operacion]``): operaciones ejecutadas, en
  orden. No se expone mutable fuera.

Los atributos ``efectivo`` y ``comision`` tienen ``@property``/setter
con validacion. Las posiciones y las operaciones se manipulan a traves
de metodos (``invertir``, ``desinvertir``, ``valor_total``).

La cartera puede recibir opcionalmente un ``repositorio`` con la interfaz
``guardar_cartera``/``guardar_posiciones``/``guardar_operacion``. Asi la
persistencia se inyecta sin acoplar el dominio a SQLite (patron
*repository* + inyeccion de dependencias). Los metodos ``comprar`` y
``vender`` son las variantes estrictas que lanzan excepciones de dominio.
"""

from __future__ import annotations

from math import isfinite
from typing import TYPE_CHECKING, Any

from .excepciones import (
    DatosInvalidos,
    FondosInsuficientes,
    InstrumentoDesconocido,
    OperacionInvalida,
    PosicionInsuficiente,
)
from .operacion import Operacion

if TYPE_CHECKING:
    from .mercado import Mercado


class Cartera:
    """Cartera de inversion con efectivo, posiciones e historial."""

    def __init__(
        self,
        propietario: str,
        efectivo: float = 0.0,
        comision: float = 0.0,
        *,
        repositorio: Any | None = None,
    ) -> None:
        if not isinstance(propietario, str) or not propietario.strip():
            raise DatosInvalidos("propietario no puede estar vacio")
        self.propietario: str = propietario.strip()
        self.efectivo = efectivo
        self.comision = comision
        self._capital_inicial = float(efectivo)
        # Internos: se exponen de forma inmutable.
        self._inversiones: dict[str, int] = {}
        self._historial: list[Operacion] = []
        self._curva_valor: list[float] = (
            [self._capital_inicial] if self._capital_inicial > 0 else []
        )
        self._repositorio = repositorio

    @classmethod
    def desde_estado(
        cls,
        propietario: str,
        efectivo: float,
        comision: float,
        posiciones: dict[str, int],
        historial: list[Operacion] | tuple[Operacion, ...],
        *,
        capital_inicial: float | None = None,
        curva: list[float] | tuple[float, ...] | None = None,
        repositorio: Any | None = None,
    ) -> Cartera:
        """Reconstruye una cartera desde un almacen (SQLite, JSON...)."""
        cartera = cls(propietario, efectivo, comision, repositorio=repositorio)
        if capital_inicial is not None:
            cartera._capital_inicial = float(capital_inicial)
            cartera._curva_valor = (
                [cartera._capital_inicial] if cartera._capital_inicial > 0 else []
            )
        if curva:
            valores = [float(v) for v in curva if float(v) > 0]
            if valores:
                cartera._curva_valor = valores
        for tid, cantidad in posiciones.items():
            if cantidad > 0:
                cartera._inversiones[str(tid).upper()] = int(cantidad)
        cartera._historial = list(historial)
        return cartera

    # ---- properties ------------------------------------------------------
    @property
    def efectivo(self) -> float:
        return self._efectivo

    @efectivo.setter
    def efectivo(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("efectivo debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0:
            raise DatosInvalidos(f"efectivo debe ser un numero finito >= 0 (recibido {v})")
        self._efectivo = v

    @property
    def comision(self) -> float:
        return self._comision

    @comision.setter
    def comision(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("comision debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0:
            raise DatosInvalidos(f"comision debe ser un numero finito >= 0 (recibido {v})")
        self._comision = v

    @property
    def capital_inicial(self) -> float:
        return self._capital_inicial

    @property
    def posiciones(self) -> tuple[tuple[str, int], ...]:
        """Vista inmutable de las posiciones (instrumento_id, cantidad)."""
        return tuple(self._inversiones.items())

    @property
    def historial(self) -> tuple[Operacion, ...]:
        return tuple(self._historial)

    @property
    def total_operaciones(self) -> int:
        return len(self._historial)

    @property
    def curva_valor(self) -> tuple[float, ...]:
        """Serie de valor liquidativo anotada por la simulacion."""
        return tuple(self._curva_valor)

    @property
    def repositorio(self) -> Any | None:
        return self._repositorio

    @repositorio.setter
    def repositorio(self, valor: Any | None) -> None:
        self._repositorio = valor

    # ---- API del dominio -------------------------------------------------
    def posicion(self, instrumento_id: str) -> int:
        return self._inversiones.get(str(instrumento_id).upper(), 0)

    def invertir(
        self,
        mercado: Mercado,
        instrumento_id: str,
        cantidad: int,
        precio: float,
        fecha: str,
    ) -> Operacion | None:
        """Compra ``cantidad`` unidades. ``None`` si no llega el efectivo."""
        self._validar_orden(mercado, instrumento_id, cantidad, precio)
        coste = float(cantidad) * float(precio) + self._comision
        if coste > self._efectivo:
            return None
        op = Operacion(
            fecha=fecha,
            instrumento_id=str(instrumento_id).upper(),
            cantidad=cantidad,
            precio_ejecucion=float(precio),
            tipo="compra",
        )
        clave = str(instrumento_id).upper()
        self._inversiones[clave] = self._inversiones.get(clave, 0) + cantidad
        self._efectivo -= coste
        self._historial.append(op)
        self._persistir(op)
        return op

    def desinvertir(
        self,
        mercado: Mercado,
        instrumento_id: str,
        cantidad: int,
        precio: float,
        fecha: str,
    ) -> Operacion | None:
        """Vende ``cantidad`` unidades. ``None`` si no hay saldo suficiente."""
        self._validar_orden(mercado, instrumento_id, cantidad, precio)
        clave = str(instrumento_id).upper()
        tenencia = self._inversiones.get(clave, 0)
        if cantidad > tenencia:
            return None
        ingreso = float(cantidad) * float(precio) - self._comision
        op = Operacion(
            fecha=fecha,
            instrumento_id=clave,
            cantidad=cantidad,
            precio_ejecucion=float(precio),
            tipo="venta",
        )
        nuevo = tenencia - cantidad
        if nuevo == 0:
            del self._inversiones[clave]
        else:
            self._inversiones[clave] = nuevo
        self._efectivo += ingreso
        self._historial.append(op)
        self._persistir(op)
        return op

    def comprar(
        self,
        mercado: Mercado,
        instrumento_id: str,
        cantidad: int,
        precio: float | None = None,
        fecha: str | None = None,
    ) -> Operacion:
        """Variante estricta de ``invertir``: lanza ``FondosInsuficientes``."""
        clave = str(instrumento_id).upper()
        precio_final = mercado.precio_de(clave) if precio is None else float(precio)
        op = self.invertir(
            mercado,
            clave,
            cantidad,
            precio_final,
            fecha or f"s{mercado.sesion:04d}",
        )
        if op is None:
            raise FondosInsuficientes(
                f"efectivo insuficiente: se necesitan "
                f"{cantidad * precio_final + self._comision:.2f} EUR y hay {self._efectivo:.2f}"
            )
        return op

    def vender(
        self,
        mercado: Mercado,
        instrumento_id: str,
        cantidad: int,
        precio: float | None = None,
        fecha: str | None = None,
    ) -> Operacion:
        """Variante estricta de ``desinvertir``: lanza ``PosicionInsuficiente``."""
        clave = str(instrumento_id).upper()
        precio_final = mercado.precio_de(clave) if precio is None else float(precio)
        op = self.desinvertir(
            mercado,
            clave,
            cantidad,
            precio_final,
            fecha or f"s{mercado.sesion:04d}",
        )
        if op is None:
            raise PosicionInsuficiente(
                f"posicion insuficiente de {instrumento_id!r}: "
                f"hay {self.posicion(instrumento_id)} y se piden {cantidad}"
            )
        return op

    def valor_total(self, mercado: Mercado) -> float:
        """Efectivo + valor liquidativo de las posiciones a precio actual."""
        total = self._efectivo
        for tid, cantidad in self._inversiones.items():
            total += cantidad * mercado.precio_de(tid)
        return total

    def valor_invertido(self, mercado: Mercado) -> float:
        """Valor de mercado de las posiciones, sin contar el efectivo."""
        return sum(
            cantidad * mercado.precio_de(tid) for tid, cantidad in self._inversiones.items()
        )

    def anotar_valor(self, valor: float | None = None, mercado: Mercado | None = None) -> float:
        """Anade un punto a la curva de valor (patrimonio) de la cartera.

        Se puede pasar el valor ya calculado o el mercado para calcularlo.
        Devuelve el valor anotado.
        """
        if valor is None:
            if mercado is None:
                raise DatosInvalidos("indica 'valor' o 'mercado' para anotar la curva")
            valor = self.valor_total(mercado)
        v = float(valor)
        if not isfinite(v) or v <= 0:
            raise DatosInvalidos("el valor de la cartera debe ser finito y > 0")
        self._curva_valor.append(v)
        return v

    def resumen(self, mercado: Mercado) -> dict[str, float | int | str]:
        """Resumen plano pensado para GUI y exportadores."""
        return {
            "propietario": self.propietario,
            "capital_inicial": self._capital_inicial,
            "efectivo": self._efectivo,
            "comision": self._comision,
            "posiciones": len(self._inversiones),
            "valor_invertido": self.valor_invertido(mercado),
            "valor_total": self.valor_total(mercado),
            "operaciones": len(self._historial),
        }

    # ---- internos --------------------------------------------------------
    def _validar_orden(
        self,
        mercado: Mercado,
        instrumento_id: str,
        cantidad: int,
        precio: float,
    ) -> None:
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise OperacionInvalida("cantidad debe ser un entero > 0")
        if not isinstance(precio, (int, float)) or isinstance(precio, bool):
            raise DatosInvalidos("precio debe ser un numero")
        if not isfinite(float(precio)) or float(precio) <= 0:
            raise DatosInvalidos("precio debe ser un numero finito > 0")
        if str(instrumento_id).upper() not in mercado.instrumentos:
            raise InstrumentoDesconocido(f"instrumento {instrumento_id!r} no esta en el mercado")

    def _persistir(self, op: Operacion) -> None:
        if self._repositorio is None:
            return
        self._repositorio.guardar_cartera(self)
        self._repositorio.guardar_posiciones(self.propietario, dict(self._inversiones))
        self._repositorio.guardar_operacion(self.propietario, op)

    # ---- print ------------------------------------------------------------
    def mostrar(self) -> None:
        """Imprime el estado actual de la cartera."""
        print(
            f"[Cartera] {self.propietario!r}: "
            f"efectivo={self._efectivo:.2f} EUR  "
            f"comision={self._comision:.2f}  "
            f"posiciones={len(self._inversiones)}  "
            f"ops={len(self._historial)}"
        )
        for tid, qty in self._inversiones.items():
            print(f"   - {tid}: {qty}")
        for op in self._historial:
            print(f"   . {op!r}")

    def __repr__(self) -> str:
        return (
            f"Cartera(propietario={self.propietario!r}, "
            f"efectivo={self._efectivo:.2f}, comision={self._comision:.2f}, "
            f"posiciones={len(self._inversiones)}, ops={len(self._historial)})"
        )
