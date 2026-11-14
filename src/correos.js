// Correos de Banco BICE reenviados por el titular: valida el reenvío y lee el comprobante de transferencia o de pago de cuentas.

import { headerValue, htmlToText } from "./alertas.js";
import { longDate, rutKey } from "./cartola.js";

const COMPROBANTE_RE = /Hicimos la transferencia que nos pediste/i;
const MONTO_RE = /Monto \$\s*([\d.]+)/i;
const DESTINO_RE = /Cuenta de destino Nombre (.+?) RUT ([\d.]+-[\dkK]) Banco (.+?) Tipo de cuenta/i;
const OPERACION_RE = /N.mero de operaci.n (\d+)/i;
const FECHA_RE = /(\d{1,2} [a-z]{3,4}\.? \d{4}) - (\d{2}:\d{2}) h/i;
const SALUDO_RE = /Hola,? (.+?) Hicimos la transferencia/i;
// "Comprobante de pago de cuentas": "Realizaste el pago de la/s siguiente/s cuenta/s: Monto total pagado $24.219 … Empresa Nº Cliente
// Vencimiento Monto Enel 33394993 24-11-2026 $24.219 14-11-2026 07:46 hrs Operación Nº EXP0099620261132427621 - 259215520"
const PAGO_RE = /Realizaste el pago de la\/s siguiente\/s cuenta\/s/i;
const PAGO_TOTAL_RE = /Monto total pagado \$\s*([\d.]+)/i;
const PAGO_CUANDO_RE = /(\d{2})-(\d{2})-(\d{4}) (\d{2}:\d{2}) hrs/i;
const PAGO_OP_RE = /Operaci.n N\S*\s*([A-Z0-9]+)/i;
const PAGO_FILA_RE = /(\S.*?)\s+([\w.-]+)\s+(\d{2})-(\d{2})-(\d{4})\s+\$\s*([\d.]+)/g;

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/* Devuelve {ok: true, mov} o {ok: false, reason}.
   forwarders: correos separados por coma que pueden reenviar; ownRut: RUT del titular o null. */
export function parseBankMail(raw, envelopeFrom, forwarders, ownRut) {
  const from = String(envelopeFrom || "").trim().toLowerCase();
  const allowed = String(forwarders || "").toLowerCase().split(",").map((s) => s.trim()).filter(Boolean);
  if (!from || !allowed.includes(from)) return { ok: false, reason: "remitente" };

  const msg = splitMessage(raw);
  if (!msg) return { ok: false, reason: "sin_cuerpo" };

  const domain = escapeRe(from.split("@")[1]);
  const auth = headerValue(msg.head, "authentication-results") || headerValue(msg.head, "arc-authentication-results") || "";
  if (!new RegExp(`dkim=pass\\s+header\\.d=${domain}`, "i").test(auth) || !new RegExp(`dmarc=pass\\s+header\\.from=${domain}`, "i").test(auth)) {
    return { ok: false, reason: "autenticacion" };
  }

  const parts = {};
  collectText(msg.head, msg.body, 0, parts);
  const clean = (t) => String(t || "").replace(/\s+/g, " ").trim();
  const pago = [parts.plain, parts.html].map(clean).find((t) => PAGO_RE.test(t));
  if (pago) return parsePago(pago, msg.head);
  const text = clean(parts.plain || parts.html);
  if (!COMPROBANTE_RE.test(text)) return { ok: false, reason: "no_comprobante" };

  const monto = text.match(MONTO_RE), destino = text.match(DESTINO_RE), cuando = text.match(FECHA_RE);
  if (!monto || !destino || !cuando) return { ok: false, reason: "formato" };
  const fecha = longDate(cuando[1].replace(".", ""));
  if (!fecha) return { ok: false, reason: "formato" };

  const nombre = destino[1].trim(), rut = destino[2];
  if (ownRut ? rutKey(rut) === rutKey(ownRut) : sameName(nombre, (text.match(SALUDO_RE) || [])[1])) return { ok: false, reason: "cuenta_propia" };

  const operacion = text.match(OPERACION_RE), messageId = headerValue(msg.head, "message-id");
  const id = operacion ? `correo:op${operacion[1]}` : messageId ? `correo:${messageId}` : null;
  if (!id) return { ok: false, reason: "sin_id" };

  return {
    ok: true,
    mov: {
      id,
      fecha,
      hora: cuando[2],
      comercio: nombre,
      tipo: "Transferencia",
      monto: Number(monto[1].replace(/\./g, "")),
      rut_destino: rut,
      banco_destino: destino[3].trim(),
    },
  };
}

/* Pago de cuentas: un movimiento "Pago de cuenta" por cada cuenta de la tabla (empresa, número de cliente, vencimiento y monto).
   Si la tabla no cuadra con el monto total, un solo movimiento por el total. Id: correo:pago<operación> (#n si son varias). */
