// Notificaciones push (Web Push): cifrado aes128gcm (RFC 8291) y firma VAPID (RFC 8292) con WebCrypto, sin dependencias.
// VAPID_JWK es un secreto del Worker: la clave privada P-256 en formato JWK. La pública sale de sus x e y.

import { SignJWT, importJWK } from "jose";

const enc = new TextEncoder();
const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), (c) => c.charCodeAt(0));
const concat = (...parts) => {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let i = 0;
  for (const p of parts) { out.set(p, i); i += p.length; }
  return out;
};

const vapidJwk = (env) => {
  try { return env.VAPID_JWK ? JSON.parse(env.VAPID_JWK) : null; } catch { return null; }
};

/* Clave pública VAPID (punto sin comprimir en base64url), la que usa el front al suscribirse; null si no está configurada. */
export function vapidPublicKey(env) {
  const jwk = vapidJwk(env);
  return jwk ? b64u(concat(new Uint8Array([4]), unb64u(jwk.x), unb64u(jwk.y))) : null;
}

async function hkdf(salt, ikm, info, bytes) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, key, bytes * 8));
}

/* Cuerpo cifrado para una suscripción: un solo registro aes128gcm con la clave pública efímera en la cabecera. */
async function encrypt(sub, payload) {
  const uaPublic = unb64u(sub.p256dh), authSecret = unb64u(sub.auth);
  const local = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const asPublic = new Uint8Array(await crypto.subtle.exportKey("raw", local.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPublic, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: "ECDH", public: uaKey }, local.privateKey, 256));

  const ikm = await hkdf(authSecret, shared, concat(enc.encode("WebPush: info\0"), uaPublic, asPublic), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);

  const key = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const body = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, key, concat(enc.encode(payload), new Uint8Array([2]))));
  const rs = new Uint8Array([0, 0, 16, 0]); // tamaño de registro 4096
  return concat(salt, rs, new Uint8Array([asPublic.length]), asPublic, body);
}

async function vapidAuth(env, endpoint) {
  const jwk = vapidJwk(env);
  const key = await importJWK({ ...jwk, alg: "ES256" }, "ES256");
  const jwt = await new SignJWT({})
    .setProtectedHeader({ alg: "ES256", typ: "JWT" })
    .setAudience(new URL(endpoint).origin)
    .setSubject(env.PUSH_SUBJECT || "mailto:push@localhost")
    .setExpirationTime("12h")
    .sign(key);
  return `vapid t=${jwt}, k=${vapidPublicKey(env)}`;
}

/* Envía {title, body, tag, url} a todas las suscripciones y borra las que el servicio de push da por vencidas (404/410).
   Devuelve cuántas se entregaron. */
export async function sendPush(env, msg) {
  if (!vapidJwk(env)) return 0;
  const subs = await env.DB.prepare("SELECT endpoint, p256dh, auth FROM push_subs").all();
  const payload = JSON.stringify(msg);
  let sent = 0;
  await Promise.all(subs.results.map(async (sub) => {
    try {
      const res = await fetch(sub.endpoint, {
        method: "POST",
        headers: {
          authorization: await vapidAuth(env, sub.endpoint),
          "content-encoding": "aes128gcm",
          "content-type": "application/octet-stream",
          ttl: "86400",
          urgency: "high",
        },
        body: await encrypt(sub, payload),
      });
      if (res.status === 404 || res.status === 410) {
        await env.DB.prepare("DELETE FROM push_subs WHERE endpoint = ?").bind(sub.endpoint).run();
      } else if (res.ok) sent++;
      else console.error("push", res.status, (await res.text()).slice(0, 200));
    } catch (err) {
      console.error("push", String(err).slice(0, 200));
    }
  }));
  return sent;
}
