"""Tests de persistencia: SQLite, memoria, JSON, servicio y exportadores."""

from __future__ import annotations

import json
import sqlite3

import pytest

from bolsa_sim.cartera import Cartera
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.estrategias import ComprarMantener
from bolsa_sim.excepciones import ErrorPersistencia, FormatoNoSoportado
from bolsa_sim.operacion import Operacion
from bolsa_sim.persistencia import (
    RepositorioFactory,
    RepositorioJSON,
    RepositorioMemoria,
    RepositorioSQLite,
    ServicioPersistencia,
    conectar,
    inicializar_esquema,
    version_esquema,
)
from bolsa_sim.persistencia.db import verificar_esquema
from bolsa_sim.persistencia.exportadores import (
    ExportadorCSV,
    ExportadorJSON,
    crear_exportador,
    datos_exportacion,
    exportar_resultados,
    exportar_simulacion,
    formatos_disponibles,
)
from bolsa_sim.persistencia.repositorios import Repositorio
from bolsa_sim.simulacion import simular


def _estado() -> tuple:
    mercado = mercado_demo(semilla=7)
    cartera = cartera_demo()
    for _ in range(3):
        mercado.avanzar_sesion(10)
    cartera.comprar(mercado, "ACME", 2, fecha="s0001")
    cartera.vender(mercado, "ACME", 1, fecha="s0002")
    cartera.anotar_valor(mercado=mercado)
    return mercado, cartera


def _repo(backend: str, tmp_path) -> Repositorio:
    if backend == "memoria":
        return RepositorioFactory.crear("memoria")
    if backend == "json":
        return RepositorioFactory.crear("json", tmp_path / "estado.json")
    return RepositorioFactory.crear("sqlite", tmp_path / "estado.sqlite")


@pytest.mark.parametrize("backend", ["memoria", "sqlite", "json"])
def test_servicio_guarda_y_carga_estado(backend, tmp_path) -> None:
    mercado, cartera = _estado()
    repo = _repo(backend, tmp_path)
    servicio = ServicioPersistencia(repo)
    servicio.guardar_estado(mercado, cartera)
    servicio.guardar_estado(mercado, cartera)  # idempotente
    assert servicio.listar_carteras() == ["Dani"]
    cargado_mercado, cargado_cartera = servicio.cargar_estado(
        mercado.nombre, cartera.propietario, semilla=7
    )
    assert cargado_mercado.sesion == mercado.sesion
    assert cargado_mercado.volumen_total == mercado.volumen_total
    assert set(cargado_mercado.instrumentos) == set(mercado.instrumentos)
    assert cargado_mercado.precio_de("ACME") == pytest.approx(mercado.precio_de("ACME"))
    assert cargado_cartera.efectivo == pytest.approx(cartera.efectivo)
    assert cargado_cartera.posiciones == cartera.posiciones
    assert cargado_cartera.historial == cartera.historial
    assert cargado_cartera.capital_inicial == pytest.approx(1_000.0)
    assert len(cargado_cartera.curva_valor) == len(cartera.curva_valor)
    assert len(cargado_mercado.sesiones) == mercado.sesion
    servicio.cerrar()


def test_servicio_carga_inexistente(tmp_path) -> None:
    servicio = ServicioPersistencia(RepositorioMemoria())
    with pytest.raises(ErrorPersistencia):
        servicio.cargar_mercado("X")
    with pytest.raises(ErrorPersistencia):
        servicio.cargar_cartera("Nadie")


def test_memoria_estado_y_operaciones() -> None:
    repo = RepositorioMemoria()
    mercado, cartera = _estado()
    servicio = ServicioPersistencia(repo)
    servicio.guardar_estado(mercado, cartera)
    estado = repo.estado()
    copia = RepositorioMemoria()
    copia.cargar_estado(estado)
    assert copia.listar_carteras() == ["Dani"]
    assert copia.listar_operaciones("Dani") == list(cartera.historial)
    assert copia.cargar_cartera("Nadie") is None
    assert copia.listar_sesiones("Otra") == []
    repo.cerrar()


def test_sincronizacion_append_only() -> None:
    repo = RepositorioMemoria()
    cartera = Cartera("Dani", efectivo=1_000.0)
    op1 = Operacion("s1", "ACME", 1, 10.0, "compra")
    op2 = Operacion("s2", "ACME", 1, 11.0, "compra")
    repo.guardar_cartera(cartera)
    repo.guardar_operacion("Dani", op1)
    assert repo.sincronizar_operaciones("Dani", [op1]) == 0
    assert repo.sincronizar_operaciones("Dani", [op1, op2]) == 1
    assert repo.listar_operaciones("Dani") == [op1, op2]
    with pytest.raises(ErrorPersistencia):
        repo.sincronizar_operaciones("Dani", [op2])


def test_sqlite_errores_de_cartera_inexistente(tmp_path) -> None:
    repo = RepositorioSQLite(tmp_path / "x.sqlite")
    with pytest.raises(ErrorPersistencia):
        repo.guardar_posiciones("Nadie", {"ACME": 1})
    with pytest.raises(ErrorPersistencia):
        repo.guardar_operacion("Nadie", Operacion("s1", "ACME", 1, 10.0, "compra"))
    repo.cerrar()


def test_sqlite_guarda_instrumentos_actualizados(tmp_path) -> None:
    repo = RepositorioSQLite(tmp_path / "x.sqlite")
    mercado, _ = _estado()
    repo.guardar_instrumentos(mercado.instrumentos.values())
    mercado.instrumentos["ACME"].precio_base = 999.0
    repo.guardar_instrumentos(mercado.instrumentos.values())
    datos = {d["id"]: d for d in repo.listar_instrumentos()}
    assert datos["ACME"]["precio_base"] == pytest.approx(999.0)
    assert datos["ACME"]["tipo"] == "accion"
    repo.cerrar()


