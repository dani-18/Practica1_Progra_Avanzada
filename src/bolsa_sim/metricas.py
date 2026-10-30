"""Metricas de rentabilidad y riesgo sobre series de precios o de valor.

El modulo es deliberadamente **puro** (sin estado) para que sea facil de
testear y de reutilizar desde CLI, GUI, exportadores y simulaciones.

Todas las series se interpretan como valores al cierre de sesiones
consecutivas. Las anualizaciones usan por defecto ``252`` sesiones por ano
(convencion de mercados bursatiles).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from statistics import fmean, stdev
from typing import TYPE_CHECKING

from .excepciones import DatosInvalidos

if TYPE_CHECKING:
    from .cartera import Cartera
    from .mercado import Mercado

SESIONES_POR_ANIO = 252


def _validar_serie(serie: list[float] | tuple[float, ...]) -> list[float]:
    if not isinstance(serie, (list, tuple)):
        raise DatosInvalidos("la serie debe ser una lista o tupla de precios")
    valores = [float(v) for v in serie]
    if not valores:
        raise DatosInvalidos("la serie no puede estar vacia")
    if any(not isfinite(v) or v <= 0 for v in valores):
        raise DatosInvalidos("todos los valores de la serie deben ser finitos y > 0")
    return valores


def rentabilidades(serie: list[float] | tuple[float, ...]) -> list[float]:
    """Rentabilidades simples periodo a periodo."""
    valores = _validar_serie(serie)
    return [valores[i] / valores[i - 1] - 1.0 for i in range(1, len(valores))]


def rentabilidad_total(serie: list[float] | tuple[float, ...]) -> float:
    valores = _validar_serie(serie)
    if len(valores) < 2:
        return 0.0
    return valores[-1] / valores[0] - 1.0


def rentabilidad_anualizada(
    serie: list[float] | tuple[float, ...],
    sesiones_por_anio: int = SESIONES_POR_ANIO,
) -> float:
    """CAGR a partir de la rentabilidad total y el numero de periodos."""
    valores = _validar_serie(serie)
    periodos = len(valores) - 1
    if periodos <= 0:
        return 0.0
    total = valores[-1] / valores[0]
    if total <= 0:
        return -1.0
    return total ** (sesiones_por_anio / periodos) - 1.0


def volatilidad_anualizada(
    serie: list[float] | tuple[float, ...],
    sesiones_por_anio: int = SESIONES_POR_ANIO,
) -> float:
    """Desviacion tipica muestral de las rentabilidades, anualizada."""
    retornos = rentabilidades(serie)
    if len(retornos) < 2:
        return 0.0
    return stdev(retornos) * sqrt(sesiones_por_anio)


def max_drawdown(serie: list[float] | tuple[float, ...]) -> float:
    """Maxima caida desde un maximo previo, como magnitud positiva.

    ``0.20`` significa que en el peor momento la serie llego a perder un
    20 % respecto a su maximo anterior.
    """
    valores = _validar_serie(serie)
    pico = valores[0]
    peor = 0.0
    for valor in valores:
        pico = max(pico, valor)
        caida = 1.0 - valor / pico
        peor = max(peor, caida)
    return peor


def ratio_sharpe(
    serie: list[float] | tuple[float, ...],
    tasa_libre_anual: float = 0.0,
    sesiones_por_anio: int = SESIONES_POR_ANIO,
) -> float:
    """Rentabilidad media excedente por unidad de volatilidad."""
    retornos = rentabilidades(serie)
    if len(retornos) < 2:
        return 0.0
    libre = (1.0 + tasa_libre_anual) ** (1.0 / sesiones_por_anio) - 1.0
    exceso = [r - libre for r in retornos]
    desviacion = stdev(exceso)
    if desviacion == 0:
        return 0.0
    return fmean(exceso) / desviacion * sqrt(sesiones_por_anio)


def ratio_sortino(
    serie: list[float] | tuple[float, ...],
    tasa_libre_anual: float = 0.0,
    sesiones_por_anio: int = SESIONES_POR_ANIO,
) -> float:
    """Como Sharpe, pero penaliza solo la volatilidad a la baja."""
    retornos = rentabilidades(serie)
    if len(retornos) < 2:
        return 0.0
    libre = (1.0 + tasa_libre_anual) ** (1.0 / sesiones_por_anio) - 1.0
    exceso = [r - libre for r in retornos]
    bajistas = [min(0.0, r) for r in exceso]
    desviacion = sqrt(fmean(r * r for r in bajistas))
    if desviacion == 0:
        return 0.0
    return fmean(exceso) / desviacion * sqrt(sesiones_por_anio)


@dataclass(frozen=True, slots=True)
class MetricasInversion:
    """Resumen numerico de una serie de valor (precio o patrimonio)."""

    valor_inicial: float
    valor_final: float
    rentabilidad_total: float
    rentabilidad_anualizada: float
    volatilidad_anualizada: float
    max_drawdown: float
    ratio_sharpe: float
    ratio_sortino: float
    num_periodos: int

    def a_dict(self) -> dict[str, float | int]:
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"rentabilidad={self.rentabilidad_total:+.2%}  "
            f"anualizada={self.rentabilidad_anualizada:+.2%}  "
            f"volatilidad={self.volatilidad_anualizada:.2%}  "
            f"max_drawdown={self.max_drawdown:.2%}  "
            f"sharpe={self.ratio_sharpe:.2f}  sortino={self.ratio_sortino:.2f}"
        )


def calcular_metricas(
    serie: list[float] | tuple[float, ...],
    *,
    tasa_libre_anual: float = 0.0,
    sesiones_por_anio: int = SESIONES_POR_ANIO,
) -> MetricasInversion:
    """Calcula todas las metricas de una serie en una sola llamada."""
    valores = _validar_serie(serie)
    return MetricasInversion(
        valor_inicial=valores[0],
        valor_final=valores[-1],
        rentabilidad_total=rentabilidad_total(valores),
        rentabilidad_anualizada=rentabilidad_anualizada(valores, sesiones_por_anio),
        volatilidad_anualizada=volatilidad_anualizada(valores, sesiones_por_anio),
        max_drawdown=max_drawdown(valores),
        ratio_sharpe=ratio_sharpe(valores, tasa_libre_anual, sesiones_por_anio),
        ratio_sortino=ratio_sortino(valores, tasa_libre_anual, sesiones_por_anio),
        num_periodos=len(valores) - 1,
    )


def metricas_cartera(
    cartera: Cartera,
    mercado: Mercado,
    *,
    valor_inicial: float | None = None,
    tasa_libre_anual: float = 0.0,
) -> MetricasInversion:
    """Metricas de la curva de valor de una cartera.

    Si la cartera no tiene curva registrada se comparan el capital inicial
    y el valor liquidativo actual, lo que da una foto (no una serie) de la
    rentabilidad conseguida.
    """
    curva = list(cartera.curva_valor)
    if len(curva) < 2:
        inicial = cartera.capital_inicial if valor_inicial is None else float(valor_inicial)
        curva = [max(inicial, 1e-9), max(cartera.valor_total(mercado), 1e-9)]
    return calcular_metricas(curva, tasa_libre_anual=tasa_libre_anual)


__all__ = [
    "SESIONES_POR_ANIO",
    "MetricasInversion",
    "calcular_metricas",
    "max_drawdown",
    "metricas_cartera",
    "ratio_sharpe",
    "ratio_sortino",
    "rentabilidad_anualizada",
    "rentabilidad_total",
    "rentabilidades",
    "volatilidad_anualizada",
]
