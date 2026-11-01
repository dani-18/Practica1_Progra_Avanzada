# Simulador de Bolsa y Carteras de Inversion (v1.0.0)

> **Practicas 1-4 de Tecnicas de Programacion Avanzada** — Grupo A — curso 2026-2027.
> Simulador didactico de bolsa con jerarquia de instrumentos, estrategias de
> inversion, metricas de rentabilidad/riesgo, persistencia SQLite, exportacion
> JSON/CSV, GUI Tkinter y simulacion concurrente.
>
> PRAC1: 4 clases de dominio con `@property`/setter.
> PRAC2: `Accion`/`Bono`/`ETF` heredando de `InstrumentoBase` (polimorfismo) y CLI.
> **PRAC3: Strategy + Factory + excepciones de dominio + SQLite + JSON/CSV.**
> **PRAC4: GUI, concurrencia, cobertura >= 70 % y tag `v1.0.0`.**

## Indice

1. [Que hace el simulador](#1-que-hace-el-simulador)
   * [1.1 Casos de uso reales](#11-casos-de-uso-reales)
   * [1.2 Varias carteras y usuarios](#12-varias-carteras-y-usuarios)
   * [1.3 Alcance y limites](#13-alcance-y-limites)
2. [Instalacion y ejecucion rapida](#2-instalacion-y-ejecucion-rapida)
3. [Dominio y jerarquia](#3-dominio-y-jerarquia)
4. [Uso financiero: mercado, estrategias y metricas](#4-uso-financiero-mercado-estrategias-y-metricas)
5. [Persistencia y exportacion](#5-persistencia-y-exportacion)
6. [Concurrencia](#6-concurrencia)
7. [GUI](#7-gui)
8. [CLI interactiva](#8-cli-interactiva)
9. [Patrones y decisiones de diseno](#9-patrones-y-decisiones-de-diseno)
10. [Pruebas y calidad](#10-pruebas-y-calidad)
11. [Estructura del repositorio](#11-estructura-del-repositorio)
12. [Documentacion y roadmap](#12-documentacion-y-roadmap)

## 1. Que hace el simulador

El proyecto modela un pequeno mercado bursatil y permite:

* crear acciones, bonos y ETFs con validacion de sus invariantes;
* evolucionar precios con un movimiento browniano geometrico reproducible;
* aplicar shocks de mercado (`-15 %`, rally, etc.);
* comprar y vender con comisiones, controlando efectivo y posiciones;
* ejecutar estrategias (`comprar_mantener`, `momentum`, `rebalanceo`);
* calcular rentabilidad total/anualizada, volatilidad, Sharpe, Sortino y max
  drawdown;
* guardar y recuperar el estado completo en SQLite (o memoria/JSON);
* gestionar **varias carteras** (un usuario por cartera) y elegir la activa;
* exportar cartera, operaciones, sesiones y metricas a JSON/CSV;
* comparar estrategias en paralelo y operar desde CLI o GUI.

La logica de negocio esta separada de la infraestructura. El paquete runtime
es **solo biblioteca estandar** (`sqlite3`, `tkinter`, `concurrent.futures`...).

### 1.1 Casos de uso reales

El foco del proyecto es el **comportamiento financiero**, no la herramienta que
lo rodea. Estos son resultados reproducibles (semilla 42 o 7) que se pueden
repetir con el codigo de [`docs/CASOS_DE_USO.md`](docs/CASOS_DE_USO.md):

| Caso | Resultado real |
|---|---|
| Comprar y mantener 120 sesiones (10 000 EUR) | `+2,31 %`, drawdown `1,14 %`, Sharpe `1,95`, 3 operaciones |
| Crash del 15 % con 20 ACME | `-4,14 %`, drawdown `7,69 %`, volatilidad `10,77 %`, Sharpe `-0,76` |
| Comparar tres estrategias (120 sesiones) | `comprar_mantener` `+0,78 %`; `momentum` `-6,09 %` y 64 operaciones |
| Guardar/cargar en SQLite | 49 operaciones y 30 sesiones reconstruidas sin duplicados |

Ejemplo minimo de cartera y metricas:

```python
from bolsa_sim import ComprarMantener, Simulador
from bolsa_sim.demo import cartera_demo, mercado_demo

resultado = Simulador(
    mercado_demo(semilla=42),
    cartera_demo(efectivo=10_000.0),
    ComprarMantener(fraccion=0.95),
    sesiones=120,
).ejecutar()

print(resultado)             # [comprar_mantener] 120 sesiones ... (+2.31%) ops=3
print(resultado.metricas)    # rentabilidad, volatilidad, Sharpe, Sortino, drawdown
```

### 1.2 Varias carteras y usuarios

Cada cartera pertenece a un usuario y mantiene su propio efectivo, posiciones,
historial y curva de valor. `GestorCarteras` las registra, evita duplicados y
decide cual es la **cartera activa**:

```python
from bolsa_sim import GestorCarteras
from bolsa_sim.demo import cartera_demo, mercado_demo

mercado = mercado_demo(semilla=42)
gestor = GestorCarteras(cartera_demo())      # Dani
ana = gestor.crear("Ana", efectivo=2_000.0)  # queda activa
gestor.seleccionar("Dani")
gestor.actual.invertir(mercado, "ACME", 2, mercado.precio_de("ACME"), "s0000")
gestor.seleccionar("Ana")                    # las posiciones de Ana siguen vacias
print(gestor.nombres())                      # ('Dani', 'Ana')
```

En la CLI: `portfolios`, `new <usuario>`, `use <usuario>`. En la GUI, el
desplegable **Usuario** cambia la cartera activa y el boton **Nueva cartera**
la crea. `save`/`load` persisten y recuperan **todas** las carteras.

### 1.3 Alcance y limites

* Es un **simulador didactico**: los precios son sinteticos (movimiento
  browniano geometrico) y no se conecta a mercados reales.
* No es un sistema de trading ni una recomendacion de inversion.
* La persistencia guarda snapshots de sesion y el estado completo; no esta
  pensada para series historicas de alta frecuencia.
* La GUI es una herramienta de demostracion, no un terminal profesional.
* Las lineas futuras (datos reales, benchmark/alpha, Markowitz) estan en la
  hoja de ruta, no implementadas.

Separar el alcance evita prometer mas de lo que el codigo hace y mantiene el
esfuerzo principal en el dominio, que es el objetivo de la asignatura.

## 2. Instalacion y ejecucion rapida

```bash
python --version                  # 3.10 o superior
python -m venv .venv
.venv\Scripts\Activate.ps1        # o: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]" # pytest, coverage, black, ruff, pre-commit
```

Comandos principales:

```bash
python -m bolsa_sim                 # demo financiera completa
python -m bolsa_sim --cli           # consola interactiva
python -m bolsa_sim --gui           # interfaz grafica Tkinter
python -m bolsa_sim --simulate --sessions 120 --strategy momentum --seed 42
python -m bolsa_sim --parallel --sessions 60
python -m bolsa_sim --export resultados.json
python -m bolsa_sim --verbose      # logging DEBUG en consola
python -m bolsa_sim --log-file bolsa.log
python -m bolsa_sim --version       # bolsa-sim 1.0.0
```

### Logging

La biblioteca usa `logging` de la stdlib y **no** escribe nada al importarse.
La aplicacion configura nivel y destinos:

```bash
python -m bolsa_sim --verbose                 # DEBUG
python -m bolsa_sim --quiet                   # solo errores
python -m bolsa_sim --log-file bolsa.log      # consola + fichero
BOLSA_LOG_LEVEL=INFO python -m bolsa_sim
```

Se registran simulaciones, guardados/cargas, shocks y errores de dominio. El
detalle para desarrolladores esta en [`docs/DESARROLLO.md`](docs/DESARROLLO.md).

Tambien esta el entry point `bolsa-sim`:

```bash
bolsa-sim --cli
bolsa-sim --simulate --strategy rebalanceo
```

Ejemplo de salida de la demo (semilla 42, resultados reproducibles):

```text
== Demo (PRAC2: jerarquia de instrumentos) ==
[Accion] ACME (ACME): 'Acme Corp'  precio_base=120.00  volatilidad=0.20  flujo_anual=1.80
   sector='Tecnologia'  dividendo_anual=1.80  tipo='accion'
[Bono] BONO10 (B10): 'Bono 10 anos'  precio_base=100.00  volatilidad=0.05  flujo_anual=40.00
[ETF] SP500 (SPX): 'ETF S&P 500'  precio_base=400.00  volatilidad=0.15  flujo_anual=0.00
...
metricas: rentabilidad=-0.05%  anualizada=-2.58%  volatilidad=1.12%  ...
```

## 3. Dominio y jerarquia

| Clase | Rol | Atributos clave |
|---|---|---|
| `InstrumentoBase` | clase padre de la jerarquia | `id`, `nombre`, `simbolo`, `volatilidad`, `precio_base` |
| `Accion` | renta variable | `sector`, `dividendo_anual` |
| `Bono` | renta fija | `cupon_anual`, `valor_nominal`, `vencimiento` |
| `ETF` | fondo cotizado | `indice`, `comision_gestion` |
| `Operacion` | value object inmutable | `fecha`, `instrumento_id`, `cantidad`, `precio_ejecucion`, `tipo` |
| `Cartera` | efectivo, posiciones, historial | `propietario`, `efectivo`, `comision` |
| `Mercado` | cotizaciones y sesiones | `nombre`, `instrumentos`, `sesion`, `volumen_total`, `deriva` |

Las subclases usan `super().__init__()`, validan sus campos con
`@property`/setter y sobrescriben el comportamiento polimorfico:

```python
from bolsa_sim import Accion, Bono, ETF

instrumentos = [
    Accion("ACME", "Acme Corp", "ACME", 0.20, 120.0, sector="Tecnologia", dividendo_anual=1.80),
    Bono("BONO10", "Bono 10 anos", "B10", 0.05, 100.0, cupon_anual=0.04, vencimiento=10),
    ETF("SP500", "ETF S&P 500", "SPX", 0.15, 400.0, indice="S&P 500", comision_gestion=0.002),
]

for instrumento in instrumentos:
    # Mismo metodo, comportamiento distinto segun el tipo concreto.
    print(instrumento.tipo, instrumento.flujo_anual())

# accion 1.8 | bono 40.0 | etf 0.0
```

`ETF` no sobrescribe `flujo_anual()`: hereda el `0.0` de la base para mostrar
que una subclase solo implementa lo que le aplica. `mostrar()` se reutiliza
con `super().mostrar()` y anade los campos propios.

### Fabrica de instrumentos

`FabricaInstrumentos` aplica **Factory** y permite reconstruir la jerarquia
desde JSON/SQLite sin `isinstance` en el llamador:

```python
from bolsa_sim import FabricaInstrumentos, instrumento_a_dict

fabrica = FabricaInstrumentos.por_defecto()
datos = instrumento_a_dict(instrumentos[0])
copia = fabrica.desde_dict(datos)
assert copia == instrumentos[0]   # igualdad por id
```

## 4. Uso financiero: mercado, estrategias y metricas

### Mercado y shocks

```python
from bolsa_sim import Mercado
from bolsa_sim.demo import instrumentos_demo

mercado = Mercado("Bolsa", {i.id: i for i in instrumentos_demo()}, semilla=42, deriva=0.0005)
for _ in range(30):
    mercado.avanzar_sesion(volumen=100)

mercado.aplicar_shock(-0.10)       # crash puntual del 10 %
print(mercado.historial_precios("ACME"))
print(mercado.rendimiento_desde_inicio("ACME"))
```

### Simulacion de una estrategia

```python
from bolsa_sim import Momentum, Simulador
from bolsa_sim.demo import cartera_demo, mercado_demo

resultado = Simulador(
    mercado_demo(semilla=42),
    cartera_demo(),
    Momentum(ventana=10, fraccion=0.3),
    sesiones=120,
).ejecutar()

print(resultado)             # valor inicial -> final, rentabilidad, operaciones
print(resultado.metricas)    # volatilidad, Sharpe, Sortino, drawdown
```

Salida orientativa (semilla 42, 30 sesiones):

```text
[momentum] 30 sesiones  valor 1000.00 -> 976.33 EUR  (-2.37%)  ops=19
rentabilidad=-2.37%  anualizada=-18.23%  volatilidad=1.50%  max_drawdown=2.37%  ...
```

Las estrategias disponibles son:

| Estrategia | Idea | Parametros |
|---|---|---|
| `comprar_mantener` | reparte el capital al inicio y no vuelve a operar | `fraccion` |
| `momentum` | compra impulso positivo y vende el negativo | `ventana`, `umbral`, `fraccion`, `max_posiciones` |
| `rebalanceo` | corrige desviaciones sobre pesos objetivo | `pesos`, `banda` |

Se pueden crear por fabrica: `crear_estrategia("momentum", ventana=10)`.

### Metricas

```python
from bolsa_sim import calcular_metricas, metricas_cartera

metricas = calcular_metricas([100, 110, 105, 120])
print(metricas.rentabilidad_total)      # 0.20
print(metricas.max_drawdown)            # ~0.045
print(metricas.ratio_sharpe)

metricas_cartera(cartera, mercado)      # metricas sobre la curva de valor
```

## 5. Persistencia y exportacion

SQLite es el almacen principal. `RepositorioFactory` elige backend
(**Factory**) y `ServicioPersistencia` guarda/carga el estado completo.

```python
from bolsa_sim.persistencia import RepositorioFactory, ServicioPersistencia

repo = RepositorioFactory.crear("sqlite", "datos.sqlite")
servicio = ServicioPersistencia(repo)

servicio.guardar_estado(mercado, cartera)
mercado2, cartera2 = servicio.cargar_estado("Bolsa", "Dani")
servicio.exportar(mercado2, cartera2, "resultados.csv", "csv")
servicio.cerrar()
```

Para varias carteras:

```python
servicio.guardar_carteras(mercado, [cartera_dani, cartera_ana])
mercado2, carteras = servicio.cargar_carteras("Bolsa")
```

Backends: `sqlite` (principal), `memoria` (tests/simulaciones) y `json`
(fichero portable). El esquema incluye `instrumento`, `cartera`, `posicion`,
`operacion`, `sesion` y `precio_sesion`; el libro de operaciones es
**append-only**. El detalle de diseno esta en
[`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

Exportacion:

```python
from bolsa_sim.persistencia import exportar_resultados, exportar_simulacion

exportar_resultados(mercado, cartera, "resultados.json", "json")
exportar_resultados(mercado, cartera, "resultados.csv", "csv")
exportar_simulacion(resultado, "simulacion.json")
```

El CSV usa formato largo (`registro` = `metrica`, `resumen`, `posicion`,
`operacion`, `precio_sesion`) para ser consumible por hoja de calculo sin
perder informacion.

## 6. Concurrencia

Los escenarios son independientes (mercado, cartera y estrategia propios) y
se ejecutan en un `ThreadPoolExecutor`:

```python
from bolsa_sim import Escenario, ejecutar_escenarios

resultados = ejecutar_escenarios([
    Escenario("base", "comprar_mantener", semilla=42, sesiones=60),
    Escenario("tendencia", "momentum", semilla=42, sesiones=60),
    Escenario("rebalanceo", "rebalanceo", semilla=42, sesiones=60),
], max_workers=3)

for r in resultados:
    print(r.escenario.nombre, r.resultado.rentabilidad_total)
```

Desde la terminal: `python -m bolsa_sim --parallel --sessions 60`.

## 7. GUI

```bash
python -m bolsa_sim --gui
```

La ventana muestra la tabla del mercado, las posiciones, el panel de metricas
y la curva de valor. Incluye un desplegable **Usuario** para cambiar de
cartera y un boton **Nueva cartera** para crear otro usuario. Botones:
avanzar sesion, shock -10 %, comprar, vender, comparar estrategias
(concurrente), metricas, guardar/cargar y exportar.

Tkinter se importa de forma perezosa, por lo que el paquete y los tests
funcionan en entornos sin display (CI). Los helpers de formato y el calculo
de puntos del grafico son funciones puras testeadas.

## 8. CLI interactiva

```bash
python -m bolsa_sim --cli
```

| Comando | Accion |
|---|---|
| `help` / `?` | muestra la ayuda |
| `list` / `ls` | lista instrumentos y precios |
| `market` | estado del mercado |
| `portfolio` / `status` | cartera activa y valor liquidativo |
| `portfolios` / `carteras` | lista las carteras y marca la activa |
| `new <usuario> [efectivo] [comision]` | crea una cartera y la activa |
| `use <usuario>` | cambia la cartera activa |
| `price <id>` | precio actual |
| `buy <id> <cantidad> [precio]` | compra |
| `sell <id> <cantidad> [precio]` | vende |
| `next [volumen]` | avanza una sesion |
| `shock <variacion>` | aplica un shock (ej. `-0.15`) |
| `history` | historial de operaciones |
| `metrics` | rentabilidad, volatilidad, Sharpe, drawdown |
| `chart <id>` | grafico ASCII de precios |
| `strategies` | lista estrategias |
| `strategy <nombre> [k=v...]` | fija la estrategia de simulacion |
| `simulate [n] [estrategia] [k=v...]` | simula y muestra metricas |
| `parallel [n]` | compara estrategias en paralelo |
| `export <json\|csv> <ruta>` | exporta resultados |
| `save [ruta]` | guarda en SQLite (o backend actual) |
| `load <ruta> [propietario]` | carga un estado guardado |
| `quit` / `exit` | sale |

Ejemplo:

```text
bolsa> portfolios
Carteras (2):
 * Dani             efectivo=   1000.00 EUR  valor=   1000.00 EUR  ops=0
   Ana              efectivo=   2000.00 EUR  valor=   2000.00 EUR  ops=0
bolsa> use Ana
Cartera activa: 'Ana' (efectivo=2000.00 EUR, posiciones=0)
bolsa> buy acme 2
Compra ejecutada: Operacion(fecha='s0000', tipo='compra', ...)
bolsa> next 50
Sesion 1: ACME=119.93  BONO10=99.98  SP500=399.87
bolsa> metrics
Capital inicial=1000.00 EUR  valor actual=998.00 EUR
rentabilidad=-0.20%  anualizada=...  sharpe=...
bolsa> simulate 60 momentum
[momentum] 60 sesiones  valor 1000.00 -> ... EUR
bolsa> export json resultados.json
Exportado json en resultados.json
bolsa> save datos.sqlite
Estado guardado (RepositorioSQLite).
```

## 9. Patrones y decisiones de diseno

| Patron | Implementacion |
|---|---|
| **Strategy** | `EstrategiaInversion` (`ComprarMantener`, `Momentum`, `Rebalanceo`) y `Exportador` (`ExportadorJSON`, `ExportadorCSV`). |
| **Factory** | `FabricaInstrumentos`, `RepositorioFactory`, `crear_estrategia`. |
| **Repository** | `Repositorio` + `RepositorioSQLite` / `RepositorioMemoria` / `RepositorioJSON`. |
| **Inyeccion de dependencias** | `Cartera(..., repositorio=repo)` y `Mercado(..., repositorio=repo)`. |
| **Template Method** | `InstrumentoBase.mostrar()` y `flujo_anual()` reutilizados por las subclases. |
| **Value Object** | `Operacion` (`frozen=True, slots=True`). |
| **Registry / Manager** | `GestorCarteras`: registro de usuarios y cartera activa. |

Decisiones que conviene poder justificar:

* **Igualdad por `id`**: un `Accion` y un `Bono` con el mismo `id` son el
  mismo instrumento logico. Es util para agregar posiciones y reconstruir
  desde el almacen; el tipo concreto se conserva en la instancia. Documentado
  en `docs/ARQUITECTURA.md` (limitacion: un `id` es unico en todo el mercado).
* **Estrategia decide, simulador ejecuta**: mantiene las estrategias puras y
  testeables, y permite paralelizar escenarios sin estado compartido.
* **Append-only**: las operaciones no se modifican; `sincronizar_operaciones`
  verifica el prefijo guardado antes de anadir el sufijo nuevo.
* **Excepciones de dominio compatibles**: heredan tambien de `ValueError` /
  `KeyError` / `RuntimeError` para no romper el contrato de la biblioteca.
* **Deriva y shock**: la deriva modela tendencia; el shock modela un evento
  extremo sin falsear el contador de sesiones.
* **Sin dependencias runtime**: SQLite, Tkinter y concurrencia vienen con
  Python; el proyecto sigue siendo facil de instalar y corregir.

## 10. Pruebas y calidad

```bash
python -m pytest -q                        # 245 tests
python -m pytest --cov=bolsa_sim           # cobertura ~94 %
python -m pytest --cov=bolsa_sim --cov-fail-under=70
python -m black --check src tests
python -m ruff check src tests
```

Estado actual: **245 tests**, **93,88 %** de cobertura.

Los tests cubren casos limite de validacion, operaciones invalidas,
fondos/posiciones insuficientes, shocks extremos, series vacias/planas,
persistencia SQLite, JSON corrupto, exportacion, concurrencia, logging y GUI.
CI ejecuta Black, Ruff y pytest con `--cov-fail-under=70` en Python 3.10-3.13.
El detalle de comandos y convenciones esta en
[`docs/DESARROLLO.md`](docs/DESARROLLO.md).

## 11. Estructura del repositorio

```text
Practica_Progra_Avanzada/
|-- .github/workflows/ci.yml       CI + publicacion de API en GitHub Pages
|-- .pre-commit-config.yaml        hooks locales
|-- CHANGELOG.md
|-- LICENSE                        MIT
|-- README.md
|-- pyproject.toml                 metadata, Black/Ruff/pytest/coverage
|-- docs/
|   |-- ARQUITECTURA.md            diseno, patrones, formulas, decisiones
|   |-- CASOS_DE_USO.md            escenarios financieros con salidas reales
|   |-- DESARROLLO.md              guia de desarrollo, logging, CI y entrega
|   `-- api/                       API generada por pdoc y publicada en Pages
|-- src/bolsa_sim/
|   |-- __init__.py                API publica y version 1.0.0
|   |-- __main__.py                flags --demo/--cli/--gui/--simulate/--parallel/--export/--log-file
|   |-- instrumento.py             InstrumentoBase
|   |-- accion.py / bono.py / etf.py
|   |-- operacion.py               value object append-only
|   |-- cartera.py                 efectivo, posiciones, historial, curva
|   |-- mercado.py                 GBM, shocks, historial de precios
|   |-- fabrica.py                 FabricaInstrumentos + serializacion
|   |-- gestor_carteras.py         varias carteras + cartera activa
|   |-- excepciones.py             jerarquia ErrorBolsa
|   |-- logging_config.py          logging stdlib configurable
|   |-- metricas.py                rentabilidad, riesgo, Sharpe, Sortino
|   |-- estrategias.py             Strategy + fabrica de estrategias
|   |-- simulacion.py              Simulador + ResultadoSimulacion
|   |-- concurrencia.py            escenarios en ThreadPoolExecutor
|   |-- cli.py                     Shell interactiva
|   |-- gui.py                     GUI Tkinter (import perezoso)
|   |-- demo.py                    escenario de ejemplo reutilizable
|   |-- py.typed                   marcador PEP 561
|   `-- persistencia/
|       |-- __init__.py            API publica
|       |-- db.py                  conexion, PRAGMAs, transacciones, version
|       |-- esquema.sql            DDL
|       |-- repositorios.py        SQLite / memoria / JSON (Strategy)
|       |-- fabrica.py             RepositorioFactory (Factory)
|       |-- servicio.py            guardar/cargar estado completo
|       `-- exportadores.py        JSON / CSV (Strategy)
`-- tests/                         245 tests
```

## 12. Documentacion y roadmap

* `README.md` (este documento) y `CHANGELOG.md`.
* [`docs/CASOS_DE_USO.md`](docs/CASOS_DE_USO.md): escenarios financieros con
  salidas reales (comprar y mantener, crash, comparacion, persistencia).
* [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md): patrones, formulas,
  persistencia, concurrencia y decisiones.
* [`docs/DESARROLLO.md`](docs/DESARROLLO.md): entorno, tests, logging, CI y
  checklist de entrega.
* API automatica con `pdoc`:

```bash
python -m pip install -e ".[docs]"
python -m pdoc bolsa_sim -o docs/api --docformat google
```

CI genera `docs/api` en cada push y, desde `main`, la **publica en GitHub
Pages** con `actions/deploy-pages`:

<https://dani-18.github.io/Practica1_Progra_Avanzada/>

Asi la API evoluciona con el codigo y no depende de capturas manuales. Si se
quiere publicar en otro repositorio, basta ajustar el remoto y activar Pages
con origen **GitHub Actions**.

**Estado del roadmap**: PRAC1, PRAC2, PRAC3 y PRAC4 completadas. Lineas
futuras: mas estrategias (valor, pares, Markowitz), datos reales de mercado,
benchmark/alpha/beta, series historicas completas en SQLite y empaquetado de
escritorio.

## 13. Seguridad y licencia

- No consume credenciales ni servicios externos; `.env.example` solo tiene
  parametros de demo.
- El paquete runtime es **stdlib only**.
- Licencia MIT (ver `LICENSE`).
