"""Tests de la fabrica de instrumentos y su serializacion."""

from __future__ import annotations

import json

import pytest

from bolsa_sim.accion import Accion
from bolsa_sim.bono import Bono
from bolsa_sim.etf import ETF
from bolsa_sim.excepciones import DatosInvalidos, TipoInstrumentoDesconocido
from bolsa_sim.fabrica import (
    CAMPOS_COMUNES,
    CAMPOS_ESPECIFICOS,
    FabricaInstrumentos,
    cargar_instrumentos_json,
    guardar_instrumentos_json,
    instrumento_a_dict,
    instrumentos_a_dicts,
)
from bolsa_sim.instrumento import InstrumentoBase


def _accion() -> Accion:
    return Accion(
        "ACME", "Acme Corp", "ACME", 0.2, 120.0, sector="Tecnologia", dividendo_anual=1.8
    )


def _bono() -> Bono:
    return Bono("BONO10", "Bono 10a", "B10", 0.05, 100.0, cupon_anual=0.04, vencimiento=10)


def _etf() -> ETF:
    return ETF("SPX", "ETF S&P", "SPX", 0.15, 400.0, indice="S&P 500", comision_gestion=0.002)


def test_dict_incluye_campos_comunes_y_especificos() -> None:
    datos = instrumento_a_dict(_accion())
    assert set(CAMPOS_COMUNES).issubset(datos)
    assert set(CAMPOS_ESPECIFICOS["accion"]).issubset(datos)
    assert datos["tipo"] == "accion"
    assert datos["sector"] == "Tecnologia"


def test_dict_de_instrumento_base_no_tiene_campos_extra() -> None:
    datos = instrumento_a_dict(InstrumentoBase("X", "X", "X", 0.1, 10.0))
    assert datos == {
        "tipo": "instrumento",
        "id": "X",
        "nombre": "X",
        "simbolo": "X",
        "volatilidad": 0.1,
        "precio_base": 10.0,
    }


def test_roundtrip_de_la_jerarquia() -> None:
    fabrica = FabricaInstrumentos.por_defecto()
    assert fabrica.tipos == ("accion", "bono", "etf")
    for original in (_accion(), _bono(), _etf()):
        copia = fabrica.desde_dict(instrumento_a_dict(original))
        assert type(copia) is type(original)
        assert copia == original
        assert copia.precio_base == pytest.approx(original.precio_base)
        assert copia.flujo_anual() == pytest.approx(original.flujo_anual())


def test_crear_con_tipo_mayusculas() -> None:
    fabrica = FabricaInstrumentos.por_defecto()
    inst = fabrica.crear("ACCION", id="A", nombre="A", simbolo="A", volatilidad=0.1, precio_base=1)
    assert isinstance(inst, Accion)


def test_tipo_desconocido() -> None:
    fabrica = FabricaInstrumentos.por_defecto()
    with pytest.raises(TipoInstrumentoDesconocido):
        fabrica.crear("futuro", id="F", nombre="F", simbolo="F", volatilidad=0.1, precio_base=1)
    with pytest.raises(TipoInstrumentoDesconocido):
        fabrica.crear("")


def test_campos_desconocidos_y_faltantes() -> None:
    fabrica = FabricaInstrumentos.por_defecto()
    with pytest.raises(DatosInvalidos):
        fabrica.crear(
            "accion",
            id="A",
            nombre="A",
            simbolo="A",
            volatilidad=0.1,
            precio_base=1,
            campo_raro=1,
        )
    with pytest.raises(DatosInvalidos):
        fabrica.crear("bono", id="B")


def test_desde_dict_valida_entrada() -> None:
    fabrica = FabricaInstrumentos.por_defecto()
    with pytest.raises(DatosInvalidos):
        fabrica.desde_dict({"id": "A"})  # type: ignore[dict-item]
    with pytest.raises(DatosInvalidos):
        fabrica.desde_dict(["no", "es", "mapping"])  # type: ignore[arg-type]
    with pytest.raises(DatosInvalidos):
        fabrica.desde_dict({"tipo": "accion"})


def test_registrar_clase_invalida() -> None:
    fabrica = FabricaInstrumentos()
    with pytest.raises(DatosInvalidos):
        fabrica.registrar("", Accion)
    with pytest.raises(DatosInvalidos):
        fabrica.registrar("x", dict)  # type: ignore[arg-type]


def test_registrar_subclase_personalizada() -> None:
    class Futuro(InstrumentoBase):
        tipo = "futuro"

    fabrica = FabricaInstrumentos()
    fabrica.registrar("futuro", Futuro)
    inst = fabrica.crear("futuro", id="F", nombre="F", simbolo="F", volatilidad=0.1, precio_base=1)
    assert isinstance(inst, Futuro)


def test_json_roundtrip(tmp_path) -> None:
    ruta = tmp_path / "sub" / "instrumentos.json"
    instrumentos = [_accion(), _bono(), _etf()]
    destino = guardar_instrumentos_json(instrumentos, ruta)
    assert destino == ruta and ruta.exists()
    recuperados = cargar_instrumentos_json(ruta)
    assert [type(i) for i in recuperados] == [Accion, Bono, ETF]
    assert [i.id for i in recuperados] == ["ACME", "BONO10", "SPX"]


def test_json_invalido(tmp_path) -> None:
    ruta = tmp_path / "mal.json"
    ruta.write_text("{no es json", encoding="utf-8")
    with pytest.raises(DatosInvalidos):
        cargar_instrumentos_json(ruta)
    ruta.write_text(json.dumps({"no": "lista"}), encoding="utf-8")
    with pytest.raises(DatosInvalidos):
        cargar_instrumentos_json(ruta)
    with pytest.raises(DatosInvalidos):
        cargar_instrumentos_json(tmp_path / "no_existe.json")


def test_instrumentos_a_dicts() -> None:
    datos = instrumentos_a_dicts([_accion(), _bono()])
    assert [d["tipo"] for d in datos] == ["accion", "bono"]
