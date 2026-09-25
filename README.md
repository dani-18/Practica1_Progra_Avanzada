# Simulador de Bolsa y Carteras de Inversion (PRAC1, modelo minimo)

> **Practica 1 de Tecnicas de Programacion Avanzada** — Grupo A — curso 2026-2027.
> Version minima: **4 clases** de dominio, una preparada como padre para
> la jerarquia que se anadira en PRAC2, con ``@property``/setter y
> ``mostrar()`` para imprimir el estado en cada una.

## Indice

1. [Vision general](#1-vision-general)
2. [Las 4 clases](#2-las-4-clases)
3. [Requisitos e instalacion](#3-requisitos-e-instalacion)
4. [Ejecucion](#4-ejecucion)
5. [Pruebas y calidad](#5-pruebas-y-calidad)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Roadmap](#7-roadmap)
8. [Documentacion adicional](#8-documentacion-adicional)
9. [Seguridad y licencia](#9-seguridad-y-licencia)

## 1. Vision general

Esta primera entrega se centra en el Tema 1 (objetos, memoria y
encapsulamiento) y eleva la tematica "12. Simulador de Bolsa y
Carteras de Inversion" al nivel de prueba de concepto. La version
final del proyecto (PRAC2-PRAC4) ira anadiendo herencia, patrones,
GUI y concurrencia. Aqui se entrega el **nucleo minimo** con cuatro
clases que muestran las bases de cualquier programa orientado a objetos
en Python: `__init__`, encapsulamiento con `@property` + setter,
inmutabilidad con `@dataclass(frozen=True)`, representacion y
igualdad por contenido, y un diseno pensado para que la primera
clase (`InstrumentoBase`) sea el padre de una jerarquia futura.

```bash
python -m bolsa_sim --demo
```

imprime el estado de las 4 clases y luego hace 5 sesiones de mercado
con compras / ventas de ACME para terminar con el valor liquidativo
de la cartera.

## 2. Las 4 clases

| Clase             | Atributos (5)                                                                                | Properties con setter | Notas                                    |
|-------------------|----------------------------------------------------------------------------------------------|-----------------------|------------------------------------------|
| `InstrumentoBase` | `id`, `nombre`, `simbolo`, `volatilidad`, `precio_base`                                     | `volatilidad`, `precio_base` | **Clase padre** preparada para PRAC2 (`Accion`, `Bono`, `ETF`). |
| `Cartera`         | `propietario`, `efectivo`, `_inversiones`, `comision`, `_historial`                          | `efectivo`, `comision`     | Compra/venta con comision; efectivo positivo. |
| `Operacion`       | `fecha`, `instrumento_id`, `cantidad`, `precio_ejecucion`, `tipo`                             | (no, frozen)              | `@dataclass(frozen=True)`; inmutable.      |
| `Mercado`         | `nombre`, `_rng_seed`, `instrumentos`, `sesion`, `volumen_total`                              | `sesion`, `volumen_total`  | Avanza sesiones con shock gaussiano.      |

Cada clase expone `mostrar()` (el `print` que se invoca desde el
demo) y un `__repr__` no ambiguo. Las tres clases con `properties`
muestran el patron "validacion con `@property` + setter" que es el
objetivo didactico del Tema 1.

Diagrama textual de relaciones:

```
            InstrumentoBase       (padre preparado para PRAC2)
                  ^
                  | (asociacion)
                  | instancia por Mercado.instrumentos
                  |
              Mercado ----compone----- Cartera
                |                          |
                | registra                 | registra (Operacion)
                v                          v
            instrumentos            _historial: list[Operacion]
```

## 3. Requisitos e instalacion

```bash
python --version                  # 3.10 o superior
python -m venv .venv
.venv\Scripts\Activate.ps1        # o: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"  # pytest, coverage, black, ruff, reportlab, pre-commit
```

Sin extras: `python -m pip install -e .`

## 4. Ejecucion

```bash
python -m bolsa_sim --demo      # flujo completo: 2 instrumentos + mercado + cartera
python -m bolsa_sim --version   # imprime 'bolsa-sim 0.2.0'
```

Tambien desde el entry point:

```bash
bolsa-sim --demo
```

## 5. Pruebas y calidad

```bash
python -m pytest -q                        # 37 tests en ~0.1 s
python -m pytest --cov=bolsa_sim           # cobertura ~93 %
python -m black --check src tests
python -m ruff check src tests
```

Resultado actual:

```
TOTAL ... 93 % coverage
37 passed in 0.10s
```

## 6. Estructura del repositorio

```text
Practica_Progra_Avanzada/
|-- .github/workflows/ci.yml     CI: black + ruff + pytest (multi-version Python)
|-- .pre-commit-config.yaml      hooks locales de calidad
|-- .env.example
|-- .gitignore
|-- CHANGELOG.md
|-- LICENSE                      MIT
|-- README.md
|-- pyproject.toml               configuracion Black/Ruff/pytest/coverage
|-- legacy/                      version extendida anterior (informativa)
|   |-- docs/    src/    tests/
|-- tools/
|   `-- generar_propuesta_pdf.py
|-- docs/
|   `-- propuesta_PRAC1.md       fuente Markdown de la propuesta
|-- src/bolsa_sim/
|   |-- __init__.py              4 clases exportadas
|   |-- __main__.py              CLI minimo
|   |-- instrumento.py           InstrumentoBase  (5 attrs + 2 properties)
|   |-- cartera.py               Cartera          (5 attrs + 2 properties)
|   |-- operacion.py             Operacion        (5 attrs, frozen)
|   `-- mercado.py               Mercado          (5 attrs + 2 properties)
`-- tests/
    |-- conftest.py
    |-- test_instrumento.py
    |-- test_cartera.py
    |-- test_operacion.py
    |-- test_mercado.py
    |-- test_integration.py      hello flow + comprobacion de herencia
    `-- test_main.py             CLI smoke
```

## 7. Roadmap

| Hito   | Tema | Foco                                                                  |
|--------|------|------------------------------------------------------------------------|
| **PRAC1** | **1** | **Este esqueleto.** 4 clases, encapsulamiento, frozen dataclass, herencia preparada. |
| PRAC2  | 2    | Jerarquia ``Accion/Bono/ETF(InstrumentoBase)``, excepciones, genericidad. |
| PRAC3  | 3    | Strategy + Factory para perfiles de cartera.                            |
| PRAC4  | 4    | GUI, concurrencia, ≥ 70 % cobertura, tag ``v1.0.0``.                    |

## 8. Documentacion adicional

* `docs/propuesta_PRAC1.md` — propuesta en Markdown. Genera PDF academico
  con `python tools/generar_propuesta_pdf.py`.
* `legacy/` — primer esquema del proyecto (antes de reducir a 4 clases).
  Se conserva como bitacora historica.

## 9. Seguridad y licencia

- No consume credenciales; ``.env`` solo tiene parametros de demo.
- El paquete runtime es **stdlib only**.
- Licencia: MIT (ver ``LICENSE``).
