"""Estrategias de inversion (patron **Strategy**) y su fabrica.

Una estrategia no ejecuta ordenes: **decide** que haria en el contexto
actual y devuelve una lista de :class:`Decision`. El simulador es quien
las ejecuta contra la cartera. Esa separacion hace las estrategias puras,
testeables y faciles de combinar con la concurrencia.

Estrategias incluidas:

* ``comprar_mantener``: reparte el capital al principio y no vuelve a operar.
* ``momentum``: compra los instrumentos con mejor tendencia y vende los que
  pierden impulso.
* ``rebalanceo``: mantiene pesos objetivo y corrige desviaciones.

La fabrica evita que CLI/GUI/persistencia conozcan las clases concretas::

    estrategia = crear_estrategia("momentum", ventana=10)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .excepciones import DatosInvalidos, EstrategiaDesconocida

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .cartera import Cartera
    from .mercado import Mercado

TipoOrden = Literal["compra", "venta"]


@dataclass(frozen=True, slots=True)
class Decision:
    """Orden que una estrategia propone ejecutar."""

    instrumento_id: str
    tipo: TipoOrden
    cantidad: int

    def __post_init__(self) -> None:
        if not self.instrumento_id.strip():
            raise DatosInvalidos("instrumento_id no puede estar vacio")
        if self.tipo not in ("compra", "venta"):
            raise DatosInvalidos("tipo debe ser 'compra' o 'venta'")
        if isinstance(self.cantidad, bool) or self.cantidad <= 0:
            raise DatosInvalidos("cantidad debe ser un entero > 0")

    def __repr__(self) -> str:
        return f"Decision({self.tipo} {self.cantidad} {self.instrumento_id})"


@dataclass(frozen=True, slots=True)
class ContextoMercado:
    """Foto inmutable del estado que recibe una estrategia."""

    mercado: Mercado
    cartera: Cartera
    sesion: int

    def precio(self, instrumento_id: str) -> float:
        return self.mercado.precio_de(instrumento_id)

    def valor_total(self) -> float:
        return self.cartera.valor_total(self.mercado)

    def posicion(self, instrumento_id: str) -> int:
        return self.cartera.posicion(instrumento_id)

    def momentum(self, instrumento_id: str, ventana: int) -> float | None:
        """Rentabilidad de las ultimas ``ventana`` sesiones (``None`` si faltan datos)."""
        serie = self.mercado.historial_precios(instrumento_id)
        if ventana < 1 or len(serie) < ventana + 1:
            return None
        return serie[-1] / serie[-ventana - 1] - 1.0

    def peso(self, instrumento_id: str) -> float:
        total = self.valor_total()
        if total <= 0:
            return 0.0
        return self.posicion(instrumento_id) * self.precio(instrumento_id) / total


class EstrategiaInversion(ABC):
    """Interfaz comun de todas las estrategias (Strategy)."""

    nombre: str = "base"
    descripcion: str = ""

    @abstractmethod
    def decidir(self, contexto: ContextoMercado) -> list[Decision]:
        """Devuelve las ordenes que la estrategia ejecutaria ahora."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(nombre={self.nombre!r})"


