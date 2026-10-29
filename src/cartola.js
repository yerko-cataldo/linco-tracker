// Cartolas BICE (CSV separado por ";") de la tarjeta de crédito y de la cuenta: lectura y conciliación con las alertas de Visa.

const DATE_RE = /^(\d{2})\/(\d{2})\/(\d{4})$/;
const CUOTA_RE = /^(.*?)\s+(\d{1,2})-(\d{2})\s+CUOTA$/i;
const COMPRA_RE = /^(.*?)\s+COMPRAS$/i;
const DE_RE = /^(\d+)\s+de\s+(\d+)$/i;

const isoDate = (s) => {
  const m = String(s || "").trim().match(DATE_RE);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : null;
};
const clpInt = (s) => {
  const t = String(s || "").replace(/CLP|\$|\s/g, "").replace(/\./g, "");
  return /^-?\d+$/.test(t) ? Number(t) : null;
};

/* Devuelve {inicio, totalCargos, totalAbonos, rows} o null si el texto no es una cartola. */
export function parseCartola(text) {
  const lines = String(text).replace(/^﻿/, "").split(/\r?\n/).map((l) => l.split(";").map((c) => c.trim()));
  let inicio = null, totalAbonos = null, totalCargos = null, head = -1;
  for (let i = 0; i < lines.length; i++) {
    const c = lines[i];
    if (c[0] === "Inicio periodo" && lines[i + 1]) {
      inicio = isoDate(lines[i + 1][0]);
      const ia = c.indexOf("Total Abonos"), ic = c.indexOf("Total Cargos");
      if (ia >= 0) totalAbonos = clpInt(lines[i + 1][ia]);
      if (ic >= 0) totalCargos = clpInt(lines[i + 1][ic]);
    }
    if (c[0] === "Fecha" && c.includes("Detalle")) { head = i; break; }
  }
  if (head < 0) return null;
  const hc = lines[head], iCat = hc.indexOf("Categoria"), iDet = hc.indexOf("Detalle"), iCuo = hc.indexOf("Cuotas");
  const iMon = hc.findIndex((h) => h.startsWith("Monto"));
  if (iDet < 0 || iMon < 0) return null;

  const rows = [], seen = {};
  for (const c of lines.slice(head + 1)) {
    const fecha = isoDate(c[0]);
    if (!fecha) continue;
    const monto = clpInt(c[iMon]);
    if (monto === null) continue;
    const rawDet = c[iDet] || "";
    const pendiente = rawDet.startsWith("*");
    const detalle = rawDet.replace(/^\*\s*/, "").trim();
    let comercio = detalle, tipo, cuota = null, cuotas = null, m;
    if (monto < 0) tipo = "Abono";
    else if ((m = detalle.match(CUOTA_RE))) {
      comercio = m[1].trim(); cuota = Number(m[2]); cuotas = Number(m[3]);
      tipo = cuota === 0 ? "Compra" : "Cuota";
    } else {
      if ((m = detalle.match(COMPRA_RE))) comercio = m[1].trim();
      tipo = "Compra";
      const d = String(c[iCuo] || "").match(DE_RE);
      if (d) { cuota = Number(d[1]); cuotas = Number(d[2]); }
    }
    const base = `${fecha}|${detalle}|${monto}|${c[iCuo] || ""}`;
    seen[base] = (seen[base] || 0) + 1;
    rows.push({
      bancoId: `bice:${base}#${seen[base]}`,
      fecha, comercio, detalle, tipo, monto, cuota, cuotas, pendiente,
      catBanco: (iCat >= 0 && c[iCat]) || null,
    });
  }
  return { inicio, totalCargos, totalAbonos, rows };
}

/* ---------- cartola de la cuenta: solo las compras con la tarjeta de débito ---------- */
export const CUENTA_PREFIX = "bicecta:";
const MESES = { ene: 1, feb: 2, mar: 3, abr: 4, may: 5, jun: 6, jul: 7, ago: 8, sep: 9, sept: 9, oct: 10, nov: 11, dic: 12 };
const LONG_DATE_RE = /^(\d{1,2})\s+([a-z]{3,4})\.?\s+(\d{4})$/i;
const PERIODO_RE = /^(\d{1,2}\s+[a-z]{3,4}\.?\s+\d{4})\s+-\s+(\d{1,2}\s+[a-z]{3,4}\.?\s+\d{4})$/i;
// "Cargo por Compra en HIP LIDER NUNOA   El 23/10/2026  a las  13:37:48., Monto 20.780"
const COMPRA_CTA_RE = /^Cargo por Compra en\s+(.+?)\s+El\s+(\d{2}\/\d{2}\/\d{4})\s+a las\s+(\d{2}:\d{2})/i;

