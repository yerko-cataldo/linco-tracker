-- Correos entrantes de Email Routing guardados sin procesar (alertas de compra de Visa).
CREATE TABLE IF NOT EXISTS inbox_raw (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  received_at   TEXT NOT NULL DEFAULT (datetime('now')),
  envelope_from TEXT NOT NULL,
  envelope_to   TEXT NOT NULL,
  subject       TEXT,
  auth_results  TEXT,                    -- cabecera Authentication-Results (SPF, DKIM, DMARC)
  raw_size      INTEGER NOT NULL,
  raw           TEXT                     -- mensaje completo; NULL si supera el máximo
);
