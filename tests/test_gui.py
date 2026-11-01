"""Tests de la GUI: helpers puros y ventana Tkinter cuando hay display."""

from __future__ import annotations

import pytest

from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.gui import (
    AplicacionGUI,
    EstadoGUI,
    formatear_instrumentos,
    formatear_posiciones,
    gui_disponible,
    puntos_curva,
    resumen_cartera,
)


def test_formatear_instrumentos() -> None:
    filas = formatear_instrumentos(mercado_demo())
    assert len(filas) == 3
    assert filas[0][0] == "ACME"
    assert filas[0][3] == "120.00"


def test_formatear_posiciones_y_resumen() -> None:
    mercado = mercado_demo()
    cartera = cartera_demo()
    cartera.comprar(mercado, "ACME", 2, fecha="s1")
    filas = formatear_posiciones(cartera, mercado)
    assert filas == [("ACME", "2", "120.00", "240.00")]
    resumen = resumen_cartera(cartera, mercado)
    assert resumen["propietario"] == "Dani"
    assert resumen["efectivo"] == "759.00 EUR"
    assert resumen["invertido"] == "240.00 EUR"
    assert resumen["operaciones"] == "1"
    assert resumen["rentabilidad"].startswith("-")


def test_puntos_curva() -> None:
    assert puntos_curva([]) == []
    assert puntos_curva([100.0]) == [(12, 90.0)]
    plana = puntos_curva([100.0, 100.0], ancho=100, alto=50)
    assert all(y == 25.0 for _, y in plana)
    puntos = puntos_curva([100.0, 110.0, 105.0], ancho=100, alto=50)
    assert puntos[0] == (12, 38.0)
    assert puntos[1] == (50, 12.0)
    assert puntos[2] == (88, 25.0)


def test_estado_gui() -> None:
    estado = EstadoGUI.por_defecto()
    assert estado.mercado.nombre == "Bolsa Continuo"
    assert estado.cartera.propietario == "Dani"


def test_gui_disponible_devuelve_bool() -> None:
    assert isinstance(gui_disponible(), bool)


@pytest.fixture
def ventana(monkeypatch):
    pytest.importorskip("tkinter")
    if not gui_disponible():
        pytest.skip("sin entorno grafico")
    import tkinter as tk

    raiz = tk.Tk()
    raiz.withdraw()
    app = AplicacionGUI(raiz, mercado_demo(), cartera_demo())
    try:
        yield app, raiz, monkeypatch
    finally:
        app.cerrar()
        raiz.destroy()


def test_gui_actualiza_tablas(ventana) -> None:
    app, raiz, _ = ventana
    raiz.update_idletasks()
    assert len(app.tabla.get_children()) == 3
    app.avanzar_sesion()
    app.aplicar_shock(-0.10)
    assert app.mercado.sesion == 1
    assert "Shock aplicado" in app.estado.get()


def test_gui_compra_y_venta(ventana) -> None:
    app, _raiz, monkeypatch = ventana
    import tkinter.simpledialog as simpledialog

    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **k: 1)
    seleccion = app.tabla.get_children()
    app.tabla.selection_set(seleccion[0])
    app.comprar()
    assert app.cartera.posicion("ACME") == 1
    assert "Compra ejecutada" in app.estado.get()
    assert len(app.tabla_posiciones.get_children()) == 1

    # ``actualizar`` reconstruye la tabla: hay que volver a seleccionar.
    app.tabla.selection_set(app.tabla.get_children()[0])
    app.vender()
    assert app.cartera.posicion("ACME") == 0
    assert "Venta ejecutada" in app.estado.get()


def test_gui_errores_de_compra(ventana) -> None:
    app, _, monkeypatch = ventana
    import tkinter.simpledialog as simpledialog

    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **k: 100)
    app.tabla.selection_set(app.tabla.get_children()[0])
    app.comprar()
    assert "Error:" in app.estado.get()


def test_gui_metricas_y_simulacion(ventana) -> None:
    app, _, monkeypatch = ventana
    import tkinter.messagebox as messagebox

    mensajes: list[str] = []
    monkeypatch.setattr(messagebox, "showinfo", lambda titulo, texto: mensajes.append(titulo))
    app.mostrar_metricas()
    app.simular()
    assert "Metricas de la cartera" in mensajes
    assert "Comparacion de estrategias (60 sesiones)" in mensajes


def test_gui_guardar_cargar_exportar(ventana, tmp_path) -> None:
    app, _, monkeypatch = ventana
    import tkinter.filedialog as filedialog

    ruta = tmp_path / "gui.sqlite"
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(ruta))
    app.guardar()
    assert ruta.exists()
    assert "Estado guardado" in app.estado.get()
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(ruta))
    app.cargar()
    assert app.servicio is not None

    destino = tmp_path / "gui.json"
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(destino))
    mensajes: list[str] = []
    import tkinter.messagebox as messagebox

    monkeypatch.setattr(messagebox, "showinfo", lambda titulo, texto: mensajes.append(texto))
    app.exportar()
    assert destino.exists()
    assert mensajes


def test_gui_dialogos_cancelados(ventana) -> None:
    app, _, monkeypatch = ventana
    import tkinter.filedialog as filedialog
    import tkinter.simpledialog as simpledialog

    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **k: None)
    app.tabla.selection_set(app.tabla.get_children()[0])
    app.comprar()
    app.vender()
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: "")
    app.guardar()
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: "")
    app.cargar()
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: "")
    app.exportar()


def test_gui_sin_seleccion(ventana) -> None:
    app, _, _ = ventana
    assert app._seleccionado() is None
    assert "Selecciona" in app.estado.get()


def test_gui_crear_y_cambiar_cartera(ventana) -> None:
    app, _raiz, monkeypatch = ventana
    import tkinter.simpledialog as simpledialog

    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **k: "Ana")
    monkeypatch.setattr(simpledialog, "askfloat", lambda *a, **k: 1_500.0)
    app.nueva_cartera()
    assert app.cartera.propietario == "Ana"
    assert app.cartera.efectivo == 1_500.0
    assert "Ana" in app.selector_cartera["values"]
    assert "Ana" in app.estado.get()

    app.selector_cartera.set("Dani")
    app.seleccionar_cartera()
    assert app.cartera.propietario == "Dani"
    assert "Dani" in app.estado.get()
