/**
 * API REST gratuita para titulares de noticias cripto.
 * Lee el JSON generado por GitHub Actions y lo sirve con filtros,
 * paginación y CORS abierto. Free tier de Cloudflare Workers:
 * 100,000 requests/día, sin tarjeta de crédito.
 *
 * Endpoints:
 *   GET /                          -> todos los titulares (máx 50 por defecto)
 *   GET /?source=coindesk          -> filtra por fuente
 *   GET /?limit=10                 -> limita resultados
 *   GET /?q=bitcoin                -> busca en el título
 *   GET /sources                   -> lista las fuentes disponibles
 */

//
const RAW_JSON_URL =
  "https://raw.githubusercontent.com/alejandroceo/crypto-news-api/main/data/news.json";

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, OPTIONS",
  "access-control-allow-headers": "Content-Type",
};

async function fetchNews() {
  const res = await fetch(RAW_JSON_URL, {
    cf: { cacheTtl: 300, cacheEverything: true }, // cachea 5 min en el edge
  });
  if (!res.ok) {
    throw new Error(`upstream status ${res.status}`);
  }
  return res.json();
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=120",
      ...CORS_HEADERS,
    },
  });
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    try {
      const data = await fetchNews();

      if (url.pathname === "/sources") {
        return jsonResponse({ sources: data.sources, updated_at: data.updated_at });
      }

      let items = data.items;

      const source = url.searchParams.get("source");
      if (source) {
        items = items.filter((i) => i.source === source.toLowerCase());
      }

      const q = url.searchParams.get("q");
      if (q) {
        const needle = q.toLowerCase();
        items = items.filter((i) => i.title.toLowerCase().includes(needle));
      }

      const limit = Math.min(parseInt(url.searchParams.get("limit") || "50", 10), 200);
      const offset = parseInt(url.searchParams.get("offset") || "0", 10);
      const paged = items.slice(offset, offset + limit);

      return jsonResponse({
        updated_at: data.updated_at,
        total: items.length,
        count: paged.length,
        offset,
        limit,
        items: paged,
      });
    } catch (err) {
      return jsonResponse({ error: "no se pudo obtener las noticias", detail: String(err) }, 502);
    }
  },
};