const longDate = (s) => {
  const m = String(s || "").trim().match(LONG_DATE_RE);
  const mes = m && MESES[m[2].toLowerCase()];
  return mes ? `${m[3]}-${String(mes).padStart(2, "0")}-${m[1].padStart(2, "0")}` : null;
};

/* Devuelve {desde, hasta, totalCargos, cargos, omitidos, rows} o null si el texto no es una cartola de cuenta.
   rows: compras con débito, con la fecha y hora de la compra; omitidos: los demás movimientos. */
export function parseCuenta(text) {
  const lines = String(text).replace(/^﻿/, "").split(/\r?\n/).map((l) => l.split(";").map((c) => c.trim()));
  let desde = null, hasta = null, totalCargos = null, head = -1;
  for (let i = 0; i < lines.length; i++) {
    const c = lines[i], first = c.find(Boolean) || "";
    const p = first.match(PERIODO_RE);
    if (p) [desde, hasta] = [longDate(p[1]), longDate(p[2])].sort();
    if (/^total cargos$/i.test(first) && lines[i + 1]) totalCargos = clpInt(lines[i + 1].find(Boolean));
    if (c.includes("Fecha") && c.some((h) => /^Descripci/i.test(h))) { head = i; break; }
  }
  if (head < 0) return null;
  const hc = lines[head], iFec = hc.indexOf("Fecha"), iDes = hc.findIndex((h) => /^Descripci/i.test(h));
  const iCat = hc.findIndex((h) => /^Categor/i.test(h)), iMon = hc.findIndex((h) => h.startsWith("Monto"));
  if (iMon < 0) return null;

  const rows = [], seen = {};
  let cargos = 0, omitidos = 0;
  for (const c of lines.slice(head + 1)) {
    const fechaCta = longDate(c[iFec]), monto = clpInt(c[iMon]);
    if (!fechaCta || monto === null) continue;
    const cargo = iCat < 0 || /^cargo/i.test(c[iCat] || "");
    if (cargo) cargos += monto;
    const detalle = (c[iDes] || "").replace(/\s+/g, " ").trim();
    const m = cargo && (c[iDes] || "").match(COMPRA_CTA_RE);
    if (!m) { omitidos++; continue; }
    const base = `${detalle}|${monto}`;
    seen[base] = (seen[base] || 0) + 1;
    rows.push({
      bancoId: `${CUENTA_PREFIX}${base}#${seen[base]}`,
      fecha: isoDate(m[2]) || fechaCta, hora: m[3], comercio: m[1].trim(), detalle,
      tipo: "Compra", monto, cuota: null, cuotas: null, pendiente: false, catBanco: null,
    });
  }
  return { desde, hasta, totalCargos, cargos, omitidos, rows };
}

const dayDiff = (a, b) => Math.abs(Date.parse(a) - Date.parse(b)) / 864e5;

/* Plan de conciliación: {update: [[movId, row]], insert: [row], refresh: [row]}.
   1. Fila ya importada (mismo bancoId): se actualiza.
   2. Compra con alerta del mismo monto a 3 días o menos: se une a la alerta más cercana.
   3. Compra con una sola alerta a 2 días o menos y monto a ±5%: se une a esa alerta.
   4. Resto: movimiento nuevo de fuente cartola. */
export function planConciliation(rows, existing) {
  const byBanco = new Map(existing.filter((e) => e.banco_id).map((e) => [e.banco_id, e]));
  const free = existing.filter((e) => !e.banco_id && e.fuente === "alerta" && e.moneda === "CLP");
  const used = new Set(), plan = { update: [], insert: [], refresh: [] };
  const pick = (cands) => cands.sort((a, b) => a.d - b.d)[0];

  for (const r of rows) {
    if (byBanco.has(r.bancoId)) { plan.refresh.push(r); continue; }
    let hit = null;
    if (r.tipo === "Compra") {
      const near = free.filter((e) => !used.has(e.id)).map((e) => ({ e, d: dayDiff(e.fecha, r.fecha) }));
      hit = pick(near.filter((x) => x.d <= 3 && x.e.monto === r.monto));
      if (!hit) {
        const fuzzy = near.filter((x) => x.d <= 2 && Math.abs(x.e.monto - r.monto) <= 0.05 * r.monto);
        if (fuzzy.length === 1) hit = fuzzy[0];
      }
    }
    if (hit) { used.add(hit.e.id); plan.update.push([hit.e.id, r]); }
    else plan.insert.push(r);
  }
  return plan;
}
