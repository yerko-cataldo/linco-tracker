// Compara modelos en la "propuesta para completar el día" con el mismo prompt y el mismo
// post-proceso que la app (macros desde la base de alimentos y afinado de porciones).
//
// Las llamadas pasan por el Worker local (`wrangler dev`), así cada modelo recibe el mismo
// mensaje de sistema y el mismo proxy que en producción. Elige el modelo al levantar el Worker:
//   npx wrangler dev --port 8787 --var PROVIDER_COACH:workers-ai --var MODEL_COACH:@cf/meta/llama-4-scout-17b-16e-instruct
//   npx wrangler dev --port 8787 --var PROVIDER_COACH:anthropic --var MODEL_COACH:claude-sonnet-5-5   (requiere ANTHROPIC_API_KEY en .dev.vars)
//
// Uso:
//   node eval/compare_plan.mjs run --export lincoyan-AAAA-MM-DD.json --label llama4 [--base http://localhost:8787] [--days 3]
//   node eval/compare_plan.mjs report
// Los resultados quedan en eval/results/plan/ (ignorado por git: contiene tus comidas).

import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "eval", "results", "plan");
const args = Object.fromEntries(process.argv.slice(3).reduce((a, x, i, l) => (x.startsWith("--") ? [...a, [x.slice(2), l[i + 1]]] : a), []));
const cmd = process.argv[2];

// Escenarios: para cada día reciente con desayuno, almuerzo y algo más, se simula
// la mañana sin haber comido y la tarde después del almuerzo, con el historial anterior a ese día.
const SCENARIOS = [
  { id: "manana", label: "8:00, sin haber comido", now: "08:00", upTo: -1 },
  { id: "tarde", label: "16:30, después del almuerzo", now: "16:30", upTo: 1 },
];

function loadApp() {
  const html = fs.readFileSync(path.join(ROOT, "public", "index.html"), "utf8");
  let src = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].pop()[1];
  const patch = (a, b) => { if (!src.includes(a)) throw new Error("No encontré en index.html: " + a.slice(0, 60)); src = src.replace(a, b); };
  // Reloj controlado por el escenario
  patch("const today = () => ymd(new Date());", "const today = () => globalThis.__T.date;");
  patch("const nowHM = () => { const d = new Date(); return `${pad(d.getHours())}:${pad(d.getMinutes())}`; };", "const nowHM = () => globalThis.__T.now;");
  patch(/const chileNow = \(\) => [^\n]*/.exec(src)[0], "const chileNow = () => globalThis.__T.chile;");
  src = src.replace(/\ninit\(\);\s*$/, "\n");
  const E = {};
  const el = (s) => (E[s] = E[s] || { id: s, hidden: false, innerHTML: "", value: "", contains: () => false, scrollIntoView() {}, classList: { add() {}, remove() {} } });
  const ctx = {
    console, Math, Date, JSON, Intl, Set, Map, Promise, setTimeout, clearTimeout, __T: { date: "2026-01-01", now: "08:00", chile: "" },
    document: { querySelector: el, querySelectorAll: () => [], activeElement: null },
    window: { addEventListener() {} }, navigator: {}, localStorage: { getItem: () => null, setItem() {} },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
  };
  vm.createContext(ctx);
  vm.runInContext(src + "\n;globalThis.__app = {S, generatePlan, planNeed, planSlots, mealHistory, slotOf, setTune: f => { tunePlanOpt = f; }, tunePlanOpt, renderPlan: () => {}};", ctx);
  return ctx;
}

function chileLabel(date, hm) {
  const [y, m, d] = date.split("-").map(Number);
  const s = new Date(y, m - 1, d).toLocaleDateString("es-CL", { weekday: "long", day: "numeric", month: "long" });
  return `${s}, ${hm}`;
}

