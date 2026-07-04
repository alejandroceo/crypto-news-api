"""
Scraper de titulares de noticias de criptomonedas.
Lee feeds RSS públicos (no hace scraping agresivo de HTML, así que es
estable y no rompe términos de servicio) y genera data/news.json.
"""
import feedparser
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

# Agrega o quita fuentes aquí. Todas son feeds RSS públicos.
FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
    "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
    "theblock": "https://www.theblock.co/rss.xml",
    "cryptonews": "https://cryptonews.com/news/feed/",
}

ITEMS_PER_SOURCE = 25
OUTPUT_PATH = Path(__file__).parent / "data" / "news.json"


def make_id(link: str) -> str:
    return hashlib.sha256(link.encode("utf-8")).hexdigest()[:12]


def normalize_date(entry) -> str:
    # feedparser ya parsea la fecha a struct_time en published_parsed
    if getattr(entry, "published_parsed", None):
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    return ""


def scrape_source(name: str, url: str) -> list[dict]:
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        print(f"[warn] no se pudo leer {name}: {feed.bozo_exception}", file=sys.stderr)
        return []

    items = []
    for entry in feed.entries[:ITEMS_PER_SOURCE]:
        link = entry.get("link", "")
        if not link:
            continue
        items.append({
            "id": make_id(link),
            "title": entry.get("title", "").strip(),
            "link": link,
            "source": name,
            "published": normalize_date(entry),
            "summary": entry.get("summary", "")[:300] if entry.get("summary") else "",
        })
    return items


def scrape_all() -> list[dict]:
    all_items = []
    for name, url in FEEDS.items():
        try:
            all_items.extend(scrape_source(name, url))
        except Exception as e:
            print(f"[error] fallo en {name}: {e}", file=sys.stderr)

    # dedupe por id, por si dos feeds republican el mismo link
    seen = set()
    deduped = []
    for item in all_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            deduped.append(item)

    deduped.sort(key=lambda x: x["published"], reverse=True)
    return deduped


def main():
    items = scrape_all()
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "sources": list(FEEDS.keys()),
        "items": items,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OK: {len(items)} titulares guardados en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
