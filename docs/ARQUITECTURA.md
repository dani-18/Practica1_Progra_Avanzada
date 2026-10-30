# Arquitectura del simulador (v1.0.0)

Documento de diseño de la entrega PRAC3 + PRAC4. Complementa al `README.md`
(uso rápido) y a la API generada con `pdoc` (`docs/api/`).

## 1. Capas

```
+---------------------------------------------------------------+
|  Interfaz: CLI (cli.py) | GUI Tkinter (gui.py) | __main__.py  |
+---------------------------------------------------------------+
|  Aplicacion: simulacion.py | concurrencia.py | metricas.py    |
+---------------------------------------------------------------+
|  Dominio: instrumento.py / accion.py / bono.py / etf.py       |
|           cartera.py | operacion.py | mercado.py              |
|           estrategias.py | fabrica.py | excepciones.py        |
+---------------------------------------------------------------+
|  Infraestructura: persistencia/ (SQLite, JSON, memoria)       |
+---------------------------------------------------------------+
```

El dominio no importa SQLite, Tkinter ni argparse. La persistencia se
inyecta mediante un repositorio (interfaz `Repositorio`) y una fachada de
servicio (`ServicioPersistencia`). Eso permite probar el dominio con un
repositorio en memoria y cambiar de backend sin tocar las clases de negocio.

## 2. Modelo de dominio

```
             InstrumentoBase (id, nombre, simbolo, volatilidad, precio_base)
              ^             ^              ^
              |             |              |
           Accion         Bono           ETF
        sector,div     cupon,nominal,  indice,comision
                       vencimiento

  Mercado 1 --- * InstrumentoBase
  Cartera 1 --- * Operacion (append-only, frozen dataclass)
  Cartera 1 --- * posicion abierta {instrumento_id: cantidad}
```

* **`InstrumentoBase`** valida los campos comunes con `@property`/setter y
  define el contrato polimorfico `tipo`, `flujo_anual()` y `mostrar()`.
* **`Accion`**, **`Bono`** y **`ETF`** usan `super().__init__()`, anaden sus
  campos y sobrescriben solo lo que aplica (`ETF` hereda `flujo_anual()`).
* **`Operacion`** es un *value object* inmutable (`frozen=True, slots=True`);
  el libro de operaciones nunca se modifica.
* **`Cartera`** valida efectivo/comision, mantiene posiciones e historial y
  puede recibir un repositorio inyectado para persistir cada operacion.
* **`Mercado`** evoluciona precios, guarda una serie historica por instrumento
  y snapshots de cada sesion; acepta una deriva y shocks extremos.

### Igualdad por `id`

Dos instrumentos con el mismo `id` son iguales (`__eq__`), aunque uno sea
`Accion` y otro `Bono`. Es una decision deliberada: el `id` es la clave
logica del instrumento dentro de un mercado y de una cartera, y permite
agregar posiciones y reconstruir objetos desde SQLite/JSON sin duplicados.
El tipo concreto se conserva en el objeto y en la columna `tipo`; si en el
futuro se quisiera permitir el mismo `id` en mercados distintos, habria que
ampliar la clave a `(mercado_id, instrumento_id)`. Esta limitacion esta
documentada y cubierta por tests.

## 3. Simulacion financiera

Cada sesion aplica un movimiento browniano geometrico discreto:

```
precio[t+1] = precio[t] * (1 + deriva + 0.02 * volatilidad * Z)
Z ~ N(0, 1)
```

* `deriva` modela mercados alcistas/bajistas (`--drift 0.001`).
* `aplicar_shock(-0.15)` simula un crash puntual sin avanzar la sesion.
* La semilla de `random.Random` hace las ejecuciones reproducibles.
* `historial_precios(id)` y `mercado.sesiones` alimentan metricas y
  exportadores.

Metricas implementadas en `metricas.py` (funciones puras):

| Metrica | Formula / convencion |
|---|---|
| Rentabilidad total | `precio_final / precio_inicial - 1` |
| Rentabilidad anualizada | CAGR con `252` sesiones/ano |
| Volatilidad anualizada | desviacion tipica de retornos * `sqrt(252)` |
| Max drawdown | mayor caida desde un maximo previo (magnitud positiva) |
| Sharpe | exceso medio / desviacion tipica * `sqrt(252)` |
| Sortino | exceso medio / desviacion de retornos negativos |

## 4. Patrones de diseno

| Patron | Donde | Para que |
|---|---|---|
| **Strategy** | `estrategias.py` | `ComprarMantener`, `Momentum` y `Rebalanceo` comparten `decidir(contexto)`. |
| **Strategy** | `persistencia/exportadores.py` | `ExportadorJSON` y `ExportadorCSV` comparten `exportar(datos, ruta)`. |
| **Factory** | `fabrica.py` | `FabricaInstrumentos` reconstruye `Accion/Bono/ETF` desde diccionarios. |
| **Factory** | `persistencia/fabrica.py` | `RepositorioFactory` elige SQLite, memoria o JSON. |
| **Factory** | `estrategias.crear_estrategia` | Resuelve la estrategia por nombre y parametros. |
| **Repository** | `persistencia/repositorios.py` | Aisla el dominio del almacen y permite backends intercambiables. |
| **Dependency injection** | `Cartera(..., repositorio=repo)` | Persistencia opcional sin acoplar el dominio. |
| **Template Method** | `InstrumentoBase.mostrar/flujo_anual` | Las subclases reutilizan el formato y amplian el comportamiento. |
| **Value Object** | `Operacion` | Inmutabilidad y comparacion por contenido. |

