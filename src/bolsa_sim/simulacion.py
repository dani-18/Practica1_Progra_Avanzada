"""Simulador: orquesta ``MercadoSimulado`` + ``Cartera`` + una estrategia.

Es la pieza que demuestra el **flujo inicial** ("hello flow") exigido
por la PRAC1: crear mercado, anadir activos, arrancar una simulacion y
ver como evoluciona la cartera. Tambien ejercita la separacion de
responsabilidades:
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from .activos import Activo
from .cartera import Cartera
from .estrategias import CompraYMantiene
from .mercado import MercadoSimulado


# ---------------------------------------------------------------------------
# Protocolo de estrategia (duck typing). En PRAC2 lo convertiremos en un
# ``ABC`` para anadir hooks y genericidad. Mientras, basta con declarar
# la forma esperada con ``Protocol``.
# ---------------------------------------------------------------------------
class EstrategiaProtocol(Protocol):
    """Cualquier objeto con un metodo ``generar_orden`` compatible."""

    def generar_orden(
        self, cartera: Cartera, mercado: MercadoSimulado, sesion: int
    ) -> tuple[object, ...]: ...


@dataclass(frozen=True, slots=True)
class ResultadoSimulacion:
    """Resumen inmutable del resultado de una simulacion."""

    sesiones_ejecutadas: int
    efectivo_inicial: float
    efectivo_final: float
    valor_inicial: float
    valor_final: float
    operaciones_ejecutadas: int

    @property
    def roi_porcentaje(self) -> float:
        if self.valor_inicial <= 0:
            return float("nan")
        return (self.valor_final - self.valor_inicial) / self.valor_inicial * 100


class Simulador:
    """Orquesta la ejecucion de una simulacion completa."""

    def __init__(
        self,
        mercado: MercadoSimulado,
        cartera: Cartera,
        estrategia: object,
        *,
        verbose: bool = False,
    ) -> None:
        self._mercado = mercado
        self._cartera = cartera
        # Acepta cualquier "pato" con ``generar_orden`` (duck typing).
        self._estrategia = estrategia
        self._verbose = bool(verbose)

    def ejecutar(self, sesiones: int) -> ResultadoSimulacion:
        """Avanza ``sesiones`` dias, ejecutando la estrategia en cada uno.

        En cada sesion: (1) la estrategia produce 0..N ordenes; (2) la
        cartera las ejecuta; (3) el mercado avanza un dia. Este orden es
        importante: las ordenes se interpretan al precio de cierre de la
        sesion anterior y el movimiento del mercado cierra la nueva.
        """
        efectivo_inicial = self._cartera.efectivo
        valor_inicial = self._cartera.valor_total(self._mercado)
        for sesion in range(1, sesiones + 1):
            ordenes = tuple(
                self._estrategia.generar_orden(
                    self._cartera, self._mercado, self._mercado.sesion_actual + 1
                )
            )
            for ord_obj in ordenes:
                ticker = ord_obj.ticker
                cantidad = int(ord_obj.cantidad)
                tipo = ord_obj.tipo
                if tipo.value == "compra":
                    self._cartera.comprar(self._mercado, ticker, cantidad)
                else:
                    self._cartera.vender(self._mercado, ticker, cantidad)
                if self._verbose:
                    print(f"  [s={sesion}] {tipo.value} {cantidad} x {ticker}")
            self._mercado.avanzar_sesion()
        valor_final = self._cartera.valor_total(self._mercado)
        return ResultadoSimulacion(
            sesiones_ejecutadas=sesiones,
            efectivo_inicial=efectivo_inicial,
            efectivo_final=self._cartera.efectivo,
            valor_inicial=valor_inicial,
            valor_final=valor_final,
            operaciones_ejecutadas=self._cartera.total_transacciones,
        )

    @staticmethod
    def demo_basica(activos: Iterable[Activo], sesiones: int = 5) -> ResultadoSimulacion:
        """Atajo para una demo reproducible e independiente del CLI."""
        mercado = MercadoSimulado(activos, semilla=42)
        cartera = Cartera(10_000.0)
        estrategia = CompraYMantiene(tuple(a.ticker for a in mercado.activos()))
        return Simulador(mercado, cartera, estrategia).ejecutar(sesiones)