async function run() {
  if (!args.export || !args.label) throw new Error("Faltan --export y --label.");
  const base = args.base || "http://localhost:8787", nDays = Number(args.days || 3);
  const exp = JSON.parse(fs.readFileSync(path.resolve(args.export), "utf8"));
  const ctx = loadApp(), app = ctx.__app, S = app.S;
  Object.assign(S.lib, exp.lib || {});
  S.days = exp.days || {};
  if (!(S.lib.foods || []).length) throw new Error("La exportación no trae tu base de alimentos (lib.foods). Exporta de nuevo desde la app.");
  S.mode = "api"; S.tab = "nutricion"; S.planMeals = 0; S.planNote = "";

  // Días recientes con al menos 3 comidas con hora, una de ellas antes de las 11 y otra en el almuerzo
  const days = Object.keys(S.days).sort().reverse().filter((d) => {
    const slots = (S.days[d].meals || []).map((m) => app.slotOf(m.time)).filter((x) => x !== null);
    return slots.length >= 3 && slots.includes(0) && slots.includes(1);
  }).slice(0, nDays);
  if (!days.length) throw new Error("No encontré días con desayuno y almuerzo registrados con hora.");

  // Llamada al Worker con la misma forma que usa el front (tier complex, json)
  let last = null;
  S.sample = {
    json: async (prompt) => {
      const t0 = Date.now();
      const r = await fetch(`${base}/api/ai`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ messages: [{ role: "user", content: prompt }], tier: "complex", json: true, max_tokens: Number(args.max || 4000) }),
      });
      const body = await r.json().catch(() => ({}));
      last = { status: r.status, latency_s: (Date.now() - t0) / 1000, model: body.model, provider: body.provider, truncated: body.truncated, error: body.error, promptChars: prompt.length };
      if (!r.ok) throw { code: body.error || "upstream" };
      const t = String(body.text || "").replace(/```json|```/g, "").trim(), a = t.indexOf("{"), b = t.lastIndexOf("}");
      last.raw = t;
      try { return JSON.parse(t.slice(a, b + 1)); } catch { throw { code: "invalid_json" }; }
    },
  };
  // Guarda los totales antes del afinado: miden qué tan bien suma el modelo por sí solo
  const tune = app.tunePlanOpt;
  let rawTotals = [];
  app.setTune((meals, need) => { const out = tune(meals, need); rawTotals.push({ kcal: meals.reduce((s, m) => s + m.tot.kcal, 0), p: meals.reduce((s, m) => s + m.tot.p, 0) }); return out; });

  const results = [];
  for (const date of days) {
    const full = S.days[date];
    for (const sc of SCENARIOS) {
      const eaten = sc.upTo < 0 ? [] : full.meals.filter((m) => { const s = app.slotOf(m.time); return s !== null && s <= sc.upTo; });
      S.days[date] = { ...full, meals: eaten };
      ctx.__T.date = date; ctx.__T.now = sc.now; ctx.__T.chile = chileLabel(date, sc.now);
      S.plan = null; last = null; rawTotals = [];
      const { need, st } = app.planNeed(date);
      process.stdout.write(`${args.label} · ${date} · ${sc.label}… `);
      await app.generatePlan();
      const p = S.plan || {};
      results.push({
        label: args.label, date, scenario: sc.id, scenarioLabel: sc.label, slots: app.planSlots(date, st), eaten: eaten.map((m) => `${m.time} ${m.desc}`),
        need, call: last && { ...last, raw: undefined }, raw: last && last.raw, status: p.status, err: p.err, nota: p.nota,
        opts: (p.opts || []).map((o, i) => ({
          k: o.k, raw: rawTotals[i], tot: o.tot,
          meals: o.meals.map((m) => ({ slot: m.slot, desc: m.desc, tot: m.tot, items: m.items.map((it) => ({ name: it.name, g: it.g, kcal: it.kcal, p: it.p, ai: it.ai })) })),
        })),
      });
      console.log(p.status === "ok" ? `ok (${last.latency_s.toFixed(1)} s)` : `error: ${p.err}`);
      S.days[date] = full;
    }
  }
  fs.mkdirSync(OUT, { recursive: true });
  const file = path.join(OUT, `${args.label}.json`);
  fs.writeFileSync(file, JSON.stringify({ label: args.label, model: results.find((r) => r.call)?.call?.model, at: new Date().toISOString(), goals: S.lib.goals, results }, null, 2));
  console.log("Guardado en", path.relative(ROOT, file));
}

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const n0 = (x) => (x === undefined || x === null || !isFinite(x) ? "—" : Math.round(x).toLocaleString("es-CL"));
const pct = (x) => (x === null || !isFinite(x) ? "—" : `${x > 0 ? "+" : ""}${Math.round(x * 100)}%`);

