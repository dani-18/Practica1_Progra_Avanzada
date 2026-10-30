"""``Mercado``: motor de cotizaciones para un conjunto de instrumentos.

Atributos (5):

* ``nombre`` (str, no vacio).
* ``_rng_seed`` (int o ``None``): semilla para la simulacion.
* ``instrumentos`` (dict ``{id: InstrumentoBase}``).
* ``sesion`` (int ``>= 0``): contador de sesiones transcurridas.
* ``volumen_total`` (int ``>= 0``): unidades totales movidas.

La simulacion usa un movimiento browniano geometrico discreto::

    precio_{t+1} = precio_t * (1 + deriva + 0.02 * volatilidad * Z)

donde ``Z ~ N(0, 1)``. La ``deriva`` permite modelar mercados alcistas o
bajistas y el shock es proporcional a la volatilidad de cada instrumento.
Cada sesion guarda un snapshot de precios en ``historial_precios`` para
poder calcular metricas y persistir/exportar la evolucion del mercado.
"""

from __future__ import annotations

import random
from math import isfinite
from typing import TYPE_CHECKING, Any

from .excepciones import DatosInvalidos, InstrumentoDesconocido, InstrumentoDuplicado
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
        deriva: float = 0.0,
        repositorio: Any | None = None,
    ) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise DatosInvalidos("nombre no puede estar vacio")
        if not isinstance(instrumentos, dict):
            raise TypeError("instrumentos debe ser dict")
        for tid, inst in instrumentos.items():
            if not isinstance(inst, InstrumentoBase):
                raise TypeError(f"instrumento {tid!r} no es InstrumentoBase")
        if semilla is not None and (isinstance(semilla, bool) or not isinstance(semilla, int)):
            raise TypeError("semilla debe ser int o None")
        if isinstance(deriva, bool) or not isinstance(deriva, (int, float)):
            raise TypeError("deriva debe ser un numero finito")
        if not isfinite(float(deriva)) or not -1.0 <= float(deriva) <= 1.0:
            raise DatosInvalidos("deriva debe estar en [-1, 1]")

        self.nombre: str = nombre.strip()
        self.instrumentos: dict[str, InstrumentoBase] = dict(instrumentos)
        self._rng_seed: int | None = semilla
        self._rng = random.Random(semilla)
        self._deriva = float(deriva)
        self._repositorio = repositorio
        self.sesion = 0
        self.volumen_total = 0
        # Serie historica por instrumento (incluye el precio inicial).
        self._historial_precios: dict[str, list[float]] = {
            tid: [float(inst.precio_base)] for tid, inst in self.instrumentos.items()
        }
        # Snapshots de cada sesion: {'numero', 'volumen', 'precios'}.
        self._sesiones: list[dict[str, Any]] = []

    # ---- properties de solo lectura --------------------------------------
    @property
    def semilla(self) -> int | None:
        return self._rng_seed

    @property
    def repositorio(self) -> Any | None:
        return self._repositorio

    @repositorio.setter
    def repositorio(self, valor: Any | None) -> None:
        self._repositorio = valor

    @property
    def deriva(self) -> float:
        return self._deriva

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(self.instrumentos.keys())

    @property
    def sesiones(self) -> tuple[dict[str, Any], ...]:
        """Snapshots inmutables de las sesiones ya celebradas."""
        return tuple(
            {
                "numero": s["numero"],
                "volumen": s["volumen"],
                "precios": dict(s["precios"]),
            }
            for s in self._sesiones
        )

    def historial_precios(self, instrumento_id: str) -> tuple[float, ...]:
        """Serie de precios de cierre del instrumento (desde su alta)."""
        if instrumento_id not in self._historial_precios:
            raise InstrumentoDesconocido(f"instrumento {instrumento_id!r} no esta en el mercado")
        return tuple(self._historial_precios[instrumento_id])

    @property
    def series(self) -> dict[str, tuple[float, ...]]:
        return {tid: tuple(serie) for tid, serie in self._historial_precios.items()}

    # ---- properties con validacion ---------------------------------------
    @property
    def sesion(self) -> int:
        return self._sesion

    @sesion.setter
    def sesion(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise DatosInvalidos("sesion debe ser un entero >= 0")
        self._sesion = valor

    @property
    def volumen_total(self) -> int:
        return self._volumen_total

    @volumen_total.setter
    def volumen_total(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise DatosInvalidos("volumen_total debe ser un entero >= 0")
        self._volumen_total = valor

    # ---- API -------------------------------------------------------------
    def precio_de(self, instrumento_id: str) -> float:
        if instrumento_id not in self.instrumentos:
            raise InstrumentoDesconocido(f"instrumento {instrumento_id!r} no esta en el mercado")
        return float(self.instrumentos[instrumento_id].precio_base)

    def precios_actuales(self) -> dict[str, float]:
        return {tid: float(inst.precio_base) for tid, inst in self.instrumentos.items()}

    def registrar(self, instrumento: InstrumentoBase) -> None:
        if instrumento.id in self.instrumentos:
            raise InstrumentoDuplicado(f"instrumento {instrumento.id!r} ya figura en el mercado")
        self.instrumentos[instrumento.id] = instrumento
        self._historial_precios[instrumento.id] = [float(instrumento.precio_base)]

    def registrar_precio(self, instrumento_id: str, precio: float) -> float:
        """Anade un precio externo a la serie historica (importacion/datos manuales).

        No avanza la sesion: es util para cargar series historicas o para
        preparar escenarios deterministas en tests.
        """
        if instrumento_id not in self.instrumentos:
            raise InstrumentoDesconocido(f"instrumento {instrumento_id!r} no esta en el mercado")
        if isinstance(precio, bool) or not isinstance(precio, (int, float)):
            raise TypeError("precio debe ser un numero")
        if not isfinite(float(precio)) or float(precio) <= 0:
            raise DatosInvalidos("precio debe ser un numero finito > 0")
        valor = float(precio)
        self.instrumentos[instrumento_id].precio_base = valor
        self._historial_precios[instrumento_id].append(valor)
        return valor

    def avanzar_sesion(self, volumen: int = 100) -> dict[str, float]:
        """Avanza 1 sesion aplicando un shock gaussiano a cada precio.

        ``volumen`` es el numero de unidades movidas en el mercado
        durante la sesion (suma a ``volumen_total``). Devuelve los
        nuevos precios.
        """
        if isinstance(volumen, bool) or not isinstance(volumen, int) or volumen <= 0:
            raise DatosInvalidos("volumen debe ser un entero > 0")

        nuevos: dict[str, float] = {}
        for inst in self.instrumentos.values():
            sigma = float(inst.volatilidad)
            # Volatilidad pequena: sqrt(dt) como factor de escala diario.
            shock = self._rng.gauss(0.0, 1.0)
            factor = 1.0 + self._deriva + 0.02 * sigma * shock
            if factor <= 0:
                factor = 0.5  # limite inferior de seguridad
            inst.aplicar_factor(factor)
            nuevos[inst.id] = float(inst.precio_base)
            self._historial_precios[inst.id].append(float(inst.precio_base))

        self.sesion = self._sesion + 1
        self.volumen_total = self._volumen_total + volumen
        snapshot = {"numero": self._sesion, "volumen": volumen, "precios": dict(nuevos)}
        self._sesiones.append(snapshot)
        if self._repositorio is not None:
            self._repositorio.guardar_sesion(self.nombre, self._sesion, volumen, dict(nuevos))
        return nuevos

    def avanzar_sesiones(self, sesiones: int, volumen: int = 100) -> list[dict[str, float]]:
        """Avanza ``sesiones`` sesiones consecutivas y devuelve sus precios."""
        if isinstance(sesiones, bool) or not isinstance(sesiones, int) or sesiones <= 0:
            raise DatosInvalidos("sesiones debe ser un entero > 0")
        return [self.avanzar_sesion(volumen) for _ in range(sesiones)]

    def aplicar_shock(self, variacion: float) -> dict[str, float]:
        """Aplica un shock inmediato a todos los precios (p. ej. ``-0.15``).

        No incrementa ``sesion``: sirve para modelar un crash o un rally
        puntual dentro de la sesion actual. La serie historica se amplia
        para que las metricas reflejen el impacto.
        """
        if isinstance(variacion, bool) or not isinstance(variacion, (int, float)):
            raise TypeError("variacion debe ser un numero")
        if not isfinite(float(variacion)) or float(variacion) <= -1.0:
            raise DatosInvalidos("variacion debe ser finita y > -1 (p. ej. -0.15)")
        factor = 1.0 + float(variacion)
        nuevos: dict[str, float] = {}
        for inst in self.instrumentos.values():
            inst.aplicar_factor(factor)
            nuevos[inst.id] = float(inst.precio_base)
            self._historial_precios[inst.id].append(float(inst.precio_base))
        return nuevos

    def rendimiento_sesion(self, instrumento_id: str) -> float | None:
        """Variacion porcentual de la ultima sesion (``None`` si no hay)."""
        serie = self.historial_precios(instrumento_id)
        if len(serie) < 2:
            return None
        return serie[-1] / serie[-2] - 1.0

    def rendimiento_desde_inicio(self, instrumento_id: str) -> float:
        serie = self.historial_precios(instrumento_id)
        return serie[-1] / serie[0] - 1.0

    def restaurar_estado(
        self,
        sesion: int,
        volumen_total: int,
        precios: dict[str, float],
        *,
        series: dict[str, list[float]] | None = None,
        sesiones: list[dict[str, Any]] | None = None,
    ) -> None:
        """Fija el estado del mercado tras cargarlo de un almacen."""
        for tid, precio in precios.items():
            if tid in self.instrumentos:
                self.instrumentos[tid].precio_base = float(precio)
        for tid, valores in (series or {}).items():
            if tid in self.instrumentos and valores:
                self._historial_precios[tid] = [float(v) for v in valores]
        self.sesion = sesion
        self.volumen_total = volumen_total
        if sesiones is not None:
            self._sesiones = [
                {
                    "numero": int(s["numero"]),
                    "volumen": int(s["volumen"]),
                    "precios": {str(k): float(v) for k, v in s["precios"].items()},
                }
                for s in sesiones
            ]

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
            f"deriva={self._deriva:+.2%}  instrumentos={len(self.instrumentos)}"
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
            f"semilla={self._rng_seed}, deriva={self._deriva})"
        )
