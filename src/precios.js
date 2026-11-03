// Precios de referencia de Unimarc: búsqueda en el catálogo público de VTEX y precio por kg, litro o unidad.
//
// 1. unimarcSearch() consulta el buscador del catálogo con el texto pedido (hasta 20 productos).
// 2. parseUnimarc() deja cada producto con nombre, marca, categoría, link a unimarc.cl, precio y precio por kg, litro o unidad.
// 3. Los productos sin stock o sin precio quedan fuera.

const VTEX_SEARCH = "https://unimarc.vtexcommercestable.com.br/api/catalog_system/pub/products/search";
const PRODUCT_URL = "https://www.unimarc.cl/product/";
const MAX_RESULTS = 20;

// Contenido del envase escrito en el nombre ("400g", "1 Kg", "1,5 L", "330 ml")
const SIZE_RE = /(\d+(?:[.,]\d+)?)\s*(kg|kilo|gr|g|lt|l|ml|cc)\b/i;

function sizeFromName(name) {
  const m = String(name).match(SIZE_RE);
  if (!m) return null;
  const v = parseFloat(m[1].replace(",", ".")), u = m[2].toLowerCase();
  if (u === "kg" || u === "kilo") return { per: "kg", qty: v };
  if (u === "lt" || u === "l") return { per: "L", qty: v };
  if (u === "ml" || u === "cc") return { per: "L", qty: v / 1000 };
  return { per: "kg", qty: v / 1000 };
}

function productData(p) {
  try {
    return JSON.parse((p.ProductData || [])[0] || "{}");
  } catch {
    return {};
  }
}

/* Precio por unidad de medida:
   - measurementUnit "kg": producto a granel; Price es por kg.
   - ProductData.measurement_unit_un "Kg" o "litro": unit_multiplier_un es el contenido del envase en kg o litros.
   - "unidad": unit_multiplier_un es la cantidad de unidades del envase (huevos).
   - Sin datos: contenido leído del nombre. */
export function unitPrice(p) {
  const item = (p.items || [])[0] || {};
  const offer = ((item.sellers || [])[0] || {}).commertialOffer || {};
  const price = Number(offer.Price);
  if (!(price > 0) || offer.IsAvailable === false) return null;
  const pd = productData(p), mu = String(pd.measurement_unit_un || "").toLowerCase(), qty = Number(pd.unit_multiplier_un) || 0;
  if (String(item.measurementUnit).toLowerCase() === "kg") return { price, per: "kg", unitPrice: price, qty: Number(item.unitMultiplier) || 1 };
  if (mu === "kg" && qty > 0) return { price, per: "kg", unitPrice: price / qty, qty };
  if ((mu === "litro" || mu === "lt" || mu === "l") && qty > 0) return { price, per: "L", unitPrice: price / qty, qty };
  if (mu === "unidad" && qty > 0) return { price, per: "un", unitPrice: price / qty, qty };
  const s = sizeFromName(p.productName);
  return s && s.qty > 0 ? { price, per: s.per, unitPrice: price / s.qty, qty: s.qty } : { price, per: "un", unitPrice: price, qty: 1 };
}

export function parseUnimarc(list) {
  return (Array.isArray(list) ? list : []).map((p) => {
    const u = unitPrice(p);
    if (!u || !p.productName || !p.linkText) return null;
    const offer = (((p.items || [])[0] || {}).sellers || [])[0]?.commertialOffer || {};
    return {
      name: String(p.productName).replace(/\s+/g, " ").trim(),
      brand: p.brand || "",
      cat: (p.categories || [])[0] || "",
      url: PRODUCT_URL + p.linkText,
      price: Math.round(u.price),
      listPrice: Math.round(Number(offer.ListPrice) || u.price),
      per: u.per,
      unitPrice: Math.round(u.unitPrice),
      qty: u.qty,
    };
  }).filter(Boolean);
}

export async function unimarcSearch(q) {
  const url = `${VTEX_SEARCH}?ft=${encodeURIComponent(q)}&_from=0&_to=${MAX_RESULTS - 1}`;
  const res = await fetch(url, { headers: { accept: "application/json", "user-agent": "Mozilla/5.0 (compatible; Lincoyan/1.0)" } });
  if (!res.ok) throw new Error(`unimarc ${res.status}`);
  return parseUnimarc(await res.json());
}
