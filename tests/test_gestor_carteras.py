"""Tests del gestor de carteras (varios usuarios y cartera activa)."""

from __future__ import annotations

import pytest

from bolsa_sim import Cartera, GestorCarteras
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.excepciones import CarteraDesconocida, CarteraDuplicada, DatosInvalidos


def test_registra_cartera_inicial() -> None:
    cartera = cartera_demo()
    gestor = GestorCarteras(cartera)
    assert gestor.actual is cartera
    assert gestor.activa == "Dani"
    assert gestor.nombres() == ("Dani",)


def test_crear_y_seleccionar_carteras() -> None:
    gestor = GestorCarteras(cartera_demo())
    ana = gestor.crear("Ana", efectivo=2_000.0, comision=2.5)
    assert gestor.actual is ana
    assert ana.efectivo == 2_000.0
    assert ana.comision == 2.5
    assert gestor.nombres() == ("Dani", "Ana")

    gestor.seleccionar("dani")
    assert gestor.actual.propietario == "Dani"
    gestor.seleccionar("ANA")
    assert gestor.actual.propietario == "Ana"


def test_duplicados_no_distinguen_mayusculas() -> None:
    gestor = GestorCarteras(cartera_demo())
    with pytest.raises(CarteraDuplicada):
        gestor.crear("Dani")
    with pytest.raises(CarteraDuplicada):
        gestor.crear("dani", efectivo=1.0)
    with pytest.raises(CarteraDuplicada):
        gestor.registrar(Cartera("DANI"))


def test_nombre_vacio() -> None:
    gestor = GestorCarteras()
    with pytest.raises(DatosInvalidos):
        gestor.crear("   ")


def test_cartera_desconocida() -> None:
    gestor = GestorCarteras(cartera_demo())
    with pytest.raises(CarteraDesconocida):
        gestor.seleccionar("Nadie")
    with pytest.raises(CarteraDesconocida):
        gestor.obtener("Nadie")


def test_gestor_vacio() -> None:
    gestor = GestorCarteras()
    assert len(gestor) == 0
    with pytest.raises(CarteraDesconocida):
        _ = gestor.actual
    with pytest.raises(CarteraDesconocida):
        _ = gestor.activa


def test_desde_carteras_y_consulta() -> None:
    dani = cartera_demo()
    ana = Cartera("Ana", efectivo=500.0)
    gestor = GestorCarteras.desde_carteras([dani, ana], activa="ana")
    assert gestor.activa == "Ana"
    assert list(gestor) == [dani, ana]
    assert "Dani" in gestor
    assert "dani" in gestor
    assert "Nadie" not in gestor
    assert 42 not in gestor
    assert gestor.obtener("DANI") is dani
    assert gestor.carteras() == (dani, ana)


def test_registrar_tipo_invalido() -> None:
    gestor = GestorCarteras()
    with pytest.raises(TypeError):
        gestor.registrar("no-es-cartera")  # type: ignore[arg-type]


def test_carteras_son_independientes() -> None:
    mercado = mercado_demo()
    gestor = GestorCarteras(cartera_demo())
    ana = gestor.crear("Ana", efectivo=1_000.0)
    gestor.seleccionar("Dani")
    gestor.actual.invertir(mercado, "ACME", 2, mercado.precio_de("ACME"), "s0000")
    assert gestor.actual.posicion("ACME") == 2
    gestor.seleccionar("Ana")
    assert ana.posicion("ACME") == 0
