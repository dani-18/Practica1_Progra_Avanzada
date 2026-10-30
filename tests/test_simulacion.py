"""Tests del motor de simulacion."""

from __future__ import annotations

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.estrategias import ComprarMantener, EstrategiaInversion, Momentum
from bolsa_sim.excepciones import DatosInvalidos, ErrorSimulacion
from bolsa_sim.simulacion import ResultadoSimulacion, Simulador, simular


@pytest.mark.parametrize("estrategia", [ComprarMantener(), Momentum(ventana=3)])
def test_ejecutar_simulacion(estrategia) -> None:
    mercado = mercado_demo(semilla=11)
    cartera = cartera_demo()
    resultado = simular(mercado, cartera, estrategia, sesiones=15, volumen=20)
    assert isinstance(resultado, ResultadoSimulacion)
    assert resultado.estrategia == estrategia.nombre
    assert resultado.sesiones == 15
    assert mercado.sesion == 15
    assert mercado.volumen_total == 300
    assert len(resultado.curva) == 16
    assert resultado.valor_inicial == pytest.approx(1_000.0)
    assert resultado.valor_final == pytest.approx(cartera.valor_total(mercado))
    assert resultado.numero_operaciones >= 0
    assert resultado.metricas.num_periodos == 15
    assert "sesiones" in str(resultado)


def test_resultado_es_serializable() -> None:
    resultado = simular(mercado_demo(semilla=7), cartera_demo(), ComprarMantener(), sesiones=5)
    datos = resultado.a_dict()
    assert datos["estrategia"] == "comprar_mantener"
    assert len(datos["curva"]) == 6
    assert isinstance(datos["operaciones"], list)
    assert "metricas" in datos
    assert datos["rentabilidad_total"] == pytest.approx(resultado.rentabilidad_total)


def test_simulacion_reproducible() -> None:
    r1 = simular(mercado_demo(semilla=123), cartera_demo(), Momentum(ventana=3), sesiones=20)
    r2 = simular(mercado_demo(semilla=123), cartera_demo(), Momentum(ventana=3), sesiones=20)
    assert r1.curva == r2.curva
    assert r1.operaciones == r2.operaciones


def test_simulador_valida_parametros() -> None:
    mercado = mercado_demo()
    cartera = cartera_demo()
    for sesiones in (0, -1, True):
        with pytest.raises(DatosInvalidos):
            Simulador(mercado, cartera, ComprarMantener(), sesiones=sesiones)
    for volumen in (0, -1, True):
        with pytest.raises(DatosInvalidos):
            Simulador(mercado, cartera, ComprarMantener(), volumen=volumen)


def test_error_de_estrategia_se_reenvuelve() -> None:
    class Rota(EstrategiaInversion):
        nombre = "rota"

        def decidir(self, contexto):
            raise RuntimeError("boom")

    with pytest.raises(ErrorSimulacion):
        Simulador(mercado_demo(), cartera_demo(), Rota(), sesiones=2).ejecutar()


def test_simulacion_sin_curva_previa() -> None:
    cartera = Cartera("Dani", efectivo=1_000.0)
    resultado = simular(mercado_demo(semilla=2), cartera, ComprarMantener(), sesiones=3)
    assert resultado.curva[0] == pytest.approx(1_000.0)
    assert len(resultado.curva) == 4


def test_ejecuta_ordenes_de_compra_y_venta() -> None:
    mercado = mercado_demo(semilla=5)
    cartera = cartera_demo()
    simular(mercado, cartera, ComprarMantener(), sesiones=2)
    assert cartera.total_operaciones >= 1
    assert any(op.tipo == "compra" for op in cartera.historial)
