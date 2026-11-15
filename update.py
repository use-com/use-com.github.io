import asyncio
import base64
import os
import re
import traceback

import websockets
from aiohttp import web, ClientSession

try:
    import requests
except ImportError:
    requests = None

# ════════════════ КОНФИГ ════════════════
ORIGIN = "https://web.max.ru"
TARGET_WS = "wss://api.oneme.ru/websocket"
UA = "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "ru,en;q=0.9"}
PING_INTERVAL = 30

WS_PORT = 8765
HTTP_PORT = 8766

JS_DIR = "_app/immutable/chunks"
JS_FILES = ["BWj-8FBy.js", "RmCTWSHK.js"]

# ═══ ВСТАВЬ ТОКЕН ЗДЕСЬ ═══
GITHUB_TOKEN = None          # "ghp_..." или None, если автопатч не нужен
GITHUB_OWNER = "use-com"
GITHUB_REPO  = "use-com.github.io"
GITHUB_BRANCH = "main"
# ════════════════════════════════════════

URL_PATTERNS = {
    "ws":   re.compile(r'wss://[a-zA-Z0-9.\-]+(?::\d+)?/[^`"\'\s]*/websocket'),
    "http": re.compile(r'https://(?:id\.vk\.ru|api\.oneme\.ru)[a-zA-Z0-9.\-/?=&%]*'),
    "lhr":  re.compile(r'https://[a-zA-Z0-9.\-]+\.lhr\.life'),
}

def log(*a): print(*a, flush=True)

# ═══════════════ WebSocket Прокси ═══════════════
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
            log("    ✅ MAX OK")
            await asyncio.gather(
                pipe(client_ws, server_ws, "C→S"),
                pipe(server_ws, client_ws, "S→C"),
            )
    except Exception as e:
        log(f"    ❌ {type(e).__name__}: {e}")
    finally:
        try: await client_ws.close()
        except: pass

# ═══════════════ HTTP Прокси (капча) ═══════════════
async def http_handler(request):
    target_url = request.path_qs
    if target_url.startswith('/'):
        target_url = target_url[1:]
    if not target_url.startswith('http'):
        return web.Response(status=400, text="Bad target: " + target_url)

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
                data=await request.read(), allow_redirects=True
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

# ═══════════════ Патч локальных JS ═══════════════
def patch_local(ws_url, http_url):
    if not ws_url: return
    for fname in JS_FILES:
        path = os.path.join(JS_DIR, fname)
        if not os.path.exists(path): continue
        try:
            with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
                text = f.read()
            new_text = URL_PATTERNS["ws"].sub(ws_url, text)
            if http_url:
                new_text = URL_PATTERNS["http"].sub(
                    lambda m: f"http://127.0.0.1:{HTTP_PORT}/{m.group(0)}", new_text
                )
            if new_text != text:
                with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
                    f.write(new_text)
                log(f"✅ Локальный JS обновлён: {fname}")
        except Exception as e:
            log(f"Ошибка локального патча {fname}: {e}")

# ═══════════════ Патч GitHub ═══════════════
def patch_github(ws_url, http_url):
    if not GITHUB_TOKEN or not requests:
        log("ℹ️ Автопатч GitHub отключён (нет токена или requests)")
        return
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    for fname in JS_FILES:
        path = f"{JS_DIR}/{fname}"
        api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
        try:
            r = requests.get(api, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=15)
            r.raise_for_status()
            data = r.json()
            sha = data["sha"]
            content = base64.b64decode(data["content"]).decode("utf-8")
        except Exception as e:
            log(f"❌ GitHub GET {fname}: {e}")
            continue

        new_content = URL_PATTERNS["ws"].sub(ws_url, content)
        if http_url:
            new_content = URL_PATTERNS["http"].sub(
                lambda m: f"http://127.0.0.1:{HTTP_PORT}/{m.group(0)}", new_content
            )
        if new_content == content:
            log(f"ℹ️ {fname}: уже актуален на GitHub")
            continue
        try:
            r = requests.put(
                api, headers=headers,
                json={
                    "message": f"auto: patch {fname}",
                    "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"),
                    "sha": sha,
                    "branch": GITHUB_BRANCH,
                },
                timeout=20,
            )
            r.raise_for_status()
            log(f"✅ GitHub обновлён: {fname}")
        except Exception as e:
            log(f"❌ GitHub PUT {fname}: {e}")

def patch_all(ws_url, http_url):
    patch_local(ws_url, http_url)
    patch_github(ws_url, http_url)

# ═══════════════ localhost.run ═══════════════
async def ssh_tunnel_watcher(port, name):
    """Держит ssh-туннель живым, URL отдаёт через Queue."""
    url_queue = asyncio.Queue()

    async def runner():
        while True:
            log(f"→ Поднимаю туннель {name} (порт {port})...")
            proc = await asyncio.create_subprocess_exec(
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-o", "ServerAliveInterval=30",
                "-o", "ExitOnForwardFailure=yes",
                "-R", f"80:localhost:{port}",
                "nokey@localhost.run",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            got_url = False
            try:
                async for raw in proc.stdout:
                    line = raw.decode("utf-8", errors="replace").rstrip()
                    m = URL_PATTERNS["lhr"].search(line)
                    if m and not got_url:
                        url = m.group(0)
                        log(f"→ {name} URL: {url}")
                        await url_queue.put(url)
                        got_url = True
            except asyncio.CancelledError:
                proc.terminate()
                raise
            except Exception as e:
                log(f"Туннель {name} ошибка: {e}")
            finally:
                if proc.returncode is None:
                    proc.terminate()
                    try: await asyncio.wait_for(proc.wait(), timeout=5)
                    except: pass
            await asyncio.sleep(5)

    asyncio.create_task(runner())
    return await url_queue.get()

async def manage_tunnels():
    try:
        ws_url, http_url = await asyncio.gather(
            ssh_tunnel_watcher(WS_PORT, "WS"),
            ssh_tunnel_watcher(HTTP_PORT, "HTTP"),
        )
        ws_wss = ws_url.replace("https://", "wss://") + "/websocket"
        patch_all(ws_wss, http_url)
        log("✅ Туннели подняты, JS пропатчен (локально + GitHub).")
        await asyncio.Future()
    except Exception as e:
        log(f"Ошибка туннелей: {e}")
        traceback.print_exc()

# ═══════════════ Main ═══════════════
async def main():
    await websockets.serve(
        ws_handler, "127.0.0.1", WS_PORT,
        ping_interval=PING_INTERVAL, compression=None
    )
    log(f"ws-прокси на ws://127.0.0.1:{WS_PORT}/websocket")

    app = web.Application()
    app.router.add_route('*', '/{path:.*}', http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', HTTP_PORT)
    await site.start()
    log(f"http-прокси на http://127.0.0.1:{HTTP_PORT}/")

    asyncio.create_task(manage_tunnels())
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("→ Остановлено")