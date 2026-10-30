"""Tests de la jerarquia de excepciones de dominio."""

from __future__ import annotations

import pytest

from bolsa_sim.excepciones import (
    DatosInvalidos,
    ErrorBolsa,
    ErrorPersistencia,
    ErrorSimulacion,
    EstrategiaDesconocida,
    FondosInsuficientes,
    FormatoNoSoportado,
    InstrumentoDesconocido,
    InstrumentoDuplicado,
    OperacionInvalida,
    PosicionInsuficiente,
    TipoInstrumentoDesconocido,
)


def test_todas_heredan_de_error_bolsa() -> None:
    for clase in (
        DatosInvalidos,
        ErrorPersistencia,
        ErrorSimulacion,
        EstrategiaDesconocida,
        FondosInsuficientes,
        FormatoNoSoportado,
        InstrumentoDesconocido,
        InstrumentoDuplicado,
        OperacionInvalida,
        PosicionInsuficiente,
        TipoInstrumentoDesconocido,
    ):
        assert issubclass(clase, ErrorBolsa)


def test_compatibilidad_con_excepciones_builtin() -> None:
    assert issubclass(DatosInvalidos, ValueError)
    assert issubclass(InstrumentoDesconocido, KeyError)
    assert issubclass(ErrorPersistencia, RuntimeError)
    with pytest.raises(ValueError):
        raise OperacionInvalida("cantidad")
    with pytest.raises(KeyError):
        raise InstrumentoDesconocido("NOPE")


def test_errores_de_operacion_son_operacion_invalida() -> None:
    assert issubclass(FondosInsuficientes, OperacionInvalida)
    assert issubclass(PosicionInsuficiente, OperacionInvalida)
