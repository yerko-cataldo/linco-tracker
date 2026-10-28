-- Movimientos de tarjeta de crédito: uno por transacción, creados desde las alertas de compra de Visa.
CREATE TABLE IF NOT EXISTS movimientos (
  id         TEXT PRIMARY KEY,           -- clave de deduplicación: alerta:<Message-Id>
  fecha      TEXT NOT NULL,              -- YYYY-MM-DD en hora de Chile
  hora       TEXT,                       -- HH:MM en hora de Chile
  comercio   TEXT NOT NULL,
  ciudad     TEXT,
  pais       TEXT,
  tarjeta    TEXT NOT NULL,              -- últimos 4 dígitos
  tipo       TEXT NOT NULL,              -- tipo de transacción informado por Visa
  moneda     TEXT NOT NULL,
  monto      REAL NOT NULL,              -- en la moneda de la transacción
  fuente     TEXT NOT NULL,              -- alerta
  inbox_id   INTEGER,                    -- fila de inbox_raw de origen
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos (fecha);
