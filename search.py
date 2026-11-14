#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from urllib.parse import urljoin, unquote
import re
import sys

import requests

BASE_URL = "https://web.max.ru"
ROOT = Path(__file__).resolve().parent

# Сюда можно вручную добавить пути, которые точно нужно проверить/скачать
EXTRA_PATHS = [
    "/_app/immutable/workers/RenderWorkerEntrypoint-94r4WKY2.js",
]

TEXT_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".json",
    ".svg", ".txt", ".map", ".xml",
}

# Ищем /_app/... и https://web.max.ru/_app/...
ASSET_RE = re.compile(
    r"(?:https?://web\.max\.ru)?(/_app/[A-Za-z0-9_@%./+\-]+)"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def normalize_path(path: str) -> str:
    path = path.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return path


def safe_local_path(url_path: str) -> Path | None:
    """
    Преобразует /_app/... в локальный путь внутри ROOT.
    Защита от ../
    """
    rel = Path(unquote(url_path.lstrip("/")))
    if ".." in rel.parts:
        return None
    return ROOT / rel


def collect_paths_from_local_files() -> set[str]:
    paths: set[str] = set()

    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in ASSET_RE.finditer(text):
            paths.add(normalize_path(m.group(1)))

    for item in EXTRA_PATHS:
        paths.add(normalize_path(item))

    return paths


def download_if_needed(url_path: str) -> str:
    local = safe_local_path(url_path)
    if local is None:
        return f"SKIP (небезопасный путь): {url_path}"

    if local.exists() and local.stat().st_size > 0:
        return f"OK (уже есть): {url_path}"

    url = urljoin(BASE_URL + "/", url_path.lstrip("/"))

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        return f"ERROR (сеть): {url_path} -> {e}"

    if r.status_code != 200:
        return f"FAIL ({r.status_code}): {url_path}"

    if not r.content:
        return f"FAIL (пустой ответ): {url_path}"

    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(r.content)
    return f"DOWNLOADED: {url_path} ({len(r.content)} bytes)"


def main() -> int:
    print(f"Проект: {ROOT}")
    print(f"База:   {BASE_URL}")
    print()

    paths = sorted(collect_paths_from_local_files())

    if not paths:
        print("Не найдено ссылок /_app/... в локальных файлах.")
        print("Проверьте, что скрипт лежит в корне проекта.")
        return 1

    print(f"Найдено путей для проверки: {len(paths)}")
    print()

    results = []
    for i, url_path in enumerate(paths, 1):
        print(f"[{i}/{len(paths)}] {url_path}")
        result = download_if_needed(url_path)
        print("   ", result)
        results.append(result)

    print("\n===== ИТОГ =====")
    downloaded = [x for x in results if x.startswith("DOWNLOADED")]
    failed = [x for x in results if x.startswith("FAIL") or x.startswith("ERROR")]

    print(f"Скачано: {len(downloaded)}")
    print(f"Ошибок:  {len(failed)}")

    if failed:
        print("\nНе удалось получить:")
        for item in failed:
            print(" -", item)

    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())