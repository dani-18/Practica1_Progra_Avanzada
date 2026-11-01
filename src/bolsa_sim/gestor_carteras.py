"""Gestion de varias carteras (un usuario por cartera).

El simulador puede operar con varias carteras a la vez: cada una tiene su
propio efectivo, posiciones, historial y curva de valor. :class:`GestorCarteras`
mantiene el registro, valida duplicados y decide cual es la **cartera activa**
sobre la que trabajan la CLI, la GUI y la persistencia.

Uso::

    gestor = GestorCarteras(cartera_demo())
    gestor.crear("Ana", efectivo=2_000.0)
    gestor.seleccionar("Ana")
    print(gestor.actual.propietario)   # Ana
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .cartera import Cartera
from .excepciones import CarteraDesconocida, CarteraDuplicada, DatosInvalidos


class GestorCarteras:
    """Registro ordenado de carteras con una cartera activa."""

    def __init__(self, cartera_inicial: Cartera | None = None) -> None:
        self._carteras: dict[str, Cartera] = {}
        self._activa: str | None = None
        if cartera_inicial is not None:
            self.registrar(cartera_inicial)

    # ---- construccion ----------------------------------------------------
    @classmethod
    def desde_carteras(
        cls,
        carteras: Iterable[Cartera],
        *,
        activa: str | None = None,
    ) -> GestorCarteras:
        """Crea un gestor a partir de una coleccion (p. ej. cargada de SQLite)."""
        gestor = cls()
        for cartera in carteras:
            gestor.registrar(cartera, activar=False)
        if activa is not None:
            gestor.seleccionar(activa)
        elif gestor._carteras:
            gestor._activa = next(iter(gestor._carteras))
        return gestor

    def registrar(self, cartera: Cartera, *, activar: bool = True) -> Cartera:
        """Anade una cartera ya construida (no permite duplicados)."""
        if not isinstance(cartera, Cartera):
            raise TypeError("solo se pueden registrar objetos Cartera")
        clave = cartera.propietario
        if self._existe(clave):
            raise CarteraDuplicada(f"ya existe una cartera para {clave!r}")
        self._carteras[clave] = cartera
        if activar or self._activa is None:
            self._activa = clave
        return cartera

    def crear(
        self,
        propietario: str,
        efectivo: float = 1_000.0,
        comision: float = 1.0,
        *,
        activar: bool = True,
    ) -> Cartera:
        """Crea una cartera nueva y, por defecto, la deja activa."""
        nombre = str(propietario).strip()
        if not nombre:
            raise DatosInvalidos("el propietario no puede estar vacio")
        if self._existe(nombre):
            raise CarteraDuplicada(f"ya existe una cartera para {nombre!r}")
        cartera = Cartera(nombre, efectivo=efectivo, comision=comision)
        return self.registrar(cartera, activar=activar)

    # ---- seleccion -------------------------------------------------------
    def seleccionar(self, propietario: str) -> Cartera:
        """Activa una cartera por nombre (sin distinguir mayusculas)."""
        clave = self._resolver(propietario)
        self._activa = clave
        return self._carteras[clave]

    @property
    def actual(self) -> Cartera:
        """Cartera activa; falla si el gestor esta vacio."""
        if self._activa is None:
            raise CarteraDesconocida("no hay carteras registradas")
        return self._carteras[self._activa]

    @property
    def activa(self) -> str:
        """Nombre de la cartera activa."""
        return self.actual.propietario

    # ---- consulta --------------------------------------------------------
    def nombres(self) -> tuple[str, ...]:
        return tuple(self._carteras)

    def carteras(self) -> tuple[Cartera, ...]:
        return tuple(self._carteras.values())

    def obtener(self, propietario: str) -> Cartera:
        return self._carteras[self._resolver(propietario)]

    def __iter__(self) -> Iterator[Cartera]:
        return iter(self._carteras.values())

    def __len__(self) -> int:
        return len(self._carteras)

    def __contains__(self, propietario: object) -> bool:
        if not isinstance(propietario, str):
            return False
        try:
            self._resolver(propietario)
        except CarteraDesconocida:
            return False
        return True

    # ---- internos --------------------------------------------------------
    def _existe(self, propietario: str) -> bool:
        objetivo = propietario.strip().casefold()
        return any(nombre.casefold() == objetivo for nombre in self._carteras)

    def _resolver(self, propietario: str) -> str:
        clave = str(propietario).strip()
        if clave in self._carteras:
            return clave
        objetivo = clave.casefold()
        coincidencias = [nombre for nombre in self._carteras if nombre.casefold() == objetivo]
        if len(coincidencias) == 1:
            return coincidencias[0]
        disponibles = ", ".join(self._carteras) or "ninguna"
        raise CarteraDesconocida(
            f"cartera {propietario!r} no encontrada (disponibles: {disponibles})"
        )


__all__ = ["GestorCarteras"]
