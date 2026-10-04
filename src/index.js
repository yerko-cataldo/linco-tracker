// Lincoyán: Worker que protege el sitio, guarda tus datos en D1 y hace de proxy al modelo.
import { jwtVerify, createRemoteJWKSet } from "jose";

const LIB_KEYS = new Set(["goals", "profile", "techniques", "songs", "books", "coach", "foods", "combos"]);
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const MAX_DOC_BYTES = 256 * 1024;
const MAX_IMAGES = 3;
const MAX_IMAGE_B64 = 7_000_000;

let JWKS = null;

export default {
  async fetch(request, env) {
    const user = await authorize(request, env);
    if (!user) return new Response("No autorizado", { status: 403 });

    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);

    try {
      return await api(request, env, url);
    } catch (err) {
      console.error(err);
      return json({ error: "internal" }, 500);
    }
  },
};

/* ---------- autenticación: valida el JWT que agrega Cloudflare Access ---------- */
async function authorize(request, env) {
  if (env.DEV_BYPASS_AUTH === "1") return { email: "dev@local" }; // solo en .dev.vars
  const token = request.headers.get("cf-access-jwt-assertion");
  if (!token) return null;
  JWKS ??= createRemoteJWKSet(new URL(`${env.ACCESS_TEAM_DOMAIN}/cdn-cgi/access/certs`));
  try {
    const { payload } = await jwtVerify(token, JWKS, { issuer: env.ACCESS_TEAM_DOMAIN, audience: env.ACCESS_AUD });
    const email = String(payload.email || "").toLowerCase();
    if (env.ALLOWED_EMAIL && email !== env.ALLOWED_EMAIL.toLowerCase()) return null;
    return { email };
  } catch {
    return null;
  }
}

/* ---------- API ---------- */
async function api(request, env, url) {
  const { pathname: p } = url;
  const m = request.method;
  let match;

  if (p === "/api/state" && m === "GET") {
    const [days, lib] = await env.DB.batch([
      env.DB.prepare("SELECT date, data FROM days ORDER BY date DESC LIMIT 400"),
      env.DB.prepare("SELECT key, data FROM lib"),
    ]);
    return json({
      days: Object.fromEntries(days.results.map((r) => [r.date, JSON.parse(r.data)])),
      lib: Object.fromEntries(lib.results.map((r) => [r.key, JSON.parse(r.data)])),
    });
  }

  if ((match = p.match(/^\/api\/days\/(\d{4}-\d{2}-\d{2})$/)) && m === "PUT") {
    const body = await readDoc(request);
    if (!body) return json({ error: "bad_body" }, 400);
    await upsertDay(env, match[1], body).run();
    return json({ ok: true });
  }

  if ((match = p.match(/^\/api\/lib\/([a-z]+)$/)) && m === "PUT") {
    if (!LIB_KEYS.has(match[1])) return json({ error: "unknown_key" }, 404);
    const body = await readDoc(request);
    if (!body) return json({ error: "bad_body" }, 400);
    await upsertLib(env, match[1], body).run();
    return json({ ok: true });
  }

  if (p === "/api/import" && m === "POST") {
    const text = await request.text();
    if (text.length > 20 * 1024 * 1024) return json({ error: "too_large" }, 413);
    let data;
    try { data = JSON.parse(text); } catch { return json({ error: "bad_json" }, 400); }
    const stmts = [];
    for (const [date, doc] of Object.entries(data.days || {})) {
      if (DATE_RE.test(date) && doc && typeof doc === "object") stmts.push(upsertDay(env, date, JSON.stringify(doc)));
    }
    for (const [key, doc] of Object.entries(data.lib || {})) {
      if (LIB_KEYS.has(key) && doc && typeof doc === "object") stmts.push(upsertLib(env, key, JSON.stringify(doc)));
    }
    for (let i = 0; i < stmts.length; i += 50) await env.DB.batch(stmts.slice(i, i + 50));
    return json({ ok: true, imported: stmts.length });
  }

  if (p === "/api/usage" && m === "GET") {
    const rows = await env.DB.prepare("SELECT * FROM ai_usage ORDER BY day DESC LIMIT 31").all();
    return json({ limit: Number(env.AI_DAILY_LIMIT || 150), days: rows.results });
  }

  if (p === "/api/ai" && m === "POST") return ai(request, env);

  return json({ error: "not_found" }, 404);
}

