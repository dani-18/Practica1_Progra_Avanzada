"""Interfaz interactiva de linea de comandos del simulador.

Se lanza con::

    python -m bolsa_sim --cli

y ofrece una consola para operar el mercado: listar instrumentos, consultar
precios, comprar/vender, avanzar sesiones, ver cartera e historial, calcular
metricas, simular estrategias, comparar escenarios en paralelo, aplicar
shocks y guardar/cargar el estado en SQLite.

El procesamiento de cada linea esta separado de la lectura por teclado
(``Shell.ejecutar`` recibe una cadena y devuelve si hay que continuar),
lo que permite probar la interfaz sin entrada interactiva.
"""

from __future__ import annotations

import os
import shlex
from collections.abc import Callable
from typing import Any

from .cartera import Cartera
from .concurrencia import comparar_estrategias
from .demo import cartera_demo, mercado_demo
from .estrategias import (
    ESTRATEGIAS,
    EstrategiaInversion,
    crear_estrategia,
    estrategia_desde_pares,
)
from .excepciones import ErrorBolsa
from .gestor_carteras import GestorCarteras
from .logging_config import obtener_logger
from .mercado import Mercado
from .metricas import metricas_cartera
from .persistencia.exportadores import exportar_resultados, formatos_disponibles
from .persistencia.fabrica import RepositorioFactory
from .persistencia.servicio import ServicioPersistencia
from .simulacion import Simulador

log = obtener_logger(__name__)


