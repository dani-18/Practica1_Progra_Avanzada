"""Estrategias de inversion (subconjunto minimo para PRAC1).

Por ahora **no** hay una jerarquia ``Estrategia`` comun: cada estrategia
es una clase independiente con la misma interfaz ``generar_orden``
("duck typing"). Esa decision se justifica por dos razones:

1. El Tema 2 (PRAC2) introduce herencia, polimorfismo y genericidad;
   reservamos ese diseno para esa entrega y asi se ve la progresion.
2. El Tema 1 no exige polimorfismo: basta con que las dos clases
   tengan el mismo metodo "como pato" para que el ``Simulador`` las
   use indistintamente.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .activos import TipoOperacion

if TYPE_CHECKING:  # import solo para tipado, evita ciclos en tiempo de ejecucion
    from .cartera import Cartera
    from .mercado import MercadoSimulado


@dataclass(frozen=True, slots=True)
class Orden:
    """Una orden discreta producida por una estrategia."""

    tipo: TipoOperacion
    ticker: str
    cantidad: int


class CompraYMantiene:
    """Buy & Hold: compra ``cantidad`` de cada ticker en la primera sesion.

    Una sola compra al inicio, luego no hace nada. Es el patron mas
    sencillo para entender el flujo entrada -> mercado -> cartera.
    """

    def __init__(self, tickers: Iterable[str], cantidad_por_ticker: int = 5) -> None:
        if cantidad_por_ticker <= 0:
            raise ValueError("cantidad_por_ticker debe ser positivo")
        self._tickers: tuple[str, ...] = tuple(t.upper() for t in tickers)
        if not self._tickers:
            raise ValueError("CompraYMantiene requiere al menos un ticker")
        self._cantidad = int(cantidad_por_ticker)
        self._ejecutado = False

    def generar_orden(
        self, cartera: Cartera, mercado: MercadoSimulado, sesion: int
    ) -> tuple[Orden, ...]:
        if self._ejecutado:
            return ()
        self._ejecutado = True
        return tuple(Orden(TipoOperacion.COMPRA, t, self._cantidad) for t in self._tickers)


class AportePeriodico:
    """DCA simplificado: aporta ``efectivo_por_sesion`` cada ``cadencia`` dias.

    Si hay efectivo disponible en la cartera y el mercado tiene
    suficientes tickers, se compra una cantidad fija del ticker
    principal (``ticker_principal``) hasta agotar el saldo previsto.
    """

    def __init__(
        self,
        ticker_principal: str,
        efectivo_por_sesion: float = 100.0,
        cadencia: int = 5,
    ) -> None:
        if efectivo_por_sesion <= 0:
            raise ValueError("efectivo_por_sesion debe ser positivo")
        if cadencia <= 0:
            raise ValueError("cadencia debe ser positivo")
        self._ticker = ticker_principal.upper()
        self._aporte = float(efectivo_por_sesion)
        self._cadencia = int(cadencia)

    def generar_orden(
        self, cartera: Cartera, mercado: MercadoSimulado, sesion: int
    ) -> tuple[Orden, ...]:
        if sesion <= 0 or sesion % self._cadencia != 0:
            return ()
        if self._ticker not in mercado:
            return ()
        precio = mercado.precio_de(self._ticker)
        if precio <= 0 or cartera.efectivo < self._aporte:
            return ()
        cantidad = int(self._aporte // precio)
        if cantidad <= 0:
            return ()
        # Limitamos a lo que el efectivo permite (incluyendo comision tipica).
        max_por_efectivo = int((cartera.efectivo - cartera.comision_por_operacion) // precio)
        if max_por_efectivo <= 0:
            return ()
        cantidad = min(cantidad, max_por_efectivo)
        return (Orden(TipoOperacion.COMPRA, self._ticker, cantidad),)
