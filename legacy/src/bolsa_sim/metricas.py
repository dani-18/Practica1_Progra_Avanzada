"""Metricas de rentabilidad y riesgo (subconjunto minimo para PRAC1).

En esta primera iteracion el "motor" de metricas es muy ligero:
rentabilidad total y drawdown maximo. Mas adelante (PRAC4) se anadiran
volatilidad anualizada, ratio de Sharpe, VaR, etc.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import isfinite
from typing import TypeGuard


def _es_finito(x: float) -> TypeGuard[float]:
    return isfinite(x)


def rentabilidad_total(inicial: float, final: float, *, como_porcentaje: bool = True) -> float:
    """Rentabilidad total acumulada sobre el periodo.

    ``roi = (final - inicial) / inicial``. Devuelve infinito si el
    capital inicial es 0; eso se considera un caso degenerado.
    """
    if not (_es_finito(inicial) and _es_finito(final)):
        raise ValueError("rentabilidad_total requiere valores finitos")
    if inicial == 0:
        return float("inf") if final > 0 else 0.0
    roi = (final - inicial) / inicial
    return roi * 100 if como_porcentaje else roi


def drawdown_maximo(valores: Iterable[float]) -> float:
    """Calculo del maximo drawdown (caida pico-a-valle).

    Recorre la serie de valor liquidativo y devuelve la mayor perdida
    relativa respecto al maximo observado hasta el momento. Devuelve
    un valor no positivo (``<= 0``).
    """
    max_vista = float("-inf")
    pico_drawdown = 0.0  # 0 es cota superior: drawdowns son <= 0.
    hay_valor = False
    for v in valores:
        if not _es_finito(v):
            continue
        hay_valor = True
        max_vista = max(max_vista, v)
        if max_vista > 0:
            drawdown = (v - max_vista) / max_vista
            pico_drawdown = min(pico_drawdown, drawdown)
    if not hay_valor:
        return 0.0
    return pico_drawdown