// Métricas por opción: error de kcal del modelo (antes del afinado), proteína tras el afinado,
// comida más chica (detecta "cenas de brócoli") e ingredientes fuera de la base.
function metrics(r, o) {
  const minMeal = Math.min(...o.meals.map((m) => m.tot.kcal));
  return {
    kcalErrRaw: o.raw ? o.raw.kcal / r.need.kcal - 1 : null,
    kcalErr: o.tot.kcal / r.need.kcal - 1,
    protShort: Math.max(0, r.need.p - o.tot.p),
    minMeal, tuned: o.k !== 1,
    aiItems: o.meals.reduce((s, m) => s + m.items.filter((i) => i.ai).length, 0),
  };
}

function report() {
  const runs = fs.readdirSync(OUT).filter((f) => f.endsWith(".json")).map((f) => JSON.parse(fs.readFileSync(path.join(OUT, f), "utf8")));
  if (!runs.length) throw new Error("No hay resultados en eval/results/plan/. Corre primero `run`.");
  const avg = (a) => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : null);
  const summary = runs.map((run) => {
    const ok = run.results.filter((r) => r.status === "ok"), ms = ok.flatMap((r) => r.opts.map((o) => metrics(r, o)));
    return {
      label: run.label, model: run.model, n: run.results.length, ok: ok.length,
      kcalErrRaw: avg(ms.filter((m) => m.kcalErrRaw !== null).map((m) => Math.abs(m.kcalErrRaw))),
      kcalErr: avg(ms.map((m) => Math.abs(m.kcalErr))),
      tunedShare: ms.length ? ms.filter((m) => m.tuned).length / ms.length : null,
      protShort: avg(ms.map((m) => m.protShort)),
      tinyMeals: ms.filter((m) => m.minMeal < 200).length,
      aiItems: avg(ms.map((m) => m.aiItems)),
      latency: avg(run.results.filter((r) => r.call).map((r) => r.call.latency_s)),
    };
  });
  const keys = [...new Set(runs.flatMap((r) => r.results.map((x) => `${x.date}|${x.scenario}`)))];
  const card = (r) => {
    if (!r) return `<div class="col muted">sin resultado</div>`;
    if (r.status !== "ok") return `<div class="col"><p class="bad">Error: ${esc(r.err)}</p>${r.raw ? `<pre>${esc(r.raw.slice(0, 600))}</pre>` : ""}</div>`;
    return `<div class="col">${r.nota ? `<p class="muted">${esc(r.nota)}</p>` : ""}${r.opts.map((o, i) => {
      const m = metrics(r, o);
      return `<div class="opt"><h4>Opción ${i + 1} <span class="muted">${o.k !== 1 ? `afinada ×${o.k}` : "sin afinar"}</span></h4>
        ${o.meals.map((ml) => `<div class="meal"><b>${esc(ml.slot)}</b> ${esc(ml.desc)}<br><span>${esc(ml.items.map((it) => `${it.name} ${n0(it.g)} g${it.ai ? "*" : ""}`).join(", "))}</span><br><span class="muted">${n0(ml.tot.kcal)} kcal · P ${n0(ml.tot.p)} g</span></div>`).join("")}
        <p class="tot">Modelo: ${n0(o.raw?.kcal)} kcal (${pct(m.kcalErrRaw)}) → final ${n0(o.tot.kcal)} kcal (${pct(m.kcalErr)}) · P ${n0(o.tot.p)} / ${n0(r.need.p)} g</p></div>`;
    }).join("")}<p class="muted small">${r.call ? `${r.call.latency_s.toFixed(1)} s` : ""}</p></div>`;
  };
  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Propuesta del día: comparación</title>
