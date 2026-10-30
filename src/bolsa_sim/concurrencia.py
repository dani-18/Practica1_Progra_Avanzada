"""Ejecucion concurrente de escenarios de simulacion.

Cada escenario construye su propio mercado, cartera y estrategia, por lo
que no comparte estado mutable y puede ejecutarse en un
``ThreadPoolExecutor`` sin bloqueos. La semilla hace los resultados
reproducibles aunque se ejecuten en paralelo.

Ejemplo::

    escenarios = escenarios_por_defecto()
    resultados = ejecutar_escenarios(escenarios, max_workers=4)
    for r in resultados:
        print(r.escenario.nombre, r.resultado.rentabilidad_total)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .demo import cartera_demo, mercado_demo
from .estrategias import crear_estrategia, estrategias_disponibles
from .excepciones import DatosInvalidos, ErrorSimulacion, EstrategiaDesconocida
from .simulacion import ResultadoSimulacion, Simulador


@dataclass(frozen=True, slots=True)
class Escenario:
    """Configuracion independiente de una simulacion."""

    nombre: str
    estrategia: str = "comprar_mantener"
    semilla: int = 42
    sesiones: int = 60
    volumen: int = 100
    parametros: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise DatosInvalidos("el nombre del escenario no puede estar vacio")
        if isinstance(self.semilla, bool) or not isinstance(self.semilla, int):
            raise DatosInvalidos("semilla debe ser un entero")
        if isinstance(self.sesiones, bool) or not isinstance(self.sesiones, int):
            raise DatosInvalidos("sesiones debe ser un entero")
        if self.sesiones <= 0:
            raise DatosInvalidos("sesiones debe ser un entero > 0")


@dataclass(frozen=True, slots=True)
class ResultadoEscenario:
    """Resultado de un escenario, con su configuracion de origen."""

    escenario: Escenario
    resultado: ResultadoSimulacion

    def a_dict(self) -> dict[str, Any]:
        return {
            "escenario": {
                "nombre": self.escenario.nombre,
                "estrategia": self.escenario.estrategia,
                "semilla": self.escenario.semilla,
                "sesiones": self.escenario.sesiones,
                "volumen": self.escenario.volumen,
                "parametros": self.escenario.parametros,
            },
            "resultado": self.resultado.a_dict(),
        }


def ejecutar_escenario(escenario: Escenario) -> ResultadoEscenario:
    """Ejecuta un escenario aislado y devuelve su resultado."""
    try:
        estrategia = crear_estrategia(escenario.estrategia, **escenario.parametros)
    except EstrategiaDesconocida:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        raise ErrorSimulacion(f"escenario {escenario.nombre!r}: {exc}") from exc
    mercado = mercado_demo(semilla=escenario.semilla)
    cartera = cartera_demo()
    resultado = Simulador(
        mercado,
        cartera,
        estrategia,
        sesiones=escenario.sesiones,
        volumen=escenario.volumen,
    ).ejecutar()
    return ResultadoEscenario(escenario=escenario, resultado=resultado)


def ejecutar_escenarios(
    escenarios: list[Escenario] | tuple[Escenario, ...],
    *,
    max_workers: int | None = None,
) -> list[ResultadoEscenario]:
    """Ejecuta los escenarios en paralelo, conservando el orden de entrada."""
    if not escenarios:
        raise DatosInvalidos("se necesita al menos un escenario")
    if max_workers is not None and (
        isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1
    ):
        raise DatosInvalidos("max_workers debe ser un entero >= 1 o None")
    trabajadores = min(max_workers or len(escenarios), len(escenarios))
    with ThreadPoolExecutor(max_workers=trabajadores) as ejecutor:
        return list(ejecutor.map(ejecutar_escenario, escenarios))


def escenarios_por_defecto(
    semillas: tuple[int, ...] = (7, 42, 99),
    sesiones: int = 60,
) -> list[Escenario]:
    """Una matriz estrategia x semilla para comparar en paralelo."""
    if not semillas:
        raise DatosInvalidos("se necesita al menos una semilla")
    return [
        Escenario(
            nombre=f"{estrategia}-s{semilla}",
            estrategia=estrategia,
            semilla=semilla,
            sesiones=sesiones,
        )
        for semilla in semillas
        for estrategia in estrategias_disponibles()
    ]


def comparar_estrategias(
    semilla: int = 42,
    sesiones: int = 60,
) -> list[ResultadoEscenario]:
    """Ejecuta todas las estrategias con la misma semilla."""
    escenarios = [
        Escenario(
            nombre=f"{nombre}-s{semilla}",
            estrategia=nombre,
            semilla=semilla,
            sesiones=sesiones,
        )
        for nombre in estrategias_disponibles()
    ]
    return ejecutar_escenarios(escenarios)


__all__ = [
    "Escenario",
    "ResultadoEscenario",
    "comparar_estrategias",
    "ejecutar_escenario",
    "ejecutar_escenarios",
    "escenarios_por_defecto",
]
