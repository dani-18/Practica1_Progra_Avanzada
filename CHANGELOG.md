# Changelog

Todos los cambios relevantes del proyecto, en orden cronologico
inverso. Sigue "Keep a Changelog".

## [0.2.0] - 2026-09-25 - PRAC1 (reduccion minima)

### Cambios
- **Reduccion del modelo a 4 clases** segun requisito del alumno:
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
