-- Esquema de la base de datos SQLite (fuente unica de verdad).
-- Se aplica con ``bolsa_sim.persistencia.db.inicializar_esquema``.

CREATE TABLE IF NOT EXISTS meta (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

-- Instrumentos: campos comunes + los propios de cada subclase en JSON.
CREATE TABLE IF NOT EXISTS instrumento (
    id          TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    simbolo     TEXT NOT NULL,
    tipo        TEXT NOT NULL,
    volatilidad REAL NOT NULL,
    precio_base REAL NOT NULL,
    detalle     TEXT NOT NULL DEFAULT '{}'
);

-- Carteras (una fila por propietario).
CREATE TABLE IF NOT EXISTS cartera (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    propietario    TEXT NOT NULL UNIQUE,
    efectivo       REAL NOT NULL CHECK (efectivo >= 0),
    comision       REAL NOT NULL CHECK (comision >= 0),
    capital_inicial REAL NOT NULL DEFAULT 0,
    curva_valor    TEXT NOT NULL DEFAULT '[]'
);

-- Posiciones abiertas (estado actual).
CREATE TABLE IF NOT EXISTS posicion (
    cartera_id     INTEGER NOT NULL REFERENCES cartera(id) ON DELETE CASCADE,
    instrumento_id TEXT    NOT NULL,
    cantidad       INTEGER NOT NULL CHECK (cantidad > 0),
    PRIMARY KEY (cartera_id, instrumento_id)
);

-- Libro de operaciones: APPEND-ONLY (la aplicacion nunca hace UPDATE/DELETE).
CREATE TABLE IF NOT EXISTS operacion (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cartera_id       INTEGER NOT NULL REFERENCES cartera(id) ON DELETE CASCADE,
    fecha            TEXT NOT NULL,
    instrumento_id   TEXT NOT NULL,
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_ejecucion REAL NOT NULL CHECK (precio_ejecucion > 0),
    tipo             TEXT NOT NULL CHECK (tipo IN ('compra', 'venta'))
);

-- Sesiones de mercado y snapshot de precios al cierre.
CREATE TABLE IF NOT EXISTS sesion (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    mercado  TEXT NOT NULL,
    numero   INTEGER NOT NULL,
    volumen  INTEGER NOT NULL CHECK (volumen > 0),
    UNIQUE (mercado, numero)
);

CREATE TABLE IF NOT EXISTS precio_sesion (
    sesion_id      INTEGER NOT NULL REFERENCES sesion(id) ON DELETE CASCADE,
    instrumento_id TEXT    NOT NULL,
    precio         REAL    NOT NULL CHECK (precio > 0),
    PRIMARY KEY (sesion_id, instrumento_id)
);

CREATE INDEX IF NOT EXISTS idx_operacion_cartera ON operacion(cartera_id);
CREATE INDEX IF NOT EXISTS idx_sesion_mercado ON sesion(mercado);
CREATE INDEX IF NOT EXISTS idx_precio_sesion ON precio_sesion(sesion_id);
