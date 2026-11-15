#!/usr/bin/env python3
"""
update_max_js.py — обновляет JS-файлы локального бандла MAX,
скачивая свежие версии с web.max.ru по тем же путям.

НЕ трогает файлы, которые были добавлены вручную (service-worker.js,
proxy.py, auto_update_url.py и т.п.) — только те, что перечислены
в манифесте `_app/immutable/` или найдены как файлы с известными
паттернами имён (start.*.js, chunks/*.js и т.д.).

Запуск из корня проекта:
    python update_max_js.py
"""

import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ════════════════ КОНФИГ ════════════════
BASE_URL = "https://web.max.ru"
ROOT_DIR = Path(".")            # запускать из корня проекта
# ════════════════════════════════════════

# Файлы/папки, которые НЕ трогаем никогда (добавлены вручную)
SKIP_NAMES = {
    "service-worker.js",
    "proxy.py",
    "gen_cert.py",
    "clean.py",
    "diag.py",
    "fix.py",
    "patch_ws.py",
    "auto_update_url.py",
    "update_max_js.py",
    "srv.crt",
    "srv.key",
    "favicon.png",
    "site.webmanifest",
}

# Папки, внутри которых трогаем только .js/.css/.json
SCAN_DIRS = [
    "_app/immutable",
]

# Допустимые расширения для обновления
ALLOWED_EXT = {".js", ".mjs", ".css", ".json", ".webmanifest", ".woff2", ".svg", ".png"}


def should_skip(rel_path: str) -> bool:
    name = os.path.basename(rel_path)
    if name in SKIP_NAMES:
        return True
    # локальные заметки / логи / скрипты
    if rel_path.endswith((".py", ".txt", ".log", ".md")):
        return True
    return False


def collect_local_files() -> list[Path]:
    """Собирает все файлы, которые похожи на часть бандла MAX."""
    files = []
    for d in SCAN_DIRS:
        base = ROOT_DIR / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in ALLOWED_EXT:
                continue
            rel = str(p.relative_to(ROOT_DIR)).replace("\\", "/")
            if should_skip(rel):
                continue
            files.append(p)
    return files


def fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 16; Pixel 10) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/152.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "ru,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                print(f"  ← HTTP {resp.status}")
                return None
            return resp.read()
    except urllib.error.HTTPError as e:
        print(f"  ← HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  ← {type(e).__name__}: {e}")
        return None


def main():
    files = collect_local_files()
    if not files:
        print("Не найдено файлов для обновления (проверь, что запущен из корня проекта).")
        sys.exit(1)

    print(f"Найдено {len(files)} файлов. Начинаю обновление с {BASE_URL}\n")

    updated = 0
    unchanged = 0
    not_found = 0
    failed = 0

    for p in files:
        rel = str(p.relative_to(ROOT_DIR)).replace("\\", "/")
        url = f"{BASE_URL}/{rel}"

        # читаем текущий размер
        old_size = p.stat().st_size if p.exists() else 0
        print(f"→ {rel}  (локально {old_size} байт)")

        data = fetch(url)
        if data is None:
            # сервер не отдал — оставляем как есть
            not_found += 1
            continue

        if p.exists() and p.read_bytes() == data:
            print(f"  = без изменений")
            unchanged += 1
            continue

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        print(f"  ✅ обновлён: {old_size} → {len(data)} байт")
        updated += 1

    print(f"\nИтого:")
    print(f"  обновлено:     {updated}")
    print(f"  без изменений: {unchanged}")
    print(f"  нет на сервере:{not_found}")
    print(f"  ошибок:        {failed}")


if __name__ == "__main__":
    main()