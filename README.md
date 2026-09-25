# Simulador de Bolsa y Carteras de Inversion

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![Docs: pdoc](https://img.shields.io/badge/docs-pdoc-lightgrey.svg)](https://pdoc.dev/)

> **Practica 1 de Tecnicas de Programacion Avanzada** — Grupo A — curso 2026-2027.
> Simulacion didactica de un mercado de valores con activos ficticios
> para experimentar con estrategias, gestion de carteras y metricas
> basicas de rentabilidad/riesgo.

---

## Indice rapido

1. [Vision general](#1-vision-general)
2. [Caracteristicas implementadas (PRAC1)](#2-caracteristicas-implementadas-prac1)
3. [Requisitos](#3-requisitos)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Instalacion](#5-instalacion)
6. [Ejecucion rapida](#6-ejecucion-rapida)
7. [Pruebas y calidad](#7-pruebas-y-calidad)
8. [Documentacion y propuesta](#8-documentacion-y-propuesta)
9. [Modelo de dominio (Tema 1)](#9-modelo-de-dominio-tema-1)
10. [Defecto conceptual corregido](#10-defecto-conceptual-corregido)
11. [Roadmap](#11-roadmap)
12. [Notas de seguridad](#12-notas-de-seguridad)
13. [Licencia](#13-licencia)

---

## 1. Vision general

El proyecto implementa un pequeno **simulador de bolsa** sobre el que
se demuestra el Tema 1 de la asignatura: *objetos, memoria y
encapsulamiento*. La tematica es la "12. Simulador de Bolsa y
Carteras de Inversion" del enunciado, cubierta **a nivel de PoC** en
esta primera entrega y ampliable en PRAC2-PRAC4 con herencia,
patrones, GUI y concurrencia.

Una corrida tipica del proyecto es:

```
$ python -m bolsa_sim --demo --sesiones 30 --semilla 42
== Demo: Simulador de Bolsa y Carteras de Inversion (PRAC1) ==
  activos:    ['ACME', 'GLOB', 'OILX', 'TECH', 'BONO10']
  efectivo:   10000.00 EUR
  sesiones:   30
  semilla:    42
 sesion    efectivo   valor total  ...
    1    3491.00        9995.56 ...
   ...
   30    3384.12       10312.44 ...
== Resumen ==
  sesiones=30 valor_inicial=10000.00 EUR valor_final=10312.44 EUR
  ROI total = 3.12 %
  drawdown maximo (aprox, 2 puntos) = 0.00 %
```

## 2. Caracteristicas implementadas (PRAC1)

- **Modelado de activos.** Clase `Activo` escrita a mano, con
  `@property` + setter con validacion (`ticker`, `nombre`, `precio`,
  `volatilidad`, `dividendo_anual`). `__repr__`, `__eq__` y
  `__hash__` para que dos activos con el mismo *ticker* sean el mismo
  objeto logico.
- **Tipos y value objects.** `TipoActivo` y `TipoOperacion` como
  `Enum`. `BarraDiaria` como `NamedTuple` inmutable y hashable.
- **Posicion.** Cantidad validada (no negativa, entera).
- **Transaccion.** `@dataclass(frozen=True, slots=True)` con validacion
  en `__post_init__`. Historial **inmutable**.
- **Cartera.** Efectivo + posiciones (`dict`) + transacciones (`list`).
  Compra / venta con comisiones y rebote si no hay saldo.
- **Mercado.** `MercadoSimulado` con paseo aleatorio (movimiento
  browniano geometrico), semilla inyectable y `tuple[BarraDiaria, ...]`
  como historial hacia el cliente.
- **Simulador.** Compone mercado + cartera + estrategia. Estrategia
  modelada con `Protocol` y *duck typing*; dos estrategias de partida:
  `CompraYMantiene` y `AportePeriodico` (DCA).
- **Metricas.** `rentabilidad_total`, `drawdown_maximo`
  (extensibles a Sharpe y volatilidad en PRAC4).
- **Memoria.** Modulo con demostraciones de identidad (`is`) vs
  igualdad (`==`), *aliasing*, *rebinding*, *hashable* vs no, **el
  defecto del argumento por defecto mutable** (identificado, explicado
  y corregido).
- **CLI.** Entry point `python -m bolsa_sim` con subcomandos
  `--demo`, `--memoria`, `--sesiones`, `--semilla`, `--version`.
- **Tests.** 77 casos con `pytest` + `coverage` (≈ 87 % de cobertura,
  supera el objetivo final del 70 %).
- **Calidad.** `black`, `ruff`, hooks `pre-commit` y workflow de CI.
- **Docs.** Markdown + PDF de la propuesta + `pdoc` regenerable.

## 3. Requisitos

- **Python 3.10 o superior** (probado con 3.14).
- *Solo* la biblioteca estandar para **ejecutar** el simulador. Las
  herramientas de desarrollo (`pytest`, `black`, `ruff`,
  `reportlab`, `pdoc`, `pre-commit`) son *dependencias opcionales*
  declaradas en `pyproject.toml`.
- **No** se conecta a internet, **no** se usan APIs reales y **no**
  se suben secretos.

## 4. Estructura del repositorio

```text
Practica_Progra_Avanzada/                <-- raiz del repo (este directorio)
+-- .github/workflows/ci.yml             Black + Ruff + pytest en CI
+-- .pre-commit-config.yaml              Hooks locales opcionales
+-- .env.example                         Plantilla de variables de entorno
+-- .gitignore                           venv/, __pycache__/, .env, ...
+-- .venv/                               Entorno virtual local (gitignored)
+-- CHANGELOG.md                         Versionado narrativo
+-- LICENSE                              MIT
+-- README.md                            Este fichero
+-- pyproject.toml                       Configuracion Black/Ruff/pytest/coverage
+-- dev_pdf_text.txt                     Salida temporal de inspeccion del PDF
+-- docs/
|   +-- api/                             HTML generado por pdoc (incluido)
|   +-- propuesta_PRAC1.md               Fuente Markdown de la propuesta
|   +-- PRAC1_Propuesta_SimuladorBolsa.pdf   PDF generado para entrega
|   +-- defecto_estado_compartido.md     Ejercicio del Tema 1 explicado
|   +-- decisiones_diseno.md             Tradeoffs adoptados (10 decisiones)
+-- src/bolsa_sim/
|   +-- __init__.py                      Metadatos + API publica
|   +-- __main__.py                      CLI (argparse)
|   +-- activos.py                       Activo, Posicion, Transaccion, ...
|   +-- mercado.py                       MercadoSimulado
|   +-- cartera.py                       Cartera (compra/venta/valor_total)
|   +-- estrategias.py                   CompraYMantiene, AportePeriodico
|   +-- simulacion.py                    Simulador y ResultadoSimulacion
|   +-- metricas.py                      Rentabilidad + drawdown
|   +-- memoria.py                       Demostraciones Tema 1
|   +-- config.py                        Configuracion desde os.environ
|   +-- py.typed                         PEP 561 (paquete tipado)
+-- tests/
|   +-- conftest.py
|   +-- test_modelo.py                   Pruebas de humo exigidas por PRAC1
|   +-- test_activos.py
|   +-- test_cartera.py
|   +-- test_mercado.py
|   +-- test_estrategias.py
|   +-- test_simulacion.py               Mini-integracion
|   +-- test_memoria.py                  Tema 1 + defecto mutable
|   +-- test_metricas.py
|   +-- test_config.py
|   +-- test_main.py                     CLI smoke tests
+-- tools/
    +-- generar_propuesta_pdf.py         CLI para regenerar la propuesta PDF
+-- htmlcov/                             Reporte HTML de coverage (gitignored)
```

## 5. Instalacion

```bash
# 1) clonar y entrar
git clone https://github.com/dani-18/Practica1_Progra_Avanzada.git
cd Practica1_Progra_Avanzada

# 2) crear y activar un entorno virtual (recomendado)
python -m venv .venv
#  Windows (PowerShell):
.venv\Scripts\Activate.ps1
#  Unix/macOS (bash/zsh):
source .venv/bin/activate

# 3) instalar el paquete en modo desarrollo con todas las extras
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
```

> *Si no quieres instalar todo*, basta con `python -m pip install -e .`
> (instala el paquete solo y permite ejecutar `python -m bolsa_sim`).

## 6. Ejecucion rapida

```bash
# --demo              Hello flow (30 sesiones, semilla 42)
python -m bolsa_sim --demo

# --memoria           Demostraciones de identidad, aliasing y defecto mutable
python -m bolsa_sim --memoria

# --demo --sesiones N --semilla S  Parametros del demo
python -m bolsa_sim --demo --sesiones 60 --semilla 7

# --version           Version del paquete
python -m bolsa_sim --version
```

Tambien se puede usar el entry point instalado:

```bash
bolsa-sim --demo
```

> Las variables de entorno del paquete (`SIMULADOR_SEMILLA`,
> `SIMULADOR_SESIONES`, `SIMULADOR_EFECTIVO_INICIAL`,
> `SIMULADOR_TICKERS`) sobreescriben los *defaults*. Si existe un
> `.env`, la primera vez exportalas con `set -a; source .env; set +a`
> (Unix) o el bucle de PowerShell documentado en `docs/`.

## 7. Pruebas y calidad

### Suite completa

```bash
python -m pytest                  # ~77 tests en <1 s
python -m pytest --cov=bolsa_sim  # con cobertura
```

**Resultado esperado** (al cierre de PRAC1):

```
TOTAL ... 87 % coverage
77 passed in ~0.25s
```

### Smoke tests (subconjunto que la asignatura pide)

```bash
python -m pytest tests/test_modelo.py -v
```

### Formateo y lint

```bash
python -m black --check src tests
python -m ruff check src tests
python -m ruff format src tests    # opcional, actua como Black
```

### Pre-commit (opcional)

```bash
python -m pip install pre-commit
pre-commit install                 # activa los hooks
pre-commit run --all-files         # ejecutar a mano
```

## 8. Documentacion y propuesta

| Recurso                                              | Comando                                                                         |
|------------------------------------------------------|---------------------------------------------------------------------------------|
| **Propuesta** (Markdown)                             | `docs/propuesta_PRAC1.md`                                                       |
| **Propuesta** (PDF, para entregar)                   | `python tools/generar_propuesta_pdf.py` genera `docs/PRAC1_Propuesta_SimuladorBolsa.pdf` |
| **Defecto mutable explicado** (Tema 1)               | `docs/defecto_estado_compartido.md`                                             |
| **Decisiones de diseno** (10 decisiones justificadas) | `docs/decisiones_diseno.md`                                                     |
| **Documentacion API** (HTML generado por pdoc)       | `python -m pdoc bolsa_sim --output-dir docs/api`                                |

## 9. Modelo de dominio (Tema 1)

```
+-----------------+         contiene 0..N
| MercadoSimulado |----------------------+
| -tickers        |                      v
| -historial      |              +--------------+
+-----------------+              |  Posicion    |
         |                       |  -activo     |
         | actualiza precios     |  -cantidad   |
         v                       +------+-------+
+-----------------+                     | referencia
|     Activo      |<--------------------+
| -ticker         |
| -precio         |
| -volatilidad    |
+-----------------+
         ^
         |
+-----------------+         registra
|    Cartera      |------------------+
| -efectivo       |                  v
| -posiciones     |        +-----------------------+
| -transacciones  |        |  Transaccion (frozen) |
+-----------------+        |  -tipo, -ticker,      |
         ^                |  -cantidad, -precio,  |
         | opera          |  -comision            |
         |                +-----------------------+
+-----------------+
|   Simulador     |   compone
| +ejecutar(n)    |-------+
+-----------------+       v
+-----------------+   MercadoSimulado + Cartera + Estrategia
|   Estrategia    |
|   (Protocol)    |
+-----------------+
```

El detalle completo (relaciones, tipos, multiplicidades y decisiones
explicitas) esta en `docs/propuesta_PRAC1.md` y `docs/decisiones_diseno.md`.

## 10. Defecto conceptual corregido

El temario pide *identificar, explicar y corregir un defecto conceptual
asociado al estado compartido*. Lo hemos trabajado en dos frentes:

1. **Demostracion.** `src/bolsa_sim/memoria.py` contiene una funcion
   defectuosa (`registrar_evento_defectuoso`) con `# noqa: B006` para
   que el linter anote el bug; y su version corregida
   (`registrar_evento_correcto`) justo al lado.
2. **Documentacion.** `docs/defecto_estado_compartido.md` explica con
   detalle el modelo (por que Python evalua los valores por defecto
   una sola vez, como desemboca en aliasing, y la correccion
   idiomatica con `None` como centinela).
3. **Tests.** `tests/test_memoria.py` cubre:
   - que el defecto produce `is True` (lista compartida),
   - que la correccion produce `is not`,
   - que el comportamiento se invierte si el llamante pasa su lista.

## 11. Roadmap

| Hito | Tema | Entregable principal                                       |
|------|------|------------------------------------------------------------|
| **PRAC1** | 1 | **Esta entrega.** Esqueleto, modelo, memoria, PoC.      |
| PRAC2     | 2 | Herencia en activos, excepciones de dominio, ``Strategy`` como ``ABC``. |
| PRAC3     | 3 | Patrones (Factory, Observer, Strategy formal).            |
| PRAC4     | 4 | GUI + concurrencia; cobertura >= 70 %; tag ``v1.0.0``.    |

## 12. Notas de seguridad

- **Sin secretos.** Este proyecto no consume credenciales, tokens ni
  claves API. El fichero `.env` *no* debe subirse al repo; esta
  incluido en `.gitignore` y solo `.env.example` se versiona con
  valores de demostracion.
- **Determinismo.** El RNG inyectable (`random.Random`) hace que las
  simulaciones sean reproducibles: util para depurar y para los tests.

## 13. Licencia

Distribuido bajo la **Licencia MIT**. Ver [`LICENSE`](./LICENSE).
(Copyright © 2026 dani-18 y colaboradores.)
