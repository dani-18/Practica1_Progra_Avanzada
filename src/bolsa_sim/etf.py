"""``ETF``: fondo cotizado (hereda de ``InstrumentoBase``).

Un ETF replica un indice y cobra una comision de gestion anual (TER).
Ademas de lo heredado, anade:

* ``indice`` (str): indice replicado, no vacio.
* ``comision_gestion`` (float ``>= 0``): TER anual (``0.002`` = 0,20 %).

No reparte rentas periodicas propias: hereda ``flujo_anual`` de la base
(``0.0``) para demostrar que una subclase **no** esta obligada a
sobrescribir todos los metodos, solo los que le aplican.
"""

from __future__ import annotations

from math import isfinite

from .instrumento import InstrumentoBase


class ETF(InstrumentoBase):
    """ETF que replica un indice y cobra comision de gestion."""

    tipo: str = "etf"

    def __init__(
        self,
        id: str,
        nombre: str,
        simbolo: str,
        volatilidad: float,
        precio_base: float,
        *,
        indice: str = "General",
        comision_gestion: float = 0.0,
    ) -> None:
        super().__init__(id, nombre, simbolo, volatilidad, precio_base)
        self.indice = indice
        self.comision_gestion = comision_gestion

    # ---- propiedades propias ---------------------------------------------
    @property
    def indice(self) -> str:
        return self._indice

    @indice.setter
    def indice(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError("indice no puede estar vacio")
        self._indice = valor.strip()

    @property
    def comision_gestion(self) -> float:
        return self._comision_gestion

    @comision_gestion.setter
    def comision_gestion(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("comision_gestion debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0:
            raise ValueError(f"comision_gestion debe ser un numero finito >= 0 (recibido {v})")
        self._comision_gestion = v

    # ---- comportamiento propio -------------------------------------------
    def coste_anual(self, importe: float) -> float:
        """Comision de gestion anual sobre ``importe`` invertido."""
        if not isinstance(importe, (int, float)) or isinstance(importe, bool):
            raise TypeError("importe debe ser un numero")
        return float(importe) * self._comision_gestion

    def mostrar(self) -> None:
        """Reutiliza el formato de la base y anade los campos de ETF."""
        super().mostrar()
        print(
            f"   indice={self._indice!r}  "
            f"comision_gestion={self._comision_gestion:.4f}  tipo={self.tipo!r}"
        )

    def __repr__(self) -> str:
        return (
            f"ETF(id={self.id!r}, simbolo={self.simbolo!r}, "
            f"nombre={self.nombre!r}, indice={self._indice!r}, "
            f"volatilidad={self._volatilidad}, precio_base={self._precio_base}, "
            f"comision_gestion={self._comision_gestion})"
        )
