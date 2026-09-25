# Decisiones de diseno (PRAC1)

Justificacion de las elecciones de diseno tomadas en el codigo del
modelo de dominio. Cada decision tiene: contexto, alternativa(s)
descartada(s) y motivo.

## D1. ``Activo`` no se declara como ``@dataclass``.

* **Contexto.** Hay que mostrar el modelo de memoria (Tema 1):
  ``__init__``, atributos privados con guion bajo, ``@property`` y
  ``@setter`` con validacion, ``__repr__``, ``__eq__``, ``__hash__``.
* **Descartado.** ``@dataclass(frozen=True)`` representa todo eso
  automaticamente, pero como una caja negra. Para una primera entrega
  didactica preferimos que el alumno *vea* cada pieza.
* **Mitigacion.** Las clases **inmutables** (como ``Transaccion`` y
  ``BarraDiaria``) **si** usan ``frozen`` ``@dataclass``; eso deja
  ``Activo`` como ejemplo de clase mutable con propiedades, y los
  *value objects* como ejemplos de inmutabilidad.

## D2. ``Posicion`` declara ``__hash__ = None``.

* **Contexto.** ``Posicion`` tiene ``__eq__`` que compara por
  ``(activo, cantidad)``. En Python, una clase con ``__eq__``
  implementada y sin ``__hash__`` ya es no-hashable, pero el linter
  ``PLW1641`` (incluido en Ruff) avisa. Para dejar el contrato
  explicito, lo declaramos ``__hash__ = None``.
* **Por que importa.** Un hashable sirve como clave de dict y en set;
  una posicion de cartera representa una relacion mutable, no es
  razonable usarla asi.

## D3. ``Transaccion`` es ``@dataclass(frozen=True, slots=True)``.

* **Contexto.** El historial de operaciones no debe modificarse
  "a posteriori"; esto es un requisito del dominio (auditoria).
* **Beneficios.** ``slots=True`` ahorra memoria y evita la creacion
  dinamica de atributos; ``frozen=True`` descarta ``__init__``
  ejecutivos con setters publicos.
* **Validacion.** Se anade ``__post_init__`` para validar los
  invariantes (no negativos, sin ``NaN``).

## D4. ``BarraDiaria`` es una ``NamedTuple``.

* El temario dice: "si es un dato compuesto de campos fijos que
  queda determinado al construir el objeto, es una tupla".
  Una OHLCV encaja perfectamente; ademas, eso facilita que las
  barras sean hashable (pueden ser claves) y los historiales se
  expongan como ``tuple[BarraDiaria, ...]`` (inmutable).

## D5. ``Cartera`` usa ``list`` para transacciones y ``dict`` para posiciones.

* ``dict`` para ``_posiciones``: busqueda O(1) por ticker, buena
  eleccion para una coleccion acotada que crece y decrece. La clave
  es un ticker, cadena inmutable y hashable.
* ``list`` para ``_transacciones``: el registro crece monotona-
  mente y se accede en orden. Insertar en cualquier sitio, sin
  clave natural, habla de una lista.

## D6. ``MercadoSimulado`` almacena el historial como ``tuple``.

* Es el "escaparate" hacia el cliente. Internamente almacenamos en
  listas (porque mutamos), pero todas las operaciones que el
  cliente usa (``historial_de(ticker)``) devuelven ``tuple``. Asi
  probamos que pasar por la frontera inmutable es mas barato y
  fuerza al cliente a producir historia nueva en lugar de mutar.

## D7. ``Simulador`` usa ``Protocol`` para la estrategia.

* **Por que no usar un ``ABC`` con herencia.** El Tema 2 introduce
  herencia, polimorfismo y genericidad; **lo reservamos para PRAC2**.
  En PRAC1 queremos mostrar que dos clases **dispares** que
  implementan el mismo metodo pueden cooperar (duck typing).
* ``Protocol`` documenta la "forma" esperada por ``Simulador`` sin
  obligar a una clase base; el ``isinstance`` duck-test se valida
  en tiempo de uso.

## D8. ``defecto mutable default`` se **demuestra**, no se oculta.

* En ``memoria.py`` se mantiene la funcion defectuosa
  ``registrar_evento_defectuoso`` con ``# noqa: B006`` para que el
  linter anote explicitamente el bug. La funcion "correcta"
  ``registrar_evento_correcto`` esta justo al lado. La entrega con
  proposito pedagogico gana a la limpieza de un warning.

## D9. Inyeccion de semilla en ``MercadoSimulado``.

* Toda la simulacion es reproducible si se pasa una semilla al RNG
  (``random.Random(semilla)``). Eso permite tests deterministas y
  comparar configuraciones distintas bajo el mismo regimen.

## D10. ``enumerate`` y ``tuple`` como retornos en APIs publicas.

* Cada vez que un metodo devuelve una coleccion que el cliente no
  debe mutar, el tipo es ``tuple[X, ...]``. Es una promesa barata
  que elimina varias categorias de bugs en el lado del cliente.