const upsertDay = (env, date, body) =>
  env.DB.prepare(
    "INSERT INTO days(date, data, updated_at) VALUES(?1, ?2, datetime('now')) " +
    "ON CONFLICT(date) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at"
  ).bind(date, body);

const upsertLib = (env, key, body) =>
  env.DB.prepare(
    "INSERT INTO lib(key, data, updated_at) VALUES(?1, ?2, datetime('now')) " +
    "ON CONFLICT(key) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at"
  ).bind(key, body);

async function readDoc(request) {
  const text = await request.text();
  if (!text || text.length > MAX_DOC_BYTES) return null;
  try {
    const v = JSON.parse(text);
    return v && typeof v === "object" && !Array.isArray(v) ? text : null;
  } catch {
    return null;
  }
}

/* ---------- proxy al modelo: Workers AI (gratis) o Anthropic, según la tarea ---------- */
// Tareas: "default" (registro rápido, chat), "complex" (revisión semanal, panel de nutrición), visión (fotos).
function pickRoute(env, tier, hasImages) {
  if (hasImages) return { provider: env.PROVIDER_VISION || "workers-ai", model: env.MODEL_VISION };
  if (tier === "complex") return { provider: env.PROVIDER_COACH || "workers-ai", model: env.MODEL_COACH };
  return { provider: env.PROVIDER_DEFAULT || "workers-ai", model: env.MODEL_DEFAULT };
}

async function ai(request, env) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "bad_json" }, 400); }
  const messages = Array.isArray(body.messages) ? body.messages : [];
  if (!messages.length || messages[messages.length - 1].role !== "user") return json({ error: "bad_messages" }, 400);

  const images = (Array.isArray(body.images) ? body.images : []).slice(0, MAX_IMAGES)
    .filter((i) => i && typeof i.data === "string" && i.data.length < MAX_IMAGE_B64 && /^image\/(jpeg|png|webp|gif)$/.test(i.media_type));
  const route = pickRoute(env, body.tier, images.length > 0);
  if (route.provider === "anthropic" && !env.ANTHROPIC_API_KEY) return json({ error: "no_api_key" }, 503);
  if (route.provider === "workers-ai" && !env.AI) return json({ error: "no_ai_binding" }, 503);

  // Tope diario de llamadas (hora de Chile) para acotar gasto y cuota gratis
  const today = new Date().toLocaleDateString("en-CA", { timeZone: "America/Santiago" });
  const limit = Number(env.AI_DAILY_LIMIT || 150);
  const row = await env.DB.prepare("SELECT calls FROM ai_usage WHERE day = ?1").bind(today).first();
  if (row && row.calls >= limit) return json({ error: "rate_limited", limit }, 429);
  await env.DB.prepare(
    "INSERT INTO ai_usage(day, calls) VALUES(?1, 1) ON CONFLICT(day) DO UPDATE SET calls = calls + 1"
  ).bind(today).run();

  const msgs = messages.map((x) => ({ role: x.role === "assistant" ? "assistant" : "user", content: String(x.content ?? "") }));
  const system = [
    "Responde en español de Chile.",
    body.json ? "Responde únicamente con JSON válido, sin texto adicional ni bloques de código." : "",
  ].filter(Boolean).join(" ");
  const stream = !!body.stream && !body.json;
  const maxTokens = Math.min(Math.max(Number(body.max_tokens) || 2000, 64), 4000);

  try {
    const out = route.provider === "anthropic"
      ? await runAnthropic(env, route.model, system, msgs, images, stream, maxTokens)
      : await runWorkersAI(env, route.model, system, msgs, images, stream, maxTokens);

    if (stream) {
      return new Response(out.stream, {
        headers: { "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" },
      });
    }
    await env.DB.prepare(
      "UPDATE ai_usage SET input_tokens = input_tokens + ?2, output_tokens = output_tokens + ?3 WHERE day = ?1"
    ).bind(today, out.inTok || 0, out.outTok || 0).run();
    return json({ text: out.text, truncated: !!out.truncated, provider: route.provider, model: route.model });
  } catch (err) {
    const msg = String((err && err.message) || err);
    console.error("ai", route.provider, route.model, msg.slice(0, 500));
    if (/neuron|4006|daily free allocation/i.test(msg)) return json({ error: "rate_limited", reason: "workers_ai_quota" }, 429);
    return json({ error: "upstream" }, 502);
  }
}

