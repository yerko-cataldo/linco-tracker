import { finContext, catInfo, isIncoming } from "./finanzas.js";
import { applyProposal } from "./agente.js";

// Reloj (Galaxy Watch, app en AndroidStudioProjects/lincoyan/wear): resumen del día y acciones rápidas.
// El plan de series replica, simplificada, la lógica del checklist de public/index.html (habitual(), nextStep(),
// warmIds(), "wk-done"): sin el catálogo EX_CAT, los ejercicios se agrupan por nombre normalizado y no se reordenan
// por tipo. Si cambias esa lógica en la web, revisa también esta.

const GYM_LABEL = { push: "Push", pull: "Pull", legs: "Legs", full: "Full body", core: "Core", torsoA: "Torso A", piernaA: "Pierna A", torsoB: "Torso B", piernaB: "Pierna B" };
const TL_CYCLE = ["torsoA", "piernaA", "torsoB", "piernaB"];
// Copia de DEFAULT_ROUTINE de la web: la rutina base mientras no haya sesiones anteriores del tipo
const DEFAULT_ROUTINE = {
  push: ["Press banca", "Press inclinado con mancuernas", "Press militar", "Elevaciones laterales", "Extensión de tríceps"],
  pull: ["Jalón al pecho con polea", "Remo en máquina", "Face pull", "Curl con barra Z", "Curl martillo"],
  legs: ["Sentadilla hack", "Extensión de cuádriceps", "Curl femoral sentado", "Elevación de talones", "Aductores en máquina", "Abductores en máquina"],
  full: ["Sentadilla", "Press banca", "Remo en polea", "Press militar", "Curl femoral"],
  core: ["Elevación de piernas", "Crunch inverso", "Plancha", "Plancha lateral", "Bicho muerto"],
  torsoA: ["Press banca", "Jalón al pecho con polea", "Press inclinado con barra", "Remo en máquina", "Elevaciones laterales", "Curl con barra Z", "Extensión de tríceps"],
  piernaA: ["Sentadilla hack", "Peso muerto rumano", "Curl femoral sentado", "Extensión de cuádriceps", "Elevación de talones", "Crunch en polea", "Pallof press"],
  torsoB: ["Press militar", "Remo en polea", "Press de pecho en máquina", "Jalón con agarre estrecho", "Face pull", "Elevaciones laterales", "Curl martillo", "Extensión de tríceps sobre la cabeza"],
  piernaB: ["Hip thrust", "Prensa", "Curl femoral", "Aductores en máquina", "Abductores en máquina", "Elevación de talones sentado", "Elevación de piernas", "Plancha lateral"],
};
const DEFAULT_GOALS = { kcal: 2550, protein: 190, water: 10, gymWeek: 3 };
const HABIT_SESSIONS = 3, DEFAULT_SETS = 3, DEFAULT_REPS = 10;
const REP_RANGE = [8, 12], REP_FLOOR = 6, WARM_RATIO = 0.75, LB_KG = 0.4536;
const SET_SEC = 30, REST_MAX = 600, HISTORY_DAYS = 400;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const FREQ_DAYS = 45, PENDING_DAYS = 45;

const norm = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
const addDays = (date, n) => new Date(Date.parse(date + "T12:00:00Z") + n * 864e5).toISOString().slice(0, 10);
const uid = () => Math.random().toString(36).slice(2, 10);
const chileToday = () => new Date().toLocaleDateString("en-CA", { timeZone: "America/Santiago" });
const loadOf = (s) => (Number(s.kg) || 0) * (s.unit === "lb" ? LB_KG : 1);
const e1rm = (s) => loadOf(s) * (s.reps > 1 ? 1 + s.reps / 30 : 1);
const kgStep = (kg, unit) => (unit === "nivel" ? 1 : unit === "lb" ? 5 : kg < 20 ? 1 : 2.5);
const wTxt = (kg, unit) => `${unit === "nivel" ? "nivel " : ""}${String(Math.round(kg * 10) / 10).replace(".", ",")}${unit === "nivel" ? "" : unit === "lb" ? " lb" : " kg"}`;

function normDay(d, date) {
  const o = Object.assign({ date, meals: [], weight: null, water: 0, creatine: false, bass: { minutes: 0, logs: [], songs: [] }, study: [] }, d || {});
  o.act = Object.assign({ gym: "", gymMin: 0, tennisMin: 0, bikeMin: 0, bikeKm: 0, sets: [] }, o.act || {});
  return o;
}

