-- Detalle de cada movimiento: productos comprados, un documento JSON por movimiento.
CREATE TABLE IF NOT EXISTS mov_detalle (
  mov_id     TEXT PRIMARY KEY,           -- movimientos.id
  data       TEXT NOT NULL,              -- {text, items: [...]}
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
