// Correos de Banco BICE reenviados por el titular: valida el reenvío y lee el comprobante de transferencia.

import { headerValue, htmlToText } from "./alertas.js";
import { longDate, rutKey } from "./cartola.js";

const COMPROBANTE_RE = /Hicimos la transferencia que nos pediste/i;
const MONTO_RE = /Monto \$\s*([\d.]+)/i;
const DESTINO_RE = /Cuenta de destino Nombre (.+?) RUT ([\d.]+-[\dkK]) Banco (.+?) Tipo de cuenta/i;
const OPERACION_RE = /N.mero de operaci.n (\d+)/i;
const FECHA_RE = /(\d{1,2} [a-z]{3,4}\.? \d{4}) - (\d{2}:\d{2}) h/i;
const SALUDO_RE = /Hola,? (.+?) Hicimos la transferencia/i;

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
  const text = String(parts.plain || parts.html || "").replace(/\s+/g, " ").trim();
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
    },
  };
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
  else if (/^text\/html/i.test(contentType)) out.html ??= htmlToText(decodeText(body, encoding, charset));
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
