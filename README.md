# crypto-news-api

Scraper automatizado de titulares de noticias cripto + API REST gratuita.
Sin servidor propio, sin costos, 100% público.

- **Scraper**: lee feeds RSS de CoinDesk, Cointelegraph, Decrypt, Bitcoin Magazine,
  The Block y CryptoNews.
- **Automatización**: GitHub Actions corre el scraper cada 15 min y commitea
  `data/news.json`.
- **API**: Cloudflare Worker gratuito sirve ese JSON con filtros, búsqueda
  y paginación.

---

## Paso a paso — Setup

### 1. Crear el repositorio en GitHub

```bash
cd crypto-news-api
git init
git add .
git commit -m "init: crypto news scraper + api"
gh repo create crypto-news-api --public --source=. --push
```

Si no tienes `gh` (GitHub CLI), créalo manualmente en github.com → New repository
→ público → y luego:

```bash
git remote add origin https://github.com/alejandroceo/crypto-news-api.git
git branch -M main
git push -u origin main
```

### 2. Habilitar GitHub Actions

No necesitas hacer nada extra: el workflow en `.github/workflows/scrape.yml`
se activa solo al hacer push. Para forzar la primera corrida sin esperar
los 15 min:

1. Ve a tu repo → pestaña **Actions**.
2. Click en "Scrape crypto news" → **Run workflow** → Run workflow.
3. Espera ~30 segundos, refresca, y verás el commit automático con
   `data/news.json` lleno de titulares.

A partir de ahí corre solo cada 15 minutos, gratis (GitHub da 2000 min/mes
gratis en repos públicos, y esto consume ~1 min por corrida = totalmente
dentro del límite incluso corriendo cada 15 min todo el mes).

### 3. Verificar que el JSON ya es público

Sin hacer nada más, tu JSON ya es accesible en:

```
https://raw.githubusercontent.com/alejandroceo/crypto-news-api/main/data/news.json
```

Pruébalo:

```bash
curl https://raw.githubusercontent.com/alejandroceo/crypto-news-api/main/data/news.json
```

Esto YA es una "API" de solo lectura, gratis, pública, sin que montes nada más.
Si solo necesitas eso, puedes parar aquí.

### 4. (Opcional pero recomendado) Deploy del Worker para tener una API REST real

Esto te da filtros (`?source=`, `?q=`, `?limit=`), CORS, y caché en el edge.

```bash
cd worker
npm install -g wrangler   # CLI de Cloudflare, gratis
wrangler login            # abre el navegador, login con cuenta gratuita
```

Edita `worker.js` y cambia esta línea con tu usuario/repo real:

```js
const RAW_JSON_URL = "https://raw.githubusercontent.com/alejandroceo/crypto-news-api/main/data/news.json";
```

Luego:

```bash
wrangler deploy
```

Te va a dar una URL del tipo:

```
https://crypto-news-api.TU_SUBDOMINIO.workers.dev
```

Esa es tu API REST pública y gratuita (100,000 requests/día gratis,
sin tarjeta de crédito).

---

## Endpoints de la API

| Endpoint | Descripción |
|---|---|
| `GET /` | Todos los titulares (máx 50 por defecto) |
| `GET /?source=coindesk` | Filtra por fuente |
| `GET /?q=bitcoin` | Busca en el título |
| `GET /?limit=10&offset=20` | Paginación |
| `GET /sources` | Lista de fuentes disponibles |

Ejemplo de respuesta:

```json
{
  "updated_at": "2026-06-30T14:00:00+00:00",
  "total": 134,
  "count": 10,
  "offset": 0,
  "limit": 10,
  "items": [
    {
      "id": "a1b2c3d4e5f6",
      "title": "Bitcoin supera los $XX,XXX en medio de...",
      "link": "https://...",
      "source": "coindesk",
      "published": "2026-06-30T13:45:00+00:00",
      "summary": "..."
    }
  ]
}
```

---

## Cómo consumirla desde otro proyecto

### Python

```python
import requests

API = "https://crypto-news-api.TU_SUBDOMINIO.workers.dev"

resp = requests.get(API, params={"limit": 5, "source": "cointelegraph"})
data = resp.json()

for item in data["items"]:
    print(f"[{item['source']}] {item['title']}")
    print(item["link"])
```

### JavaScript / Node / frontend

```javascript
const API = "https://crypto-news-api.TU_SUBDOMINIO.workers.dev";

async function getLatestNews(query = {}) {
  const params = new URLSearchParams(query);
  const res = await fetch(`${API}/?${params}`);
  const data = await res.json();
  return data.items;
}

const news = await getLatestNews({ limit: 10, q: "ethereum" });
news.forEach(n => console.log(`${n.source}: ${n.title}`));
```

### cURL / bash

```bash
curl "https://crypto-news-api.TU_SUBDOMINIO.workers.dev/?source=decrypt&limit=5"
```

### Directo del JSON crudo (sin Worker)

Si no quieres montar el Worker, puedes consumir el raw JSON directo
(sin filtros, pero igual de gratis y público):

```python
import requests
data = requests.get(
    "https://raw.githubusercontent.com/alejandroceo/crypto-news-api/main/data/news.json"
).json()
```

---

## Agregar o quitar fuentes

Edita el diccionario `FEEDS` en `scraper.py`. Cualquier feed RSS válido sirve.
Algunos otros feeds cripto públicos que puedes agregar:

- `https://www.newsbtc.com/feed/`
- `https://cryptoslate.com/feed/`
- `https://u.today/rss`
- `https://beincrypto.com/feed/`

Después de editar, solo haz commit/push; la próxima corrida del Action
ya usará las nuevas fuentes.

---

## Costos (todo gratis)

| Servicio | Límite gratis | Uso real de este proyecto |
|---|---|---|
| GitHub Actions (repo público) | 2000 min/mes | ~96 min/mes (cada 15 min) |
| GitHub raw / Pages | Ilimitado razonable | Mínimo |
| Cloudflare Workers | 100,000 req/día | Depende de tus consumidores |

No necesitas tarjeta de crédito en ningún paso.
