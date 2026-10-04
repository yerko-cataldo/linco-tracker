-- Un documento JSON por día y uno por colección de la biblioteca (metas, perfil, técnicas, canciones, libros, coach).
CREATE TABLE IF NOT EXISTS days (
  date       TEXT PRIMARY KEY,           -- YYYY-MM-DD
  data       TEXT NOT NULL,              -- JSON del día
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lib (
  key        TEXT PRIMARY KEY,           -- goals | profile | techniques | songs | books | coach
  data       TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Contador diario de llamadas al modelo, para el tope de gasto y para que veas tu consumo.
CREATE TABLE IF NOT EXISTS ai_usage (
  day           TEXT PRIMARY KEY,        -- YYYY-MM-DD en hora de Chile
  calls         INTEGER NOT NULL DEFAULT 0,
  input_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0
);