function warmIds(sets) {
  const top = Math.max(0, ...sets.filter((s) => !s.drop).map(loadOf)), out = new Set();
  if (!top) return out;
  for (const s of sets) { if (s.drop || !loadOf(s) || loadOf(s) >= WARM_RATIO * top) break; out.add(s.id); }
  return out;
}

function groupSets(sets) {
  const gs = [];
  for (const s of sets) {
    const k = norm(s.ex);
    let g = gs.find((x) => x.k === k);
    if (!g) gs.push((g = { k, ex: String(s.ex || "").trim(), sets: [] }));
    g.sets.push(s);
  }
  for (const g of gs) {
    g.warm = warmIds(g.sets);
    g.work = g.sets.filter((s) => !g.warm.has(s.id) && !s.drop);
    const w = g.work.length ? g.work : g.sets;
    g.top = w.reduce((a, s) => (e1rm(s) > e1rm(a) || (e1rm(s) === e1rm(a) && s.reps > a.reps) ? s : a));
  }
  return gs;
}

// Doble progresión en 8–12 reps sobre la última sesión (nextStep() de la web)
function nextStep(g) {
  const work = g.work.length ? g.work : g.sets, top = Math.max(...work.map((s) => Number(s.kg) || 0)), u = g.top.unit;
  if (!top) return { kind: "keep", txt: "suma 1 o 2 reps por serie" };
  const reps = work.filter((s) => (Number(s.kg) || 0) === top).map((s) => s.reps);
  if (Math.min(...reps) >= REP_RANGE[1]) {
    const kg = top + (u === "nivel" ? 1 : u === "lb" ? (top >= 80 ? 10 : 5) : top >= 40 ? 5 : 2.5);
    return { kind: "up", top, kg, reps: REP_RANGE[0], txt: `sube a ${wTxt(kg, u)}` };
  }
  if (Math.max(...reps) < REP_FLOOR) {
    const r = kgStep(top, u), kg = Math.min(Math.max(r, Math.round((top * 0.9) / r) * r), top - r);
    return { kind: "down", top, kg, reps: REP_RANGE[0], txt: `baja a ${wTxt(kg, u)}` };
  }
  return { kind: "keep", top, txt: `mantén ${wTxt(top, u)} y suma reps` };
}

// "Le toca": sigue la rotación Torso/Pierna si la última sesión fue de ella; si no, el Push/Pull/Legs menos hecho en la semana
function suggestType(hist, date) {
  const last = hist.filter((h) => h.date <= date && ["push", "pull", "legs", ...TL_CYCLE].includes(h.act.gym)).map((h) => h.act.gym).pop();
  if (TL_CYCLE.includes(last)) return TL_CYCLE[(TL_CYCLE.indexOf(last) + 1) % TL_CYCLE.length];
  const d = new Date(date + "T12:00:00Z"), monday = new Date(d - ((d.getUTCDay() + 6) % 7) * 864e5).toISOString().slice(0, 10);
  const n = { push: 0, pull: 0, legs: 0 };
  hist.forEach((h) => { if (h.date >= monday && h.date <= date && h.act.gym in n) n[h.act.gym]++; });
  return Object.keys(n).sort((a, b) => n[a] - n[b])[0];
}

