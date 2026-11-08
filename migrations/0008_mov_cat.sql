-- Categoría de un movimiento puntual (gana sobre la del comercio) y la que sugiere el agente de compras al llegar
ALTER TABLE movimientos ADD COLUMN cat TEXT;          -- confirmada para esta compra ("esta vez el almacén fue comida")
ALTER TABLE movimientos ADD COLUMN cat_sug TEXT;      -- sugerida por el agente, por confirmar
ALTER TABLE movimientos ADD COLUMN cat_sug_why TEXT;  -- por qué la sugirió y alternativas, en una frase
