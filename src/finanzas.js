// Finanzas en el Worker: categoría de un movimiento y gasto por categoría, para el agente y el clasificador de compras.
// Copia de finCatInfoCalc(), finBaseRule(), isPurchase() y finCatTotals() de public/index.html: si cambias esa lógica en la web, cambia esta.
// Diferencia: aquí la categoría propia del movimiento (movimientos.cat, migración 0008) y la sugerida por el agente (cat_sug)
// entran igual que en la web, que también las lee.

export const FIN_CATS_BASE = ["Supermercado", "Comida y delivery", "Restaurantes y bares", "Transporte", "Arriendo y gastos comunes", "Hogar", "Salud", "Deporte", "Mascotas", "Entretención", "Suscripciones", "Ropa", "Compras", "Educación", "Viajes", "Servicios", "Transferencias", "Comisiones e intereses", "Otros", "Inversiones y ahorro"];
const FIN_NOSPEND_BASE = ["Inversiones y ahorro"];
const FIN_SPEND = ["compra", "transferencia", "pago de cuenta", "cargo del banco"];
const BANK_CATS = { "Hogar": "Hogar", "Entretenimiento": "Entretención", "Shopping": "Compras", "Servicios Profesionales": "Servicios", "Autos Y Transporte": "Transporte", "Salud Y Bienestar": "Salud", "Viajes": "Viajes", "Servicios Financieros": "Servicios", "Otros Gastos": "Otros" };
const FIN_BASE_RULES = [
  ["Inversiones y ahorro", ["fintual", "racional", "fondos mutuos", "deposito a plazo", "apv", "agf", "buda", "binance", "criptomarkt", "orionx"]],
  ["Mascotas", ["veterinaria", "veterinario", "petshop", "pet", "mascota", "superzoo", "jardin zoo"]],
  ["Arriendo y gastos comunes", ["edificio", "condominio", "comunidad", "administracion", "gastos comunes", "arriendo"]],
  ["Comisiones e intereses", ["sobregiro", "intereses", "comision", "mantencion"]],
  ["Servicios", ["cuentas de servicio"]],
  ["Comida y delivery", ["uber eats", "rappi", "pedidosya", "justo", "didi food", "cornershop"]],
  ["Supermercado", ["unimarc", "lider", "lidercl", "jumbo", "tottus", "santa isabel", "acuenta", "alvi", "minimarket", "market", "carniceria", "panaderia", "pasteleria", "emporio", "verduleria", "almacen", "tostaduria", "feria", "fruteria"]],
  ["Restaurantes y bares", ["bar", "restaurant", "restobar", "cafe", "cafeteria", "sushi", "pizza", "pizzeria", "cerveceria", "birras", "sangucheria", "fuente de soda", "starbucks", "juan maestro", "dominos", "mcdonalds", "burger"]],
  ["Transporte", ["uber trip", "uber rides", "cabify", "didi", "metro", "bip", "copec", "shell", "aramco", "petrobras", "estacionamiento", "parking", "autopista", "tag"]],
  ["Salud", ["farmacia", "salcobrand", "cruz verde", "ahumada", "dr simi", "clinica", "dental", "laboratorio", "optica"]],
  ["Deporte", ["easycancha", "wellhub", "gympass", "smartfit", "sportlife", "pacific", "gimnasio", "gym", "decathlon"]],
  ["Suscripciones", ["netflix", "spotify", "disney", "hbo", "youtube", "apple com", "icloud", "google", "openai", "chatgpt", "prime video", "amazon prime"]],
  ["Compras", ["mercadolibre", "falabella", "paris", "ripley", "aliexpress", "temu", "shein", "amazon", "hites", "abcdin"]],
  ["Entretención", ["cine", "cinemark", "cineplanet", "puntoticket", "ticketmaster", "passline", "buin zoo"]],
  ["Hogar", ["sodimac", "homecenter", "easy", "ikea", "construmart", "imperial"]],
];
// Comercios genéricos de comida: la regla base los manda a Supermercado, pero pueden ser comida para llevar; el clasificador pregunta
export const FOOD_AMBIGUOUS = ["almacen", "minimarket", "market", "emporio", "panaderia", "pasteleria", "botilleria", "kiosko", "kiosco", "local", "comercial", "distribuidora", "sanguch", "completos", "empanadas"];
export const FOOD_CATS = ["Supermercado", "Comida y delivery", "Restaurantes y bares"];

