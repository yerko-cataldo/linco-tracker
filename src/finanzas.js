// Finanzas en el Worker: categoría de un movimiento y gasto por categoría, para el agente y el clasificador de compras.
// Copia de finCatInfoCalc(), finBaseRule(), isPurchase() y finCatTotals() de public/index.html: si cambias esa lógica en la web, cambia esta.
// Diferencia: aquí la categoría propia del movimiento (movimientos.cat, migración 0008) y la sugerida por el agente (cat_sug)
// entran igual que en la web, que también las lee.

export const FIN_CATS_BASE = ["Supermercado", "Comida y delivery", "Restaurantes y bares", "Transporte", "Arriendo y gastos comunes", "Hogar", "Luz", "Agua", "Gas", "Celular e internet", "Salud", "Deporte", "Mascotas", "Entretención", "Suscripciones", "Ropa", "Compras", "Educación", "Viajes", "Servicios", "Transferencias", "Comisiones e intereses", "Otros", "Inversiones y ahorro"];
const FIN_NOSPEND_BASE = ["Inversiones y ahorro"];
const FIN_SPEND = ["compra", "transferencia", "pago de cuenta", "cargo del banco"];
const BANK_CATS = { "Hogar": "Hogar", "Entretenimiento": "Entretención", "Shopping": "Compras", "Servicios Profesionales": "Servicios", "Autos Y Transporte": "Transporte", "Salud Y Bienestar": "Salud", "Viajes": "Viajes", "Servicios Financieros": "Servicios", "Otros Gastos": "Otros" };
const FIN_BASE_RULES = [
  ["Inversiones y ahorro", ["fintual", "racional", "fondos mutuos", "deposito a plazo", "apv", "agf", "buda", "binance", "criptomarkt", "orionx"]],
  ["Mascotas", ["veterinaria", "veterinario", "petshop", "pet", "mascota", "superzoo", "jardin zoo"]],
  ["Arriendo y gastos comunes", ["edificio", "condominio", "comunidad", "administracion", "gastos comunes", "arriendo"]],
  ["Comisiones e intereses", ["sobregiro", "intereses", "comision", "mantencion"]],
  ["Luz", ["enel", "cge", "chilquinta", "saesa", "frontel", "luz osorno"]],
  ["Agua", ["aguas andinas", "esval", "essbio", "nuevosur", "aguas del valle", "smapa"]],
  ["Gas", ["metrogas", "lipigas", "abastible", "gasco", "gasvalpo"]],
  ["Celular e internet", ["entel", "movistar", "wom", "claro", "vtr", "gtd", "mundo pacifico", "virgin mobile", "simple"]],
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

/* Subcategorías (copia de SUB_BASE, SUB_RULES y finSubInfo() de la web): la del movimiento (movimientos.sub) → la recordada para el
   comercio en esa categoría (lib.fin.subOf) → la sugerida por el comercio. Solo vale si está en el catálogo de la categoría. */
export const SUB_BASE = {
  "Supermercado": ["Despensa", "Frutas y verduras", "Carnes y pescados", "Lácteos y huevos", "Panadería", "Bebidas", "Aseo y limpieza", "Higiene personal"],
  "Comida y delivery": ["Almuerzo", "Cena", "Desayuno o café", "Antojo"],
  "Restaurantes y bares": ["Almuerzo", "Cena", "Café", "Bar y copete", "Salida con amigos"],
  "Transporte": ["Uber o taxi", "Micro y metro", "Bencina", "Estacionamiento", "Peajes y TAG", "Bicicleta", "Mantención del auto"],
  "Arriendo y gastos comunes": ["Arriendo", "Gastos comunes", "Dividendo"],
  "Hogar": ["Muebles", "Decoración", "Ferretería", "Electrodomésticos", "Limpieza", "Reparaciones"],
  "Celular e internet": ["Plan celular", "Internet hogar", "TV cable"],
  "Salud": ["Farmacia", "Consulta médica", "Dentista", "Exámenes", "Psicólogo", "Isapre o Fonasa", "Óptica"],
  "Deporte": ["Gimnasio", "Canchas", "Clases", "Equipamiento", "Inscripciones"],
  "Mascotas": ["Comida", "Premios", "Juguetes", "Ropa y accesorios", "Veterinario", "Peluquería", "Remedios"],
  "Entretención": ["Cine", "Conciertos y eventos", "Juegos", "Libros", "Salidas"],
  "Suscripciones": ["YouTube Premium", "Spotify", "Netflix", "Google One", "iCloud", "Disney+", "Max", "Prime Video", "ChatGPT"],
  "Ropa": ["Ropa", "Zapatos", "Accesorios"],
  "Compras": ["Tecnología", "Regalos", "Compras online"],
  "Educación": ["Cursos", "Libros", "Matrícula y arancel", "Materiales"],
  "Viajes": ["Pasajes", "Alojamiento", "Comida en viaje", "Tours y panoramas", "Transporte en viaje"],
  "Servicios": ["Profesionales", "Trámites"],
  "Transferencias": ["Familia", "Amigos", "Pagos"],
  "Comisiones e intereses": ["Comisiones", "Intereses", "Impuestos", "Seguros"],
  "Inversiones y ahorro": ["Fintual", "APV", "Depósito a plazo", "Acciones", "Cripto"]
};
const SUB_RULES = [
  ["Suscripciones", "YouTube Premium", ["youtube"]], ["Suscripciones", "Spotify", ["spotify"]], ["Suscripciones", "Netflix", ["netflix"]],
  ["Suscripciones", "Google One", ["google one", "google storage", "googleone"]], ["Suscripciones", "iCloud", ["icloud", "apple com bill"]],
  ["Suscripciones", "Disney+", ["disney"]], ["Suscripciones", "Max", ["hbo", "max com"]], ["Suscripciones", "Prime Video", ["prime video", "amazon prime"]],
  ["Suscripciones", "ChatGPT", ["openai", "chatgpt"]],
  ["Transporte", "Uber o taxi", ["uber trip", "uber rides", "cabify", "didi", "taxi"]], ["Transporte", "Bencina", ["copec", "shell", "aramco", "petrobras"]],
  ["Transporte", "Micro y metro", ["metro", "bip"]], ["Transporte", "Estacionamiento", ["estacionamiento", "parking"]], ["Transporte", "Peajes y TAG", ["autopista", "tag"]],
  ["Restaurantes y bares", "Café", ["starbucks", "cafe", "cafeteria", "juan valdez"]], ["Restaurantes y bares", "Bar y copete", ["bar", "cerveceria", "birras", "restobar"]],
  ["Salud", "Farmacia", ["farmacia", "salcobrand", "cruz verde", "ahumada", "dr simi"]], ["Salud", "Dentista", ["dental"]], ["Salud", "Óptica", ["optica"]],
  ["Salud", "Exámenes", ["laboratorio"]],
  ["Deporte", "Gimnasio", ["smartfit", "sportlife", "pacific", "gimnasio", "gym", "wellhub", "gympass"]], ["Deporte", "Canchas", ["easycancha"]],
  ["Mascotas", "Veterinario", ["veterinaria", "veterinario"]],
  ["Entretención", "Cine", ["cine", "cinemark", "cineplanet"]], ["Entretención", "Conciertos y eventos", ["puntoticket", "ticketmaster", "passline"]],
  ["Celular e internet", "Plan celular", ["entel pcs", "wom", "movistar movil", "claro movil"]], ["Celular e internet", "Internet hogar", ["vtr", "gtd", "mundo pacifico"]],
  ["Arriendo y gastos comunes", "Gastos comunes", ["edificio", "condominio", "comunidad", "administracion", "gastos comunes"]],
  ["Arriendo y gastos comunes", "Arriendo", ["arriendo"]],
  ["Inversiones y ahorro", "Fintual", ["fintual"]], ["Inversiones y ahorro", "APV", ["apv"]], ["Inversiones y ahorro", "Depósito a plazo", ["deposito a plazo"]],
  ["Inversiones y ahorro", "Cripto", ["buda", "binance", "criptomarkt", "orionx"]], ["Inversiones y ahorro", "Acciones", ["racional"]]
];
export const subList = (cat, ctx) => [...new Set([...(SUB_BASE[cat] || []), ...(((ctx.fin.subs || {})[cat]) || [])])];
function subRule(cat, comercio) {
  const words = norm(comercio).split(/[^a-z0-9]+/).filter(Boolean), joined = words.join("");
  for (const [c, sub, kws] of SUB_RULES) {
    if (c !== cat) continue;
    for (const kw of kws) { const k = norm(kw).replace(/[^a-z0-9]/g, ""); if (k.length < 6 && !kw.includes(" ") ? words.includes(k) : joined.includes(k)) return sub; }
  }
  return null;
}
export function subInfo(m, ctx, cat = catInfo(m, ctx).cat) {
  if (!cat || isIncoming(m)) return "";
  const list = subList(cat, ctx), ok = (s) => !!s && list.includes(s);
  if (ok(m.sub)) return m.sub;
  const k = finKey(m.comercio);
  const mem = Object.entries(ctx.fin.subOf || {}).find(([key, v]) => { const i = key.indexOf("|"); return key.slice(0, i) === cat && finSameMerchant(key.slice(i + 1), k) && ok(v); });
  if (mem) return mem[1];
  const r = subRule(cat, m.comercio);
  return ok(r) ? r : "";
}

export const isPurchase = (m, ctx) => m.moneda === "CLP" && FIN_SPEND.includes(norm(m.tipo)) && !ctx.noSpend.has(catInfo(m, ctx).cat);

/* Fijos y variables (finFixedWhy() de la web): fijo si la categoría lo es (FIN_FIXED_BASE o lib.fin.catKind), si el comercio
   se cobra con periodicidad (finRecurring()) o si es una cuota. La detección de recurrentes necesita el historial (400 días). */
export const FIN_FIXED_BASE = ["Arriendo y gastos comunes", "Luz", "Agua", "Gas", "Celular e internet", "Servicios", "Suscripciones", "Comisiones e intereses", "Educación"];
const FIN_FREQ = [["semanal", 6, 8, 3, 52 / 12], ["mensual", 26, 35, 2, 1], ["anual", 355, 375, 2, 1 / 12]];
const median = (a) => { const s = [...a].sort((x, y) => x - y), n = s.length; return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : null; };
const daysBetween = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5);

