"""Activos financieros ficticios y sus operaciones basicas.

En este modulo se modela el **que** del simulador: los instrumentos
(``Activo``), las posiciones que un inversor mantiene sobre ellos
(``Posicion``), las transacciones que las modifican (``Transaccion``) y la
historia diaria observable del mercado (``BarraDiaria``).

Notas de diseno (PRAC1, Tema 1):

* ``Activo`` esta escrita a mano (no como ``@dataclass``) para hacer
  explicitos los mecanismos que ilustra el Tema 1: ``__init__``,
  atributos privados con el guion bajo inicial, ``@property``/``@setter``
  con validacion, ``__repr__`` y ``__eq__``. Ademas implementa
  ``__hash__`` para que pueda usarse como clave de diccionario (los
  tickers son identificadores unicos).
* ``BarraDiaria`` es una ``NamedTuple``: es un dato compuesto de campos
  fijos que se determina al construir el objeto, inmutable y hashable,
  exactamente el caso para el que el temario recomienda tuplas.
* ``Transaccion`` es un ``@dataclass(frozen=True, slots=True)`` con
  validacion en ``__post_init__``. Su contrato es "no puede
  modificarse"; eso elimina la posibilidad de mutar accidentalmente el
  historial de operaciones, una fuente frecuente de bugs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import NamedTuple


# =============================================================================
# Enums
# =============================================================================
class TipoActivo(Enum):
    """Clasificacion del instrumento dentro del universo simulado."""

    ACCION = "accion"
    BONO = "bono"
    ETF = "etf"

    def __str__(self) -> str:
        return self.value


class TipoOperacion(Enum):
    """Sentido de una operacion registrada en la cartera."""

    COMPRA = "compra"
    VENTA = "venta"

    def __str__(self) -> str:
        return self.value


# =============================================================================
# Value objects (tuplas inmutables)
# =============================================================================
class BarraDiaria(NamedTuple):
    """OHLCV basico de un activo en una sesion concreta.

    Es una tupla inmutable: una vez construida no puede mutarse (no
    admite ``append`` ni asignacion por indice). Ademas es *hashable*
    porque todos sus campos lo son, lo que permite usarla como clave de
    un diccionario o en conjuntos.
    """

    sesion: int
    apertura: float
    cierre: float
    maximo: float
    minimo: float
    volumen: int


# =============================================================================
# Activo
# =============================================================================
class Activo:
    """Instrumento financiero ficticio con precio y volatilidad propios.

    Cada instancia representa una clase de activo identificable unicamente
    por su *ticker*. Las validaciones se aplican en los ``setter`` para
    que el codigo cliente pueda seguir usando la sintaxis de atributo
    (``activo.precio = ...``) sin perder las garantias del invariante.

    Invariantes:

    * ``ticker`` no vacio, sin espacios, en MAYUSCULAS, longitud ``<=8``.
    * ``nombre`` no vacio.
    * ``precio`` numero finito ``> 0``.
    * ``volatilidad`` numero finito en ``[0, 5]`` (5 admite shocks muy
      agresivos en demo; se documenta en la propuesta).
    * ``dividendo_anual`` numero finito ``>= 0``.
    """

    __slots__ = (
        "_dividendo_anual",
        "_nombre",
        "_precio",
        "_ticker",
        "_volatilidad",
        "sector",
        "tipo",
    )

    def __init__(
        self,
        ticker: str,
        nombre: str,
        precio_inicial: float,
        volatilidad: float = 0.2,
        *,
        tipo: TipoActivo = TipoActivo.ACCION,
        sector: str = "General",
        dividendo_anual: float = 0.0,
    ) -> None:
        # ``setter`` explicitos: si fallan, lanzan ``ValueError`` y la
        # instancia queda en un estado consistente (no se llega a crear).
        self.ticker = ticker
        self.nombre = nombre
        self.precio = precio_inicial
        self.volatilidad = volatilidad
        if not isinstance(tipo, TipoActivo):
            raise TypeError("tipo debe ser un TipoActivo")
        self.tipo = tipo
        if not isinstance(sector, str) or not sector.strip():
            raise ValueError("sector no puede estar vacio")
        self.sector = sector.strip()
        self.dividendo_anual = dividendo_anual

    # -- ticker -------------------------------------------------------------
    @property
    def ticker(self) -> str:
        return self._ticker

    @ticker.setter
    def ticker(self, valor: str) -> None:
        if not isinstance(valor, str):
            raise TypeError("el ticker debe ser una cadena de texto")
        limpio = valor.strip().upper()
        if not limpio:
            raise ValueError("el ticker no puede estar vacio")
        if " " in limpio:
            raise ValueError("el ticker no puede contener espacios")
        if len(limpio) > 8:
            raise ValueError("el ticker no puede tener mas de 8 caracteres")
        self._ticker = limpio

    # -- nombre -------------------------------------------------------------
    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str):
            raise TypeError("el nombre debe ser una cadena de texto")
        limpio = valor.strip()
        if not limpio:
            raise ValueError("el nombre no puede estar vacio")
        self._nombre = limpio

    # -- precio -------------------------------------------------------------
    @property
    def precio(self) -> float:
        return self._precio

    @precio.setter
    def precio(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("el precio debe ser un numero finito")
        v = float(valor)
        if not isfinite(v):
            raise ValueError("el precio debe ser un numero finito")
        if v <= 0:
            raise ValueError(f"el precio debe ser positivo (recibido {v})")
        self._precio = v

    # -- volatilidad --------------------------------------------------------
    @property
    def volatilidad(self) -> float:
        return self._volatilidad

    @volatilidad.setter
    def volatilidad(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("la volatilidad debe ser un numero finito")
        v = float(valor)
        if not isfinite(v):
            raise ValueError("la volatilidad debe ser un numero finito")
        if v < 0 or v > 5:
            raise ValueError(f"la volatilidad debe estar en [0, 5] (recibido {v})")
        self._volatilidad = v

    # -- dividendos ---------------------------------------------------------
    @property
    def dividendo_anual(self) -> float:
        return self._dividendo_anual

    @dividendo_anual.setter
    def dividendo_anual(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("el dividendo_anual debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0:
            raise ValueError(f"el dividendo_anual debe ser un numero finito >= 0 (recibido {v})")
        self._dividendo_anual = v

    # -- colaboracion con colecciones --------------------------------------
    def __repr__(self) -> str:
        return (
            f"Activo(ticker={self._ticker!r}, nombre={self._nombre!r}, "
            f"precio={self._precio}, volatilidad={self._volatilidad}, "
            f"tipo={self.tipo!r})"
        )

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Activo):
            return NotImplemented
        return self._ticker == otro._ticker

    def __hash__(self) -> int:
        return hash(self._ticker)

    # -- operaciones del dominio -------------------------------------------
    def aplicar_factor(self, factor: float) -> float:
        """Aplica un multiplicador al precio (por ejemplo, ``1.02``).

        Devuelve el **nuevo** precio. Se valida para evitar precios
        negativos (escenario posible si el mercado tiene ``factor<=0``).
        """
        if not isinstance(factor, (int, float)) or isinstance(factor, bool):
            raise TypeError("el factor debe ser un numero")
        nuevo = self._precio * float(factor)
        if nuevo <= 0 or not isfinite(nuevo):
            raise ValueError(
                f"el factor produce un precio invalido ({nuevo}); "
                "revisa la volatilidad y los shocks del mercado"
            )
        self._precio = nuevo
        return self._precio


# =============================================================================
# Posicion
# =============================================================================
class Posicion:
    """Cantidad de un ``Activo`` mantenida por una ``Cartera``.

    Modela una **asociacion** entre ``Cartera`` y ``Activo``: la posicion
    no posee al activo, lo referencia. ``cantidad`` se valida para que
    nunca sea negativa.
    """

    __slots__ = ("_activo", "_cantidad")

    def __init__(self, activo: Activo, cantidad: int = 0) -> None:
        if not isinstance(activo, Activo):
            raise TypeError("posicion requiere un Activo")
        self._activo = activo
        self.cantidad = cantidad

    @property
    def activo(self) -> Activo:
        return self._activo

    @property
    def ticker(self) -> str:
        return self._activo.ticker

    @property
    def cantidad(self) -> int:
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("la cantidad debe ser un entero")
        if valor < 0:
            raise ValueError(f"la cantidad no puede ser negativa (recibido {valor})")
        self._cantidad = valor

    def valor(self, precio_referencia: float | None = None) -> float:
        """Valor de la posicion al precio dado (o al precio actual del activo)."""
        precio = precio_referencia if precio_referencia is not None else self._activo.precio
        return self._cantidad * float(precio)

    def __repr__(self) -> str:
        return f"Posicion(ticker={self.ticker!r}, cantidad={self._cantidad})"

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Posicion):
            return NotImplemented
        return self._activo == otro._activo and self._cantidad == otro._cantidad

    # Una posicion es mutable; siguiendo el temario, una clase con
    # ``__eq__`` definido es no hashable por defecto en CPython y debe
    # serlo explícitamente si lo necesita. Lo dejamos asi:
    __hash__ = None  # type: ignore[assignment]


# =============================================================================
# Transaccion (inmutable, frozen dataclass)
# =============================================================================
@dataclass(frozen=True, slots=True)
class Transaccion:
    """Registro de una operacion ejecutada.

    Es **inmutable**: una vez ejecutada no se modifica. Esto elimina
    toda una clase de bugs (modificar el historial "a posteriori").
    La validacion en ``__post_init__`` se hace antes de que CPython
    selle la instancia, asi que cualquier ``ValueError`` impide que se
    cree el objeto en estado invalido.
    """

    sesion: int
    tipo: TipoOperacion
    ticker: str
    cantidad: int
    precio_unitario: float
    comision: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.sesion, bool) or not isinstance(self.sesion, int):
            raise TypeError("sesion debe ser un entero")
        if self.sesion < 0:
            raise ValueError("sesion no puede ser negativa")
        if not isinstance(self.tipo, TipoOperacion):
            raise TypeError("tipo debe ser un TipoOperacion")
        if not self.ticker or not isinstance(self.ticker, str):
            raise ValueError("ticker no puede estar vacio")
        if isinstance(self.cantidad, bool) or not isinstance(self.cantidad, int):
            raise TypeError("cantidad debe ser un entero")
        if self.cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        if not isfinite(self.precio_unitario) or self.precio_unitario <= 0:
            raise ValueError("precio_unitario debe ser positivo")
        if not isfinite(self.comision) or self.comision < 0:
            raise ValueError("comision no puede ser negativa")

    @property
    def importe_bruto(self) -> float:
        return self.cantidad * self.precio_unitario

    @property
    def importe_neto(self) -> float:
        signo = 1 if self.tipo is TipoOperacion.COMPRA else -1
        return signo * (self.importe_bruto + self.comision)

    def __repr__(self) -> str:
        return (
            f"Transaccion(sesion={self.sesion}, tipo={self.tipo!r}, "
            f"ticker={self.ticker!r}, cantidad={self.cantidad}, "
            f"precio={self.precio_unitario:.4f}, comision={self.comision:.4f})"
        )