function workoutPlan(hist, d, date, today) {
  const a = d.act, ended = a.sets.length > 0 && (!!a.end || date < today);
  const suggested = suggestType(hist, date), type = a.gym || suggested;
  const before = hist.filter((h) => h.date < date);
  const sessions = before.filter((h) => h.act.gym === type && h.act.sets.length).slice(-HABIT_SESSIONS);
  let habit = DEFAULT_ROUTINE[type] || [];
  if (sessions.length) {
    const pos = {};
    sessions.forEach((h) => { const gs = groupSets(h.act.sets); gs.forEach((g, i) => (pos[g.k] = pos[g.k] || { ex: g.ex, p: [] }).p.push(i / Math.max(1, gs.length - 1))); });
    const avg = (x) => x.p.reduce((s, v) => s + v, 0) / x.p.length;
    habit = Object.values(pos).sort((x, y) => avg(x) - avg(y)).map((x) => x.ex);
  }
  const done = groupSets(a.sets), names = [];
  [...done.map((g) => g.ex), ...(ended ? [] : habit)].forEach((n) => { if (!names.some((x) => norm(x) === norm(n))) names.push(n); });

  // Récords (liftStats() de la web): la mejor serie del día de un ejercicio cuando supera el 1RM estimado de todas las sesiones anteriores
  const best = {}, top = {}, prIds = new Set();
  before.forEach((h) => h.act.sets.forEach((s) => { const k = norm(s.ex), v = e1rm(s); if (!s.drop && v > (best[k] || 0)) best[k] = v; }));
  a.sets.forEach((s) => { const k = norm(s.ex), v = e1rm(s); if (!s.drop && v && (!top[k] || v > top[k].v)) top[k] = { s, v }; });
  Object.entries(top).forEach(([k, { s, v }]) => { if (best[k] && v > best[k] + 1e-9) prIds.add(s.id); });

  const exs = names.map((name) => {
    const k = norm(name), dg = done.find((g) => g.k === k);
    const prevH = [...before].reverse().find((h) => h.act.sets.some((s) => norm(s.ex) === k));
    const pg = prevH ? groupSets(prevH.act.sets.filter((s) => norm(s.ex) === k))[0] : null;
    const step = pg ? nextStep(pg) : null;
    let plan = pg
      ? pg.sets.map((s) => ({ kg: Number(s.kg) || 0, reps: s.reps, unit: s.unit || "", warm: pg.warm.has(s.id), drop: !!s.drop }))
      : Array.from({ length: DEFAULT_SETS }, () => ({ kg: 0, reps: DEFAULT_REPS, unit: "", warm: false, drop: false }));
    if (step && step.kind !== "keep") plan = plan.map((p) => (!p.warm && !p.drop && p.kg === step.top ? { ...p, kg: step.kg, reps: step.reps } : p));
    const sets = dg ? dg.sets : [], warm = dg ? dg.warm : new Set();
    const rows = sets.map((s) => ({ done: true, id: s.id, kg: Number(s.kg) || 0, reps: s.reps, unit: s.unit || "", warm: warm.has(s.id), drop: !!s.drop, pr: prIds.has(s.id) }));
    if (!ended) for (let i = sets.length; i < plan.length; i++) rows.push({ done: false, ...plan[i], pr: false });
    return { name: dg ? dg.ex : name, step: step ? step.txt : "", stepKind: step ? step.kind : "", rows };
  });
  const last = a.sets.filter((s) => s.t).sort((x, y) => y.t - x.t)[0];
  return {
    type, label: GYM_LABEL[type] || "", suggested, ended,
    lastT: last ? last.t : 0,
    last: last ? { id: last.id, ex: last.ex, kg: Number(last.kg) || 0, reps: last.reps, unit: last.unit || "" } : null,
    exs,
  };
}

// Gastos por revisar (compras y transferencias de los últimos 45 días) con su categoría actual o la sugerida por el agente
async function finPending(env) {
  try {
    const [movs, fin] = await env.DB.batch([
      env.DB.prepare("SELECT * FROM movimientos WHERE revisado = 0 AND fecha >= date('now', ?1) ORDER BY fecha DESC, hora DESC LIMIT 15").bind(`-${PENDING_DAYS} days`),
      env.DB.prepare("SELECT data FROM lib WHERE key = 'fin'"),
    ]);
    const ctx = finContext(fin.results[0] ? JSON.parse(fin.results[0].data).values : {}, movs.results);
    return {
      cats: ctx.cats,
      pending: movs.results.filter((m) => m.moneda === "CLP").map((m) => {
        const c = catInfo(m, ctx);
        return { id: m.id, fecha: m.fecha, hora: m.hora || "", comercio: m.comercio, monto: m.monto, tipo: m.tipo, cat: c.cat, src: c.src, why: m.cat_sug_why || "", incoming: isIncoming(m) };
      }),
    };
  } catch (err) {
    console.error("finPending", String(err).slice(0, 200));
    return { cats: [], pending: [] };
  }
}

// Comidas frecuentes: las de la web (lib.combos) y las que más se repiten en 45 días, agrupadas por descripción dentro de SQLite
const FREQ_SQL =
  "SELECT lower(trim(json_extract(m.value, '$.desc'))) AS k, count(*) AS n, max(d.date || '|' || json_extract(m.value, '$.id')) AS ref, " +
  "max(json_extract(m.value, '$.desc')) AS nombre, round(avg(json_extract(m.value, '$.kcal'))) AS kcal, round(avg(json_extract(m.value, '$.p'))) AS p " +
  "FROM days d, json_each(d.data, '$.meals') m WHERE d.date >= ?1 AND json_extract(m.value, '$.desc') IS NOT NULL GROUP BY k HAVING n >= 2 ORDER BY n DESC LIMIT 6";

