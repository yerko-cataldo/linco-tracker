# Lincoyán: contexto para Claude Code

Tracker personal de un solo usuario: nutrición, entreno, bajo eléctrico y estudio, con KPIs diarios y semanales y un coach de IA. En producción en **https://tracker.yerkolincoyan.cl**. La interfaz y los textos están en español de Chile.

## Stack

- **Cloudflare Worker** (`src/index.js`): valida el login, expone la API y hace de proxy al modelo.
- **Front** (`public/index.html`): un solo archivo con HTML, CSS y JS vanilla. No hay build, framework ni dependencias.
- **D1 (SQLite)**: tablas `days`, `lib` y `ai_usage`. El esquema está en `migrations/`.
- **Workers AI**: modelo por defecto `@cf/meta/llama-4-scout-17b-16e-instruct`, dentro del tier gratis de 10.000 neurons diarios. Anthropic es opcional, por variable.
- **Cloudflare Access**: login por código al correo. El Worker valida el JWT (`cf-access-jwt-assertion`) con `jose` en cada request, salvo en `/s/*` (vista compartida), que tiene una excepción Bypass en Access. `workers_dev` y `preview_urls` están desactivados.

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
  "meals": [{"id", "time", "slot", "desc", "kcal", "p", "c", "f", "fib", "plants": [], "items": [{"foodId", "name", "g", "kcal", "p", "c", "f", "fib", "plant", "ai"}], "ai"}],
  "weight": null,
  "water": 0,
  "creatine": false,
  "act": {"gym": "push|pull|legs|full|core|", "gymMin", "gymMinManual", "tennisMin", "bikeMin", "bikeKm", "sets": [{"id", "ex", "kg", "reps", "unit", "rest"}]},
  "bass": {"minutes", "logs": [{"id", "techId", "bpm", "clean"}], "songs": [songId]},
  "study": [{"id", "itemId", "amount", "minutes"}]
}
```

**`lib`**: una fila por colección, siempre envuelta en un objeto contenedor:

| Colección | Envoltura |
|---|---|
| `goals`, `profile`, `share`, `optim` | `{values: {...}}` |
| `techniques`, `songs`, `books`, `foods`, `combos` | `{list: [...]}` |
| `coach` | `{reviews: [...]}` |

En `act.sets`, `unit` es opcional (`"lb"` o `"nivel"`; sin él, kg) `rest` son los segundos de descanso después de la serie (en el checklist se mide como el intervalo entre dos series marcadas menos 30 s) y `t` es la marca de tiempo al marcarla. `act.end` (opcional) es la marca de tiempo de "Terminar entreno". En días con series, la duración del gimnasio se estima desde las series con `gymDur()` (ejecución más descansos de 2–3 min, o 60–90 s en ejercicios de core) y `act.gymMin` se ignora; si escribes los minutos a mano, quedan en `act.gymMinManual` y reemplazan al estimado. Los nombres se normalizan al catálogo `EX_CAT` (~95 ejercicios con alias en inglés y español, músculos principales y secundarios, tipo de sesión y una nota de enfoque); un nombre con palabras extra solo coincide si esas palabras están en `EX_DESC` ("máquina", "polea", "con"…).

Campos opcionales: `meals[].slot` (la comida a la que corresponde, con el nombre de una de las comidas del optimizador; se elige al registrar o editar). Sin `slot`, `mealSlotIdx()` asigna la comida más cercana a la hora, salvo que la primera comida del día caiga entre el desayuno y el almuerzo: esa cuenta como desayuno. `goals.wDate`, `goals.wFat` y `goals.wLean` (meta de peso: fecha, % de grasa meta y masa libre de grasa en kg); `profile.officeDays` y `profile.cookDays` (días de la semana como `getDay()`, 0 = domingo); `profile.inbody` (historial de exámenes); `combos[].day` (`"tele"` u `"ofi"`) y `combos[].time` (`"HH:MM"`), que forman el plan de cada tipo de día; `foods[].group` (grupo para el optimizador: `prot`, `carb`, `veg`, `fat`, `fruit`, `leg`, `lact`, `dish`; sin él lo infiere `groupOf()` por nombre y macros). `lib.optim` guarda la configuración del optimizador: `slots` (comidas del día: `{name, time, share, comps}`, donde `comps` es texto como `"pan/avena, huevo/lácteo, fruta?"` que lee `parseComps()`) y `w` (prioridades); sin ellos usa `OPT_SLOTS` y `OPT_W`. Es privada: no está en `SHARE_LIBS`.

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
| `GET /s/:token` | Vista compartida sin login: la misma app en solo lectura |
| `GET /s/:token/data` | Datos filtrados para la vista compartida |

**Vista compartida.** `lib.share = {token, areas}`, se administra en Perfil → "Compartir con amigos". El Worker (`share()`) compara el token y solo entrega los días con las áreas elegidas (`act`, `bass`, `study`, `food`), las metas de esas áreas (`SHARE_GOALS`) y sus colecciones (`SHARE_LIBS`). Nunca entrega peso, perfil, InBody, metas de peso, coach ni comidas frecuentes. El front detecta `/s/<token>` (`SHARE`), oculta las pestañas no compartidas y la edición (`.no-share` y las acciones fuera de `SHARE_ACTIONS`), y calcula la constancia y el rango solo con las áreas compartidas (`AREAS`). Si agregas un dato privado nuevo, no lo sumes a esas listas.

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
3. **Los KPIs son deterministas y explicables.** La tendencia de peso es una regresión lineal sobre 28 días. El gráfico de peso (`weightSeries()`, 12 semanas) dibuja el peso de tendencia como promedio móvil exponencial (`WEIGHT_ALPHA` = 0,1 por día, con interpolación lineal en los días sin pesaje), al estilo de The Hacker's Diet. Si hay meta de peso (`goals.wDate`, `goals.wFat`, `goals.wLean`), el peso meta es masa libre de grasa ÷ (1 − % grasa meta); la proyección y la ruta parten del valor de la regresión para hoy, la proyección sigue la pendiente de 28 días (requiere 6 pesajes en 10 días o más) y la ruta es la recta hasta la meta. El ajuste de kcal sale de 7.700 kcal ≈ 1 kg, con tope de ±250. El rango semanal es el promedio prorrateado de las 4 áreas. El 1RM estimado de cada serie usa Epley (kg × (1 + reps/30)) y un récord es un 1RM mayor que todos los anteriores del ejercicio. La constancia diaria es el promedio de las 4 áreas con tope de 100% cada una. La propuesta del día (`generatePlan()`): `planTargets()` reparte lo que falta entre las comidas que quedan (desayuno 25%, almuerzo 35%, once 15%, cena 25%, colación 12%); la IA arma cada plato para su meta con el system prompt `PLAN_SYSTEM` (el Worker lo agrega al suyo vía `body.system`); la app calcula los macros, afina cada comida que se desvía más de 7% (factor 0,6–1,6) y descarta opciones fuera de ±15% del total o con una comida bajo la mitad de su meta, con un reintento. Se regenera al registrar una comida, al cambiar "Repartir en" o al dejar un comentario. Día de oficina (`isOffice()`): día hábil con bici registrada o marcado en `officeDays`; si no, teletrabajo. La propuesta del día y el coach reciben el tipo de día y su plan base. Compras y cocina (`weekPlan()`): suma los gramos de los planes de 7 días desde el próximo día de cocina; lo que se cocina se compra en crudo o seco con factores fijos (`PREP`: arroz ×0,4, fideos ×0,43, pollo ×1,33, carne ×1,4, legumbres ×0,4); el lugar de compra sale de `food.shop` o del nombre (`shopOf()`); cada día queda a cargo de la última sesión de cocina anterior. Gimnasio: una serie es de aproximación si está al inicio y tiene menos del 75% de la carga más alta del ejercicio ese día; las series efectivas por músculo suman 1 al principal y 0,5 al secundario (referencia 10–20 por semana); récord es la mejor serie del día cuando supera el 1RM estimado de todas las sesiones anteriores; la sugerencia de la próxima sesión es doble progresión en 8–12 reps (`nextStep()`). "Pegar rutina desde tus notas" (`parseRoutine()`) lee fecha, ejercicio, series y descansos de texto libre y reemplaza las series de cada día. Optimizador de porciones (`optimize()`, sin IA). El costo es un −log posterior: J = Σ_m w_m·a_m(r_m)·r_m² + λ·Σ_i u_i² + π·Σ_comidas −log p(plato | comida), con r = (logrado − falta)/σ para P, C, G y fibra (σ = tolerancia × meta diaria; las kcal no entran porque salen de 4P + 4C + 9G), a(r) según el tipo de meta (`OPT_TYPE`: mínimo, máximo u objetivo, con asimetría κ = `OPT_KAPPA`), u = (g − habitual)/s (habitual = mediana de 60 días de registros más el plan base; s = 1,4826·MAD, mínimo `OPT_SPREAD`·habitual) y cotas solo físicas (una porción como mínimo, tope de seguridad `OPT_CAP`·habitual). p(plato | comida) con suavizado de Laplace: (veces + 1)/(comidas + platos); variación × α·p(alimento | rol); otra franja × γ; combinación nueva ε·Π p(alimento | rol); repetir un alimento × δ (`OPT_ALPHA`, `OPT_GAMMA`, `OPT_EPS`, `OPT_DELTA`). Controles: w de P, C, G y fibra, λ y π. Con los platos fijos J es convexo: descenso por coordenadas con mayorización (`optSolve()`, tolerancia 1e-7 en la solución final) y certificado KKT (`optKKT()`: gradiente proyectado ≈ 0 y multiplicador de cada cota activa); después redondeo a unidades, medias unidades o 5–10 g con búsqueda local (`optRound()`). Los candidatos de cada comida son platos (`optCandidates()`): los que comiste a esa hora (comidas con ≥70% de kcal de la base; crudos mapeados a cocidos con `optCooked()`), comidas frecuentes, platos libres o de otra franja, variaciones de un alimento por otro del mismo rol culinario (`roleOf()`, `roleAlts()`) y, solo si hay menos de 3 platos, combinaciones nuevas desde los componentes de la comida que pasen `coherent()` (todos los alimentos en un mismo tipo de comida, `MEAL_CTX`). Almuerzo y cena solo llevan platos de fondo; desayuno, media mañana y colación, livianos (`slotKinds()`, `tplKind()`). Cada comida preordena contra su parte proporcional de lo que falta y una búsqueda en haz de 40 caminos con los 6 mejores de cada comida optimiza el día completo (aproximado: no garantiza el óptimo global); se muestran opciones con similitud de Jaccard < 0,6. La "Traza del cálculo" (`optWhyBox()`) muestra cada término de J con sus números, el certificado KKT, el efecto del redondeo, los candidatos y el top 6 de cada comida, la curva de λ (`optPareto()`: error de metas frente a desvío de porciones) y exporta el problema en JSON. El "por qué" de cada porción usa el gradiente −∂J/∂g del macro que más la empuja. A qué comida corresponde un registro: `meals[].slot` o `mealSlotIdx()`. La vista es compacta: tarjetas por opción con las fotos de cada comida, y cada comida con un alimento por línea (foto, gramos con − y + o escritos, ⇄ para cambiarlo, "Registrar" y "Editar" por comida, "Deshacer"). Las fotos son de Wikimedia Commons (`public/img/alimentos/*.webp`, 128 px, elegidas por nombre con `FOOD_PHOTO`; créditos en `PHOTO_CREDITS`, en el panel "Créditos de las fotos" y en `CREDITOS.md`; al agregar una, agrega su crédito). Sin foto se usa el dibujo de línea (`FOOD_ICON` → símbolos `i-f-*` del sprite; comidas del día `i-s-*`). Cambiar un alimento (`optSwapTo()`) pone el nuevo en el lugar del anterior aunque sea de otro grupo; fijar gramos cierra su cota (lo = hi). Tus cambios (`S.opt.pin`, `fix`, `no`) son de la sesión y del día; al editar se congela la composición de la opción que veías (`S.opt.keep`) y solo se reoptimizan los gramos, salvo que pidas "Buscar otras combinaciones con mis cambios". Se validó contra scipy (L-BFGS-B): coincide hasta ~1e-7 con λ > 0; con λ = 0 el óptimo no es único. Si cambias una fórmula, actualiza también el texto que la explica en la interfaz (en el optimizador, "Cómo decide").
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
  - Ilustraciones de ejercicios en estilo silueta (`ILLU`, por nombre de ejercicio): figura plana de perfil con el aparato y el músculo trabajado en `--act`. Se generan con `tools/ilustraciones/` (Python) y se insertan en `public/index.html` entre los marcadores `ILLU:inicio`/`ILLU:fin`; no se editan a mano. Sin ilustración, se muestra la figura muscular (`bodyFig()`).
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
- Ilustraciones en silueta para el resto del catálogo: hoy hay 28 (los ejercicios de las rutinas base de Push, Pull, Legs, Full body y Core, más algunos habituales); faltan los demás.
