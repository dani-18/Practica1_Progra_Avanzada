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
"""

from __future__ import annotations

from math import isfinite
from typing import TYPE_CHECKING

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
    ) -> None:
        if not isinstance(propietario, str) or not propietario.strip():
            raise ValueError("propietario no puede estar vacio")
        self.propietario: str = propietario.strip()
        self.efectivo = efectivo
        self.comision = comision
        # Internos: se exponen de forma inmutable.
        self._inversiones: dict[str, int] = {}
        self._historial: list[Operacion] = []

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
            raise ValueError(f"efectivo debe ser un numero finito >= 0 (recibido {v})")
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
            raise ValueError(f"comision debe ser un numero finito >= 0 (recibido {v})")
        self._comision = v

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

    # ---- API del dominio -------------------------------------------------
    def invertir(
        self,
        mercado: Mercado,
        instrumento_id: str,
        cantidad: int,
        precio: float,
        fecha: str,
    ) -> Operacion | None:
        """Compra ``cantidad`` unidades. ``None`` si no llega el efectivo."""
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("cantidad debe ser un entero > 0")
        if not isinstance(precio, (int, float)) or isinstance(precio, bool):
            raise TypeError("precio debe ser un numero")
        coste = float(cantidad) * float(precio) + self._comision
        if coste > self._efectivo:
            return None
        op = Operacion(
            fecha=fecha,
            instrumento_id=instrumento_id,
            cantidad=cantidad,
            precio_ejecucion=float(precio),
            tipo="compra",
        )
        self._inversiones[instrumento_id] = self._inversiones.get(instrumento_id, 0) + cantidad
        self._efectivo -= coste
        self._historial.append(op)
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
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("cantidad debe ser un entero > 0")
        if not isinstance(precio, (int, float)) or isinstance(precio, bool):
            raise TypeError("precio debe ser un numero")
        tenencia = self._inversiones.get(instrumento_id, 0)
        if cantidad > tenencia:
            return None
        ingreso = float(cantidad) * float(precio) - self._comision
        op = Operacion(
            fecha=fecha,
            instrumento_id=instrumento_id,
            cantidad=cantidad,
            precio_ejecucion=float(precio),
            tipo="venta",
        )
        nuevo = tenencia - cantidad
        if nuevo == 0:
            del self._inversiones[instrumento_id]
        else:
            self._inversiones[instrumento_id] = nuevo
        self._efectivo += ingreso
        self._historial.append(op)
        return op

    def valor_total(self, mercado: Mercado) -> float:
        """Efectivo + valor liquidativo de las posiciones a precio actual."""
        total = self._efectivo
        for tid, cantidad in self._inversiones.items():
            precio = mercado.precio_de(tid)
            total += cantidad * float(precio)
        return total

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
