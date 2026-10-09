# Simulador de Bolsa y Carteras de Inversion (PRAC1 + PRAC2)

> **Practicas 1 y 2 de Tecnicas de Programacion Avanzada** — Grupo A — curso 2026-2027.
> PRAC1 entrega 4 clases de dominio con ``@property``/setter y ``mostrar()``.
> PRAC2 anade la **jerarquia de instrumentos** ``Accion``, ``Bono`` y
> ``ETF`` heredando de ``InstrumentoBase`` (herencia, sobrescritura y
> polimorfismo).

## Indice

1. [Vision general](#1-vision-general)
2. [Las 4 clases + jerarquia PRAC2](#2-las-4-clases--jerarquia-prac2)
3. [Requisitos e instalacion](#3-requisitos-e-instalacion)
4. [Ejecucion](#4-ejecucion)
5. [Pruebas y calidad](#5-pruebas-y-calidad)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Roadmap](#7-roadmap)
8. [Documentacion adicional](#8-documentacion-adicional)
9. [Seguridad y licencia](#9-seguridad-y-licencia)

## 1. Vision general

Esta entrega cubre los Temas 1 y 2 (objetos, encapsulamiento y
herencia) y eleva la tematica "12. Simulador de Bolsa y Carteras de
Inversion" al nivel de prueba de concepto. La **PRAC1** introduce el
nucleo minimo con cuatro clases que muestran las bases de cualquier
programa orientado a objetos en Python: `__init__`, encapsulamiento con
`@property` + setter, inmutabilidad con `@dataclass(frozen=True)`,
representacion e igualdad por contenido. La **PRAC2** anade la
**jerarquia de instrumentos** (`Accion`, `Bono` y `ETF` heredando de
`InstrumentoBase`) con `super().__init__`, sobrescritura de metodos y
polimorfismo. Las practicas PRAC3-PRAC4 iran anadiendo patrones, GUI y
concurrencia.

```bash
python -m bolsa_sim --demo
```

imprime el estado de las 4 clases base, la jerarquia de instrumentos y
luego hace 5 sesiones de mercado con compras / ventas de ACME para
terminar con el valor liquidativo de la cartera.

## 2. Las 4 clases + jerarquia PRAC2

### PRAC1 — nucleo minimo (4 clases)

| Clase             | Atributos (5)                                                                                | Properties con setter | Notas                                    |
|-------------------|----------------------------------------------------------------------------------------------|-----------------------|------------------------------------------|
| `InstrumentoBase` | `id`, `nombre`, `simbolo`, `volatilidad`, `precio_base`                                     | `volatilidad`, `precio_base` | **Clase padre** de `Accion`, `Bono`, `ETF` (PRAC2). |
| `Cartera`         | `propietario`, `efectivo`, `_inversiones`, `comision`, `_historial`                          | `efectivo`, `comision`     | Compra/venta con comision; efectivo positivo. |
| `Operacion`       | `fecha`, `instrumento_id`, `cantidad`, `precio_ejecucion`, `tipo`                             | (no, frozen)              | `@dataclass(frozen=True)`; inmutable.      |
| `Mercado`         | `nombre`, `_rng_seed`, `instrumentos`, `sesion`, `volumen_total`                              | `sesion`, `volumen_total`  | Avanza sesiones con shock gaussiano.      |

Cada clase expone `mostrar()` (el `print` que se invoca desde el
demo) y un `__repr__` no ambiguo. Las tres clases con `properties`
muestran el patron "validacion con `@property` + setter" que es el
objetivo didactico del Tema 1; las subclases aplican ademas el Tema 2
(herencia, sobrescritura de metodos y polimorfismo).

Diagrama textual de relaciones:

```
            InstrumentoBase
             ^    ^     ^
             |    |     |   (herencia PRAC2)
     Accion--+    |     +--ETF
                  |
                Bono

            InstrumentoBase
                  ^
                  | (asociacion, por id)
                  |
              Mercado ----compone----- Cartera
                |                          |
                | registra                 | registra (Operacion)
                v                          v
            instrumentos            _historial: list[Operacion]
```

### PRAC2 — jerarquia de instrumentos

Las tres subclases reutilizan ``super().__init__`` para la parte comun y
anaden campos propios con ``@property``/setter. Todas fijan su atributo
de clase ``tipo`` y demuestran **polimorfismo**: el mismo metodo
``mostrar()`` (heredado y ampliado) y un mismo metodo ``flujo_anual()``
responden distinto segun el tipo concreto.

| Subclase | `tipo`   | Atributos propios                             | `flujo_anual()`                    |
|----------|----------|-----------------------------------------------|------------------------------------|
| `Accion` | `accion` | `sector`, `dividendo_anual`                   | `dividendo_anual`                  |
| `Bono`   | `bono`   | `cupon_anual`, `valor_nominal`, `vencimiento` | `cupon_anual * valor_nominal`      |
| `ETF`    | `etf`    | `indice`, `comision_gestion`                  | `0.0` (hereda la base)             |

Helpers especificos: ``Accion.rentabilidad_por_dividendo()``,
``Bono.cupon_anual_eur()``/``Bono.rendimiento_actual()`` y
``ETF.coste_anual()``. La igualdad sigue siendo por ``id`` (heredada),
por lo que un ``Accion`` y un ``Bono`` con el mismo ``id`` son el mismo
instrumento logico.

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
python -m bolsa_sim --demo      # flujo completo: Accion + Bono + ETF + mercado + cartera
python -m bolsa_sim --version   # imprime 'bolsa-sim 0.3.0'
```

Tambien desde el entry point:

```bash
bolsa-sim --demo
```

## 5. Pruebas y calidad

```bash
python -m pytest -q                        # 66 tests en ~0.2 s
python -m pytest --cov=bolsa_sim           # cobertura ~95 %
python -m black --check src tests
python -m ruff check src tests
```

Resultado actual:

```
TOTAL ... 95 % coverage
66 passed in 0.15s
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
|-- docs/
|   `-- propuesta_PRAC1.md       fuente Markdown de la propuesta
|-- src/bolsa_sim/
|   |-- __init__.py              7 clases exportadas (4 base + 3 jerarquia)
|   |-- __main__.py              CLI minimo (demo polimorfica)
|   |-- instrumento.py           InstrumentoBase  (padre: 5 attrs + 2 properties)
|   |-- accion.py                Accion           (PRAC2: sector + dividendo)
|   |-- bono.py                  Bono             (PRAC2: cupon + nominal + vencimiento)
|   |-- etf.py                   ETF              (PRAC2: indice + comision_gestion)
|   |-- cartera.py               Cartera          (5 attrs + 2 properties)
|   |-- operacion.py             Operacion        (5 attrs, frozen)
|   `-- mercado.py               Mercado          (5 attrs + 2 properties)
`-- tests/
    |-- conftest.py
    |-- test_instrumento.py
    |-- test_accion.py           herencia + validacion + polimorfismo
    |-- test_bono.py             herencia + cupones
    |-- test_etf.py              herencia + comision de gestion
    |-- test_cartera.py
    |-- test_operacion.py
    |-- test_mercado.py
    |-- test_integration.py      hello flow + herencia + jerarquia polimorfica
    `-- test_main.py             CLI smoke
```

## 7. Roadmap

| Hito   | Tema | Foco                                                                  |
|--------|------|------------------------------------------------------------------------|
| **PRAC1** | **1** | **Entrega 1.** 4 clases, encapsulamiento, frozen dataclass, herencia preparada. |
| **PRAC2** | **2** | **Esta entrega.** Jerarquia ``Accion/Bono/ETF(InstrumentoBase)``, herencia, sobrescritura y polimorfismo. |
| PRAC3  | 3    | Strategy + Factory para perfiles de cartera; excepciones de dominio.       |
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