function parsePago(text, head) {
  const total = text.match(PAGO_TOTAL_RE), cuando = text.match(PAGO_CUANDO_RE);
  if (!total || !cuando) return { ok: false, reason: "formato" };
  const op = text.match(PAGO_OP_RE), messageId = headerValue(head, "message-id");
  const base = op ? `correo:pago${op[1]}` : messageId ? `correo:${messageId}` : null;
  if (!base) return { ok: false, reason: "sin_id" };
  const ini = text.search(/Vencimiento\s+Monto/i), fin = text.search(PAGO_CUANDO_RE);
  const tabla = ini >= 0 && fin > ini ? text.slice(ini, fin).replace(/^Vencimiento\s+Monto\s*/i, "") : "";
  const filas = [...tabla.matchAll(PAGO_FILA_RE)].map((m) => ({ empresa: m[1].trim(), cliente: m[2], vence: `${m[5]}-${m[4]}-${m[3]}`, monto: Number(m[6].replace(/\./g, "")) }));
  const tot = Number(total[1].replace(/\./g, ""));
  const list = filas.length && filas.reduce((s, f) => s + f.monto, 0) === tot ? filas : [{ empresa: "Pago de cuentas", cliente: null, vence: null, monto: tot }];
  const fecha = `${cuando[3]}-${cuando[2]}-${cuando[1]}`;
  return {
    ok: true,
    movs: list.map((f, i) => ({
      id: list.length > 1 ? `${base}#${i + 1}` : base, fecha, hora: cuando[4], comercio: f.empresa, tipo: "Pago de cuenta", monto: f.monto, cliente: f.cliente, vence: f.vence,
    })),
  };
}

/* Texto de la parte HTML de un correo del banco: separa las celdas y filas de las tablas (htmlToText() las junta) y decodifica las entidades. */
const ENTITIES = { nbsp: " ", amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", ordm: "º", ordf: "ª", deg: "°", aacute: "á", eacute: "é", iacute: "í", oacute: "ó", uacute: "ú", ntilde: "ñ", Aacute: "Á", Eacute: "É", Iacute: "Í", Oacute: "Ó", Uacute: "Ú", Ntilde: "Ñ", uuml: "ü" };
function bankHtmlText(html) {
  const spaced = String(html).replace(/<\/(td|th)\s*>/gi, " </$1>").replace(/<\/tr\s*>/gi, "\n</tr>");
  return htmlToText(spaced)
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&([a-z]+);/gi, (m, k) => ENTITIES[k] ?? m);
}

/* Los nombres del destino y del saludo coinciden cuando todas las palabras del destino están en el saludo. */
function sameName(destino, saludo) {
  if (!saludo) return false;
  const tokens = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").split(/\s+/).filter(Boolean);
  const hello = new Set(tokens(saludo));
  const dest = tokens(destino);
  return dest.length > 0 && dest.every((t) => hello.has(t));
}

function splitMessage(raw) {
  const sep = String(raw).match(/\r?\n\r?\n/);
  return sep ? { head: raw.slice(0, sep.index), body: raw.slice(sep.index + sep[0].length) } : null;
}

function headerParam(value, name) {
  const m = String(value || "").match(new RegExp(`${name}="?([^";\\s]+)"?`, "i"));
  return m ? m[1] : null;
}

/* Recorre las partes MIME y deja en out.plain el primer text/plain y en out.html el primer text/html. */
function collectText(head, body, depth, out) {
  const contentType = headerValue(head, "content-type") || "text/plain";
  const boundary = /^multipart\//i.test(contentType) ? headerParam(contentType, "boundary") : null;
  if (boundary) {
    if (depth > 4) return;
    for (const part of body.split(`--${boundary}`).slice(1)) {
      if (part.startsWith("--")) break;
      const sub = splitMessage(part.replace(/^\r?\n/, ""));
      if (sub) collectText(sub.head, sub.body, depth + 1, out);
    }
    return;
  }
  const encoding = (headerValue(head, "content-transfer-encoding") || "").toLowerCase();
  const charset = headerParam(contentType, "charset") || "utf-8";
  if (/^text\/plain/i.test(contentType)) out.plain ??= decodeText(body, encoding, charset);
  else if (/^text\/html/i.test(contentType)) out.html ??= bankHtmlText(decodeText(body, encoding, charset));
}

/* Decodifica base64 o quoted-printable y convierte los bytes desde el charset indicado. */
function decodeText(body, encoding, charset) {
  let bin;
  if (encoding === "base64") bin = atob(body.replace(/\s+/g, ""));
  else if (encoding === "quoted-printable") {
    bin = body
      .replace(/=\r?\n/g, "")
      .replace(/=([0-9A-Fa-f]{2})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
  } else return body;
  if (/^(iso-8859-1|latin1|windows-1252|us-ascii)$/i.test(charset)) return bin;
  try {
    return new TextDecoder(charset).decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  } catch {
    return new TextDecoder("utf-8").decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  }
}
