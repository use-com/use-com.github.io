import asyncio
import re
import subprocess
import sys
import os
import traceback
import websockets
from aiohttp import web, ClientSession

# ════════════════ КОНФИГ ════════════════
ORIGIN = "https://web.max.ru"
TARGET_WS = "wss://api.oneme.ru/websocket"
UA = "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "ru,en;q=0.9"}
PING_INTERVAL = 30

WS_PORT = 8765
HTTP_PORT = 8766

# Локальные JS, которые нужно патчить
JS_DIR = "_app/immutable/chunks"
JS_FILES = ["BWj-8FBy.js", "RmCTWSHK.js"]  # основные, где URL

# GitHub (опционально)
GITHUB_TOKEN = None
GITHUB_OWNER = "use-com"
GITHUB_REPO = "use-com.github.io"
GITHUB_BRANCH = "main"
# ════════════════════════════════════════

URL_PATTERNS = {
    "ws": re.compile(r'wss://[a-zA-Z0-9.\-]+(?::\d+)?/[^`"\'\s]*websocket'),
    "http": re.compile(r'https://(?:id\.vk\.ru|api\.oneme\.ru)[a-zA-Z0-9.\-/?=&%]*'),
    "lhr": re.compile(r'https://[a-zA-Z0-9.\-]+\.lhr\.life'),
}

def log(*a): print(*a, flush=True)

# ─────────────── WebSocket Прокси ───────────────
async def pipe(src, dst, label):
    try:
        async for msg in src:
            log(f"[{label}] {len(msg)} байт")
            await dst.send(msg)
    except websockets.ConnectionClosed as e:
        log(f"[{label}] закрыт code={e.code}")
    except Exception as e:
        log(f"[{label}] {type(e).__name__}: {e}")

async def ws_handler(client_ws):
    log(f">>> WS КЛИЕНТ. origin={client_ws.request.headers.get('Origin')}")
    try:
        async with websockets.connect(
            TARGET_WS, origin=ORIGIN, user_agent_header=UA,
            additional_headers=HEADERS, subprotocols=["graphql-ws"],
            extensions=[], compression=None,
            ping_interval=PING_INTERVAL, ping_timeout=10,
        ) as server_ws:
            log(f"    ✅ MAX OK")
            await asyncio.gather(
                pipe(client_ws, server_ws, "C→S"),
                pipe(server_ws, client_ws, "S→C"),
            )
    except Exception as e:
        log(f"    ❌ {type(e).__name__}: {e}")
    finally:
        try: await client_ws.close()
        except: pass

# ─────────────── HTTP Прокси (для капчи) ───────────────
async def http_handler(request):
    target_url = request.path_qs.lstrip('/')
    if not target_url.startswith('http'):
        return web.Response(status=400, text="Bad target")

    headers = dict(request.headers)
    headers.pop('Host', None)
    headers.pop('Origin', None)
    headers['Origin'] = ORIGIN
    headers['Referer'] = ORIGIN + '/'
    headers['User-Agent'] = UA

    async with ClientSession() as session:
        try:
            async with session.request(
                request.method, target_url, headers=headers,
                data=await request.read(), allow_redirects=False
            ) as resp:
                body = await resp.read()
                resp_headers = dict(resp.headers)
                for h in ['content-security-policy', 'x-frame-options', 'content-encoding']:
                    resp_headers.pop(h, None)
                resp_headers['Access-Control-Allow-Origin'] = '*'
                resp_headers['Access-Control-Allow-Credentials'] = 'true'
                return web.Response(body=body, status=resp.status, headers=resp_headers)
        except Exception as e:
            log(f"HTTP ERR: {e}")
            return web.Response(status=502, text=str(e))

# ─────────────── Патчинг JS ───────────────
def patch_local(ws_url, http_url):
    """Патчит локальные JS-файлы."""
    if not ws_url: return
    for fname in JS_FILES:
        path = os.path.join(JS_DIR, fname)
        if not os.path.exists(path): continue
        try:
            with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
                text = f.read()
            new_text = URL_PATTERNS["ws"].sub(ws_url, text)
            if http_url:
                # Патчим id.vk.ru и api.oneme.ru через HTTP-прокси
                new_text = URL_PATTERNS["http"].sub(
                    lambda m: f"http://127.0.0.1:{HTTP_PORT}/{m.group(0)}", new_text
                )
            if new_text != text:
                with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
                    f.write(new_text)
                log(f"✅ Локальный JS обновлён: {fname}")
        except Exception as e:
            log(f"Ошибка локального патча {fname}: {e}")

# ─────────────── Туннель localhost.run ───────────────
async def ssh_tunnel_watcher(port, name):
    """Запускает ssh-туннель для порта и возвращает URL."""
    while True:
        log(f"→ Поднимаю туннель для {name} (порт {port})...")
        proc = await asyncio.create_subprocess_exec(
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-R", f"80:localhost:{port}",
            "nokey@localhost.run",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            async for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").rstrip()
                m = URL_PATTERNS["lhr"].search(line)
                if m:
                    url = m.group(0)
                    log(f"→ {name} URL: {url}")
                    return url
            await proc.wait()
        except asyncio.CancelledError:
            proc.terminate()
            raise
        except Exception:
            pass
        finally:
            if proc.returncode is None:
                proc.terminate()
        log(f"→ Туннель {name} закрылся, перезапуск...")
        await asyncio.sleep(5)

async def manage_tunnels():
    """Запускает оба туннеля параллельно и патчит JS при получении URL."""
    while True:
        try:
            # Запускаем оба туннеля параллельно
            ws_url_task = asyncio.create_task(ssh_tunnel_watcher(WS_PORT, "WS"))
            http_url_task = asyncio.create_task(ssh_tunnel_watcher(HTTP_PORT, "HTTP"))

            # Ждем, пока оба выдадут URL
            ws_url = await ws_url_task
            http_url = await http_url_task

            # Патчим локальные файлы
            ws_wss = ws_url.replace("https://", "wss://") + "/websocket"
            patch_local(ws_wss, http_url)

            # Ждем завершения любого из туннелей (если упадет — перезапуск)
            await asyncio.gather(ws_url_task, http_url_task)

        except Exception as e:
            log(f"Ошибка туннелей: {e}")
            await asyncio.sleep(10)

# ─────────────── Main ───────────────
async def main():
    # 1. WebSocket-сервер
    await websockets.serve(
        ws_handler, "127.0.0.1", WS_PORT,
        ping_interval=PING_INTERVAL, compression=None
    )
    log(f"ws-прокси на ws://127.0.0.1:{WS_PORT}/websocket")

    # 2. HTTP-сервер
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', HTTP_PORT)
    await site.start()
    log(f"http-прокси на http://127.0.0.1:{HTTP_PORT}/")

    # 3. Туннели
    asyncio.create_task(manage_tunnels())

    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("→ Остановлено")