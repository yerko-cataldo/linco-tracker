# Lincoyán: contexto para Claude Code

Tracker personal de un solo usuario: nutrición, entreno, bajo eléctrico y estudio, con KPIs diarios y semanales y un coach de IA. En producción en **https://tracker.yerkolincoyan.cl**. La interfaz y los textos están en español de Chile.

## Stack

- **Cloudflare Worker** (`src/index.js`): valida el login, expone la API y hace de proxy al modelo.
- **Front** (`public/index.html`): un solo archivo con HTML, CSS y JS vanilla. No hay build, framework ni dependencias.
- **D1 (SQLite)**: tablas `days`, `lib` y `ai_usage`. El esquema está en `migrations/`.
- **Workers AI**: modelo por defecto `@cf/meta/llama-4-scout-17b-16e-instruct`, dentro del tier gratis de 10.000 neurons diarios. Anthropic es opcional, por variable.
- **Cloudflare Access**: login por código al correo. El Worker valida el JWT (`cf-access-jwt-assertion`) con `jose` en cada request. `workers_dev` y `preview_urls` están desactivados.

## Comandos

```bash
npm run dev                # local; requiere .dev.vars con DEV_BYPASS_AUTH=1
npm run db:migrate:local   # aplica migraciones a la D1 local
npm run db:migrate         # aplica migraciones a la D1 remota (solo si hay una nueva en migrations/)
npx wrangler deploy        # despliega
```

**Si `deploy` falla con "No access to the specified resource"**, es porque hay variables `CF_API_TOKEN` o `CF_ACCOUNT_ID` exportadas en la terminal (las usa el benchmark). Wrangler las toma en vez del login OAuth. Ejecuta `unset CF_API_TOKEN CF_ACCOUNT_ID` y repite.

## Modelo de datos

Ambas tablas guardan un documento JSON por fila.

**`days`**: una fila por fecha (`YYYY-MM-DD`). Cada documento tiene esta forma:

```json
{
  "date": "2026-10-04",
  "meals": [{"id", "time", "desc", "kcal", "p", "c", "f", "fib", "plants": [], "items": [{"foodId", "name", "g", "kcal", "p", "c", "f", "fib", "plant", "ai"}], "ai"}],
  "weight": null,
  "water": 0,
  "creatine": false,
  "act": {"gym": "push|pull|legs|full|", "gymMin", "tennisMin", "bikeMin", "bikeKm", "sets": [{"id", "ex", "kg", "reps"}]},
  "bass": {"minutes", "logs": [{"id", "techId", "bpm", "clean"}], "songs": [songId]},
  "study": [{"id", "itemId", "amount", "minutes"}]
}
```

**`lib`**: una fila por colección, siempre envuelta en un objeto contenedor:

| Colección | Envoltura |
|---|---|
| `goals`, `profile` | `{values: {...}}` |
| `techniques`, `songs`, `books`, `foods`, `combos` | `{list: [...]}` |
| `coach` | `{reviews: [...]}` |

Campos opcionales: `profile.officeDays` y `profile.cookDays` (días de la semana como `getDay()`, 0 = domingo); `profile.inbody` (historial de exámenes); `combos[].day` (`"tele"` u `"ofi"`) y `combos[].time` (`"HH:MM"`), que forman el plan de cada tipo de día.

**Para agregar una colección nueva** hay que registrarla en dos lugares: `LIBKEYS` en `public/index.html` (con su envoltura) y `LIB_KEYS` en `src/index.js`. Si falta la segunda, el Worker responde 404 al guardar y la importación la ignora en silencio.

## API del Worker

| Endpoint | Función |
|---|---|
| `GET /api/state` | Últimos 400 días y todo `lib` |
| `PUT /api/days/:date` | Upsert del documento de un día |
| `PUT /api/lib/:key` | Upsert de una colección |
| `POST /api/import` | Importa `{days, lib}` (reemplaza las claves que trae) |
| `GET /api/usage` | Uso diario del modelo |
| `GET /api/metrics` | Uso frente a los límites gratis de Cloudflare (GraphQL Analytics), uso del modelo y vencimiento del dominio |
| `POST /api/ai` | Proxy al modelo |

