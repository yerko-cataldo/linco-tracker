// Uso y costo de los modelos (tabla api_usage, migración 0007), para Métricas y el presupuesto de la API de Anthropic.

// US$ por millón de tokens (entrada, salida), de la página de precios de cada proveedor (noviembre 2026).
// El costo que se muestra es una estimación; el cobro real está en console.anthropic.com → Billing.
export const MODEL_PRICES = {
  "claude-haiku-5-5": [0.1, 0.5],
  "claude-sonnet-5-5": [2, 10],
  "claude-opus-5-5": [4, 20],
  "claude-fable-5-1": [10, 50],
};

export const chileDay = () => new Date().toLocaleDateString("en-CA", { timeZone: "America/Santiago" });

export const costOf = (model, inTok, outTok) => {
  const p = MODEL_PRICES[model];
  return p ? ((inTok || 0) * p[0] + (outTok || 0) * p[1]) / 1e6 : 0;
};

// Suma una llamada; nunca rompe la respuesta si la tabla aún no existe (instancia sin la migración 0007)
export async function logUsage(env, provider, model, inTok, outTok) {
  try {
    await env.DB.prepare(
      "INSERT INTO api_usage(day, provider, model, calls, input_tokens, output_tokens, cost_usd) VALUES(?1, ?2, ?3, 1, ?4, ?5, ?6) " +
      "ON CONFLICT(day, model) DO UPDATE SET calls = calls + 1, input_tokens = input_tokens + ?4, output_tokens = output_tokens + ?5, cost_usd = cost_usd + ?6"
    ).bind(chileDay(), provider, model, inTok || 0, outTok || 0, costOf(model, inTok, outTok)).run();
  } catch (err) {
    console.error("api_usage", String(err).slice(0, 200));
  }
}

// Estado de la API de Anthropic para Métricas: key configurada, gasto del mes frente al presupuesto y vencimiento de la key
export async function anthropicStatus(env) {
  const day = chileDay(), month = day.slice(0, 7);
  let days = [];
  try {
    const r = await env.DB.prepare(
      "SELECT day, SUM(calls) AS calls, SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens, SUM(cost_usd) AS cost_usd " +
      "FROM api_usage WHERE provider = 'anthropic' AND day >= ?1 GROUP BY day ORDER BY day DESC"
    ).bind(`${month}-01`).all();
    days = r.results;
  } catch {
    days = null;  // sin la tabla api_usage
  }
  const expires = /^\d{4}-\d{2}-\d{2}$/.test(env.ANTHROPIC_KEY_EXPIRY || "") ? env.ANTHROPIC_KEY_EXPIRY : null;
  const budget = Number(env.ANTHROPIC_BUDGET_USD) || null;
  const models = [env.MODEL_AGENT, env.MODEL_COACH, env.MODEL_DEFAULT, env.MODEL_VISION].filter((m) => m && MODEL_PRICES[m]);
  return { configured: !!env.ANTHROPIC_API_KEY, budget, expires, month, today: day, models: [...new Set(models)], days };
}
