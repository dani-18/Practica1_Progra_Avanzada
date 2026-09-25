"""Cartera (Portfolio) y operaciones de compra/venta.

Una ``Cartera`` mantiene un saldo en efectivo y un conjunto de
posiciones indexadas por ticker. El registro historico de operaciones
se almacena como **lista** porque la coleccion *crece* con el tiempo
(alta, baja y reordenacion son operaciones naturales de un registro);
este es el caso que, segun el Tema 1, exige lista y no tupla.

Notas de diseno:

* ``comprar`` y ``vender`` trabajan en cantidades enteras; las comisiones
  son opcionales. Si una operacion no se puede ejecutar (fondos
  insuficientes, cantidad invalida) se devuelve ``False`` y la cartera
  queda intacta. Esto es una decision deliberada para que el caller
  pueda reaccionar. En PRAC2 introduciremos excepciones de dominio.
"""

from __future__ import annotations

from typing import Final

from .activos import Posicion, TipoOperacion, Transaccion
from .mercado import COMISION_POR_OPERACION, MercadoSimulado

COMISION_MINIMA: Final[float] = 1.0


class Cartera:
    """Cartera de inversion con efectivo en EUR y posiciones por ticker."""

    def __init__(
        self,
        efectivo_inicial: float,
        *,
        comision_por_operacion: float = COMISION_POR_OPERACION,
        nombre: str = "Cartera",
    ) -> None:
        if not isinstance(efectivo_inicial, (int, float)) or isinstance(efectivo_inicial, bool):
            raise TypeError("efectivo_inicial debe ser un numero")
        if not isfinite(efectivo_inicial) or efectivo_inicial < 0:
            raise ValueError(
                f"efectivo_inicial debe ser un numero finito >= 0 (recibido {efectivo_inicial})"
            )
        if not isfinite(comision_por_operacion) or comision_por_operacion < 0:
            raise ValueError("comision_por_operacion no puede ser negativa")

        self._efectivo: float = float(efectivo_inicial)
        self._comision: float = float(comision_por_operacion)
        self._nombre: str = nombre.strip() or "Cartera"
        # ``dict``: la coleccion de posiciones crece/decrece; no nos
        # interesa una tupla.
        self._posiciones: dict[str, Posicion] = {}
        # ``list``: historial append-only de operaciones.
        self._transacciones: list[Transaccion] = []

    # -- lectura -------------------------------------------------------------
    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def efectivo(self) -> float:
        return self._efectivo

    @property
    def comision_por_operacion(self) -> float:
        return self._comision

    @property
    def posiciones(self) -> tuple[Posicion, ...]:
        """Vista inmutable de las posiciones."""
        return tuple(self._posiciones.values())

    @property
    def transacciones(self) -> tuple[Transaccion, ...]:
        """Copia inmutable del historial (crece, pero el exterior no puede mutarlo)."""
        return tuple(self._transacciones)

    @property
    def total_transacciones(self) -> int:
        return len(self._transacciones)

    def inversion(self) -> float:
        """Capital inicial invertido en posiciones (sin efectivo libre)."""
        return sum(p.valor() for p in self._posiciones.values())

    def valor_total(self, mercado: MercadoSimulado) -> float:
        """Valor liquidativo: efectivo + posiciones valoradas a mercado."""
        return self._efectivo + sum(
            p.valor(mercado.precio_de(p.ticker)) for p in self._posiciones.values()
        )

    # -- operaciones ---------------------------------------------------------
    def comprar(
        self,
        mercado: MercadoSimulado,
        ticker: str,
        cantidad: int,
        *,
        comision: float | None = None,
    ) -> bool:
        """Compra ``cantidad`` participaciones. Devuelve ``True`` si se ejecuta."""
        if isinstance(cantidad, bool) or not isinstance(cantidad, int):
            raise TypeError("cantidad debe ser un entero")
        if cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        activo = mercado.obtener(ticker)  # KeyError si no existe
        precio = activo.precio
        coste = cantidad * precio
        comision = self._comision if comision is None else float(comision)
        coste_total = coste + comision
        if coste_total > self._efectivo:
            return False

        posicion = self._posiciones.get(ticker)
        if posicion is None:
            self._posiciones[ticker] = Posicion(activo, cantidad)
        else:
            posicion.cantidad = posicion.cantidad + cantidad
        self._efectivo -= coste_total

        self._transacciones.append(
            Transaccion(
                sesion=mercado.sesion_actual,
                tipo=TipoOperacion.COMPRA,
                ticker=ticker,
                cantidad=cantidad,
                precio_unitario=precio,
                comision=comision,
            )
        )
        return True

    def vender(
        self,
        mercado: MercadoSimulado,
        ticker: str,
        cantidad: int,
        *,
        comision: float | None = None,
    ) -> bool:
        """Vende ``cantidad`` participaciones si existen. Devuelve ``True`` si se ejecuta."""
        if isinstance(cantidad, bool) or not isinstance(cantidad, int):
            raise TypeError("cantidad debe ser un entero")
        if cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        posicion = self._posiciones.get(ticker)
        if posicion is None or posicion.cantidad < cantidad:
            return False
        activo = mercado.obtener(ticker)
        precio = activo.precio
        ingreso = cantidad * precio
        comision = self._comision if comision is None else float(comision)
        ingreso_neto = ingreso - comision

        posicion.cantidad -= cantidad
        if posicion.cantidad == 0:
            del self._posiciones[ticker]
        self._efectivo += ingreso_neto

        self._transacciones.append(
            Transaccion(
                sesion=mercado.sesion_actual,
                tipo=TipoOperacion.VENTA,
                ticker=ticker,
                cantidad=cantidad,
                precio_unitario=precio,
                comision=comision,
            )
        )
        return True

    # -- utilidades ----------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"Cartera(nombre={self._nombre!r}, efectivo={self._efectivo:.2f}, "
            f"posiciones={len(self._posiciones)}, txns={len(self._transacciones)})"
        )


# Import retardado para evitar ciclos de tipo
from math import isfinite  # noqa: E402  (se ubica al final por legibilidad)