El body de `/api/ai` es `{messages, images, tier, json, stream}`.

- **Ruteo por tarea**: `tier: "complex"` usa `PROVIDER_COACH`/`MODEL_COACH`; las imágenes usan `PROVIDER_VISION`/`MODEL_VISION`; lo demás usa `PROVIDER_DEFAULT`/`MODEL_DEFAULT`. Todo se configura en `wrangler.jsonc`.
- **Streaming**: el de Workers AI se convierte al formato SSE de Anthropic (`content_block_delta`), que es el que parsea el front.
- **Tope diario**: `AI_DAILY_LIMIT` llamadas por día, en hora de Chile.

## Principios de diseño (respetarlos al cambiar código)

1. **Los números los calcula el código, no la IA.** La IA desglosa una comida en ingredientes y gramos (`items` con `foodId`). La app calcula los macros desde `lib.foods` con `itemFromFood()` y suma con `mealFromItems()`. Solo los ingredientes que no están en la base usan valores estimados por la IA, y quedan marcados con `ai: true`. Esto corrige dos errores medidos en el benchmark: valores de crudo en vez de cocido e ingredientes omitidos al sumar.
2. **Base de alimentos (`lib.foods`):**
   - Valores por 100 g (o 100 ml) **tal como se comen**.
   - `unit`/`unitG` define la porción: "envase", "huevo", "lámina"…
   - `plant` cuenta para la diversidad de plantas, que es una heurística de microbiota.
   - Si `source` contiene "revisar", el valor es dudoso.
   - Los productos eCook traen además `satFat`, `sodiumMg` (por 100 g) y `semaforo`.
   - Las carnes crudas se nombran "(cruda)/(crudo)" y conviven con sus versiones cocidas.
3. **Los KPIs son deterministas y explicables.** La tendencia de peso es una regresión lineal sobre 28 días. El gráfico de peso (`weightSeries()`, 12 semanas) dibuja el peso de tendencia como promedio móvil exponencial (`WEIGHT_ALPHA` = 0,1 por día, con interpolación lineal en los días sin pesaje), al estilo de The Hacker's Diet. El ajuste de kcal sale de 7.700 kcal ≈ 1 kg, con tope de ±250. El rango semanal es el promedio prorrateado de las 4 áreas. El 1RM estimado de cada serie usa Epley (kg × (1 + reps/30)) y un récord es un 1RM mayor que todos los anteriores del ejercicio. La constancia diaria es el promedio de las 4 áreas con tope de 100% cada una. La propuesta del día (`generatePlan()`): `planTargets()` reparte lo que falta entre las comidas que quedan (desayuno 25%, almuerzo 35%, once 15%, cena 25%, colación 12%); la IA arma cada plato para su meta con el system prompt `PLAN_SYSTEM` (el Worker lo agrega al suyo vía `body.system`); la app calcula los macros, afina cada comida que se desvía más de 7% (factor 0,6–1,6) y descarta opciones fuera de ±15% del total o con una comida bajo la mitad de su meta, con un reintento. Se regenera al registrar una comida, al cambiar "Repartir en" o al dejar un comentario. Día de oficina (`isOffice()`): día hábil con bici registrada o marcado en `officeDays`; si no, teletrabajo. La propuesta del día y el coach reciben el tipo de día y su plan base. Compras y cocina (`weekPlan()`): suma los gramos de los planes de 7 días desde el próximo día de cocina; lo que se cocina se compra en crudo o seco con factores fijos (`PREP`: arroz ×0,4, fideos ×0,43, pollo ×1,33, carne ×1,4, legumbres ×0,4); el lugar de compra sale de `food.shop` o del nombre (`shopOf()`); cada día queda a cargo de la última sesión de cocina anterior. Si cambias una fórmula, actualiza también el texto que la explica en la interfaz.
4. **Privacidad.** No hay datos personales en el código: el perfil real llega por importación. Nunca subas exportaciones (`lincoyan-*.json`, `lincoyan-*.csv`, `exports/`) ni `.dev.vars`. Cualquier proveedor de IA nuevo debe tener una política de no entrenar con los datos.

