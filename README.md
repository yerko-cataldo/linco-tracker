# Lincoyán

Bitácora personal de nutrición, entreno, bajo y estudio, con coach de IA.

- **Front:** `public/index.html`, una sola página sin build.
- **Backend:** un Cloudflare Worker (`src/index.js`). Valida tu login de Cloudflare Access, guarda los datos en D1 (SQLite) y hace de proxy a la API de Anthropic. La API key nunca llega al navegador.
- **Datos:** dos tablas JSON, `days` y `lib`, más un contador diario de uso del modelo (`ai_usage`).

```
public/index.html         la app
src/index.js              Worker: auth, API de datos, proxy al modelo
migrations/0001_init.sql  esquema de D1
wrangler.jsonc            configuración (dominio, D1, variables)
```

## Migración paso a paso

### 0. Exporta tus datos actuales

En la versión de claude.ai: **Perfil y metas → Exportar JSON**. Guárdalo **fuera del repo**. El `.gitignore` ya excluye `lincoyan-*.json` por si acaso.

### 1. Repo privado en GitHub

```bash
git init && git add . && git commit -m "Lincoyán: primera versión"
git branch -M main
git remote add origin git@github.com:TU_USUARIO/lincoyan.git
git push -u origin main
```

### 2. Cloudflare y base de datos

Usa una cuenta personal, no la de tu empresa.

```bash
npm install
npx wrangler login
npx wrangler d1 create lincoyan      # copia el database_id que imprime a wrangler.jsonc
npm run db:migrate                   # crea las tablas en D1
```

### 3. Dominio

1. Inscribe **lincoyán.cl** en [nic.cl](https://www.nic.cl). En DNS su forma técnica (punycode) es `xn--lincoyn-mwa.cl`, y es la que va en `wrangler.jsonc`.
2. En Cloudflare, agrega el dominio con **Add a domain** (plan Free). Te dará dos nameservers.
3. En NIC Chile, reemplaza los servidores DNS del dominio por esos dos nameservers. La activación suele tardar desde minutos hasta algunas horas.

### 4. Login con Cloudflare Access

1. Ve a **Zero Trust** y crea tu equipo (plan Free). Tu *team domain* queda como `https://<equipo>.cloudflareaccess.com`.
2. Ve a **Access → Applications → Add an application → Self-hosted**:
   - **Dominio:** lincoyán.cl (y lincoyan.cl si lo compras).
   - **Política:** *Allow*, *Include → Emails →* tu correo.
   - **Método de login:** *One-time PIN* (código por correo) o Google.
3. Copia el **Application Audience (AUD) Tag** y completa en `wrangler.jsonc`:
   - `ACCESS_TEAM_DOMAIN`
   - `ACCESS_AUD`
   - `ALLOWED_EMAIL`

El Worker valida el JWT de Access en cada request, así que aunque alguien llegara al Worker por otra ruta no podría entrar. Además, la URL `*.workers.dev` está desactivada.

### 5. API key de Anthropic

En la consola de Anthropic, con tu cuenta personal:

1. Crea una key.
2. Define un **límite de gasto mensual**, por ejemplo USD 5.
3. Guárdala como secreto del Worker:

```bash
npx wrangler secret put ANTHROPIC_API_KEY
```

Además, el Worker corta en `AI_DAILY_LIMIT` llamadas al día (150 por defecto). El uso acumulado se consulta en `/api/usage`.

### 6. Primer despliegue

```bash
npx wrangler deploy
```

Abre https://lincoyán.cl. Access te pedirá el código por correo.

Luego ve a **Perfil y metas → Importar JSON** y sube el archivo del paso 0. Completa también el campo **Sobre mí**, que el coach usa como contexto.

### 7. Despliegue automático en cada push

En el dashboard: **Workers & Pages → lincoyan → Settings → Builds → Connect** y elige el repo. Deja el comando de deploy en `npx wrangler deploy`. Desde ahí, cada `git push` a `main` publica solo.

Si algún día agregas una migración nueva en `migrations/`, aplícala una vez a mano con `npm run db:migrate` antes del push.

## Desarrollo local

```bash
cp .dev.vars.example .dev.vars    # pon tu API key; DEV_BYPASS_AUTH=1 salta el login solo en local
npm run db:migrate:local
npm run dev                       # http://localhost:8787
```

## Cambiar de modelo o de proveedor

Todo se controla con variables en `wrangler.jsonc`:

- `MODEL_DEFAULT` se usa para registros, estimación de comidas y chat.
- `MODEL_COACH` se usa cuando el front pide `tier: "complex"`.
- `ANTHROPIC_BASE_URL` apunta a cualquier endpoint compatible con la Messages API de Anthropic. Sirve para un A/B con otro proveedor, cambiando también la key.

## Respaldos

- **Desde la app:** **Exportar JSON** o **Exportar CSV diario**. El CSV está listo para pandas.
- **Respaldo completo de D1:**

```bash
npx wrangler d1 export lincoyan --remote --output=exports/respaldo.sql
```
