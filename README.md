# Simulador de Bolsa y Carteras de Inversion (PRAC1 + PRAC2)

> **Practicas 1 y 2 de Tecnicas de Programacion Avanzada** — Grupo A — curso 2026-2027.
> PRAC1 entrega 4 clases de dominio con ``@property``/setter y ``mostrar()``.
> PRAC2 anade la **jerarquia de instrumentos** ``Accion``, ``Bono`` y
> ``ETF`` heredando de ``InstrumentoBase`` (herencia, sobrescritura y
> polimorfismo). Ademas incluye una **interfaz interactiva de CLI**
> (``--cli``) para operar el mercado desde la terminal.

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
polimorfismo. Las practicas PRAC3-PRAC4 iran anadiendo patrones,
**persistencia con SQLite**, GUI y concurrencia.

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
python -m bolsa_sim --demo        # flujo completo: Accion + Bono + ETF + mercado + cartera
python -m bolsa_sim --cli         # interfaz interactiva de linea de comandos
python -m bolsa_sim --version     # imprime 'bolsa-sim 0.4.0'
```

Tambien desde el entry point:

```bash
bolsa-sim --demo
bolsa-sim --cli
```

### Interfaz interactiva (`--cli`)

Abre una consola para operar el escenario de ejemplo (una `Accion`, un
`Bono` y un `ETF` con 1.000 EUR de efectivo). El procesamiento de cada
linea esta separado de la lectura por teclado, asi que es testeable.

```text
Simulador de Bolsa (CLI). Escribe 'help' para ver los comandos.
bolsa> list
Mercado 'Bolsa Continuo' (sesion 0):
  ACME     accion   Acme Corp            precio=    120.00 EUR  vol=0.20
  BONO10   bono     Bono 10 anos         precio=    100.00 EUR  vol=0.05
  SP500    etf      ETF S&P 500          precio=    400.00 EUR  vol=0.15
bolsa> buy acme 2
Compra ejecutada: Operacion(fecha='s0000', tipo='compra', ...)
bolsa> next 50
Sesion 1: ACME=119.93  BONO10=99.98  SP500=399.87
bolsa> portfolio
...
```

| Comando                                   | Accion                                  |
|-------------------------------------------|-----------------------------------------|
| `help` (`?`)                              | Muestra la ayuda.                       |
| `list` (`ls`)                             | Lista los instrumentos y sus precios.   |
| `market`                                  | Estado del mercado.                     |
| `portfolio` (`status`)                    | Cartera y valor liquidativo.            |
| `price <instrumento>`                     | Precio actual.                          |
| `buy <instrumento> <cantidad> [precio]`   | Compra.                                 |
| `sell <instrumento> <cantidad> [precio]`  | Vende.                                  |
| `next [volumen]`                          | Avanza una sesion (shock de mercado).   |
| `history`                                 | Historial de operaciones.               |
| `quit` (`exit`)                           | Sale de la consola.                     |

Si se omite `[precio]`, se usa el precio actual del mercado.

## 5. Pruebas y calidad

```bash
python -m pytest -q                        # 88 tests en ~0.2 s
python -m pytest --cov=bolsa_sim           # cobertura ~95 %
python -m black --check src tests
python -m ruff check src tests
```

Resultado actual:

```
TOTAL ... 95 % coverage
88 passed in 0.20s
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
|-- src/bolsa_sim/
|   |-- __init__.py              paquete: clases base + jerarquia + Shell
|   |-- __main__.py              entry point (--demo / --cli / --version)
|   |-- cli.py                   Shell interactiva
|   |-- demo.py                  escenario de ejemplo reutilizable
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
    |-- test_cli.py              comandos de la consola + run/quit/EOF
    `-- test_main.py             CLI smoke
```

## 7. Roadmap

### 7.1 Vision por hitos

| Hito   | Tema | Foco                                                                  |
|--------|------|------------------------------------------------------------------------|
| **PRAC1** | **1** | **Entrega 1.** 4 clases, encapsulamiento, frozen dataclass, herencia preparada. |
| **PRAC2** | **2** | **Esta entrega.** Jerarquia ``Accion/Bono/ETF(InstrumentoBase)``, herencia, sobrescritura y polimorfismo + **interfaz CLI interactiva** (``--cli``): operar mercado, cartera e historial. |
| **PRAC3** | **3** | Patrones (**Strategy + Factory**) + **excepciones de dominio** + **capa de persistencia**: **SQLite** como almacen principal y **exportacion de resultados a JSON/CSV**. |
| **PRAC4** | **4** | GUI, concurrencia, ≥ 70 % cobertura, tag ``v1.0.0``.                    |

### 7.2 PRAC3 en detalle (patrones + persistencia)

La guia de PRAC3 exige **persistencia o integracion externa**. Este hito cubre
explicitamente los cuatro puntos pedidos y los ancla en el modelo ya existente
(``Operacion``, ``Cartera``, ``Mercado``):

| Requisito PRAC3               | Solucion propuesta                                                                 |
|-------------------------------|------------------------------------------------------------------------------------|
| Persistencia                  | **SQLite** mediante el modulo de biblioteca estandar ``sqlite3`` (sin dependencias nuevas). |
| Ficheros JSON/CSV             | Exportadores ``exportar_json()`` / ``exportar_csv()`` para operaciones, carteras y precios de sesion. |
| Exportacion de resultados     | Volcado de valor liquidativo, posiciones e historial por cartera y por sesion.      |
| Almacenamiento de operaciones | Libro **append-only** en SQLite: nunca se modifica ni se borra una operacion ya escrita. |

