# Lincoyán

Tracker personal de un solo usuario para nutrición, entreno, bajo eléctrico, estudio y finanzas, con indicadores diarios y semanales y un coach de IA. Corre completo en el plan gratuito de Cloudflare: un Worker, una base D1 y Workers AI.

La interfaz está en español de Chile.

## Qué hace

| Sección | Contenido |
|---|---|
| **Resumen** | Semana como tablatura de bajo (traste 12 = meta cumplida), indicadores del día, rango semanal y mapa de constancia. |
| **Nutrición** | Registro de comidas por texto o foto: la IA las desglosa en ingredientes y la app calcula los macros desde tu base de alimentos. Propuesta del día, optimizador de porciones, lista de compras y cocina, y peso con tendencia y proyección a la meta. |
| **Entreno** | Checklist de series con descansos, 1RM estimado, récords, series efectivas por músculo, sugerencia de progresión e ilustraciones de ejercicios. |
| **Bajo** | Metrónomo y batería sintetizados con Web Audio, técnicas con su BPM limpio y repertorio. |
| **Estudio** | Libros y cursos con plan por temario, ritmo, proyección y temporizador. |
| **Finanzas** | Compras con tarjeta de crédito que llegan solas desde las alertas de Visa, conciliación con la cartola del banco, detalle de productos por compra, categorías con reglas, presupuesto y topes, recurrentes, cuotas, gráficos de distribución y evolución, gasto diario en comida y resumen del mes con IA. |
| **Coach** | Revisión semanal y chat con el contexto de tu perfil y tus registros. |
| **Perfil y metas** | Perfil, metas, importación y exportación, y un link de solo lectura para compartir algunas áreas con amigos. |
| **Métricas** | Uso frente a los límites gratis de Cloudflare, uso del modelo y vencimiento del dominio. |

## Principios

1. **Los números los calcula el código, no la IA.** La IA interpreta texto (separa una comida en ingredientes o una compra en productos) y redacta resúmenes. Los macros, montos, totales y proyecciones salen de fórmulas deterministas. Lo que estima la IA queda marcado.
2. **Cada indicador se explica en la interfaz.** Si cambias una fórmula, actualiza también el texto que la explica.
3. **Sin datos personales en el código.** Tus datos viven en D1 detrás de Cloudflare Access y entran por importación. El repo no tiene exportaciones, cartolas ni correos.

## Stack

- **Front:** `public/index.html`, un solo archivo con HTML, CSS y JavaScript sin dependencias ni build.
- **Worker:** `src/index.js` valida el login de Cloudflare Access en cada request, expone la API, hace de proxy al modelo y recibe correos por Email Routing.
- **Base de datos:** D1 (SQLite). Esquema en `migrations/`.
- **IA:** Workers AI por defecto (Llama 4 Scout, dentro del tier gratis). Anthropic es opcional, por tarea.

```
public/index.html      la app
src/index.js           Worker: login, API, proxy al modelo y correo entrante
src/alertas.js         lectura de las alertas de compra de Visa
src/cartola.js         lectura de la cartola CSV del banco y conciliación con las alertas
migrations/            esquema de D1, una migración por cambio
wrangler.jsonc         configuración: dominio, D1, modelos y variables
tools/ilustraciones/   generador de las ilustraciones de ejercicios (Python)
eval/                  benchmark de modelos para estimar comidas
docs/                  detalles técnicos y registro de cambios
```

### Tablas

| Tabla | Contenido |
|---|---|
| `days` | Un documento JSON por fecha: comidas, peso, agua, entreno, bajo y estudio. |
| `lib` | Un documento JSON por colección: metas, perfil, alimentos, técnicas, canciones, libros, coach, configuración de finanzas, etc. |
| `ai_usage` | Llamadas y tokens del modelo por día, para el tope diario. |
| `inbox_raw` | Últimos 200 correos recibidos por Email Routing, sin procesar. |
| `movimientos` | Una fila por transacción de la tarjeta, desde una alerta o desde la cartola. |
| `mov_detalle` | Productos de cada compra, un documento JSON por movimiento. |

## Puesta en marcha

Necesitas una cuenta de Cloudflare, un dominio administrado en Cloudflare y Node para ejecutar `wrangler`.

### 1. Base de datos

```bash
npm install
npx wrangler login
npx wrangler d1 create lincoyan      # copia el database_id que imprime a wrangler.jsonc
npm run db:migrate                   # crea las tablas en D1
```

### 2. Dominio y login

