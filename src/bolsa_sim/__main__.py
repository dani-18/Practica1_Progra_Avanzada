"""Entry point CLI minimo.

Uso::

    python -m bolsa_sim --demo        # imprime el flujo de las clases + jerarquia PRAC2
    python -m bolsa_sim --version     # version del paquete
"""

from __future__ import annotations

import argparse

from . import __version__
from .accion import Accion
from .bono import Bono
from .cartera import Cartera
from .etf import ETF
from .mercado import Mercado


def _demo() -> int:
    """Caso de ejemplo: las 4 clases base + la jerarquia de instrumentos."""
    # Jerarquia de instrumentos (PRAC2): las 3 subclases de InstrumentoBase.
    accion = Accion(
        id="ACME",
        nombre="Acme Corp",
        simbolo="ACME",
        volatilidad=0.20,
        precio_base=120.0,
        sector="Tecnologia",
        dividendo_anual=1.80,
    )
    bono = Bono(
        id="BONO10",
        nombre="Bono 10 anos",
        simbolo="B10",
        volatilidad=0.05,
        precio_base=100.0,
        cupon_anual=0.04,
        valor_nominal=1_000.0,
        vencimiento=10,
    )
    etf = ETF(
        id="SP500",
        nombre="ETF S&P 500",
        simbolo="SPX",
        volatilidad=0.15,
        precio_base=400.0,
        indice="S&P 500",
        comision_gestion=0.002,
    )

    # 1 mercado.
    mercado = Mercado(
        nombre="Bolsa Continuo",
        instrumentos={i.id: i for i in (accion, bono, etf)},
        semilla=42,
    )

    # 1 cartera.
    cartera = Cartera(propietario="Dani", efectivo=1_000.0, comision=1.0)

    print("== Demo (PRAC2: jerarquia de instrumentos) ==")
    # Polimorfismo: mismo ``mostrar()`` para tipos distintos.
    for instrumento in (accion, bono, etf):
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


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bolsa-sim",
        description="Simulador de Bolsa (PRAC1-PRAC2: 4 clases base + Accion/Bono/ETF).",
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
