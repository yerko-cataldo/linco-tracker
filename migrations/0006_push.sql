-- Notificaciones push (suscripciones de cada dispositivo y avisos ya enviados) y cuenta de destino de las transferencias.
CREATE TABLE IF NOT EXISTS push_subs (
  endpoint TEXT PRIMARY KEY,                     -- URL del servicio de push del navegador
  p256dh TEXT NOT NULL,                          -- clave pública del dispositivo (base64url)
  auth TEXT NOT NULL,                            -- secreto de autenticación (base64url)
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS push_log (
  key TEXT PRIMARY KEY,                          -- tr:<id de la transferencia>:<fecha>: un aviso por día
  at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Del comprobante "Hicimos la transferencia": reconoce al destinatario por RUT y muestra su cuenta en los avisos
ALTER TABLE movimientos ADD COLUMN rut_destino TEXT;
ALTER TABLE movimientos ADD COLUMN banco_destino TEXT;
