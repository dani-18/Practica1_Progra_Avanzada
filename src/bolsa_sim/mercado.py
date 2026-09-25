"""``Mercado``: motor de cotizaciones para un conjunto de instrumentos.

Atributos (5):

* ``nombre`` (str, no vacio).
* ``_rng_seed`` (int o ``None``): semilla para la simulacion.
* ``instrumentos`` (dict ``{id: InstrumentoBase}``).
* ``sesion`` (int ``>= 0``): contador de sesiones transcurridas.
* ``volumen_total`` (int ``>= 0``): unidades totales movidas.

La clase avanza sesiones con ``avanzar_sesion()``: cada instrumento
recibe un factor de variacion aleatorio proporcional a su
``volatilidad``, y ``sesion`` y ``volumen_total`` se incrementan con
setter validado. Los atributos inmutables fuera de la evolucion son
``nombre``, ``_rng_seed`` e ``instrumentos``.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .instrumento import InstrumentoBase

if TYPE_CHECKING:
    from .cartera import Cartera


class Mercado:
    """Motor que mantiene cotizaciones y avanza sesiones."""

    def __init__(
        self,
        nombre: str,
        instrumentos: dict[str, InstrumentoBase],
        *,
        semilla: int | None = None,
    ) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("nombre no puede estar vacio")
        if not isinstance(instrumentos, dict):
            raise TypeError("instrumentos debe ser dict")
        for tid, inst in instrumentos.items():
            if not isinstance(inst, InstrumentoBase):
                raise TypeError(f"instrumento {tid!r} no es InstrumentoBase")
        if semilla is not None and (isinstance(semilla, bool) or not isinstance(semilla, int)):
            raise TypeError("semilla debe ser int o None")

        self.nombre: str = nombre.strip()
        self.instrumentos: dict[str, InstrumentoBase] = dict(instrumentos)
        self._rng_seed: int | None = semilla
        self._rng = random.Random(semilla)
        self.sesion = 0
        self.volumen_total = 0

    @property
    def semilla(self) -> int | None:
        return self._rng_seed

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(self.instrumentos.keys())

    # ---- properties ------------------------------------------------------
    @property
    def sesion(self) -> int:
        return self._sesion

    @sesion.setter
    def sesion(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValueError("sesion debe ser un entero >= 0")
        self._sesion = valor

    @property
    def volumen_total(self) -> int:
        return self._volumen_total

    @volumen_total.setter
    def volumen_total(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValueError("volumen_total debe ser un entero >= 0")
        self._volumen_total = valor

    # ---- API -------------------------------------------------------------
    def precio_de(self, instrumento_id: str) -> float:
        if instrumento_id not in self.instrumentos:
            raise KeyError(f"instrumento {instrumento_id!r} no esta en el mercado")
        return float(self.instrumentos[instrumento_id].precio_base)

    def registrar(self, instrumento: InstrumentoBase) -> None:
        if instrumento.id in self.instrumentos:
            raise ValueError(f"instrumento {instrumento.id!r} ya figura en el mercado")
        self.instrumentos[instrumento.id] = instrumento

    def avanzar_sesion(self, volumen: int = 100) -> dict[str, float]:
        """Avanza 1 sesion aplicando un shock gaussiano a cada precio.

        ``volumen`` es el numero de unidades movidas en el mercado
        durante la sesion (suma a ``volumen_total``). Devuelve los
        nuevos precios.
        """
        if isinstance(volumen, bool) or not isinstance(volumen, int) or volumen <= 0:
            raise ValueError("volumen debe ser un entero > 0")

        nuevos: dict[str, float] = {}
        for inst in self.instrumentos.values():
            sigma = float(inst.volatilidad)
            # Volatilidad pequena: sqrt(dt) como factor de escala diario.
            shock = self._rng.gauss(0.0, 1.0)
            factor = 1.0 + 0.02 * sigma * shock
            if factor <= 0:
                factor = 0.5  # limite inferior de seguridad
            inst.aplicar_factor(factor)
            nuevos[inst.id] = float(inst.precio_base)
        self.sesion = self._sesion + 1
        self.volumen_total = self._volumen_total + volumen
        return nuevos

    def liquidar(self, cartera: Cartera) -> float:
        """Vende todas las posiciones de ``cartera`` a precio actual y devuelve el ingreso."""
        ingreso_bruto = 0.0
        for tid, qty in list(cartera.posiciones):
            precio = self.precio_de(tid)
            op = cartera.desinvertir(
                self,
                tid,
                qty,
                precio,
                fecha=f"s{self._sesion:04d}",
            )
            if op is not None:
                ingreso_bruto += op.importe_bruto
        return ingreso_bruto

    # ---- print -----------------------------------------------------------
    def mostrar(self) -> None:
        print(
            f"[Mercado] {self.nombre!r}  sesion={self._sesion}  "
            f"volumen_total={self._volumen_total}  semilla={self._rng_seed}  "
            f"instrumentos={len(self.instrumentos)}"
        )
        for inst in self.instrumentos.values():
            print(
                f"   - {inst.id:<8} {inst.simbolo:<6} "
                f"{inst.nombre:<28} precio_base={inst.precio_base:.2f}  "
                f"vol={inst.volatilidad:.2f}"
            )

    def __repr__(self) -> str:
        return (
            f"Mercado(nombre={self.nombre!r}, instrumentos={len(self.instrumentos)}, "
            f"sesion={self._sesion}, volumen_total={self._volumen_total}, "
            f"semilla={self._rng_seed})"
        )
