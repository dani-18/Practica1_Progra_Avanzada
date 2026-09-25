"""Demostraciones del modelo de memoria (Tema 1).

Este modulo recoge las piezas didacticas que pide el enunciado de
PRAC1: identificar, explicar y corregir el defecto del *argumento por
defecto mutable*. Tambien expone utilidades para inspeccionar aliasing,
identidad vs igualdad y la diferencia entre tuplas y listas. Todo lo
del modulo es trazable desde el CLI (``python -m bolsa_sim --memoria``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


# =============================================================================
# 1) Identidad vs igualdad
# =============================================================================
def demostrar_identidad_y_igualdad() -> str:
    """Devuelve una cadena con una sesion canonica de identidad vs igualdad."""
    lineas: list[str] = []
    a = [1, 2, 3]
    b = a  # alias: mismo objeto
    z = list(a)  # copia: objeto nuevo con mismo contenido
    n = 10

    lineas.append("== Identidad vs igualdad ==")
    lineas.append(f"  a is b      -> {a is b}   (alias: {id(a) == id(b)})")
    lineas.append(f"  a == z      -> {a == z}   (igualdad de contenido)")
    lineas.append(f"  a is z      -> {a is z}")
    lineas.append(
        f"  id(n) == id(10)  -> {id(n) == id(10)}   "
        "(pequenos enteros en CPython son singleton, un mismo '10')"
    )

    b.append(4)
    lineas.append(f"  Tras b.append(4): a -> {a!r}")
    lineas.append("  -> ``b = a`` no copia: liga un nombre nuevo al MISMO objeto.")
    lineas.append("")
    lineas.append("== Tupla vs lista (inmutabilidad) ==")
    t = (1, 2, 3)
    lineas.append(f"  id(t)        -> {hex(id(t))}")
    t2 = (*t, 4)
    lineas.append(f"  id(t) == id(t2)  -> {t is t2}  (construir la tupla nueva no muta t)")
    lineas.append(f"  hash(t)      -> {hash(t)}  (las tuplas son hashables)")

    clave: tuple[int, int] = (0, 0)
    d = {clave: "origen"}
    lineas.append(f"  d[{{(0,0): ... }}][(0,0)] -> {d[clave]}  (tupla como clave: OK)")
    return "\n".join(lineas)


# =============================================================================
# 2) Defecto: argumento por defecto mutable
# =============================================================================
def registrar_evento_defectuoso(
    nombre: str,
    eventos: list[str] = [],  # noqa: B006  (demonstration of the bug)
    operacion: str = "alta",
) -> list[str]:
    """Version *defectuosa*: el parametro por defecto mutable es compartido.

    Cada llamada acumula sobre la MISMA lista porque ``[]`` se evalua
    UNA SOLA VEZ al definir la funcion, no en cada llamada. Este es el
    bug que PRAC1 nos pide identificar.
    """
    eventos.append(f"{operacion}:{nombre}")
    return eventos


def registrar_evento_correcto(
    nombre: str, eventos: list[str] | None = None, operacion: str = "alta"
) -> list[str]:
    """Version *corregida*: se usa ``None`` como centinela y se crea una lista nueva."""
    if eventos is None:
        eventos = []
    eventos.append(f"{operacion}:{nombre}")
    return eventos


def demostrar_defecto_estado_compartido() -> str:
    """Ilustra el defecto y la correccion con trazas paso a paso."""
    lineas: list[str] = []
    lineas.append("== Defecto conceptual: argumento por defecto mutable ==")
    lineas.append("")
    lineas.append("[Defectuoso]")
    r1 = registrar_evento_defectuoso("alta")
    r2 = registrar_evento_defectuoso("alta")
    lineas.append(f"  r1={r1!r}")
    lineas.append(f"  r2={r2!r}")
    lineas.append(f"  r1 is r2 -> {r1 is r2}  <- !! misma lista en cada llamada.")
    lineas.append("")
    lineas.append("[Corregido]")
    s1 = registrar_evento_correcto("alta")
    s2 = registrar_evento_correcto("alta")
    lineas.append(f"  s1={s1!r}")
    lineas.append(f"  s2={s2!r}")
    lineas.append(f"  s1 is s2 -> {s1 is s2}  <- cada llamada tiene su propia lista.")
    return "\n".join(lineas)


# =============================================================================
# 3) Inspección de objetos en general
# =============================================================================
def inspeccionar(objetos: Iterable[tuple[str, Any]]) -> str:
    """Imprime ``id``, ``is`` e ``==`` entre los pares dados."""
    objetos = list(objetos)
    lineas: list[str] = ["== Inspeccion de objetos =="]
    for nombre, obj in objetos:
        lineas.append(f"  {nombre}: tipo={type(obj).__name__:>8}  id=0x{id(obj):x}  valor={obj!r}")
    if len(objetos) >= 2:
        a_obj = objetos[0][1]
        b_obj = objetos[1][1]
        lineas.append(f"  {objetos[0][0]} is {objetos[1][0]}  -> {a_obj is b_obj}")
        lineas.append(f"  {objetos[0][0]} == {objetos[1][0]}  -> {a_obj == b_obj}")
    return "\n".join(lineas)
