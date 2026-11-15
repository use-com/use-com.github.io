#!/usr/bin/env python3
"""
redownload_js.py — перекачивает ВСЕ .js файлы с web.max.ru
в те же пути, где они лежат локально.
"""

import os
import requests
from pathlib import Path

BASE_URL = "https://web.max.ru"
SKIP_FILES = {"service-worker.js"}  # локальный, не трогаем

def main():
    root = Path(".").resolve()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
    })

    total, ok, skip, fail = 0, 0, 0, 0

    for path in root.rglob("*.js"):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if rel in SKIP_FILES:
            continue

        total += 1
        url = f"{BASE_URL}/{rel}"
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200 and r.content:
                path.write_bytes(r.content)
                print(f"OK   {rel}  ({len(r.content)} байт)")
                ok += 1
            elif r.status_code == 404:
                print(f"SKIP {rel}  (404 на сервере)")
                skip += 1
            else:
                print(f"FAIL {rel}  (HTTP {r.status_code})")
                fail += 1
        except Exception as e:
            print(f"ERR  {rel}  ({type(e).__name__}: {e})")
            fail += 1

    print(f"\nВсего: {total}  |  Скачано: {ok}  |  Пропущено: {skip}  |  Ошибок: {fail}")

if __name__ == "__main__":
    main()