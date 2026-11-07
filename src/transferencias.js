// Transferencias recurrentes (lib.fin.transfers): si ya se hicieron en su periodo y los avisos push.
// La misma regla está en el front (trPeriod(), trState() en public/index.html); si cambias una, cambia la otra.
//   transfer = {id, name, freq: "semanal" | "mensual", day, hour, amount, max, rut, banco, cuenta, since, skip: [vencimientos]}
//   day: getDay() (0 = domingo) si es semanal; día del mes (1–31, o el último si el mes es más corto) si es mensual.
//   Monto: entre amount y max; sin max, amount ± 10%. Hecha: lo transferido en el periodo llega al mínimo.
//   Periodo: desde LEAD días antes del vencimiento hasta el día anterior al mismo punto del siguiente
//   (pagar el arriendo el 29 cuenta para el 1 del mes siguiente).
//   Destinatario: el RUT del comprobante (si la transferencia tiene rut) o un nombre con todas las palabras de name.

import { sendPush } from "./push.js";

const DOW = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
const MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
export const LEAD = { semanal: 3, mensual: 7 };
const REMIND_DAYS = 6; // avisos diarios hasta 6 días después del vencimiento

const pad = (n) => String(n).padStart(2, "0");
const addDays = (ymd, n) => {
  const d = new Date(ymd + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};
const dow = (ymd) => new Date(ymd + "T00:00:00Z").getUTCDay();
const dueIn = (t, y, m) => `${y}-${pad(m)}-${pad(Math.min(t.day, new Date(Date.UTC(y, m, 0)).getUTCDate()))}`;

/* Último vencimiento en o antes de la fecha */
function lastDue(t, ymd) {
  if (t.freq !== "mensual") return addDays(ymd, -((dow(ymd) - t.day + 7) % 7));
  let [y, m] = ymd.split("-").map(Number);
  const d = dueIn(t, y, m);
  if (d <= ymd) return d;
  if (--m === 0) { m = 12; y--; }
  return dueIn(t, y, m);
}
function nextDue(t, due) {
  if (t.freq !== "mensual") return addDays(due, 7);
  let [y, m] = due.split("-").map(Number);
  if (++m === 13) { m = 1; y++; }
  return dueIn(t, y, m);
}
export function trPeriod(t, ymd) {
  const lead = LEAD[t.freq] ?? LEAD.semanal, due = lastDue(t, addDays(ymd, lead));
  return { due, start: addDays(due, -lead), end: addDays(nextDue(t, due), -lead - 1) };
}
export function trRange(t) {
  const a = Number(t.amount) || 0, b = Number(t.max) || 0;
  return b > a ? [a, b] : [Math.round(a * 0.9), Math.round(a * 1.1)];
}

const words = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").split(/[^a-z0-9]+/).filter(Boolean);
const rutKey = (s) => String(s || "").replace(/[^0-9kK]/g, "").toUpperCase();
export function trMatches(t, mov) {
  if (t.rut && mov.rut_destino) return rutKey(t.rut) === rutKey(mov.rut_destino);
  const want = words(t.name), have = new Set(words(mov.comercio));
  return want.length > 0 && want.every((w) => have.has(w));
}

const clp = (n) => "$" + String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const amountLabel = (t) => (Number(t.max) > Number(t.amount) ? `${clp(t.amount)} a ${clp(t.max)}` : `≈ ${clp(t.amount)}`);
const periodLabel = (t) => (t.freq === "mensual" ? "este mes" : "esta semana");
const dueLabel = (t, due) => (t.freq === "mensual" ? `el ${Number(due.slice(8))} de ${MONTHS[Number(due.slice(5, 7)) - 1]}` : `el ${DOW[dow(due)]}`);

/* Fecha y hora de Chile */
function chileNow() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Santiago", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date());
  const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, hour: Number(p.hour) };
}

async function transfers(env) {
  const row = await env.DB.prepare("SELECT data FROM lib WHERE key = 'fin'").first();
  const list = row ? JSON.parse(row.data).values?.transfers : null;
  return Array.isArray(list) ? list.filter((t) => t && t.id && t.name && Number(t.amount) > 0) : [];
}

