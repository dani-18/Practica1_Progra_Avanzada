"""Punto de entrada CLI del paquete.

Uso::

    python -m bolsa_sim --demo         # hello flow completo
    python -m bolsa_sim --memoria      # demos del Tema 1 (identidad, defecto mutable)
    python -m bolsa_sim --sesiones 60  # extiende el demo a 60 dias
    python -m bolsa_sim --version      # imprime la version y sale

El modulo tambien expone ``cli()`` para el ``[project.scripts]`` del
``pyproject.toml`` (``bolsa-sim``).
"""

from __future__ import annotations

import argparse
import sys
from math import isfinite

from . import __version__
from .activos import Activo, TipoActivo
from .cartera import Cartera
from .config import cargar_configuracion
from .estrategias import CompraYMantiene
from .memoria import (
    demostrar_defecto_estado_compartido,
    demostrar_identidad_y_igualdad,
)
from .mercado import MercadoSimulado
from .metricas import drawdown_maximo, rentabilidad_total
from .simulacion import ResultadoSimulacion

# Catalogo breve de activos por defecto (estable, determinista y didactico).
ACTIVOS_DEMO: tuple[dict[str, object], ...] = (
    {"ticker": "ACME", "nombre": "Acme Corp", "precio": 120.0, "volatilidad": 0.20},
    {"ticker": "GLOB", "nombre": "Global Industries", "precio": 75.0, "volatilidad": 0.30},
    {"ticker": "OILX", "nombre": "OilX Energy", "precio": 50.0, "volatilidad": 0.40},
    {"ticker": "TECH", "nombre": "TechNova", "precio": 210.0, "volatilidad": 0.35},
    {
        "ticker": "BONO10",
        "nombre": "Bono Soberano 10a",
        "precio": 100.0,
        "volatilidad": 0.05,
        "tipo": TipoActivo.BONO,
        "dividendo": 0.04,
    },
)


def _crear_activos_demo(tickers: tuple[str, ...]) -> list[Activo]:
    activos: list[Activo] = []
    for cfg in ACTIVOS_DEMO:
        if cfg["ticker"] in tickers:
            activos.append(
                Activo(
                    ticker=str(cfg["ticker"]),
                    nombre=str(cfg["nombre"]),
                    precio_inicial=float(cfg["precio"]),  # type: ignore[arg-type]
                    volatilidad=float(cfg["volatilidad"]),  # type: ignore[arg-type]
                    tipo=cfg.get("tipo", TipoActivo.ACCION),  # type: ignore[arg-type]
                    dividendo_anual=float(cfg.get("dividendo", 0.0)),  # type: ignore[arg-type]
                )
            )
    return activos


def _imprimir_resumen(resultado: ResultadoSimulacion) -> None:
    roi = resultado.roi_porcentaje
    print("")
    print("== Resumen ==")
    print(
        f"  sesiones={resultado.sesiones_ejecutadas} "
        f"valor_inicial={resultado.valor_inicial:.2f} EUR "
        f"valor_final={resultado.valor_final:.2f} EUR"
    )
    print(f"  ROI total = {roi:.2f} %")
    print(
        f"  rentabilidad_total() = "
        f"{rentabilidad_total(resultado.valor_inicial, resultado.valor_final):.2f} %"
    )
    dd = drawdown_maximo([resultado.valor_inicial, resultado.valor_final])
    print(f"  drawdown maximo (aprox, 2 puntos) = {dd * 100:.2f} %")
    if not isfinite(roi):
        print("  (!) ROI no es un numero finito: revise el efectivo inicial.")