async function frequent(env, date) {
  const [rep, combos, foods] = await env.DB.batch([
    env.DB.prepare(FREQ_SQL).bind(addDays(date, -FREQ_DAYS)),
    env.DB.prepare("SELECT data FROM lib WHERE key = 'combos'"),
    env.DB.prepare("SELECT data FROM lib WHERE key = 'foods'"),
  ]);
  const byId = new Map((foods.results[0] ? JSON.parse(foods.results[0].data).list || [] : []).map((f) => [f.id, f]));
  const macro = (items, k) => Math.round((items || []).reduce((s, it) => { const fd = it.foodId && byId.get(it.foodId); return s + (fd ? fd[k === "kcal" ? "kcal" : "p"] * (it.g || 0) / 100 : Number(it[k]) || 0); }, 0));
  const out = (combos.results[0] ? JSON.parse(combos.results[0].data).list || [] : []).slice(0, 8)
    .map((c) => ({ ref: `c:${c.id}`, nombre: c.name, kcal: macro(c.items, "kcal"), p: macro(c.items, "p"), hora: c.time || "" }));
  for (const r of rep.results) if (!out.some((x) => norm(x.nombre) === norm(r.nombre))) out.push({ ref: `m:${r.ref}`, nombre: r.nombre, kcal: r.kcal || 0, p: r.p || 0, veces: r.n });
  return out.slice(0, 10);
}

// Ingredientes de una comida frecuente: la de la web (c:id) o una registrada antes (m:fecha|id)
async function quickItems(env, ref) {
  if (typeof ref !== "string") return null;
  if (ref.startsWith("c:")) {
    const r = await env.DB.prepare("SELECT data FROM lib WHERE key = 'combos'").first();
    const c = r && (JSON.parse(r.data).list || []).find((x) => x.id === ref.slice(2));
    return c ? { descripcion: c.name, items: c.items } : null;
  }
  const [date, id] = ref.slice(2).split("|");
  if (!DATE_RE.test(date || "")) return null;
  const r = await env.DB.prepare("SELECT data FROM days WHERE date = ?1").bind(date).first();
  const m = r && (JSON.parse(r.data).meals || []).find((x) => x.id === id);
  return m ? { descripcion: m.desc, items: m.items } : null;
}

// Solo los días con entreno y solo su parte act: SQLite la extrae para no parsear cientos de días completos
// (el plan gratis de Workers tiene 10 ms de CPU por request)
const HIST_SQL =
  "SELECT date, json_extract(data, '$.act') AS act FROM days WHERE date < ?1 " +
  "AND (json_array_length(json_extract(data, '$.act.sets')) > 0 OR coalesce(json_extract(data, '$.act.gym'), '') <> '') " +
  "ORDER BY date DESC LIMIT ?2";
const LAST_WEIGHT_SQL =
  "SELECT json_extract(data, '$.weight') AS w FROM days WHERE date <= ?1 AND json_extract(data, '$.weight') > 0 ORDER BY date DESC LIMIT 1";

async function summary(env, date) {
  const today = chileToday();
  const [histR, dayR, goalsR, weightR] = await env.DB.batch([
    env.DB.prepare(HIST_SQL).bind(date, HISTORY_DAYS),
    env.DB.prepare("SELECT data FROM days WHERE date = ?1").bind(date),
    env.DB.prepare("SELECT data FROM lib WHERE key = 'goals'"),
    env.DB.prepare(LAST_WEIGHT_SQL).bind(date),
  ]);
  const d = normDay(dayR.results[0] ? JSON.parse(dayR.results[0].data) : null, date);
  const goals = Object.assign({}, DEFAULT_GOALS, goalsR.results[0] ? JSON.parse(goalsR.results[0].data).values || {} : {});
  const hist = histR.results.reverse().map((x) => ({ date: x.date, act: normDay({ act: JSON.parse(x.act || "{}") }, x.date).act }));
  hist.push({ date, act: d.act });
  const total = (f) => Math.round(d.meals.reduce((s, m) => s + (Number(m[f]) || 0), 0));
  const d0 = new Date(date + "T12:00:00Z"), monday = new Date(d0 - ((d0.getUTCDay() + 6) % 7) * 864e5).toISOString().slice(0, 10);
  return {
    date, today,
    water: d.water || 0, waterGoal: goals.water,
    creatine: !!d.creatine, weight: d.weight ?? null,
    lastWeight: weightR.results[0] ? Number(weightR.results[0].w) : null,
    kcal: total("kcal"), kcalGoal: goals.kcal,
    protein: total("p"), proteinGoal: goals.protein,
    gymWeek: hist.filter((h) => h.date >= monday && h.act.sets.length).length, gymWeekGoal: goals.gymWeek,
    types: Object.entries(GYM_LABEL).map(([k, label]) => ({ k, label })),
    gym: workoutPlan(hist, d, date, today),
    meals: d.meals.slice(-6).map((m) => ({ id: m.id, time: m.time || "", desc: m.desc || "", kcal: Math.round(m.kcal || 0), p: Math.round(m.p || 0) })),
    frequent: await frequent(env, date),
    fin: await finPending(env),
  };
}

