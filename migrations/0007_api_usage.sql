-- Uso de modelos por día y modelo, con costo estimado (para el presupuesto de la API de Anthropic en Métricas)
CREATE TABLE IF NOT EXISTS api_usage (
  day           TEXT NOT NULL,           -- YYYY-MM-DD en hora de Chile
  provider      TEXT NOT NULL,           -- 'anthropic' | 'workers-ai'
  model         TEXT NOT NULL,
  calls         INTEGER NOT NULL DEFAULT 0,
  input_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd      REAL NOT NULL DEFAULT 0, -- estimado con los precios de MODEL_PRICES (src/index.js)
  PRIMARY KEY (day, model)
);
