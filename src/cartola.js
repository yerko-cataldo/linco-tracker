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

/* ---------- cartola de la cuenta: compras con débito, transferencias, pagos de cuentas, cargos del banco y abonos recibidos ---------- */
export const CUENTA_PREFIX = "bicecta:";
const MESES = { ene: 1, feb: 2, mar: 3, abr: 4, may: 5, jun: 6, jul: 7, ago: 8, sep: 9, sept: 9, oct: 10, nov: 11, dic: 12 };
const LONG_DATE_RE = /^(\d{1,2})\s+([a-z]{3,4})\.?\s+(\d{4})$/i;
const PERIODO_RE = /^(\d{1,2}\s+[a-z]{3,4}\.?\s+\d{4})\s+-\s+(\d{1,2}\s+[a-z]{3,4}\.?\s+\d{4})$/i;
// "Cargo por Compra en HIP LIDER NUNOA   El 23/10/2026  a las  13:37:48., Monto 20.780"
const COMPRA_CTA_RE = /^Cargo por Compra en\s+(.+?)\s+El\s+(\d{2}\/\d{2}\/\d{4})\s+a las\s+(\d{2}:\d{2})/i;
// "Transferencia de <titular> Rut <rut> desde <banco> a <destinatario> Rut <rut> a <cuenta>, el 2026-10-28 a las 14:24 hrs."
const TRANSF_RE = /^Transferencia de .+? Rut ([\d.]+-[\dk]) desde .+? a (.+?) Rut ([\d.]+-[\dk]) a .+?, el (\d{4}-\d{2}-\d{2}) a las (\d{2}:\d{2})/i;
// "Cargo por pago Cuentas de Servicio vía internet, operación realizada a las 11:08 el 12/10/2026, …"
const PAGO_RE = /^Cargo por pago (.+?)\s+v[ií]a internet/i;
const BANCO_RE = /^Cargo (impuesto|intereses|comisi[oó]n|mantenci[oó]n)\b/i;
const PAGO_TARJETA_RE = /^Cargo por abono\/pago de tarjeta de cr[eé]dito/i;
// "Abono por transferencia de NOMBRE Rut 12.690.841-5 desde Santander el 29/10/2026 a las 06:46"
const ABONO_RE = /^Abono por transferencia de (.+?) Rut ([\d.]+-[\dk]) desde .+? el (\d{2}\/\d{2}\/\d{4}) a las (\d{2}:\d{2})/i;
// "Abono por Transferencia via CCA, originador Rut: 96572800-7 Nombre: ISAPRE BANMEDICA (N.Ref: …)."
const ABONO_CCA_RE = /^Abono por Transferencia v[ií]a CCA, originador Rut: ([\dk.-]+) Nombre: (.+?)\s*\(/i;
export const rutKey = (r) => r.replace(/\./g, "").toLowerCase();
/* RUT del titular: el de origen de una transferencia enviada, o null. */
export const rutOrigen = (desc) => { const m = String(desc || "").replace(/\s+/g, " ").match(TRANSF_RE); return m ? m[1] : null; };
const DMY_RE = /(\d{2}\/\d{2}\/\d{4})/;
const HM_RE = /\b(\d{2}:\d{2})\b/;

export const longDate = (s) => {
  const m = String(s || "").trim().match(LONG_DATE_RE);
  const mes = m && MESES[m[2].toLowerCase()];
  return mes ? `${m[3]}-${String(mes).padStart(2, "0")}-${m[1].padStart(2, "0")}` : null;
};

/* Lectura de un cargo de la cuenta: {tipo, comercio, fecha, hora}, "omitir" o null si no se reconoce.
   1. Compra con débito: comercio, fecha y hora de la compra.
   2. Transferencia a otra persona: el destinatario es el comercio; una transferencia a otra cuenta propia (mismo RUT) se omite.
   3. Pago de cuenta por internet: el servicio es el comercio.
   4. Impuesto, intereses, comisión o mantención: cargo del banco.
   5. Pago de la tarjeta de crédito: se omite (sus compras ya están en la cartola de crédito). */
function cuentaCargo(desc, fechaCta) {
  let m;
  if ((m = desc.match(COMPRA_CTA_RE))) return { tipo: "Compra", comercio: m[1].trim(), fecha: isoDate(m[2]) || fechaCta, hora: m[3] };
  if ((m = desc.match(TRANSF_RE))) {
    if (m[1].replace(/\./g, "").toLowerCase() === m[3].replace(/\./g, "").toLowerCase()) return "omitir";
    return { tipo: "Transferencia", comercio: m[2].trim(), fecha: m[4], hora: m[5] };
  }
  if ((m = desc.match(PAGO_RE))) {
    const f = desc.match(DMY_RE), h = desc.match(HM_RE);
    return { tipo: "Pago de cuenta", comercio: m[1].replace(/\s+Portal\s+\S+$/i, "").trim(), fecha: (f && isoDate(f[1])) || fechaCta, hora: h ? h[1] : null };
  }
  if (BANCO_RE.test(desc)) return { tipo: "Cargo del banco", comercio: desc.replace(/^Cargo\s+/i, "").replace(/[.\s]+$/, ""), fecha: fechaCta, hora: null };
  if (PAGO_TARJETA_RE.test(desc)) return "omitir";
  return null;
}

/* Lectura de un abono de la cuenta: transferencia recibida de otra persona o institución (posible devolución), o "omitir".
   Se omiten las transferencias desde una cuenta propia (RUT del titular), las remuneraciones y los abonos no reconocidos. */
function cuentaAbono(desc, fechaCta, propios) {
  let m;
  if ((m = desc.match(ABONO_RE))) {
    if (propios.has(rutKey(m[2]))) return "omitir";
    return { tipo: "Transferencia recibida", comercio: m[1].trim(), fecha: isoDate(m[3]) || fechaCta, hora: m[4] };
  }
  if ((m = desc.match(ABONO_CCA_RE))) {
    if (propios.has(rutKey(m[1]))) return "omitir";
    return { tipo: "Transferencia recibida", comercio: m[2].trim(), fecha: fechaCta, hora: null };
  }
  return "omitir";
}

/* Devuelve {desde, hasta, totalCargos, cargos, omitidos, desconocidos, rows} o null si el texto no es una cartola de cuenta.
   rows: cargos reconocidos por cuentaCargo() y abonos de cuentaAbono() (monto negativo);
   omitidos: movimientos que se omiten; desconocidos: descripciones de cargos no reconocidos. */
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

  const rows = [], seen = {}, desconocidos = [];
  let cargos = 0, omitidos = 0;
  // RUT del titular: el de origen de las transferencias enviadas
  const propios = new Set();
  for (const c of lines.slice(head + 1)) {
    const t = (c[iDes] || "").replace(/\s+/g, " ").match(TRANSF_RE);
    if (t) propios.add(rutKey(t[1]));
  }
  for (const c of lines.slice(head + 1)) {
    const fechaCta = longDate(c[iFec]), monto = clpInt(c[iMon]);
    if (!fechaCta || monto === null) continue;
    const cargo = iCat < 0 || /^cargo/i.test(c[iCat] || "");
    if (cargo) cargos += monto;
    const detalle = (c[iDes] || "").replace(/\s+/g, " ").trim();
    const r = cargo ? cuentaCargo(detalle, fechaCta) : cuentaAbono(detalle, fechaCta, propios);
    if (r === "omitir") { omitidos++; continue; }
    if (!r) { desconocidos.push(detalle); continue; }
    const base = `${detalle}|${monto}`;
    seen[base] = (seen[base] || 0) + 1;
    rows.push({
      bancoId: `${CUENTA_PREFIX}${base}#${seen[base]}`, ...r, detalle,
      monto: cargo ? monto : -monto, cuota: null, cuotas: null, pendiente: false, catBanco: null,
    });
  }
  return { desde, hasta, totalCargos, cargos, omitidos, desconocidos, rows };
}

