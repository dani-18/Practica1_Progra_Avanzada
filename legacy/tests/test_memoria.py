"""Tests del modelo de memoria (Tema 1) y del defecto del argumento mutable."""

from __future__ import annotations

import pytest

from bolsa_sim.memoria import (
    demostrar_defecto_estado_compartido,
    demostrar_identidad_y_igualdad,
    inspeccionar,
    registrar_evento_correcto,
    registrar_evento_defectuoso,
)


def test_demostrar_identidad_y_igualdad_devuelve_texto() -> None:
    out = demostrar_identidad_y_igualdad()
    assert "Identidad" in out
    assert "Tupla" in out


def test_defecto_argumento_default_comparte_lista() -> None:
    """El bug pedagogico: la lista por defecto es la MISMA instancia."""
    r1 = registrar_evento_defectuoso("alta")
    r2 = registrar_evento_defectuoso("alta")
    assert r1 is r2
    assert r1 == r2  # contenido igual, pero identidad igual tambien


def test_correccion_argumento_default_no_comparte_lista() -> None:
    """La correccion: cada llamada parte de una lista nueva."""
    s1 = registrar_evento_correcto("alta")
    s2 = registrar_evento_correcto("alta")
    assert s1 is not s2
    assert s1 == s2


def test_pasando_lista_explicita_no_se_comparte() -> None:
    """Si el caller provee su lista, debe ser esa (correccion)."""
    buf = []
    s1 = registrar_evento_correcto("alta", eventos=buf)
    s2 = registrar_evento_correcto("alta", eventos=buf)
    assert s1 is s2 is buf  # ahora SI comparten, porque el caller lo decidio
    assert s1 == ["alta:alta", "alta:alta"]


def test_demostrar_defecto_estado_compartido_marca_ambas_partes() -> None:
    texto = demostrar_defecto_estado_compartido()
    assert "Defectuoso" in texto
    assert "Corregido" in texto


def test_tupla_es_hashable() -> None:
    t = (0, 0)
    d = {t: "origen"}
    assert d[(0, 0)] == "origen"


def test_lista_no_es_hashable_como_clave() -> None:
    with pytest.raises(TypeError):
        # Pylint/Ruff suelen avisar; la prueba lo verifica en runtime.
        d = {[0, 0]: "origen"}  # type: ignore[misc]
        _ = d[(0, 0)]


def test_inspeccionar_formatea() -> None:
    out = inspeccionar([("a", [1, 2]), ("b", [1, 2])])
    assert "a" in out and "b" in out
    assert "a == b" in out