export const catFixed = (cat, ctx) => { const k = (ctx.fin.catKind || {})[cat]; return k ? k === "fijo" : FIN_FIXED_BASE.includes(cat); };

// Comercios recurrentes: [{key, name, freq, amount, monthly}] desde todo el historial de compras
export function recurring(movs, ctx) {
  const by = {};
  for (const m of movs) if (isPurchase(m, ctx) && !(m.cuotas > 1)) (by[finKey(m.comercio)] || (by[finKey(m.comercio)] = [])).push(m);
  const out = [];
  for (const [key, xs] of Object.entries(by)) {
    if (xs.length < 2) continue;
    const med = median(xs.map((m) => m.monto)), same = xs.filter((m) => Math.abs(m.monto - med) <= 0.15 * med).sort((a, b) => a.fecha.localeCompare(b.fecha));
    if (same.length < 2) continue;
    const gaps = same.slice(1).map((m, i) => daysBetween(same[i].fecha, m.fecha)), gm = median(gaps);
    const f = FIN_FREQ.find(([, lo, hi, n]) => gm >= lo && gm <= hi && same.length >= n);
    if (!f || !gaps.every((g) => Math.abs(g - gm) <= Math.max(2, 0.25 * gm))) continue;
    out.push({ key, name: same[same.length - 1].comercio, freq: f[0], amount: med, monthly: med * f[4] });
  }
  return out;
}

// "cuota" | "categoría fija" | "recurrente" | "" (variable)
export function fixedWhy(m, ctx, recKeys) {
  if (m.cuotas > 1) return "cuota";
  if (catFixed(catInfo(m, ctx).cat || "Sin categoría", ctx)) return "categoría fija";
  const k = finKey(m.comercio);
  return recKeys.some((x) => finSameMerchant(x, k)) ? "recurrente" : "";
}

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