const dayDiff = (a, b) => Math.abs(Date.parse(a) - Date.parse(b)) / 864e5;

const nameKey = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[^a-z0-9]/g, "");

/* Plan de conciliación: {update: [[movId, row]], insert: [row], refresh: [row]}.
   1. Fila ya importada (mismo bancoId): se actualiza.
   2. Compra con alerta del mismo monto a 3 días o menos: se une a la alerta más cercana.
   3. Compra con una sola alerta a 2 días o menos y monto a ±5%: se une a esa alerta.
   4. Transferencia con correo del banco del mismo monto a 3 días o menos: se une al correo del mismo destinatario o, si no hay, al más cercano.
   5. Resto: movimiento nuevo de fuente cartola. */
export function planConciliation(rows, existing) {
  const byBanco = new Map(existing.filter((e) => e.banco_id).map((e) => [e.banco_id, e]));
  const free = existing.filter((e) => !e.banco_id && (e.fuente === "alerta" || e.fuente === "correo") && e.moneda === "CLP");
  const used = new Set(), plan = { update: [], insert: [], refresh: [] };
  const pick = (cands) => cands.sort((a, b) => a.d - b.d)[0];

  for (const r of rows) {
    if (byBanco.has(r.bancoId)) { plan.refresh.push(r); continue; }
    let hit = null;
    if (r.tipo === "Transferencia") {
      const near = free.filter((e) => e.fuente === "correo" && e.tipo === "Transferencia" && !used.has(e.id) && e.monto === r.monto)
        .map((e) => ({ e, d: dayDiff(e.fecha, r.fecha), n: nameKey(e.comercio) === nameKey(r.comercio) ? 0 : 1 }))
        .filter((x) => x.d <= 3);
      hit = near.sort((a, b) => a.n - b.n || a.d - b.d)[0] || null;
    } else if (r.tipo === "Compra") {
      const near = free.filter((e) => e.fuente === "alerta" && !used.has(e.id)).map((e) => ({ e, d: dayDiff(e.fecha, r.fecha) }));
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