def _demo_hello_flow(sesiones: int, *, semilla: int | None) -> int:
    """Ejecuta el hello flow: mercado, cartera, estrategia y tabla por sesion."""
    cfg = cargar_configuracion()
    tickers = cfg.tickers if cfg.tickers else tuple(a["ticker"] for a in ACTIVOS_DEMO)
    activos = _crear_activos_demo(tickers)  # type: ignore[arg-type]
    if not activos:
        print("No se encontraron activos para los tickers seleccionados.", file=sys.stderr)
        return 2

    semilla = semilla if semilla is not None else 42
    mercado = MercadoSimulado(activos, semilla=semilla)
    cartera = Cartera(cfg.efectivo_inicial)

    print("== Demo: Simulador de Bolsa y Carteras de Inversion (PRAC1) ==")
    print(f"  activos:    {[a.ticker for a in activos]}")
    print(f"  efectivo:   {cfg.efectivo_inicial:.2f} EUR")
    print(f"  sesiones:   {sesiones}")
    print(f"  semilla:    {semilla}")

    estrategia = CompraYMantiene(tuple(a.ticker for a in activos), cantidad_por_ticker=3)

    tickers_str = "  ".join(f"{a.ticker:>8}" for a in activos)
    print("")
    print(f"{'sesion':>6}  {'efectivo':>10}  {'valor total':>12}  {tickers_str}")
    separador = "-" * (6 + 1 + 10 + 1 + 12 + 1 + len(tickers_str) * 10)
    print(separador)

    operaciones_iniciales = 0
    for _ in range(sesiones):
        # Ejecutamos las ordenes que emita la estrategia al inicio de la sesion.
        ordenes = tuple(estrategia.generar_orden(cartera, mercado, mercado.sesion_actual + 1))
        for ord_obj in ordenes:
            ticker = ord_obj.ticker
            cantidad = int(ord_obj.cantidad)
            tipo = ord_obj.tipo
            if tipo.value == "compra":
                cartera.comprar(mercado, ticker, cantidad)
            else:
                cartera.vender(mercado, ticker, cantidad)
        mercado.avanzar_sesion()
        fila_precios = "  ".join(f"{a.precio:>8.2f}" for a in activos)
        print(
            f"{mercado.sesion_actual:>6}  "
            f"{cartera.efectivo:>10.2f}  "
            f"{cartera.valor_total(mercado):>12.2f}  "
            f"{fila_precios}"
        )
        operaciones_iniciales = operaciones_iniciales or cartera.total_transacciones

    resultado = ResultadoSimulacion(
        sesiones_ejecutadas=sesiones,
        efectivo_inicial=cfg.efectivo_inicial,
        efectivo_final=cartera.efectivo,
        valor_inicial=cfg.efectivo_inicial,
        valor_final=cartera.valor_total(mercado),
        operaciones_ejecutadas=operaciones_iniciales,
    )
    _imprimir_resumen(resultado)
    return 0


def _demo_memoria() -> int:
    """Demos didacticas del Tema 1 (identidad, tuplas, defecto mutable)."""
    print(demostrar_identidad_y_igualdad())
    print("")
    print(demostrar_defecto_estado_compartido())
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bolsa-sim",
        description="Simulador de Bolsa y Carteras de Inversion (PRAC1).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="ejecuta la demo 'hello flow' (por defecto, 30 sesiones)",
    )
    parser.add_argument(
        "--memoria",
        action="store_true",
        help="demostraciones didacticas de identidad, aliasing y defecto mutable",
    )
    parser.add_argument(
        "--sesiones",
        type=int,
        default=None,
        help="numero de sesiones a simular (por defecto: SIMULADOR_SESIONES o 30)",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=None,
        help="semilla del RNG (por defecto: SIMULADOR_SEMILLA o 42)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="imprime la version y sale",
    )
    return parser


def cli(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.version:
        print(f"bolsa-sim {__version__}")
        return 0
    if args.memoria:
        return _demo_memoria()
    cfg = cargar_configuracion()
    sesiones = args.sesiones if args.sesiones is not None else cfg.sesiones
    semilla = args.semilla if args.semilla is not None else cfg.semilla
    return _demo_hello_flow(sesiones, semilla=semilla)


if __name__ == "__main__":
    raise SystemExit(cli())
