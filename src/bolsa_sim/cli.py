"""Interfaz interactiva de linea de comandos del simulador.

Se lanza con::

    python -m bolsa_sim --cli

y ofrece una consola sencilla para operar el mercado: listar
instrumentos, consultar precios, comprar/vender, avanzar sesiones, ver
la cartera y el historial. Dentro de la sesion, ``help`` muestra la lista
de comandos y ``quit`` (o ``exit``) sale.

El procesamiento de cada linea esta separado de la lectura por teclado
(``Shell.ejecutar`` recibe una cadena y devuelve si hay que continuar),
lo que permite probar la interfaz sin entrada interactiva.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable

from .cartera import Cartera
from .demo import cartera_demo, mercado_demo
from .mercado import Mercado


class Shell:
    """Consola interactiva sobre un ``Mercado`` y una ``Cartera``."""

    def __init__(
        self,
        mercado: Mercado | None = None,
        cartera: Cartera | None = None,
        *,
        entrada: Callable[[str], str] = input,
        salida: Callable[[str], None] = print,
    ) -> None:
        self.mercado = mercado if mercado is not None else mercado_demo()
        self.cartera = cartera if cartera is not None else cartera_demo()
        self._entrada = entrada
        self._salida = salida
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
            "quit": self._cmd_quit,
            "exit": self._cmd_quit,
        }

    # ---- motor de la consola ---------------------------------------------
    def ejecutar(self, linea: str) -> bool:
        """Procesa una linea. Devuelve ``False`` cuando hay que salir."""
        try:
            partes = shlex.split(linea)
        except ValueError as exc:
            self._salida(f"Entrada no valida: {exc}")
            return True
        if not partes:
            return True
        comando, *args = partes
        metodo = self._comandos.get(comando.lower())
        if metodo is None:
            self._salida(f"Comando desconocido: {comando!r}. Usa 'help'.")
            return True
        return metodo(args)

    def run(self) -> None:
        """Bucle principal: lee lineas hasta ``quit``/``exit`` o EOF."""
        self._salida("Simulador de Bolsa (CLI). Escribe 'help' para ver los comandos.")
        while True:
            try:
                linea = self._entrada("bolsa> ")
            except (EOFError, KeyboardInterrupt):
                self._salida("")
                break
            if not self.ejecutar(linea):
                break
        self._salida("Hasta luego.")

    # ---- comandos --------------------------------------------------------
    def _cmd_help(self, args: list[str]) -> bool:
        self._salida("Comandos disponibles:")
        self._salida("  help                         muestra esta ayuda")
        self._salida("  list                         lista los instrumentos del mercado")
        self._salida("  market                       muestra el estado del mercado")
        self._salida("  portfolio | status           muestra la cartera y su valor")
        self._salida("  price <instrumento>          consulta el precio actual")
        self._salida("  buy <instrumento> <cantidad> [precio]   compra")
        self._salida("  sell <instrumento> <cantidad> [precio]  vende")
        self._salida("  next [volumen]               avanza una sesion de mercado")
        self._salida("  history                      muestra el historial de operaciones")
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

    def _cmd_price(self, args: list[str]) -> bool:
        if not args:
            self._salida("Uso: price <instrumento>")
            return True
        inst_id = args[0].upper()
        try:
            precio = self.mercado.precio_de(inst_id)
        except KeyError:
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
            except KeyError:
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
