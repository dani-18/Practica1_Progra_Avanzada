# Changelog

Todos los cambios relevantes del proyecto, en orden cronologico
inverso. Sigue "Keep a Changelog".

> Los conteos de tests de cada version son historicos. La version actual
> (1.0.0) tiene **221 tests** y una cobertura de **~94 %**.

## [1.0.0] - 2026-10-30 - PRAC3 + PRAC4 (patrones, persistencia, GUI)

### Anadido
- **Patron Strategy**:
  - `bolsa_sim.estrategias` con `EstrategiaInversion`, `ComprarMantener`,
    `Momentum` y `Rebalanceo`. Las estrategias solo **deciden**
    (`Decision`); `Simulador` ejecuta las ordenes.
  - `bolsa_sim.persistencia.exportadores` con `ExportadorJSON` y
    `ExportadorCSV` intercambiables.
- **Patron Factory**:
  - `FabricaInstrumentos` (creacion y serializacion de `Accion/Bono/ETF`).
  - `RepositorioFactory` (SQLite, memoria o JSON; infiere por extension).
  - `crear_estrategia(nombre, **parametros)`.
- **Excepciones de dominio** (`ErrorBolsa` y subclases) compatibles con
  `ValueError`/`KeyError`/`RuntimeError`.
- **Persistencia real**:
  - SQLite como almacen principal (`persistencia/db.py`, `esquema.sql`).
  - Repositorios SQLite, memoria y JSON con interfaz comun.
  - `ServicioPersistencia` para guardar/cargar mercado, cartera, posiciones,
    historial y sesiones; libro de operaciones append-only idempotente.
- **Exportacion** JSON/CSV de cartera, posiciones, operaciones, sesiones y
  metricas; `exportar_simulacion`.
- **Metricas** (`metricas.py`): rentabilidad total/anualizada, volatilidad,
  max drawdown, Sharpe y Sortino; `metricas_cartera`.
- **Simulacion mas rica**: deriva de mercado, shocks puntuales, historial y
  snapshots por sesion, curva de valor de la cartera.
- **Concurrencia** (`concurrencia.py`): escenarios independientes en
  `ThreadPoolExecutor` con resultados reproducibles.
- **GUI Tkinter** (`gui.py`): tablas de mercado/posiciones, panel de metricas,
  grafico de la curva, compra/venta, shock, simulacion, guardar/cargar/exportar.
- **CLI ampliada**: `metrics`, `chart`, `strategies`, `strategy`, `simulate`,
  `parallel`, `shock`, `export`, `save` y `load`.
- **Entry point**: `--gui`, `--simulate`, `--parallel`, `--sessions`,
  `--strategy`, `--seed`, `--drift` y `--export`.
- Documentacion de arquitectura (`docs/ARQUITECTURA.md`) y job de CI que
  genera la API con `pdoc`.
- Tests: **88 -> 221**, cobertura ~94 % (`--cov-fail-under=70`).

### Cambiado
- `Mercado` incorpora `deriva`, `historial_precios`, `series`, `sesiones`,
  `aplicar_shock`, `registrar_precio`, `avanzar_sesiones` y restauracion de
  estado. La simulacion sigue siendo reproducible por semilla.
- `Cartera` incorpora `capital_inicial`, `curva_valor`, `anotar_valor`,
  `resumen`, API estricta `comprar`/`vender` e inyeccion de repositorio.
- `InstrumentoBase` mantiene la igualdad por `id` (decision documentada).
- `pyproject.toml`: version `1.0.0`, datos de paquete para `esquema.sql` y
  `fail_under = 70`.
- CI multi-version (3.10-3.13) con cobertura obligatoria y construccion de
  documentacion.

## [0.4.0] - 2026-10-09 - Interfaz CLI interactiva

### Anadido
- ``bolsa_sim.cli.Shell``: consola interactiva lanzable con
  ``python -m bolsa_sim --cli`` (alias ``--interactive``). Comandos:
  ``help``, ``list``, ``market``, ``portfolio``, ``price``, ``buy``,
  ``sell``, ``next``, ``history`` y ``quit``/``exit``.
