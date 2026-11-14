#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from urllib.parse import urljoin, unquote
import re
import sys
import time

import requests

BASE_URL = "https://web.max.ru"
ROOT = Path(__file__).resolve().parent

# Файлы из отчёта urlscan
MP3_PATHS = [
    "/_app/immutable/assets/call_incoming.SXIFOFwL.mp3",
    "/_app/immutable/assets/call_ringing.DugJQAwV.mp3",
    "/_app/immutable/assets/call_connecting.BhrJJ8uO.mp3",
    "/_app/immutable/assets/call_reconnect.C__l9wCX.mp3",
    "/_app/immutable/assets/call_finished.CKzQ2DL0.mp3",
    "/_app/immutable/assets/call_busy.DQJCRQ5h.mp3",
    "/_app/immutable/assets/call_connected.BIn7TweB.mp3",
    "/_app/immutable/assets/call_hold.Dho9Wn8x.mp3",
    "/_app/immutable/assets/call_hold_en.BkuCC7eI.mp3",
]

# Дополнительно ищем mp3-ссылки в локальных html/css/js
TEXT_EXTENSIONS = {".html", ".htm", ".css", ".js", ".mjs", ".json", ".txt", ".map"}
MP3_RE = re.compile(
    r"(?:https?://web\.max\.ru)?(/_app/[A-Za-z0-9_@%./+\-]+\.mp3)",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://web.max.ru/",
    "Accept": "audio/mpeg,audio/*;q=0.9,*/*;q=0.8",
}

FORCE_DOWNLOAD = False  # True — перекачать даже существующие файлы


def normalize_path(path: str) -> str:
    path = path.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return path


def safe_local_path(url_path: str) -> Path | None:
    rel = Path(unquote(url_path.lstrip("/")))
    if ".." in rel.parts:
        return None
    return ROOT / rel


def collect_mp3_paths() -> list[str]:
    paths = {normalize_path(p) for p in MP3_PATHS}

    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in MP3_RE.finditer(text):
            paths.add(normalize_path(m.group(1)))

    return sorted(paths)


def download_mp3(url_path: str) -> str:
    local = safe_local_path(url_path)
    if local is None:
        return f"SKIP (небезопасный путь): {url_path}"

    if local.exists() and local.stat().st_size > 0 and not FORCE_DOWNLOAD:
        return f"OK (уже есть): {url_path} ({local.stat().st_size} bytes)"

    url = urljoin(BASE_URL + "/", url_path.lstrip("/"))
    last_error = None

    for attempt in range(1, 4):
        try:
            with requests.get(url, headers=HEADERS, timeout=60, stream=True) as r:
                if r.status_code != 200:
                    return f"FAIL ({r.status_code}): {url_path}"

                content_type = r.headers.get("Content-Type", "").lower()
                if "audio" not in content_type and "mpeg" not in content_type:
                    print(f"    warning: Content-Type = {content_type!r}")

                local.parent.mkdir(parents=True, exist_ok=True)
                tmp = local.with_suffix(local.suffix + ".part")

                size = 0
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            f.write(chunk)
                            size += len(chunk)

                if size == 0:
                    tmp.unlink(missing_ok=True)
                    return f"FAIL (пустой файл): {url_path}"

                tmp.replace(local)
                return f"DOWNLOADED: {url_path} ({size} bytes)"

        except requests.RequestException as e:
            last_error = e
            if attempt < 3:
                time.sleep(1.5 * attempt)

    return f"ERROR (сеть): {url_path} -> {last_error}"


def main() -> int:
    print(f"Проект: {ROOT}")
    print(f"База:   {BASE_URL}")
    print()

    paths = collect_mp3_paths()
    print(f"Найдено mp3-путей: {len(paths)}\n")

    results = []
    for i, url_path in enumerate(paths, 1):
        print(f"[{i}/{len(paths)}] {url_path}")
        result = download_mp3(url_path)
        print("   ", result)
        results.append(result)

    print("\n===== ИТОГ =====")
    downloaded = [x for x in results if x.startswith("DOWNLOADED")]
    skipped = [x for x in results if x.startswith("OK")]
    failed = [x for x in results if x.startswith("FAIL") or x.startswith("ERROR")]

    print(f"Скачано:      {len(downloaded)}")
    print(f"Уже было:     {len(skipped)}")
    print(f"Ошибок:       {len(failed)}")

    if failed:
        print("\nНе удалось скачать:")
        for item in failed:
            print(" -", item)
        print("\nЕсли это 403/404 — сервер не отдаёт файл без авторизации или cookies.")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())