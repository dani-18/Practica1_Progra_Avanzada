# Changelog

Todos los cambios relevantes del proyecto, en orden cronologico
inverso. Sigue "Keep a Changelog".

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
