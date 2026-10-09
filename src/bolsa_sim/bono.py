"""``Bono``: instrumento de renta fija (hereda de ``InstrumentoBase``).

Anade a la base tres atributos propios y sobrescribe el comportamiento
polimorfico:

* ``cupon_anual`` (float en ``[0, 1]``): tipo de interes anual del
  cupon (``0.04`` = 4 %).
* ``valor_nominal`` (float ``> 0``): principal del bono (p. ej. 1000).
* ``vencimiento`` (int ``> 0``): anos hasta el vencimiento.

Los tres se validan con ``@property`` + ``@setter``. La clase demuestra
que una subclase puede **reutilizar** ``__init__`` del padre y a la vez
fijar sus propios invariantes.
"""

from __future__ import annotations

from math import isfinite

from .instrumento import InstrumentoBase


class Bono(InstrumentoBase):
    """Bono con cupon anual, valor nominal y vencimiento."""

    tipo: str = "bono"

    def __init__(
        self,
        id: str,
        nombre: str,
        simbolo: str,
        volatilidad: float,
        precio_base: float,
        *,
        cupon_anual: float = 0.04,
        valor_nominal: float = 1_000.0,
        vencimiento: int = 10,
    ) -> None:
        super().__init__(id, nombre, simbolo, volatilidad, precio_base)
        self.cupon_anual = cupon_anual
        self.valor_nominal = valor_nominal
        self.vencimiento = vencimiento

    # ---- propiedades propias ---------------------------------------------
    @property
    def cupon_anual(self) -> float:
        return self._cupon_anual

    @cupon_anual.setter
    def cupon_anual(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("cupon_anual debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0 or v > 1:
            raise ValueError(f"cupon_anual debe estar en [0, 1] (recibido {v})")
        self._cupon_anual = v

    @property
    def valor_nominal(self) -> float:
        return self._valor_nominal

    @valor_nominal.setter
    def valor_nominal(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("valor_nominal debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v <= 0:
            raise ValueError(f"valor_nominal debe ser > 0 (recibido {v})")
        self._valor_nominal = v

    @property
    def vencimiento(self) -> int:
        return self._vencimiento

    @vencimiento.setter
    def vencimiento(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValueError("vencimiento debe ser un entero > 0 (anos)")
        self._vencimiento = valor

    # ---- comportamiento polimorfico --------------------------------------
    def cupon_anual_eur(self) -> float:
        """Importe del cupon anual: ``cupon_anual * valor_nominal``."""
        return self._cupon_anual * self._valor_nominal

    def flujo_anual(self) -> float:
        """Un bono paga cupones: flujo = ``cupon_anual * valor_nominal``."""
        return self.cupon_anual_eur()

    def rendimiento_actual(self, precio: float | None = None) -> float:
        """Cupon anual entre el precio de compra (rentabilidad corriente)."""
        ref = float(self.precio_base if precio is None else precio)
        if ref <= 0:
            raise ValueError("precio debe ser > 0 para calcular el rendimiento")
        return self.cupon_anual_eur() / ref

    def mostrar(self) -> None:
        """Reutiliza el formato de la base y anade los campos de bono."""
        super().mostrar()
        print(
            f"   cupon_anual={self._cupon_anual:.4f}  "
            f"valor_nominal={self._valor_nominal:.2f}  "
            f"vencimiento={self._vencimiento}a  tipo={self.tipo!r}"
        )

    def __repr__(self) -> str:
        return (
            f"Bono(id={self.id!r}, simbolo={self.simbolo!r}, "
            f"nombre={self.nombre!r}, cupon_anual={self._cupon_anual}, "
            f"valor_nominal={self._valor_nominal}, "
            f"volatilidad={self._volatilidad}, precio_base={self._precio_base}, "
            f"vencimiento={self._vencimiento})"
        )
