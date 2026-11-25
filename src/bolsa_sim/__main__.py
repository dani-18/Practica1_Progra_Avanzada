"""Entry point del paquete.

Uso::

    python -m bolsa_sim                    # demo financiera completa
    python -m bolsa_sim --gui              # interfaz grafica (Tkinter)
    python -m bolsa_sim --version
"""

from __future__ import annotations

import argparse

from . import __version__
from .cartera import Cartera
from .demo import cartera_demo, instrumentos_demo, mercado_demo
from .excepciones import ErrorBolsa
from .gui import lanzar_gui
from .logging_config import configurar_logging, obtener_logger
from .metricas import metricas_cartera
from .persistencia.exportadores import exportar_resultados

log = obtener_logger(__name__)


def _demo() -> int:
    """Caso de ejemplo: jerarquia, polimorfismo, mercado y metricas."""
    # Jerarquia de instrumentos (PRAC2): Accion, Bono y ETF.
    instrumentos = instrumentos_demo()
    accion = instrumentos[0]

    # 1 mercado y 1 cartera (escenario de ejemplo reutilizable).
    mercado = mercado_demo()
    cartera: Cartera = cartera_demo()

    print("== Demo (PRAC2: jerarquia de instrumentos) ==")
    # Polimorfismo: mismo ``mostrar()`` para tipos distintos.
    for instrumento in instrumentos:
        instrumento.mostrar()
    mercado.mostrar()
    cartera.mostrar()

    # 5 sesiones + 2 compras + 1 venta.
    for i in range(1, 6):
        nuevos = mercado.avanzar_sesion(volumen=50)
        if i in (1, 3):
            cartera.invertir(
                mercado,
                accion.id,
                2,
                precio=nuevos[accion.id],
                fecha=f"s{i:03d}",
            )
        if i == 5:
            cartera.desinvertir(
                mercado,
                accion.id,
                1,
                precio=nuevos[accion.id],
                fecha=f"s{i:03d}",
            )
        cartera.anotar_valor(mercado=mercado)

    print("\n--- tras 5 sesiones ---")
    mercado.mostrar()
    cartera.mostrar()
    print(f"valor liquidativo: {cartera.valor_total(mercado):.2f} EUR")
    # Polimorfismo de ``flujo_anual``: cada subclase responde distinto.
    flujo = sum(inst.flujo_anual() for inst in mercado.instrumentos.values())
    print(f"flujo anual agregado de 1 unidad de cada instrumento: {flujo:.2f} EUR")
    print(f"metricas: {metricas_cartera(cartera, mercado)}")

    log.info("demo completada")
    return 0


def _gui() -> int:
    return lanzar_gui()


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bolsa-sim",
        description=(
            "Simulador de Bolsa (PRAC3/PRAC4: patrones, persistencia, " "metricas y GUI)."
        ),
    )
    p.add_argument("--demo", action="store_true", help="imprime el flujo demo")
    p.add_argument("--gui", action="store_true", help="abre la interfaz grafica (Tkinter)")
    p.add_argument("--export", metavar="RUTA", help="exporta la demo a JSON/CSV")
    verbosidad = p.add_mutually_exclusive_group()
    verbosidad.add_argument(
        "-v", "--verbose", action="store_true", help="logging detallado (DEBUG)"
    )
    verbosidad.add_argument(
        "-q", "--quiet", action="store_true", help="solo errores en el logging"
    )
    p.add_argument("--log-file", metavar="RUTA", help="guarda el log en un fichero")
    p.add_argument("--version", action="store_true", help="imprime la version")
    return p


def cli(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    nivel = "DEBUG" if args.verbose else "ERROR" if args.quiet else "INFO"
    configurar_logging(nivel, args.log_file)
    log.debug("argumentos: %s", vars(args))

    try:
        if args.version:
            print(f"bolsa-sim {__version__}")
            resultado = 0
        elif args.gui:
            resultado = _gui()
        elif args.export:
            mercado = mercado_demo()
            cartera = cartera_demo()
            cartera.invertir(mercado, "ACME", 2, mercado.precio_de("ACME"), "s0000")
            formato = "csv" if args.export.lower().endswith(".csv") else "json"
            print(exportar_resultados(mercado, cartera, args.export, formato))
            resultado = 0
        else:
            resultado = _demo()
    except ErrorBolsa as exc:
        log.error("error de dominio: %s", exc)
        print(f"Error: {exc}")
        resultado = 1
    return resultado


if __name__ == "__main__":
    raise SystemExit(cli())
