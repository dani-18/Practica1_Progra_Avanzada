# PRÁCTICA 1 — Propuesta del proyecto

**Asignatura:** Técnicas de Programación Avanzada (TPA) — Grupo A
**Curso:** 2026–2027
**Temática:** *12. Simulador de Bolsa y Carteras de Inversión*
**Alumno:** dani-18

---

## 1. Problema

Implementar un esqueleto de simulador de bolsa con activos ficticios,
sobre el que se daran los siguientes pasos (PRAC2-PRAC4):

- Tipos concretos de activos derivados de una clase padre.
- Estrategias de inversion polimorficas.
- Evolucion temporal del mercado (precios, volumen).
- Gestion de cartera (compra / venta / historico).
- Metricas de rentabilidad y riesgo.

## 2. Alcance de la PRAC1

La PRAC1 cubre el **Tema 1 (objetos, memoria y encapsulamiento)** y se
entrega como un modelo minimo de **4 clases**. La propuesta es
suficientemente pequena para mostrarse en una sola sesion y, al
mismo tiempo, lo bastante completa para que las clases bases sirvan
de andamiaje en las siguientes entregas.

Las 4 clases y sus relaciones son:

```
            InstrumentoBase       (clase PADRE preparada para PRAC2)
                  ^
                  | (asociacion, por id)
                  |
              Mercado ----compone----- Cartera
                |                          |
                | registra Operacion       |
                v                          v
            instrumentos             _historial (list[Operacion])
```

Cada clase:

- tiene entre 3 y 5 atributos propios;
- expone un metodo ``mostrar()`` (imprime por pantalla su estado) y un
  ``__repr__`` claro;
- las tres clases no triviales implementan ``@property`` con
  ``@setter`` validado para uno o dos atributos.

## 3. Las 4 clases (resumen)

### InstrumentoBase (clase padre)

- Atributos: ``id``, ``nombre``, ``simbolo``, ``volatilidad``,
  ``precio_base`` (5).
- Properties: ``volatilidad`` y ``precio_base`` (con validacion).
- Helpers: ``aplicar_factor(factor)``, ``mostrar()``.
- Preparada para ser la base de ``Accion``, ``Bono`` y ``ETF`` en
  PRAC2.

### Cartera

- Atributos: ``propietario``, ``efectivo``, ``_inversiones``,
  ``comision``, ``_historial`` (5).
- Properties: ``efectivo`` y ``comision``.
- API: ``invertir()``, ``desinvertir()``, ``valor_total(mercado)``.

### Operacion

- Atributos: ``fecha``, ``instrumento_id``, ``cantidad``,
  ``precio_ejecucion``, ``tipo`` (5).
- Es un ``@dataclass(frozen=True, slots=True)``: inmutable.
- No tiene properties; el invariante se valida en ``__post_init__``.

### Mercado

- Atributos: ``nombre``, ``_rng_seed``, ``instrumentos``, ``sesion``,
  ``volumen_total`` (5).
- Properties: ``sesion`` y ``volumen_total``.
- API: ``avanzar_sesion(volumen)``, ``liquidar(cartera)``,
  ``precio_de(id)``.

## 4. Plan de las siguientes practicas

| Hito | Tema | Foco |
|------|------|------|
| PRAC2 | 2    | Herencia en activos, excepciones de dominio, ``Strategy`` como ABC. |
| PRAC3 | 3    | Patrones Factory y Observer; contenedores parametricos. |
| PRAC4 | 4    | GUI, eventos, concurrencia, cobertura >= 70 %, tag ``v1.0.0``. |

## 5. Riesgos

- El modelo minimo renuncia a caracteristicas (volatilidad por sesion,
  polimorfismo, eventos, GUI). El plan anterior muestra como se
  recuperan en PRAC2..4.
- ``InstrumentoBase`` se declara con ``__hash__ = None``: la identidad
  por ``id`` se mantiene en ``__eq__`` pero las instancias no son
  hasheables; PRAC2 podria reemplazar ``id`` por ``__hash__`` cuando la
  relacion entre instancias quede fijada por un ticker unico.

## 6. Como se ejecuta

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q --cov=bolsa_sim
python -m bolsa_sim --demo
```

---

*PRAC1 — Tecnicas de Programacion Avanzada — Grupo A — curso 2026-2027.*
