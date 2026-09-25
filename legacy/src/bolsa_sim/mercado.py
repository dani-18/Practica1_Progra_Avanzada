"""Evolucion simulada del mercado de activos.

El mercado es responsable del **como**: toma los ``Activo`` registrados
y aplica perturbaciones aleatorias (un paseo aleatorio con la
volatilidad de cada activo) para producir nuevas cotizaciones. Es
*determinista* cuando se le inyecta un ``random.Random`` con semilla.

Notas de diseno:

* La historia de cotizaciones se devuelve como ``tuple[BarraDiaria, ...]``
  para reforzar el criterio "tupla si la coleccion no debe mutar"; el
  historial es append-only desde la perspectiva del cliente.
* ``precio_de(ticker)`` funciona con un diccionario interno; se usa el
  ticker (hashable e inmutable) como clave, no el ``Activo``.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterable
from typing import Final

from .activos import Activo, BarraDiaria

# Numero magico para las comisiones, expuesto por si alguien lo quiere
# inyectar en otro modulo (p.ej., tests).
COMISION_POR_OPERACION: Final[float] = 1.0


class MercadoSimulado:
    """Motor de cotizaciones para un conjunto cerrado de activos."""

    def __init__(
        self,
        activos: Iterable[Activo],
        *,
        semilla: int | None = None,
        tendencia_drift: float = 0.0,
    ) -> None:
        self._activos: dict[str, Activo] = {}
        for act in activos:
            if not isinstance(act, Activo):
                raise TypeError("el mercado solo admite instancias de Activo")
            if act.ticker in self._activos:
                raise ValueError(f"ticker duplicado en el mercado: {act.ticker!r}")
            self._activos[act.ticker] = act

        self._rng = random.Random(semilla)
        self._sesion_actual: int = 0
        self._drift = float(tendencia_drift)
        # ``list`` por dentro (mutacion local controlada), expuesto como tuple.
        self._historial: dict[str, list[BarraDiaria]] = {t: [] for t in self._activos}

    # -- acceso --------------------------------------------------------------
    @property
    def tickers(self) -> tuple[str, ...]:
        return tuple(self._activos.keys())

    @property
    def sesion_actual(self) -> int:
        return self._sesion_actual

    @property
    def tamanio(self) -> int:
        return len(self._activos)

    def __len__(self) -> int:
        return len(self._activos)

    def __contains__(self, ticker: object) -> bool:
        return isinstance(ticker, str) and ticker in self._activos

    def activos(self) -> tuple[Activo, ...]:
        """Devuelve una tupla inmutable con los activos registrados."""
        return tuple(self._activos.values())

    def obtener(self, ticker: str) -> Activo:
        if ticker not in self._activos:
            raise KeyError(f"ticker desconocido: {ticker!r}")
        return self._activos[ticker]

    def precio_de(self, ticker: str) -> float:
        return self.obtener(ticker).precio

    # -- evolucion -----------------------------------------------------------
    def avanzar_sesion(self) -> dict[str, float]:
        """Avanza un dia y devuelve ``{ticker: nuevo_precio}``.

        Para cada activo se aplica un movimiento browniano geometrico
        simplificado: ``factor = exp(drift + sigma * N(0,1))`` y se
        descuenta un tiny sesgo para realismo de retornos largos. La
        cota inferior ``> 0`` es un invariante de ``Activo``.
        """
        resultado: dict[str, float] = {}
        self._sesion_actual += 1
        for ticker, activo in self._activos.items():
            cierre_anterior = activo.precio
            sigma = activo.volatilidad
            # 1 / 252 ~ un dia de trading sobre un ano. Mantener este
            # factor evita desvios explosivos en simulaciones largas.
            dt = 1.0 / 252.0
            shock = self._rng.gauss(0.0, 1.0)
            # sqrt(252) invierte la anualizacion para un horizon diario.
            factor = math.exp(self._drift * dt + sigma * math.sqrt(dt) * shock)
            nuevo = activo.aplicar_factor(factor)
            barra = BarraDiaria(
                sesion=self._sesion_actual,
                apertura=cierre_anterior,
                cierre=nuevo,
                maximo=max(cierre_anterior, nuevo),
                minimo=min(cierre_anterior, nuevo),
                volumen=0,  # se omite la dinamica de volumen en PRAC1.
            )
            self._historial[ticker].append(barra)
            resultado[ticker] = nuevo
        return resultado

    def simular(self, sesiones: int) -> list[dict[str, float]]:
        """Avanza ``sesiones`` dias y devuelve el historial diario."""
        if isinstance(sesiones, bool) or not isinstance(sesiones, int):
            raise TypeError("sesiones debe ser un entero")
        if sesiones < 0:
            raise ValueError("sesiones no puede ser negativo")
        resultado: list[dict[str, float]] = []
        for _ in range(sesiones):
            resultado.append(self.avanzar_sesion())
        return resultado

    def historial_de(self, ticker: str) -> tuple[BarraDiaria, ...]:
        """Serie historica del ticker como tupla inmutable."""
        barras = self._historial.get(ticker)
        if barras is None:
            raise KeyError(f"ticker desconocido: {ticker!r}")
        return tuple(barras)
