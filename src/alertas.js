// Alertas de compra de Visa: valida el correo, lo decodifica y extrae la transacción.

const CAMPOS = {
  comercio: "Comercio",
  pais: "País",
  ciudad: "Ciudad",
  tarjeta: "Tarjeta",
  tipo: "Tipo de transacción",
  moneda: "Moneda",
  monto: "Monto",
};

const VISA_FROM_RE = /@([a-z0-9-]+\.)*visa\.com$/i;
const DKIM_RE = /dkim=pass\s+header\.i=@visa\.com/i;
const DMARC_RE = /dmarc=pass\s+header\.from=visa\.com/i;

/* Devuelve {ok: true, mov} o {ok: false, reason}. */
export function parseVisaAlert(raw, envelopeFrom) {
  if (!VISA_FROM_RE.test(envelopeFrom || "")) return { ok: false, reason: "remitente" };

  const sep = raw.match(/\r?\n\r?\n/);
  if (!sep) return { ok: false, reason: "sin_cuerpo" };
  const head = raw.slice(0, sep.index);
  const body = raw.slice(sep.index + sep[0].length);

  const auth = headerValue(head, "authentication-results") || headerValue(head, "arc-authentication-results") || "";
  if (!DKIM_RE.test(auth) || !DMARC_RE.test(auth)) return { ok: false, reason: "autenticacion" };

  const text = htmlToText(decodeBody(body, (headerValue(head, "content-transfer-encoding") || "").toLowerCase()));
  const campos = {};
  for (const [key, label] of Object.entries(CAMPOS)) {
    const m = text.match(new RegExp(`^\\s*${label}:[ \\t]*(.*)$`, "m"));
    if (m) campos[key] = m[1].trim();
  }
  if (!campos.comercio || !campos.tarjeta || !campos.tipo) return { ok: false, reason: "no_alerta" };
  if (!/^\d{4}$/.test(campos.tarjeta)) return { ok: false, reason: "tarjeta_invalida" };
  if (!/^\d+(\.\d+)?$/.test(campos.monto || "")) return { ok: false, reason: "monto_invalido" };

  const when = chileDateTime(headerValue(head, "date"));
  const messageId = headerValue(head, "message-id");
  if (!messageId) return { ok: false, reason: "sin_message_id" };

  return {
    ok: true,
    mov: {
      id: `alerta:${messageId}`,
      fecha: when.fecha,
      hora: when.hora,
      comercio: campos.comercio,
      ciudad: campos.ciudad || null,
      pais: campos.pais || null,
      tarjeta: campos.tarjeta,
      tipo: campos.tipo,
      moneda: campos.moneda || "CLP",
      monto: Number(campos.monto),
    },
  };
}

/* Valor de una cabecera (la primera que aparece), con las líneas plegadas unidas. */
function headerValue(head, name) {
  const unfolded = head.replace(/\r?\n[ \t]+/g, " ");
  const m = unfolded.match(new RegExp(`^${name}:[ \\t]*(.*)$`, "im"));
  return m ? m[1].trim() : null;
}

function decodeBody(body, encoding) {
  let bin;
  if (encoding === "base64") bin = atob(body.replace(/\s+/g, ""));
  else if (encoding === "quoted-printable") {
    bin = body
      .replace(/=\r?\n/g, "")
      .replace(/=([0-9A-Fa-f]{2})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
  } else return body;
  return new TextDecoder("utf-8").decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

function htmlToText(html) {
  return html
    .replace(/<head[\s\S]*?<\/head>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<(br|\/p|\/div)\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&");
}

/* Fecha y hora de Chile a partir de la cabecera Date; si no es válida usa la hora actual. */
function chileDateTime(dateHeader) {
  let d = dateHeader ? new Date(dateHeader) : new Date();
  if (Number.isNaN(d.getTime())) d = new Date();
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/Santiago",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(d)
      .map((p) => [p.type, p.value])
  );
  return { fecha: `${parts.year}-${parts.month}-${parts.day}`, hora: `${parts.hour}:${parts.minute}` };
}
