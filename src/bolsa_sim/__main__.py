"""Entry point CLI minimo.

Uso::

    python -m bolsa_sim --demo        # imprime el flujo de las 4 clases
    python -m bolsa_sim --version     # version del paquete
"""

from __future__ import annotations

import argparse

from . import __version__
from .cartera import Cartera
from .instrumento import InstrumentoBase
from .mercado import Mercado


def _demo() -> int:
    """Caso de ejemplo: arma las 4 clases y muestra su interaccion."""
    # 2 instrumentos (la clase padre preparada para herencia futura).
    inst_a = InstrumentoBase(
        id="ACME",
        nombre="Acme Corp",
        simbolo="ACME",
        volatilidad=0.20,
        precio_base=120.0,
    )
    inst_b = InstrumentoBase(
        id="BONO10",
        nombre="Bono 10 anos",
        simbolo="B10",
        volatilidad=0.05,
        precio_base=100.0,
    )

    # 1 mercado.
    mercado = Mercado(
        nombre="Bolsa Continuo",
        instrumentos={inst_a.id: inst_a, inst_b.id: inst_b},
        semilla=42,
    )

    # 1 cartera.
    cartera = Cartera(propietario="Dani", efectivo=1_000.0, comision=1.0)

    print("== Demo (modelo minimo, 4 clases) ==")
    inst_a.mostrar()
    inst_b.mostrar()
    mercado.mostrar()
    cartera.mostrar()

    # 5 sesiones + 2 compras + 1 venta.
    for i in range(1, 6):
        nuevos = mercado.avanzar_sesion(volumen=50)
        if i in (1, 3):
            cartera.invertir(
                mercado,
                inst_a.id,
                2,
                precio=nuevos[inst_a.id],
                fecha=f"s{i:03d}",
            )
        if i == 5:
            cartera.desinvertir(
                mercado,
                inst_a.id,
                1,
                precio=nuevos[inst_a.id],
                fecha=f"s{i:03d}",
            )

    print("\n--- tras 5 sesiones ---")
    mercado.mostrar()
    cartera.mostrar()
    print(f"valor liquidativo: {cartera.valor_total(mercado):.2f} EUR")
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bolsa-sim",
        description="Simulador de Bolsa (PRAC1, modelo minimo de 4 clases).",
    )
    p.add_argument("--demo", action="store_true", help="imprime el flujo demo")
    p.add_argument("--version", action="store_true", help="imprime la version")
    return p


def cli(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.version:
        print(f"bolsa-sim {__version__}")
        return 0
    return _demo()


if __name__ == "__main__":
    raise SystemExit(cli())
