# Casos de uso financieros

Este documento enseña el simulador **funcionando**, no solo su estructura.
Todos los resultados son reproducibles con la semilla indicada (Python 3.10+,
sin dependencias de runtime).

## Caso 1 — Cartera de comprar y mantener (120 sesiones)

Objetivo: invertir 10 000 EUR en la jerarquía Acción/Bono/ETF y medir el
resultado tras 120 sesiones.

```python
from bolsa_sim import ComprarMantener, Simulador
from bolsa_sim.demo import cartera_demo, mercado_demo

mercado = mercado_demo(semilla=42)
cartera = cartera_demo(efectivo=10_000.0)
resultado = Simulador(
    mercado,
    cartera,
    ComprarMantener(fraccion=0.95),
    sesiones=120,
).ejecutar()

print(resultado)
print(resultado.metricas)
print("posiciones:", cartera.posiciones)
print("efectivo:", round(cartera.efectivo, 2))
```

Salida real:

```text
[comprar_mantener] 120 sesiones  valor 10000.00 -> 10230.90 EUR  (+2.31%)  ops=3
rentabilidad=+2.31%  anualizada=+4.91%  volatilidad=2.48%  max_drawdown=1.14%  sharpe=1.95  sortino=3.16
posiciones: (('ACME', 26), ('BONO10', 31), ('SP500', 7))
efectivo: 980.27
```

Lectura financiera:

* la estrategia reparte el 95 % del capital entre los tres instrumentos y
  reserva liquidez para comisiones;
* la cartera termina con **+2,31 %** y un drawdown máximo de solo **1,14 %**;
* el Sharpe de **1,95** indica que el retorno compensa la volatilidad asumida
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

## Caso 3 — Comparar estrategias en paralelo

Objetivo: ejecutar tres estrategias sobre el mismo mercado y comparar
resultados sin estado compartido.

```python
from bolsa_sim import comparar_estrategias

for item in comparar_estrategias(semilla=42, sesiones=120):
    print(item.escenario.estrategia, item.resultado)
```

Salida real:

```text
comprar_mantener   [comprar_mantener] 120 sesiones  valor 1000.00 -> 1007.76 EUR  (+0.78%)  ops=2
momentum           [momentum] 120 sesiones  valor 1000.00 -> 939.05 EUR  (-6.09%)  ops=64
rebalanceo         [rebalanceo] 120 sesiones  valor 1000.00 -> 1007.76 EUR  (+0.78%)  ops=2
```

Lectura financiera:

* `momentum` genera **64 operaciones** y pierde un 6,09 %: en un mercado sin
  tendencia clara, el ruido y las comisiones penalizan la estrategia;
* `comprar_mantener` y `rebalanceo` apenas operan y conservan el capital;
* la semilla hace que la comparación sea reproducible.

## Caso 4 — Guardar, recuperar y exportar

Objetivo: cerrar el ciclo de persistencia real (SQLite) y exportación.

```python
from bolsa_sim import Momentum, Simulador
from bolsa_sim.demo import cartera_demo, mercado_demo
from bolsa_sim.persistencia import (
    RepositorioFactory,
    ServicioPersistencia,
    exportar_simulacion,
)

mercado = mercado_demo(semilla=7)
cartera = cartera_demo(efectivo=5_000.0)
resultado = Simulador(mercado, cartera, Momentum(ventana=5), sesiones=30).ejecutar()

repo = RepositorioFactory.crear("sqlite", "datos.sqlite")
servicio = ServicioPersistencia(repo)
servicio.guardar_estado(mercado, cartera)

mercado2, cartera2 = servicio.cargar_estado(mercado.nombre, cartera.propietario)
print(len(cartera.historial), "->", len(cartera2.historial))
print(mercado.sesion, "->", mercado2.sesion)

exportar_simulacion(resultado, "simulacion.json")
servicio.cerrar()
```

Salida real (resumida):

```text
49 -> 49
30 -> 30
```

Las 49 operaciones, las 30 sesiones, el efectivo y las posiciones se
reconstruyen desde SQLite. El libro de operaciones es *append-only*: guardar
dos veces el mismo estado no duplica operaciones.

## Caso 5 — Varias carteras y cambio de usuario

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

## Caso 6 — Polimorfismo en el dominio

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
