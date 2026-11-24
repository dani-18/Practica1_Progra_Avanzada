# Casos de uso financieros

Este documento enseña el simulador **funcionando**, no solo su estructura.
Todos los resultados son reproducibles con la semilla indicada (Python 3.10+,
sin dependencias de runtime).

## Caso 1 — Cartera de comprar y mantener (120 sesiones)

Objetivo: invertir 10 000 EUR en la jerarquía Acción/Bono/ETF y medir el
resultado tras 120 sesiones.

```python
from bolsa_sim import Cartera, metricas_cartera
from bolsa_sim.demo import mercado_demo

mercado = mercado_demo(semilla=42)
cartera = Cartera("Dani", efectivo=10_000.0, comision=1.0)
for instrumento_id, cantidad in (("ACME", 26), ("BONO10", 31), ("SP500", 7)):
    cartera.comprar(mercado, instrumento_id, cantidad)

cartera.anotar_valor(mercado=mercado)
for _ in range(120):
    mercado.avanzar_sesion(100)
    cartera.anotar_valor(mercado=mercado)

print(metricas_cartera(cartera, mercado))
print("posiciones:", cartera.posiciones)
print("efectivo:", round(cartera.efectivo, 2))
```

Salida real:

```text
rentabilidad=+2.28%  anualizada=+4.80%  volatilidad=2.47%  max_drawdown=1.14%  sharpe=1.91  sortino=3.10
posiciones: (('ACME', 26), ('BONO10', 31), ('SP500', 7))
efectivo: 977.0
```

Lectura financiera:

* la cartera reparte el capital entre los tres instrumentos y reserva
  liquidez para comisiones;
* la cartera termina con **+2,28 %** y un drawdown máximo de solo **1,14 %**;
* el Sharpe de **1,91** indica que el retorno compensa la volatilidad asumida
  en este escenario.

## Caso 2 — Crash del 15 % y recuperación

Objetivo: comprobar cómo responde una cartera concentrada en una acción a un
shock extremo a mitad de la simulación.

```python
from bolsa_sim import Cartera, Mercado, metricas_cartera
from bolsa_sim.demo import instrumentos_demo

mercado = Mercado(
    "Bolsa Continuo",
    {i.id: i for i in instrumentos_demo()},
    semilla=7,
    deriva=0.0005,
)
cartera = Cartera("Dani", efectivo=5_000.0, comision=1.0)
cartera.invertir(mercado, "ACME", 20, mercado.precio_de("ACME"), "s0000")
cartera.anotar_valor(mercado=mercado)

for _ in range(60):
    mercado.avanzar_sesion(100)
    cartera.anotar_valor(mercado=mercado)

antes = cartera.valor_total(mercado)
mercado.aplicar_shock(-0.15)          # crash puntual

for _ in range(60):
    mercado.avanzar_sesion(100)
    cartera.anotar_valor(mercado=mercado)

print("valor antes del crash:", round(antes, 2))
print("valor final:", round(cartera.valor_total(mercado), 2))
print(metricas_cartera(cartera, mercado))
```

Salida real:

```text
valor antes del crash: 5053.09
valor final: 4793.17
rentabilidad=-4.14%  anualizada=-8.42%  volatilidad=10.77%  max_drawdown=7.69%  sharpe=-0.76  sortino=-0.78
```

Lectura financiera:

* el shock del 15 % se aplica inmediatamente a todos los precios y queda
  reflejado en la serie histórica;
* el **max drawdown (7,69 %)** es mayor que la caída final porque mide la
  peor caída desde un máximo previo;
* la volatilidad anualizada sube al **10,77 %** y el Sharpe se vuelve
  negativo: el riesgo asumido no compensó en este escenario.

## Caso 3 — Guardar, recuperar y exportar

Objetivo: cerrar el ciclo de persistencia real (SQLite) y exportación.

```python
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.persistencia import (
    RepositorioFactory,
    ServicioPersistencia,
    exportar_resultados,
)

mercado = mercado_demo(semilla=7)
cartera = cartera_demo(efectivo=5_000.0)
for _ in range(30):
    mercado.avanzar_sesion(100)
    cartera.anotar_valor(mercado=mercado)
cartera.comprar(mercado, "ACME", 2)
cartera.anotar_valor(mercado=mercado)

repo = RepositorioFactory.crear("sqlite", "datos.sqlite")
servicio = ServicioPersistencia(repo)
servicio.guardar_estado(mercado, cartera)

mercado2, cartera2 = servicio.cargar_estado(mercado.nombre, cartera.propietario)
print(len(cartera.historial), "->", len(cartera2.historial))
print(mercado.sesion, "->", mercado2.sesion)

exportar_resultados(mercado, cartera, "resultados.json", "json")
servicio.cerrar()
```

Salida real (resumida):

```text
1 -> 1
30 -> 30
```

La operación, las 30 sesiones, el efectivo y las posiciones se reconstruyen
desde SQLite. El libro de operaciones es *append-only*: guardar dos veces el
mismo estado no duplica operaciones.

## Caso 4 — Varias carteras y cambio de usuario

Objetivo: operar con dos usuarios sin mezclar posiciones.

```python
from bolsa_sim import GestorCarteras
from bolsa_sim.demo import cartera_demo, mercado_demo

mercado = mercado_demo(semilla=42)
gestor = GestorCarteras(cartera_demo())          # Dani, 1000 EUR
ana = gestor.crear("Ana", efectivo=2_000.0, comision=2.0)

gestor.actual.invertir(mercado, "ACME", 1, mercado.precio_de("ACME"), "s0000")
print("activa:", gestor.activa)
print("Ana:", ana.efectivo, ana.posiciones)

gestor.seleccionar("Dani")
print("activa:", gestor.activa, "posiciones:", gestor.actual.posiciones)

gestor.seleccionar("ana")                        # sin distinguir mayusculas
print("activa:", gestor.activa, "posiciones:", gestor.actual.posiciones)
```

Salida real:

```text
activa: Ana
Ana: 1878.0 (('ACME', 1),)
activa: Dani posiciones: ()
activa: Ana posiciones: (('ACME', 1),)
```

En la CLI equivaldria a `new Ana 2000 2`, `use Dani` y `portfolios`. Al
guardar con `save`, SQLite conserva **las dos carteras** y `load` recupera
ambas, seleccionando la que se indique.

## Caso 5 — Polimorfismo en el dominio

El mismo método se comporta distinto según el tipo concreto:

```python
from bolsa_sim import Accion, Bono, ETF

instrumentos = [
    Accion("ACME", "Acme Corp", "ACME", 0.20, 120.0, dividendo_anual=1.80),
    Bono("BONO10", "Bono 10 anos", "B10", 0.05, 100.0, cupon_anual=0.04, vencimiento=10),
    ETF("SP500", "ETF S&P 500", "SPX", 0.15, 400.0, indice="S&P 500", comision_gestion=0.002),
]
for instrumento in instrumentos:
    print(instrumento.tipo, instrumento.flujo_anual())
```

```text
accion 1.8
bono 40.0
etf 0.0
```

`ETF` no sobrescribe `flujo_anual()`: hereda el `0.0` de la base. La demo
agrega el flujo de una unidad de cada instrumento (**41,80 EUR**) sin usar
`isinstance`.