**Diseno de la capa de persistencia** (estructura objetivo):

```text
src/bolsa_sim/persistencia/
|-- __init__.py         API publica (conectar, RepositorioFactory, exportadores)
|-- db.py               conexion sqlite3, PRAGMAs y versionado de esquema
|-- esquema.sql         DDL de las tablas (fuente unica de verdad)
|-- repositorios.py     RepositorioOperaciones / RepositorioCartera / RepositorioSesiones
|-- fabrica.py          RepositorioFactory: elige backend (SQLite | memoria | JSON)   <-- Factory
`-- exportadores.py     exportar_json() / exportar_csv()                              <-- Strategy de formato
```

**Esquema SQLite propuesto** (operaciones, carteras y sesiones de mercado):

```sql
-- Instrumentos: datos comunes + campos de subclase en JSON (Accion/Bono/ETF)
CREATE TABLE instrumento (
    id           TEXT PRIMARY KEY,
    nombre       TEXT NOT NULL,
    simbolo      TEXT NOT NULL,
    tipo         TEXT NOT NULL,              -- 'accion' | 'bono' | 'etf' | ...
    volatilidad  REAL NOT NULL,
    precio_base  REAL NOT NULL,
    detalle      TEXT NOT NULL DEFAULT '{}'  -- sector/dividendo/cupon/indice, en JSON
);

-- Carteras
CREATE TABLE cartera (
    id           INTEGER PRIMARY KEY,
    propietario  TEXT NOT NULL,
    efectivo     REAL NOT NULL CHECK (efectivo >= 0),
    comision     REAL NOT NULL CHECK (comision >= 0)
);

-- Posiciones abiertas (estado actual; se recalculan desde el libro de operaciones)
CREATE TABLE posicion (
    cartera_id     INTEGER NOT NULL REFERENCES cartera(id),
    instrumento_id TEXT    NOT NULL REFERENCES instrumento(id),
    cantidad       INTEGER NOT NULL CHECK (cantidad > 0),
    PRIMARY KEY (cartera_id, instrumento_id)
);

-- Libro de operaciones: APPEND-ONLY (sin UPDATE ni DELETE)
CREATE TABLE operacion (
    id               INTEGER PRIMARY KEY,
    cartera_id       INTEGER NOT NULL REFERENCES cartera(id),
    fecha            TEXT NOT NULL,
    instrumento_id   TEXT NOT NULL REFERENCES instrumento(id),
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_ejecucion REAL NOT NULL CHECK (precio_ejecucion > 0),
    tipo             TEXT NOT NULL CHECK (tipo IN ('compra', 'venta'))
);

-- Mercados y sesiones de mercado
CREATE TABLE mercado (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL,
    semilla INTEGER
);
CREATE TABLE sesion (
    id         INTEGER PRIMARY KEY,
    mercado_id INTEGER NOT NULL REFERENCES mercado(id),
    numero     INTEGER NOT NULL,   -- contador de sesion (Mercado.sesion)
    volumen    INTEGER NOT NULL,   -- volumen_total acumulado
    UNIQUE (mercado_id, numero)
);
-- Snapshot de precios al cierre de cada sesion
CREATE TABLE precio_sesion (
    sesion_id      INTEGER NOT NULL REFERENCES sesion(id),
    instrumento_id TEXT    NOT NULL REFERENCES instrumento(id),
    precio         REAL    NOT NULL CHECK (precio > 0),
    PRIMARY KEY (sesion_id, instrumento_id)
);
```

**Tareas de PRAC3:**

1. ``persistencia/db.py``: abrir conexion, ``PRAGMA foreign_keys=ON``,
   ``journal_mode=WAL`` y esquema versionado (migraciones simples).
2. Repositorios con **Strategy**: misma interfaz (``guardar_operacion``,
   ``cargar_historial``, ``guardar_sesion``, ...) para los backends SQLite,
   en memoria y JSON.
3. **Factory** (``RepositorioFactory``) que devuelve el repositorio adecuado
   segun la configuracion (p. ej. ``--db ruta.sqlite``).
4. Integrar ``Cartera``/``Mercado`` para que ``invertir``, ``desinvertir`` y
   ``avanzar_sesion`` persistan mediante inyeccion del repositorio, sin
   acoplar el dominio al motor de almacenamiento.
5. Exportadores JSON/CSV de resultados (valor liquidativo, posiciones,
   historial de operaciones y precios por sesion).
6. Excepciones de dominio (``ErrorPersistencia``, ``InstrumentoDesconocido``,
   ``OperacionInvalida``, ...).
7. Tests con ``sqlite3`` en memoria (``:memory:``) para no tocar disco y
   mantener la cobertura >= 70 %.

## 8. Documentacion adicional

* `README.md` (este documento) y `CHANGELOG.md` — guia de uso e historico
  de cambios.
* La ayuda embebida de la consola: `python -m bolsa_sim --cli` y luego
  `help`.

## 9. Seguridad y licencia

- No consume credenciales; ``.env`` solo tiene parametros de demo.
- El paquete runtime es **stdlib only**.
- Licencia: MIT (ver ``LICENSE``).