<style>
:root{--bg:#f6f1e7;--surface:#fffaf0;--ink:#2b2621;--muted:#7a6f63;--line:#e3d9c8;--bad:#b3412e}
@media (prefers-color-scheme:dark){:root{--bg:#22272e;--surface:#2d333b;--ink:#cdd9e5;--muted:#8b98a5;--line:#444c56;--bad:#e5735b}}
body{background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif;margin:0;padding:24px 16px}
main{max-width:1400px;margin:0 auto}h1{font-size:1.4rem}h2{font-size:1.1rem;margin:32px 0 6px}h4{margin:0 0 6px;font-size:.95rem}
table{border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--line);border-radius:8px;overflow:hidden}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right}th:first-child,td:first-child{text-align:left}
.grid{display:grid;grid-template-columns:repeat(${runs.length},minmax(0,1fr));gap:12px}@media (max-width:800px){.grid{grid-template-columns:1fr}}
.col{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px}.col>h3{margin:0 0 8px;font-size:1rem}
.opt{border-top:1px solid var(--line);padding-top:8px;margin-top:8px}.meal{margin:6px 0;font-size:.9rem}.tot{font-size:.88rem;margin:8px 0 0}
.muted{color:var(--muted)}.small{font-size:.8rem}.bad{color:var(--bad)}pre{white-space:pre-wrap;font-size:.75rem}
</style></head><body><main>
<h1>Propuesta del día: comparación de modelos</h1>
<p class="muted">Mismo prompt y mismo post-proceso que la app. "Error del modelo" = kcal que suma lo que propuso, calculadas con tu base, frente a las que faltaban, antes del afinado (±25% máx.). "Comidas &lt; 200 kcal" cuenta opciones con alguna comida casi vacía. * = ingrediente fuera de tu base, estimado por la IA.</p>
<table><thead><tr><th>Modelo</th><th>Respuestas válidas</th><th>Error del modelo en kcal</th><th>Error final</th><th>Opciones afinadas</th><th>Proteína faltante</th><th>Comidas &lt; 200 kcal</th><th>Ingredientes estimados</th><th>Latencia</th></tr></thead><tbody>
${summary.map((s) => `<tr><td><b>${esc(s.label)}</b><br><span class="muted small">${esc(s.model || "")}</span></td><td>${s.ok} / ${s.n}</td><td>${pct(s.kcalErrRaw).replace("+", "±")}</td><td>${pct(s.kcalErr).replace("+", "±")}</td><td>${pct(s.tunedShare).replace("+", "")}</td><td>${s.protShort === null ? "—" : n0(s.protShort) + " g"}</td><td>${s.tinyMeals}</td><td>${s.aiItems === null ? "—" : s.aiItems.toFixed(1)}</td><td>${s.latency === null ? "—" : s.latency.toFixed(1) + " s"}</td></tr>`).join("")}
</tbody></table>
${keys.map((k) => {
  const [date, sc] = k.split("|"), any = runs.flatMap((r) => r.results).find((x) => x.date === date && x.scenario === sc);
  return `<h2>${esc(date)} · ${esc(any.scenarioLabel)}</h2><p class="muted">Faltan ${n0(any.need.kcal)} kcal y ${n0(any.need.p)} g de proteína. Franjas: ${esc(any.slots.join(", "))}.${any.eaten.length ? ` Ya comió: ${esc(any.eaten.join("; "))}.` : ""}</p>
  <div class="grid">${runs.map((run) => `<div><h3>${esc(run.label)}</h3>${card(run.results.find((x) => x.date === date && x.scenario === sc))}</div>`).join("")}</div>`;
}).join("")}
</main></body></html>`;
  const file = path.join(OUT, "report.html");
  fs.writeFileSync(file, html);
  console.table(summary.map((s) => ({ modelo: s.label, validas: `${s.ok}/${s.n}`, err_modelo: pct(s.kcalErrRaw), err_final: pct(s.kcalErr), prot_falta_g: s.protShort && Math.round(s.protShort), comidas_chicas: s.tinyMeals, latencia_s: s.latency && +s.latency.toFixed(1) })));
  console.log("Reporte en", path.relative(ROOT, file));
}

(cmd === "run" ? run() : cmd === "report" ? Promise.resolve(report()) : Promise.reject(new Error("Usa: run | report"))).catch((e) => { console.error(e.message || e); process.exit(1); });
