# Guía de desarrollo

Documento para quien mantiene o corrige el proyecto. El uso del simulador
está en el [`README.md`](../README.md); los escenarios financieros, en
[`CASOS_DE_USO.md`](CASOS_DE_USO.md); el diseño, en
[`ARQUITECTURA.md`](ARQUITECTURA.md).

## 1. Entorno

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate         # Linux/macOS
python -m pip install -e ".[dev,docs]"
```

El paquete runtime es **solo biblioteca estándar**. `dev` añade pytest,
coverage, Black, Ruff y pre-commit; `docs` añade pdoc.

## 2. Comandos habituales

```bash
python -m pytest -q                         # suite completa
python -m pytest --cov=bolsa_sim            # cobertura
python -m pytest --cov=bolsa_sim --cov-fail-under=70
python -m black --check src tests
python -m black src tests
python -m ruff check src tests
python -m pdoc bolsa_sim -o docs/api --docformat google
pre-commit run --all-files
```

La cobertura objetivo de PRAC3 es **≥ 55 %**; el proyecto mantiene ~94 % y CI
falla por debajo del **70 %**. La cobertura no sustituye a los casos de
negocio: al añadir una funcionalidad, incluye un escenario límite y uno de
error.

## 3. Logging

La biblioteca **no** instala handlers al importarse: solo crea loggers con
`obtener_logger(__name__)` y registra eventos. La aplicación decide el nivel y
los destinos con `configurar_logging`.

```python
from bolsa_sim.logging_config import configurar_logging, obtener_logger

configurar_logging("INFO", archivo="bolsa.log")
log = obtener_logger(__name__)
log.info("operacion ejecutada: %s", operacion)
```

Desde el entry point:

```bash
python -m bolsa_sim --verbose                 # DEBUG en consola
python -m bolsa_sim --log-file bolsa.log      # INFO en consola + fichero
python -m bolsa_sim --quiet                   # solo errores
BOLSA_LOG_LEVEL=DEBUG python -m bolsa_sim     # nivel por entorno
```

Qué se registra:

| Nivel | Evento |
|---|---|
| `INFO` | simulación iniciada/completada, estado guardado/cargado, shock aplicado |
| `DEBUG` | sesiones del mercado, argumentos y comandos de la CLI |
| `WARNING` | entradas o comandos no válidos de la CLI |
| `ERROR` | errores de dominio/persistencia antes de propagar la excepción |

`configurar_logging` es idempotente: sustituye solo sus propios handlers, no
los que haya configurado la aplicación anfitriona. El logger raíz es
`bolsa_sim` y no propaga al logger raíz de Python por defecto.

## 4. Estructura y convenciones

* `src/` layout; el dominio no importa SQLite, Tkinter ni argparse.
* Tipos con `from __future__ import annotations`; `py.typed` incluido.
* Excepciones de dominio en `excepciones.py`, compatibles con
  `ValueError`/`KeyError`/`RuntimeError`.
* Estrategias puras: `decidir(contexto)` devuelve `Decision`; `Simulador`
  ejecuta. No compartir estado mutable entre escenarios concurrentes.
* Persistencia detrás de `Repositorio`; los tests usan `memoria` o SQLite
  `:memory:`.

## 5. CI y documentación

`.github/workflows/ci.yml` ejecuta en cada push/PR:

1. Black y Ruff.
2. pytest con cobertura y `--cov-fail-under=70` en Python 3.10–3.13.
3. pdoc para generar `docs/api`.
4. En `main`, despliegue de la API en GitHub Pages.

La documentación publicada queda en
`https://dani-18.github.io/Practica1_Progra_Avanzada/`.
Para que el despliegue funcione, el repositorio debe tener Pages configurado
con origen **GitHub Actions** (el workflow intenta habilitarlo con
`enablement: true`).

## 6. Checklist antes de entregar

- [ ] `pytest` verde y cobertura ≥ 70 %.
- [ ] `black --check` y `ruff check` sin errores.
- [ ] Escenario nuevo documentado en `CASOS_DE_USO.md` si cambia el
      comportamiento visible.
- [ ] `README.md`, `CHANGELOG.md` y `ARQUITECTURA.md` sincronizados
      (tests, cobertura, versión, flags).
- [ ] `docs/api` regenerable con el comando de pdoc.
