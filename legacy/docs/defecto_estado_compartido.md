# Defecto del argumento por defecto mutable — explicación

Este documento se corresponde con el ejercicio que pide PRAC1/Tema 1:
**"Identificar, explicar y corregir un defecto conceptual asociado al
estado compartido"**. El defecto se trabaja también en código dentro de
`src/bolsa_sim/memoria.py` y se valida con tests en `tests/test_memoria.py`.

## 1. Identificar

El bug se llama "mutable default argument" y es un error muy común en
Python. Aparece en una función como esta:

```python
def registrar_evento_defectuoso(
    nombre: str, eventos: list[str] = [], operacion: str = "alta"
) -> list[str]:
    eventos.append(f"{operacion}:{nombre}")
    return eventos
```

Llamarla dos veces seguidas produce un comportamiento **incorrecto**:
ambas llamadas reciben la misma lista.

```python
r1 = registrar_evento_defectuoso("alta")
r2 = registrar_evento_defectuoso("alta")
# r1 -> ["alta:alta"]
# r2 -> ["alta:alta", "alta:alta"]
# r1 is r2   -> True   (!)
```

## 2. Explicar (por qué ocurre)

Los valores por defecto de los argumentos de una función se evalúan
**una sola vez**: en el momento de definir la función, no en cada
llamada. Si ese valor es **mutable** (lista, dict, set, etc.), todas
las invocaciones de la función comparten ese mismo objeto. La
secuencia de eventos es:

1. Python evalúa `[]` y crea una lista nueva en el *montículo*.
2. Como parte del objeto `function`, ese lista queda enlazado a
   ``__defaults__``.
3. Cada llamada que **no** reciba el argumento recuperará esa misma
   lista.
4. Si una llamada hace `lista.append(x)`, el siguiente llamante
   "verá" ese `x` desde el principio.

Equivale, en términos de aliasing, a escribir algo como:

```python
_LISTA_COMPARTIDA = []                # estado del módulo

def registrar_evento(nombre, eventos=_LISTA_COMPARTIDA):
    eventos.append(nombre)
    return eventos
```

aunque este último patrón sería más explícito y, por tanto, menos
peligroso. El mensaje del temario es claro: **el argumento por defecto
no es el sitio para inicializar colecciones**.

## 3. Corregir

La corrección idiomática es usar un centinela `None` y crear la lista
dentro del cuerpo:

```python
def registrar_evento_correcto(
    nombre: str, eventos: list[str] | None = None, operacion: str = "alta"
) -> list[str]:
    if eventos is None:
        eventos = []
    eventos.append(f"{operacion}:{nombre}")
    return eventos
```

Verificación:

```python
s1 = registrar_evento_correcto("alta")
s2 = registrar_evento_correcto("alta")
# s1 is s2  -> False
# s1 == ["alta:alta"], s2 == ["alta:alta"]
```

Si el llamante quiere **explícitamente** compartir una lista entre
varias invocaciones, la pasa por sí mismo:

```python
buf = []
registrar_evento_correcto("alta", eventos=buf)
registrar_evento_correcto("baja", eventos=buf)
# ahora buf contiene los dos eventos
```

La elección (compartir o no) deja de ser "implícita y peligrosa" y
pasa a ser "explícita y decisión del llamante".

## 4. Cómo evitarlo en el resto del paquete

* Regla práctica del proyecto: **ningún argumento por defecto mutable**.
  Si lo necesitas, declaralo `None` y construye la colección dentro de
  la función.
* El lint `ruff` incluye la regla `B006` (`Do not use mutable data
  structures for argument defaults`); la tenemos activa (ver
  `pyproject.toml`) y la única excepción se permite en la función
  *didáctica* `registrar_evento_defectuoso`, marcada con
  `# noqa: B006` para que el alumno vea la regla saltar en su sitio.

## 5. Relación con el modelo de objetos

Este defecto ilustra de forma muy directa varios puntos del Tema 1:

* **Nombres como referencias**: el `eventos` de cada función no es una
  "variable local" en el sentido de C; es un nombre ligado a un objeto
  del montículo.
* **Ciclo de vida por conteo de referencias**: el `[]` por defecto se
  libera **nunca** mientras exista el objeto función (encadenado a
  `__defaults__`).
* **Aliasing visible**: `r1 is r2` muestra la identidad compartida.
* **Mutabilidad vs inmutabilidad**: el truco funciona porque `list` es
  mutable; con una tupla `(...)`, la operación "append" ni siquiera
  existe.
