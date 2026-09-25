# Changelog

Todos los cambios relevantes del proyecto, en orden cronologico
inverso. El formato sigue "Keep a Changelog" (https://keepachangelog.com)
y este proyecto aun no sigue SemVer estricto: el versionado en la
PRAC1 es 0.1.0 (dearrollo) y pasara a 1.0.0 en la PRAC4 cuando se
etiquete la entrega final.

## [Unreleased]

### Planificado para PRAC2-PRAC4
* Jerarquia de activos (Accion/Bono/Etf) con herencia y excepciones
  de dominio.
* Strategy como ``ABC`` y contenedor generico en el Simulador.
* Patrones: Factory para construir perfiles, Observer para GUI.
* GUI (Tkinter o Textual), concurrencia para correr varios escenarios.

## [0.1.0] - 2026-09-25 - PRAC1

### Anadido
* Esqueleto del proyecto Python con `src/bolsa_sim/` y `pyproject.toml`.
* Paquete solo de biblioteca estandar (sin dependencias en runtime).
* Modelo de dominio basico: ``Activo``, ``BarraDiaria`` (NamedTuple),
  ``Posicion``, ``Transaccion`` (frozen dataclass), ``TipoActivo``,
  ``TipoOperacion``.
* ``Cartera`` con efectivo, posiciones, historial inmutable y
  validacion de operaciones (fondos insuficientes, cantidad invalida).
* ``MercadoSimulado`` con paseo aleatorio (browniano geometrico) y
  semilla inyectable para simulaciones reproducibles.
* Estrategias ``CompraYMantiene`` y ``AportePeriodico`` (DCA
  simplificado) y ``Simulador`` que las orquesta con ``Protocol``.
* Modulo ``memoria`` con la demostracion de identidad vs igualdad,
  aliasing, *rebinding*, *hashable* vs no, **defecto del argumento
  por defecto mutable** (identificado + explicado + corregido).
* ``__main__.py`` con CLI ``--demo``, ``--memoria``, ``--sesiones``,
  ``--semilla`` y ``--version``.
* Configuracion mediante variables de entorno (``config.py`` +
  ``.env.example``), sin dependencia ``python-dotenv``.
* 77 tests (4 niveles: humo, modelo, memoria, integracion) con
  cobertura inicial de 87 % (objetivo >= 70 % cumplido).
* Documentacion: README, propuesta (Markdown + PDF generado con
  reportlab), decisiones de diseno, defecto mutable explicado y
  documentacion de la API generada con pdoc.
* Hooks ``pre-commit`` (Black + Ruff) y workflow de CI en
  GitHub Actions (black --check, ruff check, pytest).
