"""``Accion``: instrumento de renta variable (hereda de ``InstrumentoBase``).

Anade a la base dos atributos propios de una accion y sobrescribe el
comportamiento polimorfico (``flujo_anual`` y ``mostrar``):

* ``sector`` (str): sector economico, no vacio.
* ``dividendo_anual`` (float ``>= 0``): dividendo bruto por accion y ano.

Ambos se validan con ``@property`` + ``@setter`` reutilizando el estilo
del Temario 1. La clase demuestra ``super().__init__`` (la parte comun
del instrumento la inicializa la clase padre) y la **sobrescritura de
metodos** (``flujo_anual``, ``mostrar``, ``__repr__``).
"""

from __future__ import annotations

from math import isfinite

from .instrumento import InstrumentoBase


class Accion(InstrumentoBase):
    """Accion con sector y dividendo anual."""

    tipo: str = "accion"

    def __init__(
        self,
        id: str,
        nombre: str,
        simbolo: str,
        volatilidad: float,
        precio_base: float,
        *,
        sector: str = "General",
        dividendo_anual: float = 0.0,
    ) -> None:
        # La parte comun la resuelve la clase padre.
        super().__init__(id, nombre, simbolo, volatilidad, precio_base)
        # Parte especifica de la subclase (usa los setters validados).
        self.sector = sector
        self.dividendo_anual = dividendo_anual

    # ---- propiedades propias ---------------------------------------------
    @property
    def sector(self) -> str:
        return self._sector

    @sector.setter
    def sector(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError("sector no puede estar vacio")
        self._sector = valor.strip()

    @property
    def dividendo_anual(self) -> float:
        return self._dividendo_anual

    @dividendo_anual.setter
    def dividendo_anual(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("dividendo_anual debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0:
            raise ValueError(f"dividendo_anual debe ser un numero finito >= 0 (recibido {v})")
        self._dividendo_anual = v

    # ---- comportamiento polimorfico --------------------------------------
    def flujo_anual(self) -> float:
        """Una accion reparte dividendos: flujo = ``dividendo_anual``."""
        return self._dividendo_anual

    def rentabilidad_por_dividendo(self, precio: float | None = None) -> float:
        """Dividendo anual entre el precio (por unidad invertida).

        Si ``precio`` es ``None`` se usa el ``precio_base`` actual.
        """
        ref = float(self.precio_base if precio is None else precio)
        if ref <= 0:
            raise ValueError("precio debe ser > 0 para calcular la rentabilidad")
        return self._dividendo_anual / ref

    def mostrar(self) -> None:
        """Reutiliza el formato de la base y anade los campos de accion."""
        super().mostrar()
        print(
            f"   sector={self._sector!r}  "
            f"dividendo_anual={self._dividendo_anual:.2f}  tipo={self.tipo!r}"
        )

    def __repr__(self) -> str:
        return (
            f"Accion(id={self.id!r}, simbolo={self.simbolo!r}, "
            f"nombre={self.nombre!r}, sector={self._sector!r}, "
            f"volatilidad={self._volatilidad}, precio_base={self._precio_base}, "
            f"dividendo_anual={self._dividendo_anual})"
        )
