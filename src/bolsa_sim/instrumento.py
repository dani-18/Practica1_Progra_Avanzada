"""``InstrumentoBase``: clase padre preparada para herencia futura.

Atributos de instancia (5):

* ``id`` (str, no vacio, "mayusculas" recomendado).
* ``nombre`` (str, no vacio).
* ``simbolo`` (str, no vacio).
* ``volatilidad`` (float en ``[0, 5]``).
* ``precio_base`` (float ``> 0``).

La clase expone ``@property`` y ``@setter`` para ``volatilidad`` y
``precio_base``, dejando ``id``, ``nombre`` y ``simbolo`` como
atributos inmutables (el ``__init__`` rechaza entradas invalidas).

Queda lista para especializarse en PRAC2::

    class Accion(InstrumentoBase):
        tipo = "accion"

    class Bono(InstrumentoBase):
        def __init__(self, id, ..., cupon_anual: float = 0.04):
            super().__init__(id, ...)
            self.cupon_anual = cupon_anual

La igualdad y el hash son por ``id`` (dos instrumentos con el mismo
identificador logico son el mismo instrumento).

En PRAC2 se anaden las subclases :class:`~bolsa_sim.accion.Accion`,
:class:`~bolsa_sim.bono.Bono` y :class:`~bolsa_sim.etf.ETF`. La base fija
el contrato polimorfico:

* ``tipo``: etiqueta de la familia (clase hija la sobrescribe).
* ``flujo_anual()``: flujo de caja anual por unidad (0.0 en la base).
* ``mostrar()``: usa ``type(self).__name__`` para que cada subclase
  imprima su propio encabezado sin reescribir el formato.
"""

from __future__ import annotations

from math import isfinite


class InstrumentoBase:
    """Plantilla base de un instrumento financiero del simulador."""

    #: Etiqueta de la familia de instrumento (las subclases la redefinen).
    tipo: str = "instrumento"

    def __init__(
        self,
        id: str,
        nombre: str,
        simbolo: str,
        volatilidad: float,
        precio_base: float,
    ) -> None:
        if not isinstance(id, str) or not id.strip():
            raise ValueError("id no puede estar vacio")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("nombre no puede estar vacio")
        if not isinstance(simbolo, str) or not simbolo.strip():
            raise ValueError("simbolo no puede estar vacio")
        # Validacion inicial: usar el setter asegura invariantes
        # desde la primera linea de vida del objeto.
        self.id: str = id.strip().upper()
        self.nombre: str = nombre.strip()
        self.simbolo: str = simbolo.strip().upper()
        self.volatilidad = volatilidad
        self.precio_base = precio_base

    # ---- propiedades con validacion --------------------------------------
    @property
    def volatilidad(self) -> float:
        return self._volatilidad

    @volatilidad.setter
    def volatilidad(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("volatilidad debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v < 0 or v > 5:
            raise ValueError(f"volatilidad debe estar en [0, 5] (recibido {v})")
        self._volatilidad = v

    @property
    def precio_base(self) -> float:
        return self._precio_base

    @precio_base.setter
    def precio_base(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("precio_base debe ser un numero finito")
        v = float(valor)
        if not isfinite(v) or v <= 0:
            raise ValueError(f"precio_base debe ser > 0 (recibido {v})")
        self._precio_base = v

    # ---- comportamiento del dominio --------------------------------------
    def aplicar_factor(self, factor: float) -> float:
        """Devuelve el nuevo ``precio_base`` multiplicado por ``factor``.

        ``1.05`` = +5 %, ``0.97`` = -3 %. Es un helper del mercado;
        se valida para impedir precios ``<= 0``.
        """
        if not isinstance(factor, (int, float)) or isinstance(factor, bool):
            raise TypeError("factor debe ser un numero")
        nuevo = float(factor) * self._precio_base
        self.precio_base = nuevo  # reusa la validacion del setter
        return self._precio_base

    def flujo_anual(self) -> float:
        """Flujo de caja anual por unidad del instrumento.

        La base no genera rentas periodicas (``0.0``); ``Accion`` lo
        sobrescribe con su dividendo y ``Bono`` con su cupon. Es el
        punto de extension polimorfico que PRAC2 introduce.
        """
        return 0.0

    def mostrar(self) -> None:
        """Imprime por pantalla un resumen del instrumento.

        Usa ``type(self).__name__`` para que las subclases hereden el
        formato y solo anadan sus campos con ``super().mostrar()``.
        """
        print(
            f"[{type(self).__name__}] {self.id} ({self.simbolo}): "
            f"{self.nombre!r}  precio_base={self.precio_base:.2f}  "
            f"volatilidad={self._volatilidad:.2f}  flujo_anual={self.flujo_anual():.2f}"
        )

    # ---- representacion e identidad --------------------------------------
    def __repr__(self) -> str:
        return (
            f"InstrumentoBase(id={self.id!r}, simbolo={self.simbolo!r}, "
            f"nombre={self.nombre!r}, volatilidad={self._volatilidad}, "
            f"precio_base={self._precio_base})"
        )

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, InstrumentoBase):
            return NotImplemented
        return self.id == otro.id

    __hash__ = None  # la igualdad por 'id' es logica y mutable: no hasheable.
