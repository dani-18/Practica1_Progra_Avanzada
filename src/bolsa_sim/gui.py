"""Interfaz grafica de escritorio con Tkinter (PRAC4).

Tkinter forma parte de la biblioteca estandar, asi que la GUI no anade
dependencias. El modulo se puede importar sin entorno grafico: las clases
de Tkinter se importan de forma perezosa dentro de ``AplicacionGUI`` y
``lanzar_gui``, y los helpers de formato son funciones puras testeables.

Uso::

    python -m bolsa_sim --gui
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .cartera import Cartera
from .demo import cartera_demo, mercado_demo
from .excepciones import ErrorBolsa
from .mercado import Mercado
from .metricas import metricas_cartera
from .persistencia.exportadores import exportar_resultados
from .persistencia.fabrica import RepositorioFactory
from .persistencia.servicio import ServicioPersistencia

if TYPE_CHECKING:
    pass


#: Altura y anchura por defecto del grafico de la cartera.
ANCHO_GRAFICO = 640
ALTO_GRAFICO = 180


def formatear_instrumentos(mercado: Mercado) -> list[tuple[str, str, str, str, str]]:
    """Filas (id, tipo, nombre, precio, volatilidad) para la tabla."""
    return [
        (
            inst.id,
            inst.tipo,
            inst.nombre,
            f"{inst.precio_base:.2f}",
            f"{inst.volatilidad:.2f}",
        )
        for inst in mercado.instrumentos.values()
    ]


def formatear_posiciones(cartera: Cartera, mercado: Mercado) -> list[tuple[str, str, str, str]]:
    """Filas (id, cantidad, precio, valor) de las posiciones abiertas."""
    filas: list[tuple[str, str, str, str]] = []
    for tid, cantidad in cartera.posiciones:
        precio = mercado.precio_de(tid)
        filas.append((tid, str(cantidad), f"{precio:.2f}", f"{cantidad * precio:.2f}"))
    return filas


def resumen_cartera(cartera: Cartera, mercado: Mercado) -> dict[str, str]:
    """Etiquetas del panel de cartera, ya formateadas."""
    metricas = metricas_cartera(cartera, mercado)
    return {
        "propietario": cartera.propietario,
        "efectivo": f"{cartera.efectivo:.2f} EUR",
        "invertido": f"{cartera.valor_invertido(mercado):.2f} EUR",
        "valor_total": f"{cartera.valor_total(mercado):.2f} EUR",
        "operaciones": str(cartera.total_operaciones),
        "rentabilidad": f"{metricas.rentabilidad_total:+.2%}",
        "sharpe": f"{metricas.ratio_sharpe:.2f}",
        "drawdown": f"{metricas.max_drawdown:.2%}",
    }


def puntos_curva(
    serie: tuple[float, ...] | list[float],
    ancho: int = ANCHO_GRAFICO,
    alto: int = ALTO_GRAFICO,
    margen: int = 12,
) -> list[tuple[float, float]]:
    """Convierte una serie de valores en coordenadas del canvas (y invertida)."""
    valores = list(serie)
    if not valores:
        return []
    if len(valores) == 1:
        return [(margen, alto / 2)]
    minimo, maximo = min(valores), max(valores)
    rango = maximo - minimo
    util_ancho = max(1, ancho - 2 * margen)
    util_alto = max(1, alto - 2 * margen)
    puntos: list[tuple[float, float]] = []
    for i, valor in enumerate(valores):
        x = margen + util_ancho * i / (len(valores) - 1)
        y = alto / 2 if rango == 0 else margen + util_alto * (1 - (valor - minimo) / rango)
        puntos.append((x, y))
    return puntos


@dataclass
class EstadoGUI:
    """Estado minimo que la GUI muestra (facilita tests sin Tk)."""

    mercado: Mercado
    cartera: Cartera

    @classmethod
    def por_defecto(cls) -> EstadoGUI:
        return cls(mercado=mercado_demo(), cartera=cartera_demo())


class AplicacionGUI:
    """Ventana principal: tabla de instrumentos, cartera y grafico."""

    def __init__(
        self,
        raiz: Any,
        mercado: Mercado | None = None,
        cartera: Cartera | None = None,
    ) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.raiz = raiz
        self.mercado = mercado if mercado is not None else mercado_demo()
        self.cartera = cartera if cartera is not None else cartera_demo()
        self.repositorio: Any | None = None
        self.servicio: ServicioPersistencia | None = None
        raiz.title("Simulador de Bolsa y Carteras")
        raiz.minsize(900, 620)
        self._construir()
        self.actualizar()

    # ---- construccion ----------------------------------------------------
    def _construir(self) -> None:
        tk, ttk = self.tk, self.ttk
        principal = ttk.Frame(self.raiz, padding=10)
        principal.pack(fill="both", expand=True)

        cabecera = ttk.Frame(principal)
        cabecera.pack(fill="x", pady=(0, 8))
        ttk.Label(
            cabecera,
            text="Simulador de Bolsa y Carteras",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")

        cuerpo = ttk.Frame(principal)
        cuerpo.pack(fill="both", expand=True)

        # --- tabla de instrumentos --------------------------------------
        izquierda = ttk.LabelFrame(cuerpo, text="Mercado", padding=6)
        izquierda.pack(side="left", fill="both", expand=True, padx=(0, 8))
        columnas = ("id", "tipo", "nombre", "precio", "vol")
        self.tabla = ttk.Treeview(
            izquierda, columns=columnas, show="headings", height=9, selectmode="browse"
        )
        for col, titulo, ancho in (
            ("id", "ID", 80),
            ("tipo", "Tipo", 80),
            ("nombre", "Nombre", 190),
            ("precio", "Precio", 90),
            ("vol", "Vol.", 60),
        ):
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="e" if col in ("precio", "vol") else "w")
        self.tabla.pack(fill="both", expand=True)

        botones = ttk.Frame(izquierda)
        botones.pack(fill="x", pady=(8, 0))
        for texto, accion in (
            ("Avanzar sesion", self.avanzar_sesion),
            ("Shock -10%", lambda: self.aplicar_shock(-0.10)),
            ("Comprar", self.comprar),
            ("Vender", self.vender),
            ("Simular", self.simular),
        ):
            ttk.Button(botones, text=texto, command=accion).pack(side="left", padx=2)

        # --- panel de cartera --------------------------------------------
        derecha = ttk.LabelFrame(cuerpo, text="Cartera", padding=6)
        derecha.pack(side="left", fill="y")
        self.variables: dict[str, Any] = {}
        for clave, etiqueta in (
            ("propietario", "Propietario"),
            ("efectivo", "Efectivo"),
            ("invertido", "Invertido"),
            ("valor_total", "Valor total"),
            ("operaciones", "Operaciones"),
            ("rentabilidad", "Rentabilidad"),
            ("sharpe", "Sharpe"),
            ("drawdown", "Max drawdown"),
        ):
            fila = ttk.Frame(derecha)
            fila.pack(fill="x", pady=2)
            ttk.Label(fila, text=f"{etiqueta}:", width=13).pack(side="left")
            variable = tk.StringVar(value="-")
            self.variables[clave] = variable
            ttk.Label(fila, textvariable=variable).pack(side="left")

        self.tabla_posiciones = ttk.Treeview(
            derecha, columns=("id", "cant", "precio", "valor"), show="headings", height=6
        )
        for col, titulo in (
            ("id", "ID"),
            ("cant", "Cant."),
            ("precio", "Precio"),
            ("valor", "Valor"),
        ):
            self.tabla_posiciones.heading(col, text=titulo)
            self.tabla_posiciones.column(col, width=72, anchor="e" if col != "id" else "w")
        self.tabla_posiciones.pack(fill="x", pady=(8, 0))

        acciones = ttk.Frame(derecha)
        acciones.pack(fill="x", pady=(8, 0))
        for texto, accion in (
            ("Metricas", self.mostrar_metricas),
            ("Guardar", self.guardar),
            ("Cargar", self.cargar),
            ("Exportar", self.exportar),
        ):
            ttk.Button(acciones, text=texto, command=accion).pack(fill="x", pady=1)

        # --- grafico ------------------------------------------------------
        grafico = ttk.LabelFrame(principal, text="Evolucion del valor de la cartera", padding=6)
        grafico.pack(fill="both", expand=True, pady=(8, 0))
        self.canvas = tk.Canvas(
            grafico, height=ALTO_GRAFICO, background="white", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.estado = tk.StringVar(value="Listo.")
        ttk.Label(principal, textvariable=self.estado, anchor="w").pack(fill="x", pady=(6, 0))

    # ---- acciones --------------------------------------------------------
    def actualizar(self) -> None:
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for fila in formatear_instrumentos(self.mercado):
            self.tabla.insert("", "end", values=fila)

        for item in self.tabla_posiciones.get_children():
            self.tabla_posiciones.delete(item)
        for fila in formatear_posiciones(self.cartera, self.mercado):
            self.tabla_posiciones.insert("", "end", values=fila)

        for clave, valor in resumen_cartera(self.cartera, self.mercado).items():
            if clave in self.variables:
                self.variables[clave].set(valor)
        self._dibujar_curva()
        self.estado.set(
            f"Sesion {self.mercado.sesion} | {self.cartera.propietario} | "
            f"{self.mercado.nombre}"
        )

    def _dibujar_curva(self) -> None:
        self.canvas.delete("all")
        serie = self.cartera.curva_valor
        if not serie:
            self.canvas.create_text(
                ANCHO_GRAFICO / 2,
                ALTO_GRAFICO / 2,
                text="Sin datos de cartera",
                fill="#888888",
            )
            return
        ancho = max(int(self.canvas.winfo_width()), ANCHO_GRAFICO)
        alto = max(int(self.canvas.winfo_height()), ALTO_GRAFICO)
        puntos = puntos_curva(serie, ancho, alto)
        if len(puntos) >= 2:
            coordenadas = [coord for punto in puntos for coord in punto]
            self.canvas.create_line(*coordenadas, fill="#1565c0", width=2)
        for x, y in puntos[-1:]:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#1565c0", outline="")
        self.canvas.create_text(
            8,
            8,
            anchor="nw",
            text=f"{serie[-1]:.2f} EUR",
            fill="#333333",
        )

    def _seleccionado(self) -> str | None:
        seleccion = self.tabla.selection()
        if not seleccion:
            self.estado.set("Selecciona un instrumento de la tabla.")
            return None
        valores = self.tabla.item(seleccion[0], "values")
        return str(valores[0]) if valores else None

    def avanzar_sesion(self) -> None:
        self.mercado.avanzar_sesion(100)
        self.actualizar()

    def aplicar_shock(self, variacion: float) -> None:
        self.mercado.aplicar_shock(variacion)
        self.actualizar()
        self.estado.set(f"Shock aplicado: {variacion:+.0%}")

    def comprar(self) -> None:
        from tkinter import simpledialog

        tid = self._seleccionado()
        if tid is None:
            return
        cantidad = simpledialog.askinteger("Comprar", f"Unidades de {tid}:", minvalue=1)
        if cantidad is None:
            return
        try:
            op = self.cartera.comprar(self.mercado, tid, cantidad)
        except ErrorBolsa as exc:
            self.estado.set(f"Error: {exc}")
            return
        self.actualizar()
        self.estado.set(f"Compra ejecutada: {op!r}")

    def vender(self) -> None:
        from tkinter import simpledialog

        tid = self._seleccionado()
        if tid is None:
            return
        cantidad = simpledialog.askinteger("Vender", f"Unidades de {tid}:", minvalue=1)
        if cantidad is None:
            return
        try:
            op = self.cartera.vender(self.mercado, tid, cantidad)
        except ErrorBolsa as exc:
            self.estado.set(f"Error: {exc}")
            return
        self.actualizar()
        self.estado.set(f"Venta ejecutada: {op!r}")

    def mostrar_metricas(self) -> None:
        from tkinter import messagebox

        metricas = metricas_cartera(self.cartera, self.mercado)
        messagebox.showinfo("Metricas de la cartera", str(metricas))

    def simular(self) -> None:
        from tkinter import messagebox

        from .concurrencia import comparar_estrategias

        resultados = comparar_estrategias(
            semilla=self.mercado.semilla if self.mercado.semilla is not None else 42,
            sesiones=60,
        )
        texto = "\n".join(
            f"{r.escenario.estrategia}: {r.resultado.rentabilidad_total:+.2%} "
            f"(Sharpe {r.resultado.metricas.ratio_sharpe:.2f})"
            for r in resultados
        )
        messagebox.showinfo("Comparacion de estrategias (60 sesiones)", texto)

    def guardar(self) -> None:
        from tkinter import filedialog

        ruta = filedialog.asksaveasfilename(
            defaultextension=".sqlite",
            filetypes=[("SQLite", "*.sqlite"), ("JSON", "*.json")],
        )
        if not ruta:
            return
        anterior = self.repositorio
        self.repositorio = RepositorioFactory.desde_ruta(ruta)
        self.servicio = ServicioPersistencia(self.repositorio)
        self.servicio.guardar_estado(self.mercado, self.cartera)
        self.cartera.repositorio = self.repositorio
        if anterior is not None and anterior is not self.repositorio:
            anterior.cerrar()
        self.estado.set(f"Estado guardado en {ruta}")

    def cargar(self) -> None:
        from tkinter import filedialog, messagebox

        ruta = filedialog.askopenfilename(
            filetypes=[("SQLite/JSON", "*.sqlite *.db *.json"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        try:
            anterior = self.repositorio
            self.repositorio = RepositorioFactory.desde_ruta(ruta)
            servicio = ServicioPersistencia(self.repositorio)
            self.mercado, self.cartera = servicio.cargar_estado(
                self.mercado.nombre,
                self.cartera.propietario,
                semilla=self.mercado.semilla,
            )
            self.servicio = servicio
            self.cartera.repositorio = self.repositorio
            if anterior is not None and anterior is not self.repositorio:
                anterior.cerrar()
            self.actualizar()
        except ErrorBolsa as exc:
            messagebox.showerror("Error al cargar", str(exc))

    def exportar(self) -> None:
        from tkinter import filedialog, messagebox

        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")],
        )
        if not ruta:
            return
        formato = "csv" if ruta.lower().endswith(".csv") else "json"
        destino = exportar_resultados(self.mercado, self.cartera, ruta, formato)
        self.estado.set(f"Exportado en {destino}")
        messagebox.showinfo("Exportacion", f"Resultados exportados en:\n{destino}")

    def cerrar(self) -> None:
        """Cierra el repositorio abierto por la ventana, si lo hay."""
        if self.servicio is not None:
            self.servicio.cerrar()


def gui_disponible() -> bool:
    """Comprueba si hay un entorno Tk utilizable (sin abrir ventana visible)."""
    try:
        import tkinter as tk
    except ImportError:  # pragma: no cover - depende de la instalacion
        return False
    try:
        raiz = tk.Tk()
    except tk.TclError:  # pragma: no cover - CI sin display
        return False
    raiz.destroy()
    return True


def lanzar_gui(
    mercado: Mercado | None = None,
    cartera: Cartera | None = None,
) -> int:
    """Abre la ventana principal y bloquea hasta cerrarla."""
    import tkinter as tk

    raiz = tk.Tk()
    app = AplicacionGUI(raiz, mercado, cartera)
    try:
        raiz.mainloop()
    finally:
        app.cerrar()
    return 0


__all__ = [
    "ALTO_GRAFICO",
    "ANCHO_GRAFICO",
    "AplicacionGUI",
    "EstadoGUI",
    "formatear_instrumentos",
    "formatear_posiciones",
    "gui_disponible",
    "lanzar_gui",
    "puntos_curva",
    "resumen_cartera",
]