export const norm = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
export const finKey = (s) => norm(s).replace(/[^a-z0-9]/g, "");
const finTokens = (s) => norm(s).replace(/^(merpago\*?|payu\s+|mp\s*\*)/, "").split(/[^a-z0-9]+/).filter((t) => t.length >= 4 && !["compras", "ltda", "chile"].includes(t));
const finSameMerchant = (a, b) => a === b || (Math.min(a.length, b.length) >= 8 && (a.startsWith(b) || b.startsWith(a)));
export const isIncoming = (m) => norm(m.tipo) === "transferencia recibida";

export function finBaseRule(comercio) {
  const words = norm(comercio).split(/[^a-z0-9]+/).filter(Boolean), joined = words.join("");
  for (const [cat, kws] of FIN_BASE_RULES) for (const kw of kws) {
    const k = norm(kw).replace(/[^a-z0-9]/g, "");
    if (k.length < 6 && !kw.includes(" ") ? words.includes(k) : joined.includes(k)) return cat;
  }
  return null;
}

// Contexto de categorías desde lib.fin y los movimientos (para la categoría del banco del mismo comercio)
export function finContext(fin, movs) {
  fin = fin || {};
  const map = {};
  for (const [k, v] of Object.entries(fin.cats || {})) if (v) map[finKey(k)] = v;
  const myCats = (fin.myCats || []).filter((c) => c && c.name);
  const cats = [...new Set([...FIN_CATS_BASE, ...myCats.map((c) => c.name)])];
  const noSpend = new Set([...FIN_NOSPEND_BASE, ...myCats.filter((c) => c.spend === false).map((c) => c.name)]);
  const bankByKey = [];
  for (const m of movs || []) if (m.cat_banco) bankByKey.push([finKey(m.comercio), m.cat_banco]);
  return { fin, map, cats, noSpend, rules: fin.rules || [], refunds: fin.refunds || {}, bankByKey };
}

// {cat, src}: la del movimiento, comercio, regla, agente, base, sugerida (comercios parecidos) o banco
export function catInfo(m, ctx) {
  const rf = ctx.refunds[m.id];
  if (rf && rf.cat) return { cat: rf.cat, src: "devolucion" };
  if (isIncoming(m)) return { cat: "", src: "" };
  if (m.cat) return { cat: m.cat, src: "movimiento" };
  const k = finKey(m.comercio);
  const pre = Object.keys(ctx.map).find((x) => finSameMerchant(x, k));
  if (pre) return { cat: ctx.map[pre], src: "comercio" };
  const rule = ctx.rules.find((r) => r.pat && k.includes(finKey(r.pat)));
  if (rule) return { cat: rule.cat, src: "regla" };
  if (m.cat_sug) return { cat: m.cat_sug, src: "agente" };
  const base = finBaseRule(m.comercio);
  if (base) return { cat: base, src: "base" };
  if (norm(m.tipo) === "transferencia") return { cat: "Transferencias", src: "base" };
  const votes = {};
  for (const t of finTokens(m.comercio)) for (const [x, c] of Object.entries(ctx.map)) if (x.includes(t)) votes[c] = (votes[c] || 0) + 1;
  const best = Object.entries(votes).sort((a, b) => b[1] - a[1])[0];
  if (best) return { cat: best[0], src: "sugerida" };
  const bank = m.cat_banco || (ctx.bankByKey.find(([x]) => finSameMerchant(x, k)) || [])[1];
  if (BANK_CATS[bank]) return { cat: BANK_CATS[bank], src: "banco" };
  return { cat: "", src: "" };
}

export const isPurchase = (m, ctx) => m.moneda === "CLP" && FIN_SPEND.includes(norm(m.tipo)) && !ctx.noSpend.has(catInfo(m, ctx).cat);

// Gasto por categoría: compras más devoluciones (abonos marcados, en negativo); cada producto detallado va a su categoría
export function spendRows(movs, ctx, det = {}) {
  const out = [];
  const byId = new Map(movs.map((m) => [m.id, m]));
  for (const m of movs) {
    if (isPurchase(m, ctx)) {
      const base = catInfo(m, ctx).cat || "Sin categoría";
      let rest = m.monto;
      for (const it of (det[m.id] || {}).items || []) {
        if (!it.amt) continue;
        out.push({ m, cat: it.cat || base, monto: it.amt });
        rest -= it.amt;
      }
      if (rest > 0) out.push({ m, cat: base, monto: rest });
    } else if (isIncoming(m) && ctx.refunds[m.id]) {
      const rf = ctx.refunds[m.id], of = rf.of && byId.get(rf.of);
      out.push({ m, cat: rf.cat || (of ? catInfo(of, ctx).cat : "") || "Sin categoría", monto: -Math.abs(m.monto) });
    }
  }
  return out;
}
