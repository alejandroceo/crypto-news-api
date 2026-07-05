#!/usr/bin/env python3
"""
Traduce los titulares de data/news.json al español y agrega el campo
`title_es` a cada item. El campo `title` original (inglés) se deja intacto,
así cualquier otro consumidor del JSON (tus ejemplos en Python/JS/curl)
sigue funcionando igual.

Se ejecuta como un paso MÁS del workflow, justo DESPUÉS del paso que
genera/actualiza data/news.json.

Requisito: pip install deep-translator
"""
import json
from pathlib import Path

from deep_translator import GoogleTranslator

NEWS_PATH = Path(__file__).parent / "data" / "news.json"


def main():
    data = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
    titles = [item["title"] for item in data["items"]]

    if not titles:
        print("No hay items para traducir.")
        return

    translator = GoogleTranslator(source="en", target="es")
    try:
        translated = translator.translate_batch(titles)
    except Exception as e:
        # Si falla la traducción (red, límite, etc.) no rompemos el workflow:
        # se deja el título en inglés como fallback para esa corrida.
        print(f"Fallo la traducción en lote, se deja todo en inglés: {e}")
        translated = titles

    for item, title_es in zip(data["items"], translated):
        item["title_es"] = title_es

    NEWS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Traducidos {len(titles)} titulares.")


if __name__ == "__main__":
    main()