1. Agrega tu dominio a Cloudflare y define la ruta del Worker en `wrangler.jsonc` (`routes`).
2. En **Zero Trust → Access → Applications**, crea una aplicación *Self-hosted* para ese dominio con una política *Allow* para tu correo y login por código al correo (*One-time PIN*).
3. Completa en `wrangler.jsonc`:
   - `ACCESS_TEAM_DOMAIN`: `https://<equipo>.cloudflareaccess.com`.
   - `ACCESS_AUD`: el *Application Audience Tag* de la aplicación.
   - `ALLOWED_EMAIL`: tu correo. También puedes guardarlo como secreto del Worker y sacarlo del archivo.
4. Para compartir con amigos, agrega en Access una excepción *Bypass* para la ruta `/s`.

El Worker valida el JWT de Access en cada request. Las URL `*.workers.dev` y las previews están desactivadas.

### 3. Despliegue

Conecta el repo en **Workers & Pages → lincoyan → Settings → Builds**. Desde ahí, cada push a `main` se despliega solo.

Las migraciones no se aplican con el push. Cuando agregues una en `migrations/`, aplícala **antes** del push con `npm run db:migrate`, o pega su SQL en la consola de D1 del panel. Si el código nuevo lee una tabla o columna que aún no existe, la app no carga.

### 4. Tus datos

Abre la app, entra con el código que llega a tu correo y ve a **Perfil y metas → Importar JSON** si tienes una exportación previa. Completa el perfil: el coach lo usa como contexto.

### 5. Finanzas (opcional)

Las compras llegan por correo y se concilian con la cartola del banco.

1. **Email Routing.** En el panel del dominio, activa **Email → Email Routing**. Crea una dirección difícil de adivinar (por ejemplo `alertas-<algo-aleatorio>@tu-dominio.cl`) con la acción **Send to a Worker → lincoyan**. No actives una regla *catch-all* hacia el Worker.
2. **Alertas de Visa.** En [Visa Purchase Alerts](https://purchasealerts.visa.com), registra tu tarjeta, usa esa dirección como correo de contacto y activa las alertas de todas las compras, sin monto mínimo. El código de verificación llega a la tabla `inbox_raw`; léelo desde la consola de D1:

   ```sql
   SELECT id, subject, substr(raw, -3000) FROM inbox_raw ORDER BY id DESC LIMIT 3;
   ```

3. **Cartola.** Descarga el CSV de movimientos de la tarjeta e impórtalo en **Finanzas → Importar cartola**. La app une cada fila con su alerta, agrega lo que falte, marca las alertas que no aparecen (posibles compras anuladas) y toma de ahí el ciclo de facturación y las cuotas.

El Worker solo acepta alertas con remitente de `visa.com` y firmas DKIM y DMARC válidas. El lector de la cartola sigue el formato del CSV de BICE (`src/cartola.js`). Otro banco requiere adaptar ese archivo.

### 6. IA con Anthropic (opcional)

Cada tarea tiene su proveedor (`workers-ai` o `anthropic`) y su modelo en `wrangler.jsonc`:

- `PROVIDER_DEFAULT` / `MODEL_DEFAULT`: registro rápido, desglose de comidas y compras, y chat.
- `PROVIDER_COACH` / `MODEL_COACH`: revisión semanal y análisis del día.
- `PROVIDER_VISION` / `MODEL_VISION`: fotos.

Si usas Anthropic, define un límite de gasto en su consola y guarda la key como secreto:

```bash
npx wrangler secret put ANTHROPIC_API_KEY
```

El Worker además corta en `AI_DAILY_LIMIT` llamadas al día, en hora de Chile. Cualquier proveedor nuevo debe tener una política de no entrenar con tus datos.

## Desarrollo local

```bash
cp .dev.vars.example .dev.vars    # DEV_BYPASS_AUTH=1 salta el login solo en local
npm run db:migrate:local
npm run dev                       # http://localhost:8787
```

Si `deploy` o `db:migrate` fallan con "No access to the specified resource", hay variables `CF_API_TOKEN` o `CF_ACCOUNT_ID` exportadas en la terminal. Bórralas con `unset CF_API_TOKEN CF_ACCOUNT_ID` y repite.

## Respaldos

- **Desde la app:** **Perfil y metas → Exportar JSON**, o el CSV por alimento.
- **Base completa:**

  ```bash
  npx wrangler d1 export lincoyan --remote --output=exports/respaldo.sql
  ```

Guarda los respaldos fuera del repo o en `exports/`. El `.gitignore` excluye `exports/`, `lincoyan-*.json`, `lincoyan-*.csv` y `.dev.vars`.

## Documentación

- `CLAUDE.md`: modelo de datos, API del Worker, fórmulas de cada indicador y convenciones del front.
- `docs/technical.md`: detalles de implementación.
- `docs/changelog.md`: registro de cambios.