## Convenciones del front

- **Renderizado:** funciones `renderX()` que escriben con `setHTML()`. `setHTML()` no reemplaza un contenedor si tiene foco en un input, para no borrar lo que el usuario escribe. Los formularios son estáticos en el HTML; solo se re-renderizan los contenedores dinámicos.
- **Acciones:** se declaran con el atributo `data-action="nombre"` y se implementan en el objeto `actions`. Hay un solo listener de clicks, por delegación.
- **Persistencia:** `saveDay(date, mutator)` y `saveLib(key, mutator)` actualizan el estado de forma optimista y encolan el `PUT`, que va uno a la vez por documento. No se usa `localStorage` para datos; la única excepción es la preferencia de tema (`lincoyan-theme`), que es por dispositivo.
- **IA en el front:** `S.sample` es un cliente de `/api/ai` con la misma interfaz que el runtime de artifacts de claude.ai. `sample(input, {onText, images, modelTier})` hace streaming; `sample.json(...)` devuelve JSON parseado.
- **Diseño:**
  - Tokens CSS en `:root`, con variante oscura por `prefers-color-scheme` o `data-theme`.
  - Modo claro en papel y tinta cálidos; modo oscuro en azul pizarra (fondo `#22272E`, tarjetas `#2D333B`, como GitHub Dark Dimmed), nunca negro ni café. Tokens: `--bg`, `--surface`, `--sunken`, `--line`, `--line-strong`, `--hl` (resalte). Colores por área: `--food` terracota, `--bass` frambuesa, `--study` azul petróleo, `--act` añil.
  - Tipografías: Pirata One solo para el logo, Archivo semiexpandida (`--display`) para títulos y números, Hanken Grotesk para el texto y los botones.
  - Paneles con borde fino y esquinas redondeadas (`--r`), sin degradados ni sombras marcadas. Barras y chips redondeados.
  - Íconos de línea como `<symbol id="i-…">` en el sprite del inicio del `<body>` (hoy, food, act, bass, study, coach, perfil, trophy). Cada sección abre con `.page-head` (ícono en `.tile` con el color del área).
  - `ring()` dibuja anillos de progreso (tarjetas del resumen, kcal y macros). El metrónomo es un dial con los pulsos en círculo; las series se muestran como tarjetas con columna "Anterior"; cada libro tiene una portada de color derivada del título.
  - El resumen semanal es una tablatura de bajo: cuerdas G/D/A/E y traste 12 = meta cumplida.
- **Audio:** el metrónomo, la batería (`GROOVES`) y las alarmas de los temporizadores se sintetizan con Web Audio en el objeto `Metro`, sin archivos de sonido. Los patrones de batería son strings de un compás de 4 tiempos (`X` acento, `x` golpe, `g` nota fantasma, `-` silencio).
- **Textos:** español de Chile, tuteo, frases en minúscula inicial, sin mayúsculas sostenidas. Un botón dice exactamente lo que hace.

## Evaluación de modelos

`eval/benchmark_llm.py` compara modelos de Workers AI contra Claude Haiku: estimación de comidas (20 casos con referencia USDA) y registro rápido (8 casos). Su último resultado: Llama 3.3 70B y Llama 4 Scout tuvieron 100% de JSON válido, ~12–13% de error porcentual en kcal y sesgo negativo de ~−35 kcal, causado por valores de crudo y por omisión de ingredientes. Ese diagnóstico motivó el principio 1.

## Pendientes conocidos

- Mostrar el semáforo de eCook (sodio y grasa saturada) al armar una comida, y llevar el stock de envases.
- Adaptar el benchmark para evaluar el desglose en ingredientes con la base, en vez de totales.
- Completar la fibra de la hallulla; verificar leche sin lactosa, palta y queso rallado contra sus etiquetas.
- Probar la estimación por foto con Llama 4 Scout usando fotos reales.