class Shell:
    """Consola interactiva sobre un ``Mercado`` y una ``Cartera``."""

    def __init__(
        self,
        mercado: Mercado | None = None,
        cartera: Cartera | None = None,
        *,
        entrada: Callable[[str], str] = input,
        salida: Callable[[str], None] = print,
        repositorio: Any | None = None,
        estrategia: EstrategiaInversion | None = None,
    ) -> None:
        self.mercado = mercado if mercado is not None else mercado_demo()
        self._gestor = GestorCarteras(cartera if cartera is not None else cartera_demo())
        self._entrada = entrada
        self._salida = salida
        self.repositorio = repositorio
        self.servicio = ServicioPersistencia(repositorio) if repositorio else None
        if repositorio is not None:
            self.cartera.repositorio = repositorio
        self.estrategia = estrategia or crear_estrategia("comprar_mantener")
        # Mapa comando -> metodo (los alias apuntan al mismo metodo).
        self._comandos: dict[str, Callable[[list[str]], bool]] = {
            "help": self._cmd_help,
            "?": self._cmd_help,
            "list": self._cmd_list,
            "ls": self._cmd_list,
            "market": self._cmd_market,
            "portfolio": self._cmd_portfolio,
            "status": self._cmd_portfolio,
            "price": self._cmd_price,
            "buy": self._cmd_buy,
            "sell": self._cmd_sell,
            "next": self._cmd_next,
            "history": self._cmd_history,
            "metrics": self._cmd_metrics,
            "strategies": self._cmd_strategies,
            "strategy": self._cmd_strategy,
            "simulate": self._cmd_simulate,
            "parallel": self._cmd_parallel,
            "shock": self._cmd_shock,
            "chart": self._cmd_chart,
            "export": self._cmd_export,
            "portfolios": self._cmd_portfolios,
            "carteras": self._cmd_portfolios,
            "users": self._cmd_portfolios,
            "new": self._cmd_new,
            "create": self._cmd_new,
            "use": self._cmd_use,
            "switch": self._cmd_use,
            "select": self._cmd_use,
            "save": self._cmd_save,
            "load": self._cmd_load,
            "quit": self._cmd_quit,
            "exit": self._cmd_quit,
        }

    @property
    def cartera(self) -> Cartera:
        """Cartera activa sobre la que operan los comandos."""
        return self._gestor.actual

    @property
    def carteras(self) -> GestorCarteras:
        """Gestor de todas las carteras de la sesion."""
        return self._gestor

    # ---- motor de la consola ---------------------------------------------
    def ejecutar(self, linea: str) -> bool:
        """Procesa una linea. Devuelve ``False`` cuando hay que salir."""
        try:
            partes = _dividir_linea(linea)
        except ValueError as exc:
            log.warning("entrada no valida en la CLI: %s", exc)
            self._salida(f"Entrada no valida: {exc}")
            return True
        if not partes:
            return True
        comando, *args = partes
        metodo = self._comandos.get(comando.lower())
        if metodo is None:
            log.warning("comando desconocido en la CLI: %r", comando)
            self._salida(f"Comando desconocido: {comando!r}. Usa 'help'.")
            return True
        log.debug("CLI ejecuta %r con argumentos=%r", comando, args)
        try:
            return metodo(args)
        except ErrorBolsa as exc:
            log.error("error de dominio en la CLI (%s): %s", comando, exc)
            self._salida(f"Error: {exc}")
            return True

    def run(self) -> None:
        """Bucle principal: lee lineas hasta ``quit``/``exit`` o EOF."""
        self._salida(
            "Simulador de Bolsa (CLI). Escribe 'help' para ver los comandos; "
            f"cartera activa: {self._gestor.activa!r}."
        )
        while True:
            try:
                linea = self._entrada("bolsa> ")
            except (EOFError, KeyboardInterrupt):
                self._salida("")
                break
            if not self.ejecutar(linea):
                break
        self._salida("Hasta luego.")

    def cerrar(self) -> None:
        """Cierra el repositorio si la sesion abrio uno."""
        if self.servicio is not None:
            self.servicio.cerrar()
        elif self.repositorio is not None:
            self.repositorio.cerrar()

    # ---- comandos --------------------------------------------------------
    def _cmd_help(self, args: list[str]) -> bool:
        self._salida("Comandos disponibles:")
        self._salida("  help                         muestra esta ayuda")
        self._salida("  list                         lista los instrumentos del mercado")
        self._salida("  market                       muestra el estado del mercado")
        self._salida("  portfolio | status           muestra la cartera activa y su valor")
        self._salida("  portfolios | carteras | users  lista las carteras y marca la activa")
        self._salida("  new <usuario> [efectivo] [comision]  crea una cartera y la activa")
        self._salida("  use <usuario>                cambia la cartera activa")
        self._salida("  price <instrumento>          consulta el precio actual")
        self._salida("  buy <instrumento> <cantidad> [precio]   compra")
        self._salida("  sell <instrumento> <cantidad> [precio]  vende")
        self._salida("  next [volumen]               avanza una sesion de mercado")
        self._salida("  shock <variacion>            aplica un shock (ej. -0.15)")
        self._salida("  history                      muestra el historial de operaciones")
        self._salida("  metrics                      metricas de rentabilidad y riesgo")
        self._salida("  chart <instrumento>          grafico ASCII de precios")
        self._salida("  strategies                   lista estrategias disponibles")
        self._salida("  strategy <nombre> [k=v...]   fija la estrategia de simulacion")
        self._salida("  simulate [n] [estrategia]    simula n sesiones y muestra metricas")
        self._salida("  parallel [n]                 compara todas las estrategias en paralelo")
        self._salida("  export <json|csv> <ruta>     exporta resultados")
        self._salida("  save [ruta]                  guarda todas las carteras en SQLite")
        self._salida("  load <ruta> [propietario]    carga el estado y elige la cartera activa")
        self._salida("  quit | exit                  sale de la consola")
        return True

    def _cmd_list(self, args: list[str]) -> bool:
        self._salida(f"Mercado {self.mercado.nombre!r} (sesion {self.mercado.sesion}):")
        for inst in self.mercado.instrumentos.values():
            self._salida(
                f"  {inst.id:<8} {inst.tipo:<8} {inst.nombre:<20} "
                f"precio={inst.precio_base:>10.2f} EUR  vol={inst.volatilidad:.2f}"
            )
        return True

    def _cmd_market(self, args: list[str]) -> bool:
        self.mercado.mostrar()
        return True

    def _cmd_portfolio(self, args: list[str]) -> bool:
        self.cartera.mostrar()
        self._salida(f"Valor liquidativo: {self.cartera.valor_total(self.mercado):.2f} EUR")
        return True

    def _cmd_portfolios(self, args: list[str]) -> bool:
        self._salida(f"Carteras ({len(self._gestor)}):")
        for nombre in self._gestor.nombres():
            cartera = self._gestor.obtener(nombre)
            marca = "*" if nombre == self._gestor.activa else " "
            self._salida(
                f" {marca} {nombre:<16} "
                f"efectivo={cartera.efectivo:>10.2f} EUR  "
                f"valor={cartera.valor_total(self.mercado):>10.2f} EUR  "
                f"ops={cartera.total_operaciones}"
            )
        return True

    def _cmd_new(self, args: list[str]) -> bool:
        if not args:
            self._salida("Uso: new <usuario> [efectivo] [comision]")
            return True
        efectivo = 1_000.0
        comision = 1.0
        if len(args) >= 2:
            try:
                efectivo = float(args[1])
            except ValueError:
                self._salida("efectivo debe ser un numero >= 0")
                return True
        if len(args) >= 3:
            try:
                comision = float(args[2])
            except ValueError:
                self._salida("comision debe ser un numero >= 0")
                return True
        try:
            cartera = self._gestor.crear(args[0], efectivo, comision)
        except ErrorBolsa as exc:
            self._salida(f"Error: {exc}")
            return True
        if self.repositorio is not None:
            cartera.repositorio = self.repositorio
        self._salida(
            f"Cartera creada y activa: {cartera.propietario!r} "
            f"(efectivo={cartera.efectivo:.2f} EUR, comision={cartera.comision:.2f})"
        )
        return True

    def _cmd_use(self, args: list[str]) -> bool:
        if not args:
            self._salida(f"Cartera activa: {self._gestor.activa!r}. Uso: use <usuario>")
            return True
        try:
            cartera = self._gestor.seleccionar(args[0])
        except ErrorBolsa as exc:
            self._salida(f"Error: {exc}")
            return True
        if self.repositorio is not None:
            cartera.repositorio = self.repositorio
        self._salida(
            f"Cartera activa: {cartera.propietario!r} "
            f"(efectivo={cartera.efectivo:.2f} EUR, posiciones={len(cartera.posiciones)})"
        )
        return True

    def _cmd_price(self, args: list[str]) -> bool:
        if not args:
            self._salida("Uso: price <instrumento>")
            return True
        inst_id = args[0].upper()
        try:
            precio = self.mercado.precio_de(inst_id)
        except ErrorBolsa:
            self._salida(f"Instrumento desconocido: {inst_id!r}")
            return True
        self._salida(f"{inst_id}: {precio:.2f} EUR")
        return True

    def _cmd_buy(self, args: list[str]) -> bool:
        if len(args) < 2:
            self._salida("Uso: buy <instrumento> <cantidad> [precio]")
            return True
        inst_id = args[0].upper()
        cantidad = self._parse_cantidad(args[1])
        if cantidad is None:
            return True
        precio = self._parse_precio(inst_id, args[2] if len(args) > 2 else None)
        if precio is None:
            return True
        op = self.cartera.invertir(self.mercado, inst_id, cantidad, precio, self._fecha())
        if op is None:
            self._salida(f"Efectivo insuficiente (disponible {self.cartera.efectivo:.2f} EUR).")
        else:
            self._salida(f"Compra ejecutada: {op!r}")
        return True

    def _cmd_sell(self, args: list[str]) -> bool:
        if len(args) < 2:
            self._salida("Uso: sell <instrumento> <cantidad> [precio]")
            return True
        inst_id = args[0].upper()
        cantidad = self._parse_cantidad(args[1])
        if cantidad is None:
            return True
        precio = self._parse_precio(inst_id, args[2] if len(args) > 2 else None)
        if precio is None:
            return True
        op = self.cartera.desinvertir(self.mercado, inst_id, cantidad, precio, self._fecha())
        if op is None:
            self._salida(f"No hay posicion suficiente de {inst_id}.")
        else:
            self._salida(f"Venta ejecutada: {op!r}")
        return True

    def _cmd_next(self, args: list[str]) -> bool:
        volumen = 100
        if args:
            try:
                volumen = int(args[0])
            except ValueError:
                self._salida("volumen debe ser un entero > 0")
                return True
        if volumen <= 0:
            self._salida("volumen debe ser un entero > 0")
            return True
        nuevos = self.mercado.avanzar_sesion(volumen)
        resumen = "  ".join(f"{tid}={precio:.2f}" for tid, precio in nuevos.items())
        self._salida(f"Sesion {self.mercado.sesion}: {resumen}")
        return True

    def _cmd_history(self, args: list[str]) -> bool:
        if not self.cartera.historial:
            self._salida("Sin operaciones registradas.")
            return True
        for op in self.cartera.historial:
            self._salida(repr(op))
        return True

    def _cmd_metrics(self, args: list[str]) -> bool:
        metricas = metricas_cartera(self.cartera, self.mercado)
        self._salida(
            f"Capital inicial={metricas.valor_inicial:.2f} EUR  "
            f"valor actual={metricas.valor_final:.2f} EUR"
        )
        self._salida(str(metricas))
        return True

    def _cmd_strategies(self, args: list[str]) -> bool:
        self._salida("Estrategias disponibles:")
        for nombre in sorted(ESTRATEGIAS):
            self._salida(f"  {nombre:<18} {ESTRATEGIAS[nombre].descripcion}")
        return True

    def _cmd_strategy(self, args: list[str]) -> bool:
        if not args:
            self._salida(
                f"Estrategia actual: {self.estrategia.nombre}. Uso: strategy <nombre> [k=v...]"
            )
            return True
        self.estrategia = estrategia_desde_pares(args[0], args[1:])
        self._salida(f"Estrategia fijada: {self.estrategia.nombre}")
        return True

    def _cmd_simulate(self, args: list[str]) -> bool:
        sesiones = 60
        nombre = self.estrategia.nombre
        parametros: list[str] = []
        if args:
            if args[0].isdigit():
                sesiones = int(args[0])
                if len(args) > 1:
                    nombre = args[1]
                    parametros = args[2:]
            else:
                nombre = args[0]
                parametros = args[1:]
        if sesiones <= 0:
            self._salida("sesiones debe ser un entero > 0")
            return True
        estrategia = estrategia_desde_pares(nombre, parametros)
        semilla = self.mercado.semilla if self.mercado.semilla is not None else 42
        mercado = mercado_demo(semilla=semilla)
        cartera = cartera_demo()
        resultado = Simulador(
            mercado, cartera, estrategia, sesiones=sesiones, volumen=100
        ).ejecutar()
        self._salida(str(resultado))
        self._salida(str(resultado.metricas))
        return True

    def _cmd_parallel(self, args: list[str]) -> bool:
        sesiones = 60
        if args:
            try:
                sesiones = int(args[0])
            except ValueError:
                self._salida("sesiones debe ser un entero > 0")
                return True
        if sesiones <= 0:
            self._salida("sesiones debe ser un entero > 0")
            return True
        semilla = self.mercado.semilla if self.mercado.semilla is not None else 42
        resultados = comparar_estrategias(semilla=semilla, sesiones=sesiones)
        self._salida(f"Comparacion en paralelo (semilla {semilla}, {sesiones} sesiones):")
        for item in resultados:
            self._salida(
                f"  {item.escenario.estrategia:<18} "
                f"valor={item.resultado.valor_final:>10.2f} EUR  "
                f"rent={item.resultado.rentabilidad_total:>8.2%}  "
                f"sharpe={item.resultado.metricas.ratio_sharpe:>6.2f}  "
                f"ops={item.resultado.numero_operaciones}"
            )
        return True

    def _cmd_shock(self, args: list[str]) -> bool:
        if not args:
            self._salida("Uso: shock <variacion> (ej. -0.15)")
            return True
        try:
            variacion = float(args[0])
        except ValueError:
            self._salida("variacion debe ser un numero (ej. -0.15)")
            return True
        nuevos = self.mercado.aplicar_shock(variacion)
        resumen = "  ".join(f"{tid}={precio:.2f}" for tid, precio in nuevos.items())
        self._salida(f"Shock {variacion:+.2%}: {resumen}")
        return True

    def _cmd_chart(self, args: list[str]) -> bool:
        if not args:
            self._salida("Uso: chart <instrumento>")
            return True
        inst_id = args[0].upper()
        serie = self.mercado.historial_precios(inst_id)
        self._salida(f"{inst_id}: {_sparkline(serie)}  ({len(serie)} puntos)")
        return True

    def _cmd_export(self, args: list[str]) -> bool:
        if len(args) < 2:
            self._salida(f"Uso: export <{'|'.join(formatos_disponibles())}> <ruta>")
            return True
        formato, ruta = args[0].lower(), args[1]
        if self.servicio is not None:
            destino = self.servicio.exportar(self.mercado, self.cartera, ruta, formato)
        else:
            destino = exportar_resultados(self.mercado, self.cartera, ruta, formato)
        self._salida(f"Exportado {formato} en {destino}")
        return True

    def _cmd_save(self, args: list[str]) -> bool:
        if self.repositorio is None:
            ruta = args[0] if args else "bolsa_sim.sqlite"
            self.repositorio = RepositorioFactory.desde_ruta(ruta)
            self.servicio = ServicioPersistencia(self.repositorio)
            self.cartera.repositorio = self.repositorio
        if self.servicio is None:  # pragma: no cover - defensivo
            self.servicio = ServicioPersistencia(self.repositorio)
        for cartera in self._gestor:
            cartera.repositorio = self.repositorio
        self.mercado.repositorio = self.repositorio
        self.servicio.guardar_carteras(self.mercado, self._gestor.carteras())
        self._salida(
            f"Estado guardado ({type(self.repositorio).__name__}): "
            f"{len(self._gestor)} cartera(s)."
        )
        return True

    def _cmd_load(self, args: list[str]) -> bool:
        if not args:
            self._salida("Uso: load <ruta> [propietario]")
            return True
        ruta = args[0]
        propietario = args[1] if len(args) > 1 else self.cartera.propietario
        repositorio = RepositorioFactory.desde_ruta(ruta)
        servicio = ServicioPersistencia(repositorio)
        try:
            mercado = servicio.cargar_mercado(self.mercado.nombre, semilla=self.mercado.semilla)
            propietarios = servicio.listar_carteras()
            if not propietarios:
                raise ErrorBolsa("el almacen no contiene carteras")
            carteras = [servicio.cargar_cartera(nombre, mercado) for nombre in propietarios]
            gestor = GestorCarteras.desde_carteras(carteras, activa=propietario)
        except ErrorBolsa:
            repositorio.cerrar()
            raise
        anterior = self.repositorio
        self.mercado = mercado
        self._gestor = gestor
        self.repositorio = repositorio
        self.servicio = servicio
        for cartera in self._gestor:
            cartera.repositorio = repositorio
        self.mercado.repositorio = repositorio
        if anterior is not None and anterior is not repositorio:
            anterior.cerrar()
        self._salida(
            f"Cargado: {len(self._gestor)} carteras ({', '.join(self._gestor.nombres())}); "
            f"activa {self._gestor.activa!r}: {mercado.sesion} sesiones, "
            f"{self.cartera.total_operaciones} operaciones."
        )
        return True

    def _cmd_quit(self, args: list[str]) -> bool:
        return False

    # ---- utilidades ------------------------------------------------------
    def _parse_cantidad(self, texto: str) -> int | None:
        try:
            cantidad = int(texto)
        except ValueError:
            self._salida("cantidad debe ser un entero > 0")
            return None
        if cantidad <= 0:
            self._salida("cantidad debe ser un entero > 0")
            return None
        return cantidad

    def _parse_precio(self, inst_id: str, texto: str | None) -> float | None:
        if texto is None:
            try:
                return self.mercado.precio_de(inst_id)
            except ErrorBolsa:
                self._salida(f"Instrumento desconocido: {inst_id!r}")
                return None
        try:
            precio = float(texto)
        except ValueError:
            self._salida("precio debe ser un numero > 0")
            return None
        if precio <= 0:
            self._salida("precio debe ser un numero > 0")
            return None
        return precio

    def _fecha(self) -> str:
        return f"s{self.mercado.sesion:04d}"


def _dividir_linea(linea: str) -> list[str]:
    """Tokeniza respetando rutas de Windows (``shlex`` posix las rompe)."""
    if os.name == "nt":
        partes = shlex.split(linea, posix=False)
        return [
            p[1:-1] if len(p) >= 2 and p[0] == p[-1] and p[0] in ("'", '"') else p for p in partes
        ]
    return shlex.split(linea)


def _sparkline(serie: tuple[float, ...] | list[float], ancho: int = 40) -> str:
    """Grafico ASCII compacto de una serie (para la consola)."""
    valores = list(serie)
    if not valores:
        return ""
    if len(valores) > ancho:
        paso = len(valores) / ancho
        valores = [valores[int(i * paso)] for i in range(ancho)]
    bloques = "▁▂▃▄▅▆▇█"
    minimo, maximo = min(valores), max(valores)
    if maximo == minimo:
        return bloques[0] * len(valores)
    escala = (len(bloques) - 1) / (maximo - minimo)
    return "".join(bloques[int((v - minimo) * escala)] for v in valores)


__all__ = ["Shell"]