/* Transferencias a ese destinatario en el periodo, de la más nueva a la más antigua */
async function movsIn(env, t, p) {
  const rows = await env.DB.prepare(
    "SELECT fecha, comercio, monto, rut_destino, banco_destino FROM movimientos WHERE tipo = 'Transferencia' AND fecha >= ? AND fecha <= ? ORDER BY fecha DESC"
  ).bind(p.start, p.end).all();
  return rows.results.filter((r) => trMatches(t, r));
}

/* Datos de la cuenta de destino: los guardados o los del último comprobante */
async function accountLine(env, t) {
  let { rut, banco } = t;
  if (!rut || !banco) {
    const rows = await env.DB.prepare(
      "SELECT comercio, rut_destino, banco_destino FROM movimientos WHERE tipo = 'Transferencia' AND rut_destino IS NOT NULL ORDER BY fecha DESC LIMIT 200"
    ).all();
    const last = rows.results.find((r) => trMatches({ ...t, rut: null }, r));
    rut ||= last?.rut_destino;
    banco ||= last?.banco_destino;
  }
  return [rut && `RUT ${rut}`, banco, t.cuenta && `cuenta ${t.cuenta}`].filter(Boolean).join(" · ");
}

/* Cron cada hora: desde el vencimiento a la hora del aviso, y hasta REMIND_DAYS días después, un aviso por día mientras falte.
   push_log evita repetir el aviso del día; si no se entregó a ningún dispositivo, se reintenta en la hora siguiente. */
export async function remindTransfers(env) {
  const list = await transfers(env);
  if (!list.length) return;
  const now = chileNow();
  for (const t of list) {
    const p = trPeriod(t, now.date);
    if ((t.skip || []).includes(p.due) || now.date < p.due || now.date > addDays(p.due, REMIND_DAYS)) continue;
    if (now.date === p.due && now.hour < (Number(t.hour) || 0)) continue;
    const paid = (await movsIn(env, t, p)).reduce((s, r) => s + r.monto, 0), [lo] = trRange(t);
    if (paid >= lo) continue;
    const key = `tr:${t.id}:${now.date}`;
    const ins = await env.DB.prepare("INSERT OR IGNORE INTO push_log (key) VALUES (?)").bind(key).run();
    if (!ins.meta.changes) continue;
    const account = await accountLine(env, t);
    const rest = paid > 0 ? ` Ya van ${clp(paid)}.` : "";
    const msg = now.date === p.due
      ? { title: `Hoy toca transferir a ${t.name}`, body: `${amountLabel(t)}.${rest}${account ? "\n" + account : ""}` }
      : { title: `Falta la transferencia a ${t.name}`, body: `${amountLabel(t)}; tocaba ${dueLabel(t, p.due)}.${rest}${account ? "\n" + account : ""}` };
    const sent = await sendPush(env, { ...msg, tag: `tr-${t.id}`, url: "/?tab=finanzas" });
    if (!sent) await env.DB.prepare("DELETE FROM push_log WHERE key = ?").bind(key).run();
  }
}

/* Al llegar el comprobante de una transferencia a un destinatario configurado: avisa que quedó registrada y si calza con el monto. */
export async function notifyTransfer(env, mv) {
  const t = (await transfers(env)).find((x) => trMatches(x, mv));
  if (!t) return;
  const p = trPeriod(t, mv.fecha), paid = (await movsIn(env, t, p)).reduce((s, r) => s + r.monto, 0), [lo, hi] = trRange(t);
  const body = (t.skip || []).includes(p.due) ? `La tenías marcada para omitir ${periodLabel(t)}.`
    : paid < lo ? `Faltan unos ${clp(lo - paid)} para lo de ${periodLabel(t)} (${amountLabel(t)}).`
    : paid > hi ? `Listo ${periodLabel(t)}; es más de lo habitual (${amountLabel(t)}).`
    : `Listo: es lo de ${periodLabel(t)}.`;
  await sendPush(env, { title: `Transferencia a ${t.name}: ${clp(mv.monto)}`, body, tag: `tr-${t.id}`, url: "/?tab=finanzas" });
}