- ``bolsa_sim.demo``: centraliza el escenario de ejemplo
  (``instrumentos_demo``/``mercado_demo``/``cartera_demo``) que ahora
  comparten la demo y la CLI.
- ``Shell.ejecutar()`` separa el procesado de cada linea de la lectura
  por teclado, lo que permite testear la interfaz sin entrada real.
- Tests: ``tests/test_cli.py`` (comandos, errores de uso, ``run``/``quit``
  y fin por EOF). **66 -> 88 tests**.

### Cambiado
- ``__main__.py``: nuevo flag ``--cli``/``--interactive``; la demo
  reutiliza ``bolsa_sim.demo``.
- Exportada ``Shell`` en el paquete (``__all__``).
- Version del paquete ``0.3.0`` -> ``0.4.0``.

## [0.3.0] - 2026-10-09 - PRAC2 (jerarquia de instrumentos)

### Anadido
- **Jerarquia de instrumentos** (herencia de ``InstrumentoBase``):
  - ``Accion``: campos ``sector`` y ``dividendo_anual``; helper
    ``rentabilidad_por_dividendo()``.
  - ``Bono``: campos ``cupon_anual``, ``valor_nominal`` y
    ``vencimiento``; helpers ``cupon_anual_eur()`` y
    ``rendimiento_actual()``.
  - ``ETF``: campos ``indice`` y ``comision_gestion``; helper
    ``coste_anual()``.
- Cada subclase usa ``super().__init__()``, valida sus campos con
  ``@property``/``@setter`` y fija su atributo de clase ``tipo``.
- **Polimorfismo**: ``InstrumentoBase`` define ``flujo_anual()`` (0.0) y
  ``mostrar()``; las subclases los sobrescriben/amplian. La demo y los
  tests suman ``flujo_anual()`` sin conocer el tipo concreto.
- Exportadas las 3 subclases en ``bolsa_sim`` (7 clases en total).
- Tests: ``test_accion.py``, ``test_bono.py``, ``test_etf.py`` y un test
  de integracion de la jerarquia polimorfica. **37 -> 66 tests** (95 %
  de cobertura).

### Cambiado
- ``InstrumentoBase.mostrar()`` usa ``type(self).__name__`` para que las
  subclases hereden el formato.
- Version del paquete ``0.2.0`` -> ``0.3.0`` (``pyproject.toml`` y
  ``__init__``).

## [0.2.0] - 2026-09-25 - PRAC1 (reduccion minima)

### Cambios
- **Modelo en 4 clases** :
  - ``InstrumentoBase``: clase padre preparada para herencia futura (PRAC2).
  - ``Cartera``: composicion por asociacion con ``Operacion`` y un ``Mercado``.
  - ``Operacion``: registro inmutable (`frozen dataclass`).
  - ``Mercado``: motor de cotizaciones con sesion y volumen_total.
- Cada clase tiene 3-5 atributos propios y un metodo ``mostrar()`` que imprime por pantalla.
- Tres de las cuatro clases exponen ``@property`` + ``@setter`` con validacion (cumple "al menos dos").
- Eliminado (movido a ``legacy/``) el modelo extendido anterior para no contaminar la entrega minima:
  ``activos.py``, ``mercado.py``, ``cartera.py`` (legacy), ``estrategias.py``, ``simulacion.py``,
  ``metricas.py``, ``memoria.py``, ``config.py``, ``__main__.py`` (legacy).

### Anadido
- ``tests/test_integration.py::test_herencia_preparada``: comprueba que ``InstrumentoBase``
  admite una subclase trivial que hereda las properties y su validacion.
- CLI minimo: ``python -m bolsa_sim --demo`` y ``--version``.
- 37 tests verdes, cobertura ~93 % (objetivo PRAC4: >= 70 %).

## [0.1.0] - 2026-09-25 - PRAC1 (modelo extendido)

### Anadido (resumen)
- Esqueleto del proyecto (`src/bolsa_sim/` con 11 modulos).
- 77 tests con cobertura ~87 %; paquete stdlib-only; CI en GitHub Actions.
- Documentos: propuesta en md+pdf, defecto mutable, decisiones de diseno, README, CHANGELOG.
