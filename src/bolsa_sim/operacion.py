"""``Operacion``: registro inmutable de una operacion sobre un instrumento.

Atributos (5):

* ``fecha`` (str "YYYY-MM-DD HH:MM").
* ``instrumento_id`` (str): referencia por id al instrumento operado.
* ``cantidad`` (int ``> 0``).
* ``precio_ejecucion`` (float ``> 0``).
* ``tipo`` (str): ``"compra"`` o ``"venta"``.

Es un value object (no tiene logica, no muta, dos operaciones son
iguales si todos sus campos coinciden). La razon de que sea inmutable
es **append-only**: nunca se modifica una operacion ya registrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

TIPOS_VALIDOS: frozenset[str] = frozenset({"compra", "venta"})


@dataclass(frozen=True, slots=True)
class Operacion:
    """Una ejecucion del libro de operaciones. Inmutable."""

    fecha: str
    instrumento_id: str
    cantidad: int
    precio_ejecucion: float
    tipo: str

    def __post_init__(self) -> None:
        if not isinstance(self.fecha, str) or not self.fecha.strip():
            raise ValueError("fecha no puede estar vacia")
        if not isinstance(self.instrumento_id, str) or not self.instrumento_id.strip():
            raise ValueError("instrumento_id no puede estar vacio")
        if (
            isinstance(self.cantidad, bool)
            or not isinstance(self.cantidad, int)
            or self.cantidad <= 0
        ):
            raise ValueError("cantidad debe ser un entero > 0")
        if (
            not isinstance(self.precio_ejecucion, (int, float))
            or isinstance(self.precio_ejecucion, bool)
            or not isfinite(float(self.precio_ejecucion))
            or float(self.precio_ejecucion) <= 0
        ):
            raise ValueError("precio_ejecucion debe ser un numero finito > 0")
        if self.tipo not in TIPOS_VALIDOS:
            raise ValueError(
                f"tipo debe ser uno de {sorted(TIPOS_VALIDOS)}, recibido {self.tipo!r}"
            )

    @property
    def importe_bruto(self) -> float:
        """Cantidad multiplicada por precio unitario."""
        return float(self.cantidad) * float(self.precio_ejecucion)

    @property
    def signo(self) -> int:
        return 1 if self.tipo == "compra" else -1

    def mostrar(self) -> None:
        """Imprime la operacion en formato legible."""
        print(
            f"[Operacion] {self.fecha} {self.tipo.upper():<5} "
            f"{self.cantidad:>6} x {self.instrumento_id:<8} "
            f"a {self.precio_ejecucion:.2f} EUR (bruto={self.importe_bruto:.2f})"
        )

    def __repr__(self) -> str:
        return (
            f"Operacion(fecha={self.fecha!r}, tipo={self.tipo!r}, "
            f"instrumento_id={self.instrumento_id!r}, cantidad={self.cantidad}, "
            f"precio_ejecucion={self.precio_ejecucion})"
        )
