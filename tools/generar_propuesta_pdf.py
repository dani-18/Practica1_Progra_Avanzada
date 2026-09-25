"""Genera ``docs/PRAC1_Propuesta_SimuladorBolsa.pdf`` a partir del Markdown.

Uso::

    python tools/generar_propuesta_pdf.py

Requiere ``reportlab`` (de ``pip install -e .[dev,docs]``). No se importa
en el paquete ni en los tests; es solo una herramienta operativa.

El marcado soportado es muy basico (encabezados ``#``/``##``/``###``,
parrafos, listas ``-`` y bloques de codigo triple-backtick). Es
deliberadamente limitado: el objetivo es producir un PDF academico a
partir de ``docs/propuesta_PRAC1.md``, no ser un Markdown completo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

ROOT = Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "docs" / "propuesta_PRAC1.md"
SALIDA = ROOT / "docs" / "PRAC1_Propuesta_SimuladorBolsa.pdf"


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="H1",
            parent=base["Heading1"],
            fontSize=18,
            spaceAfter=14,
            textColor=colors.HexColor("#1a1a1a"),
        ),
    )
    base.add(
        ParagraphStyle(
            name="H2",
            parent=base["Heading2"],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor("#2a2a2a"),
        ),
    )
    base.add(
        ParagraphStyle(
            name="H3",
            parent=base["Heading3"],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor("#3a3a3a"),
        ),
    )
    return {
        "h1": base["H1"],
        "h2": base["H2"],
        "h3": base["H3"],
        "normal": base["BodyText"],
        "code": base["Code"],
    }


def _bloque_codigo(contenido: str, estilos: dict[str, ParagraphStyle]) -> list:
    return [
        Preformatted(
            contenido,
            style=estilos["code"],
        ),
        Spacer(1, 6),
    ]


def _convertir_markdown(texto: str, estilos: dict[str, ParagraphStyle]) -> list:
    bloques: list = []
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas):
        ln = lineas[i]
        if ln.startswith("# "):
            bloques.append(Paragraph(ln[2:].strip(), estilos["h1"]))
            i += 1
            continue
        if ln.startswith("## "):
            bloques.append(Paragraph(ln[3:].strip(), estilos["h2"]))
            i += 1
            continue
        if ln.startswith("### "):
            bloques.append(Paragraph(ln[4:].strip(), estilos["h3"]))
            i += 1
            continue
        if ln.strip().startswith("```"):
            contenido: list[str] = []
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                contenido.append(lineas[i])
                i += 1
            bloques.extend(
                _bloque_codigo(
                    "\n".join(contenido),
                    estilos,
                )
            )
            i += 1
            continue
        if ln.strip() == "":
            bloques.append(Spacer(1, 6))
            i += 1
            continue
        if ln.lstrip().startswith("|"):
            # Tablas Markdown: rendrizado plano en monoespaciado.
            filas: list[str] = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                filas.append(lineas[i])
                i += 1
            bloques.extend(_bloque_codigo("\n".join(filas), estilos))
            continue
        # Listado simple o parrafo
        buf: list[str] = []
        while i < len(lineas) and lineas[i].strip() and not lineas[i].startswith("#"):
            buf.append(lineas[i])
            i += 1
        par = "<br/>".join(buf)
        # ``cursiva`` -> <i>; ``negrita`` -> <b>.
        par = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", par)
        par = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", par)
        par = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", par)
        bloques.append(Paragraph(par, estilos["normal"]))
    return bloques


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        print(f"uso: {Path(__file__).name} (sin argumentos)", file=sys.stderr)
        return 2
    if not ENTRADA.exists():
        print(f"no se encuentra la fuente: {ENTRADA}", file=sys.stderr)
        return 2

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(SALIDA),
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="Propuesta PRAC1 - Simulador de Bolsa",
        author="dani-18 y colaboradores",
    )

    md = ENTRADA.read_text(encoding="utf-8")
    estilos = _estilos()
    historia = _convertir_markdown(md, estilos)
    doc.build(historia)
    print(f"PDF generado en: {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