def test_json_persiste_entre_instancias(tmp_path) -> None:
    ruta = tmp_path / "estado.json"
    repo = RepositorioJSON(ruta)
    mercado, cartera = _estado()
    ServicioPersistencia(repo).guardar_estado(mercado, cartera)
    repo.cerrar()
    assert ruta.exists()
    repo2 = RepositorioJSON(ruta)
    assert repo2.listar_carteras() == ["Dani"]
    assert repo2.listar_operaciones("Dani") == list(cartera.historial)
    assert repo2.listar_sesiones(mercado.nombre)
    repo2.cerrar()


def test_json_corrupto(tmp_path) -> None:
    ruta = tmp_path / "mal.json"
    ruta.write_text("{no json", encoding="utf-8")
    with pytest.raises(ErrorPersistencia):
        RepositorioJSON(ruta)
    ruta.write_text(json.dumps(["no", "dict"]), encoding="utf-8")
    with pytest.raises(ErrorPersistencia):
        RepositorioJSON(ruta)


def test_fabrica_de_repositorios(tmp_path) -> None:
    assert isinstance(RepositorioFactory.crear("memoria"), RepositorioMemoria)
    assert isinstance(RepositorioFactory.crear("sqlite", tmp_path / "x.db"), RepositorioSQLite)
    assert isinstance(RepositorioFactory.crear("json", tmp_path / "x.json"), RepositorioJSON)
    assert isinstance(RepositorioFactory.desde_ruta(tmp_path / "x.json"), RepositorioJSON)
    assert isinstance(RepositorioFactory.desde_ruta(tmp_path / "x.sqlite"), RepositorioSQLite)
    assert set(RepositorioFactory.backends_disponibles()) == {"json", "memoria", "sqlite"}
    with pytest.raises(ErrorPersistencia):
        RepositorioFactory.crear("nope")
    with pytest.raises(ErrorPersistencia):
        RepositorioFactory.crear("")


def test_esquema_y_transacciones() -> None:
    conexion = conectar(":memory:")
    inicializar_esquema(conexion)
    assert version_esquema(conexion) == "1"
    verificar_esquema(conexion)
    conexion.execute("UPDATE meta SET valor = '999' WHERE clave = 'esquema_version'")
    conexion.commit()
    with pytest.raises(ErrorPersistencia):
        verificar_esquema(conexion)
    conexion.close()


def test_transaccion_rollback_real() -> None:
    from bolsa_sim.persistencia.db import transaccion

    conexion = conectar(":memory:")
    inicializar_esquema(conexion)
    with (
        pytest.raises(ErrorPersistencia),
        transaccion(conexion),
    ):
        conexion.execute("INSERT INTO meta (clave, valor) VALUES ('x', '1')")
        raise sqlite3.IntegrityError("forzado")
    fila = conexion.execute("SELECT COUNT(*) AS n FROM meta WHERE clave = 'x'").fetchone()
    assert fila["n"] == 0
    conexion.close()


def test_exportacion_json_y_csv(tmp_path) -> None:
    mercado, cartera = _estado()
    datos = datos_exportacion(mercado, cartera)
    assert datos["cartera"]["propietario"] == "Dani"
    assert datos["mercado"]["instrumentos"]
    assert datos["mercado"]["sesiones"]
    assert "rentabilidad_total" in datos["metricas"]

    ruta_json = exportar_resultados(mercado, cartera, tmp_path / "out", "json")
    assert ruta_json.suffix == ".json"
    contenido = json.loads(ruta_json.read_text(encoding="utf-8"))
    assert contenido["cartera"]["propietario"] == "Dani"

    ruta_csv = exportar_resultados(mercado, cartera, tmp_path / "out.csv", "csv")
    lineas = ruta_csv.read_text(encoding="utf-8").splitlines()
    assert lineas[0].startswith("registro,propietario")
    assert any(linea.startswith("operacion,") for linea in lineas)
    assert any(linea.startswith("posicion,") for linea in lineas)
    assert any(linea.startswith("precio_sesion,") for linea in lineas)


def test_exportacion_a_directorio(tmp_path) -> None:
    mercado, cartera = _estado()
    destino = exportar_resultados(mercado, cartera, tmp_path, "json")
    assert destino == tmp_path / "resultados_cartera.json"
    assert destino.exists()


def test_exportadores_y_formatos(tmp_path) -> None:
    assert set(formatos_disponibles()) == {"csv", "json"}
    assert isinstance(crear_exportador("json"), ExportadorJSON)
    assert isinstance(crear_exportador("CSV"), ExportadorCSV)
    with pytest.raises(FormatoNoSoportado):
        crear_exportador("pdf")
    with pytest.raises(FormatoNoSoportado):
        crear_exportador("")
    mercado, cartera = _estado()
    datos = datos_exportacion(mercado, cartera)
    assert ExportadorJSON().exportar(datos, tmp_path / "x.json").exists()
    assert ExportadorCSV().exportar(datos, tmp_path / "x.csv").exists()


def test_exportar_simulacion(tmp_path) -> None:
    resultado = simular(mercado_demo(semilla=3), cartera_demo(), ComprarMantener(), sesiones=5)
    destino = exportar_simulacion(resultado, tmp_path / "sim")
    assert destino.suffix == ".json"
    assert json.loads(destino.read_text(encoding="utf-8"))["estrategia"] == resultado.estrategia


def test_servicio_exportar(tmp_path) -> None:
    mercado, cartera = _estado()
    servicio = ServicioPersistencia(RepositorioMemoria())
    destino = servicio.exportar(mercado, cartera, tmp_path / "res.json")
    assert destino.exists()
