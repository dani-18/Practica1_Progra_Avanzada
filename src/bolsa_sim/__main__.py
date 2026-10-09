"""Entry point del paquete.

Uso::

    python -m bolsa_sim --demo        # imprime el flujo de las clases + jerarquia PRAC2
    python -m bolsa_sim --cli         # abre la interfaz interactiva
    python -m bolsa_sim --version     # version del paquete
"""

from __future__ import annotations

import argparse

from . import __version__
from .cartera import Cartera
from .cli import Shell
from .demo import cartera_demo, instrumentos_demo, mercado_demo


def _demo() -> int:
    """Caso de ejemplo: las 4 clases base + la jerarquia de instrumentos."""
    # Jerarquia de instrumentos (PRAC2): Accion, Bono y ETF.
    instrumentos = instrumentos_demo()
    accion = instrumentos[0]

    # 1 mercado y 1 cartera (mismo escenario que la CLI interactiva).
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

    print("\n--- tras 5 sesiones ---")
    mercado.mostrar()
    cartera.mostrar()
    print(f"valor liquidativo: {cartera.valor_total(mercado):.2f} EUR")
    # Polimorfismo de ``flujo_anual``: cada subclase responde distinto.
    flujo = sum(inst.flujo_anual() for inst in mercado.instrumentos.values())
    print(f"flujo anual agregado de 1 unidad de cada instrumento: {flujo:.2f} EUR")
    return 0


def _cli_interactiva() -> int:
    """Abre la interfaz interactiva de linea de comandos."""
    Shell().run()
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bolsa-sim",
        description="Simulador de Bolsa (PRAC1-PRAC2: 4 clases base + Accion/Bono/ETF).",
    )
    p.add_argument("--demo", action="store_true", help="imprime el flujo demo")
    p.add_argument(
        "--cli", "--interactive", action="store_true", help="abre la consola interactiva"
    )
    p.add_argument("--version", action="store_true", help="imprime la version")
    return p


def cli(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.version:
        print(f"bolsa-sim {__version__}")
        return 0
    if args.cli:
        return _cli_interactiva()
    return _demo()


if __name__ == "__main__":
    raise SystemExit(cli())