### Strategy sin efectos secundarios

Una estrategia **decide**, no ejecuta. `decidir(contexto)` devuelve una lista
de `Decision`; `Simulador` las aplica contra la cartera y el mercado. Esta
separacion permite testear estrategias sin mercado real, combinar decisiones
y ejecutar escenarios en paralelo sin estado compartido.

```python
from bolsa_sim import ComprarMantener, ContextoMercado, Decision

class MiEstrategia(ComprarMantener):
    nombre = "mi_estrategia"
    def decidir(self, contexto: ContextoMercado) -> list[Decision]:
        ...  # reglas propias
```

## 5. Persistencia

`persistencia/db.py` abre SQLite (`PRAGMA foreign_keys=ON`, WAL en fichero),
aplica `esquema.sql` y versiona el esquema en `meta`.

Tablas principales:

* `instrumento` (comun + `detalle` JSON para campos de subclase).
* `cartera`, `posicion`.
* `operacion` (libro append-only; nunca UPDATE/DELETE desde la aplicacion).
* `sesion`, `precio_sesion` (snapshots de mercado).

Backends:

| Backend | Uso | Caracteristica |
|---|---|---|
| `RepositorioSQLite` | produccion / CLI / GUI | almacen principal, transacciones |
| `RepositorioMemoria` | tests y simulaciones | rapido, `RLock` para concurrencia |
| `RepositorioJSON` | intercambio de estados | fichero legible y portable |

`ServicioPersistencia.guardar_estado()` es idempotente: guarda instrumentos,
cartera, posiciones, historial y sesiones. `sincronizar_operaciones()` solo
anade el sufijo nuevo y falla si el historial en memoria no es una extension
del libro persistido, protegiendo la semantica append-only.

Exportacion:

* `exportar_resultados(mercado, cartera, ruta, "json"|"csv")`.
* JSON: estructura anidada completa (cartera, posiciones, historial,
  sesiones, metricas).
* CSV: formato largo con `registro` = `metrica`, `resumen`, `posicion`,
  `operacion` o `precio_sesion`.
* `exportar_simulacion(resultado, ruta)` para resultados de simulacion.

## 6. Concurrencia

`concurrencia.py` ejecuta escenarios independientes con
`ThreadPoolExecutor`. Cada escenario construye su propio `Mercado`, `Cartera`
y estrategia; no hay estado mutable compartido. La semilla garantiza
resultados reproducibles y `ejecutar_escenarios` conserva el orden de entrada.

```python
from bolsa_sim import Escenario, ejecutar_escenarios

resultados = ejecutar_escenarios([
    Escenario("base", "comprar_mantener", semilla=42, sesiones=60),
    Escenario("tendencia", "momentum", semilla=42, sesiones=60),
], max_workers=2)
```

## 7. GUI

`gui.py` usa Tkinter (stdlib) y se importa sin entorno grafico: las clases de
Tk se cargan de forma perezosa. Muestra tabla de mercado, posiciones, panel
de metricas y grafico de la curva de valor. Los botones permiten avanzar
sesion, aplicar shock, comprar/vender, comparar estrategias, guardar, cargar
y exportar. Los helpers `formatear_instrumentos`, `formatear_posiciones`,
`resumen_cartera` y `puntos_curva` son funciones puras testeadas sin display.

## 8. Excepciones de dominio

`excepciones.py` define `ErrorBolsa` y subclases que tambien heredan de la
excepcion builtin adecuada (`ValueError`, `KeyError`, `RuntimeError`). Asi
la CLI/GUI capturan `ErrorBolsa` y el codigo antiguo sigue funcionando.

* `InstrumentoDesconocido`, `InstrumentoDuplicado`.
* `OperacionInvalida`, `FondosInsuficientes`, `PosicionInsuficiente`.
* `EstrategiaDesconocida`, `TipoInstrumentoDesconocido`.
* `ErrorPersistencia`, `ErrorSimulacion`, `FormatoNoSoportado`.

## 9. Calidad

* 221 tests, cobertura ~94 % (`--cov-fail-under=70` en CI).
* Black + Ruff + pre-commit.
* CI multi-version (3.10-3.13) y job de documentacion con `pdoc`.
* Tests con SQLite `:memory:` y ficheros temporales; la GUI se salta en CI
  sin display (`pytest.importorskip` + `gui_disponible`).

## 10. Hoja de ruta

PRAC3 y PRAC4 quedan cubiertas (patrones, excepciones, SQLite, JSON/CSV,
GUI, concurrencia, cobertura y tag `v1.0.0`). Lineas futuras:

* Mas estrategias (valor, pares, cartera eficiente de Markowitz).
* Datos reales de mercado (importacion CSV/Yahoo Finance).
* Benchmark de cartera y alpha/beta.
* Persistencia de series historicas completas en SQLite (hoy se guardan los
  snapshots de sesion).
* Empaquetado con `pipx` y ejecutable de escritorio.
