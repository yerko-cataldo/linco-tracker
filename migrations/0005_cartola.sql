-- Conciliación con la cartola BICE y bandeja de revisión.
ALTER TABLE movimientos ADD COLUMN banco_id TEXT;          -- fila de la cartola: bice:<fecha|detalle|monto|cuotas>#<n>
ALTER TABLE movimientos ADD COLUMN detalle_banco TEXT;     -- detalle tal como aparece en la cartola
ALTER TABLE movimientos ADD COLUMN cat_banco TEXT;         -- categoría que asigna el banco
ALTER TABLE movimientos ADD COLUMN cuota INTEGER;          -- número de cuota (0 = compra en cuotas aún no cobrada)
ALTER TABLE movimientos ADD COLUMN cuotas INTEGER;         -- total de cuotas
ALTER TABLE movimientos ADD COLUMN pendiente INTEGER NOT NULL DEFAULT 0;  -- 1 = sujeto a confirmación del comercio
ALTER TABLE movimientos ADD COLUMN revisado INTEGER NOT NULL DEFAULT 0;   -- 1 = revisado en la bandeja

CREATE UNIQUE INDEX IF NOT EXISTS idx_movimientos_banco ON movimientos (banco_id);