class ComprarMantener(EstrategiaInversion):
    """Invierte una fraccion del capital al inicio y no vuelve a operar."""

    nombre = "comprar_mantener"
    descripcion = "Compra una sola vez y mantiene las posiciones."

    def __init__(self, fraccion: float = 0.95) -> None:
        if isinstance(fraccion, bool) or not isinstance(fraccion, (int, float)):
            raise DatosInvalidos("fraccion debe ser un numero")
        if not 0 < float(fraccion) <= 1:
            raise DatosInvalidos("fraccion debe estar en (0, 1]")
        self.fraccion = float(fraccion)

    def decidir(self, contexto: ContextoMercado) -> list[Decision]:
        if contexto.cartera.posiciones or contexto.mercado.ids == ():
            return []
        presupuesto = contexto.cartera.efectivo * self.fraccion
        ids = contexto.mercado.ids
        por_instrumento = presupuesto / len(ids)
        decisiones: list[Decision] = []
        for tid in ids:
            cantidad = int(por_instrumento // contexto.precio(tid))
            if cantidad > 0:
                decisiones.append(Decision(tid, "compra", cantidad))
        return decisiones


class Momentum(EstrategiaInversion):
    """Sigue la tendencia: compra ganadores y vende perdedores."""

    nombre = "momentum"
    descripcion = "Compra impulso positivo y vende el impulso negativo."

    def __init__(
        self,
        ventana: int = 5,
        umbral: float = 0.0,
        fraccion: float = 0.30,
        max_posiciones: int = 3,
    ) -> None:
        if isinstance(ventana, bool) or not isinstance(ventana, int) or ventana < 1:
            raise DatosInvalidos("ventana debe ser un entero >= 1")
        if isinstance(max_posiciones, bool) or not isinstance(max_posiciones, int):
            raise DatosInvalidos("max_posiciones debe ser un entero >= 1")
        if max_posiciones < 1:
            raise DatosInvalidos("max_posiciones debe ser un entero >= 1")
        if not 0 < float(fraccion) <= 1:
            raise DatosInvalidos("fraccion debe estar en (0, 1]")
        if not isinstance(umbral, (int, float)) or isinstance(umbral, bool):
            raise DatosInvalidos("umbral debe ser un numero")
        self.ventana = ventana
        self.umbral = float(umbral)
        self.fraccion = float(fraccion)
        self.max_posiciones = max_posiciones

    def decidir(self, contexto: ContextoMercado) -> list[Decision]:
        decisiones: list[Decision] = []
        # 1) Vender lo que ha perdido impulso.
        for tid, cantidad in contexto.cartera.posiciones:
            momento = contexto.momentum(tid, self.ventana)
            if momento is not None and momento < self.umbral:
                decisiones.append(Decision(tid, "venta", cantidad))

        # 2) Comprar los mejores momentos positivos.
        candidatos: list[tuple[float, str]] = []
        for tid in contexto.mercado.ids:
            momento = contexto.momentum(tid, self.ventana)
            if momento is not None and momento > self.umbral:
                candidatos.append((momento, tid))
        candidatos.sort(reverse=True)
        elegidos = [tid for _, tid in candidatos[: self.max_posiciones]]
        if not elegidos:
            return decisiones

        efectivo = contexto.cartera.efectivo
        presupuesto = efectivo * self.fraccion / len(elegidos)
        for tid in elegidos:
            cantidad = int(presupuesto // contexto.precio(tid))
            if cantidad > 0:
                decisiones.append(Decision(tid, "compra", cantidad))
        return decisiones


class Rebalanceo(EstrategiaInversion):
    """Mantiene una cartera con pesos objetivo dentro de una banda."""

    nombre = "rebalanceo"
    descripcion = "Corrige desviaciones respecto a pesos objetivo."

    def __init__(
        self,
        pesos: Mapping[str, float] | None = None,
        banda: float = 0.05,
    ) -> None:
        if isinstance(banda, bool) or not isinstance(banda, (int, float)):
            raise DatosInvalidos("banda debe ser un numero")
        if not 0 <= float(banda) < 1:
            raise DatosInvalidos("banda debe estar en [0, 1)")
        self.pesos = dict(pesos) if pesos is not None else None
        self.banda = float(banda)

    def _objetivo(self, contexto: ContextoMercado) -> dict[str, float]:
        if self.pesos is not None:
            total = sum(self.pesos.values())
            if total <= 0:
                raise DatosInvalidos("los pesos objetivo deben sumar mas de 0")
            return {tid: peso / total for tid, peso in self.pesos.items()}
        ids = contexto.mercado.ids
        if not ids:
            return {}
        return {tid: 1.0 / len(ids) for tid in ids}

    def decidir(self, contexto: ContextoMercado) -> list[Decision]:
        objetivos = self._objetivo(contexto)
        valor = contexto.valor_total()
        if valor <= 0 or not objetivos:
            return []
        decisiones: list[Decision] = []
        efectivo = contexto.cartera.efectivo
        for tid, peso in objetivos.items():
            precio = contexto.precio(tid)
            actual = contexto.posicion(tid) * precio
            objetivo = valor * peso
            desvio = (actual - objetivo) / valor
            if abs(desvio) <= self.banda:
                continue
            if desvio < 0:
                cantidad = int((objetivo - actual) // precio)
                cantidad = min(cantidad, int(efectivo // precio))
                if cantidad > 0:
                    decisiones.append(Decision(tid, "compra", cantidad))
                    efectivo -= cantidad * precio
            else:
                cantidad = int((actual - objetivo) // precio)
                cantidad = min(cantidad, contexto.posicion(tid))
                if cantidad > 0:
                    decisiones.append(Decision(tid, "venta", cantidad))
        return decisiones


#: Registro de estrategias disponibles para la fabrica.
ESTRATEGIAS: dict[str, type[EstrategiaInversion]] = {
    ComprarMantener.nombre: ComprarMantener,
    Momentum.nombre: Momentum,
    Rebalanceo.nombre: Rebalanceo,
}


def estrategias_disponibles() -> tuple[str, ...]:
    return tuple(sorted(ESTRATEGIAS))


def crear_estrategia(nombre: str, **parametros: object) -> EstrategiaInversion:
    """Fabrica de estrategias por nombre (Factory)."""
    if not isinstance(nombre, str) or not nombre.strip():
        raise EstrategiaDesconocida("el nombre de la estrategia no puede estar vacio")
    clave = nombre.strip().lower()
    clase = ESTRATEGIAS.get(clave)
    if clase is None:
        raise EstrategiaDesconocida(
            f"estrategia desconocida: {nombre!r} (validas: {estrategias_disponibles()})"
        )
    try:
        return clase(**parametros)  # type: ignore[arg-type]
    except TypeError as exc:
        raise DatosInvalidos(f"parametros no validos para {clave!r}: {exc}") from exc


def estrategia_desde_pares(nombre: str, pares: Sequence[str]) -> EstrategiaInversion:
    """Construye una estrategia desde ``clave=valor`` (usado por la CLI).

    Los valores se convierten de forma conservadora: ``int``, ``float`` o
    ``str``. Ejemplo: ``["ventana=10", "fraccion=0.4"]``.
    """
    parametros: dict[str, object] = {}
    for par in pares:
        if "=" not in par:
            raise DatosInvalidos(f"parametro invalido {par!r}; usa clave=valor")
        clave, valor = par.split("=", 1)
        clave = clave.strip()
        if not clave:
            raise DatosInvalidos(f"parametro invalido {par!r}; usa clave=valor")
        parametros[clave] = _convertir(valor.strip())
    return crear_estrategia(nombre, **parametros)


def _convertir(valor: str) -> object:
    for convertidor in (int, float):
        try:
            return convertidor(valor)
        except ValueError:
            continue
    return valor


__all__ = [
    "ESTRATEGIAS",
    "ComprarMantener",
    "ContextoMercado",
    "Decision",
    "EstrategiaInversion",
    "Momentum",
    "Rebalanceo",
    "crear_estrategia",
    "estrategia_desde_pares",
    "estrategias_disponibles",
]