// Aplica una acción al documento del día; devuelve un error en texto o null
function applyOp(d, b) {
  const a = d.act;
  switch (b.op) {
    case "water": d.water = Math.max(0, (d.water || 0) + (Number(b.n) || 0)); return null;
    case "creatine": d.creatine = !!b.v; return null;
    case "weight": {
      if (b.kg === null) { d.weight = null; return null; }
      const kg = Number(b.kg);
      if (!(kg >= 20 && kg <= 300)) return "bad_weight";
      d.weight = Math.round(kg * 10) / 10; return null;
    }
    case "gym": if (b.type !== "" && !GYM_LABEL[b.type]) return "bad_type"; a.gym = b.type; return null;
    case "set": {
      const ex = String(b.ex || "").trim().slice(0, 80), reps = Math.round(Number(b.reps)), kg = Math.max(0, Number(b.kg) || 0);
      if (!ex || !(reps >= 1 && reps <= 500)) return "bad_set";
      if (!a.gym && GYM_LABEL[b.type]) a.gym = b.type;
      const now = Date.now(), prev = a.sets.filter((s) => s.t).sort((x, y) => y.t - x.t)[0];
      if (prev && !prev.rest) { const gap = Math.round((now - prev.t) / 1000) - SET_SEC; if (gap > 0 && gap <= REST_MAX) prev.rest = gap; }
      a.sets.push({ id: uid(), ex, kg, reps, ...(kg && (b.unit === "lb" || b.unit === "nivel") ? { unit: b.unit } : {}), ...(b.drop ? { drop: true } : {}), t: now });
      delete a.end;
      return null;
    }
    case "undo": a.sets = a.sets.filter((s) => s.id !== b.id); return null;
    case "end": a.end = Date.now(); return null;
    case "resume": delete a.end; return null;
    default: return "bad_op";
  }
}

export async function reloj(request, env, url) {
  if (request.method === "GET") {
    const date = url.searchParams.get("date") || chileToday();
    if (!DATE_RE.test(date)) return json({ error: "bad_date" }, 400);
    return json(await summary(env, date));
  }
  if (request.method !== "POST") return json({ error: "method" }, 405);
  let b;
  try { b = JSON.parse(await request.text()); } catch { return json({ error: "bad_json" }, 400); }
  const date = b.date || chileToday();
  if (!DATE_RE.test(date)) return json({ error: "bad_date" }, 400);
  // Acciones que no son del documento del día: las aplica el agente (src/agente.js) con su propia lectura-modificación-escritura
  try {
    if (b.op === "fin-cat") {
      await applyProposal(env, { kind: "categoria", args: { mov_id: b.id, categoria: b.cat, alcance: b.scope === "comercio" ? "comercio" : "este" } });
      return json(await summary(env, date));
    }
    if (b.op === "meal-quick") {
      const q = await quickItems(env, b.ref);
      if (!q || !(q.items || []).length) return json({ error: "bad_ref" }, 400);
      await applyProposal(env, { kind: "comida", args: { fecha: date, descripcion: q.descripcion, items: q.items } });
      return json(await summary(env, date));
    }
    if (b.op === "meal-del") {
      await applyProposal(env, { kind: "editar_comida", args: { fecha: date, id: b.id, accion: "borrar" } });
      return json(await summary(env, date));
    }
  } catch (err) {
    return json({ error: String(err.message || err) }, 400);
  }
  // Lee y escribe el día en el servidor, así una acción del reloj no pisa lo que guardaste desde otro dispositivo
  const row = await env.DB.prepare("SELECT data FROM days WHERE date = ?").bind(date).first();
  const d = normDay(row ? JSON.parse(row.data) : null, date);
  const err = applyOp(d, b);
  if (err) return json({ error: err }, 400);
  await env.DB.prepare(
    "INSERT INTO days(date, data, updated_at) VALUES(?1, ?2, datetime('now')) " +
    "ON CONFLICT(date) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at"
  ).bind(date, JSON.stringify(d)).run();
  return json(await summary(env, date));
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