/* Anthropic Messages API (o un endpoint compatible vía ANTHROPIC_BASE_URL) */
async function runAnthropic(env, model, system, msgs, images, stream, maxTokens) {
  const messages = msgs.map((m) => ({ ...m }));
  if (images.length) {
    const last = messages[messages.length - 1];
    last.content = [
      ...images.map((i) => ({ type: "image", source: { type: "base64", media_type: i.media_type, data: i.data } })),
      { type: "text", text: last.content },
    ];
  }
  const res = await fetch(`${env.ANTHROPIC_BASE_URL || "https://api.anthropic.com"}/v1/messages`, {
    method: "POST",
    headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model, max_tokens: maxTokens, system, messages, stream }),
  });
  if (!res.ok) throw new Error(`anthropic ${res.status}: ${(await res.text()).slice(0, 300)}`);
  if (stream) return { stream: res.body };  // ya viene en el formato SSE que entiende el front
  const data = await res.json();
  return {
    text: (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join(""),
    truncated: data.stop_reason === "max_tokens",
    inTok: data.usage?.input_tokens, outTok: data.usage?.output_tokens,
  };
}

/* Workers AI (binding AI): modelos abiertos dentro del tier gratis de Cloudflare */
async function runWorkersAI(env, model, system, msgs, images, stream, maxTokens) {
  const messages = [{ role: "system", content: system }, ...msgs.map((m) => ({ ...m }))];
  if (images.length) {
    const last = messages[messages.length - 1];
    last.content = [
      { type: "text", text: last.content },
      ...images.map((i) => ({ type: "image_url", image_url: { url: `data:${i.media_type};base64,${i.data}` } })),
    ];
  }
  const r = await env.AI.run(model, { messages, max_tokens: maxTokens, stream });
  if (stream) return { stream: workersAIToAnthropicSSE(r) };
  let text = "";
  if (typeof r?.response === "string") text = r.response;
  else if (r?.response && typeof r.response === "object") text = JSON.stringify(r.response);
  else if (r?.choices) text = r.choices[0]?.message?.content || "";
  return { text, inTok: r?.usage?.prompt_tokens, outTok: r?.usage?.completion_tokens };
}

/* Convierte el streaming de Workers AI al formato de eventos de Anthropic que parsea el front */
function workersAIToAnthropicSSE(stream) {
  const dec = new TextDecoder(), enc = new TextEncoder();
  let buf = "";
  return stream.pipeThrough(new TransformStream({
    transform(chunk, ctrl) {
      buf += dec.decode(chunk, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, i).trim();
        buf = buf.slice(i + 1);
        if (!line.startsWith("data:")) continue;
        const data = line.slice(5).trim();
        if (!data || data === "[DONE]") continue;
        let d;
        try { d = JSON.parse(data); } catch { continue; }
        const text = typeof d.response === "string" ? d.response : (d.choices?.[0]?.delta?.content || "");
        if (text) {
          const evt = { type: "content_block_delta", index: 0, delta: { type: "text_delta", text } };
          ctrl.enqueue(enc.encode(`event: content_block_delta\ndata: ${JSON.stringify(evt)}\n\n`));
        }
      }
    },
  }));
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
