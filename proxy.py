import asyncio, re, subprocess, sys, os, traceback
import websockets

# ════════════════ КОНФИГ ════════════════
ORIGIN = "https://web.max.ru"
TARGET = "wss://api.oneme.ru/websocket"
UA = "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "ru,en;q=0.9"}
PING_INTERVAL = 30

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8765

# Локальный JS, где ищем URL
LOCAL_JS = "_app/immutable/chunks/BWj-8FBy.js"

GITHUB_TOKEN = None
GITHUB_OWNER = "use-com"
GITHUB_REPO  = "use-com.github.io"
GITHUB_BRANCH = "main"
GITHUB_PATH  = "_app/immutable/chunks/BWj-8FBy.js"
# ════════════════════════════════════════

URL_PATTERN = re.compile(r'wss://[a-zA-Z0-9.\-]+(?::\d+)?/[^`"\'\s]*websocket')
LHR_URL_RE = re.compile(r'https://[a-zA-Z0-9.\-]+\.lhr\.life')

def log(*a): print(*a, flush=True)

# ─────────────── WebSocket прокси ───────────────

async def pipe(src, dst, label):
    try:
        async for msg in src:
            log(f"[{label}] {len(msg)} байт")
            await dst.send(msg)
    except websockets.ConnectionClosed as e:
        log(f"[{label}] закрыт code={e.code}")
    except Exception as e:
        log(f"[{label}] {type(e).__name__}: {e}")

async def handler(client_ws):
    log(f">>> КЛИЕНТ. origin={client_ws.request.headers.get('Origin')}")
    try:
        async with websockets.connect(
            TARGET, origin=ORIGIN, user_agent_header=UA,
            additional_headers=HEADERS, subprotocols=["graphql-ws"],
            extensions=[], compression=None,
            ping_interval=PING_INTERVAL, ping_timeout=10,
            open_timeout=15, close_timeout=5,
        ) as server_ws:
            log(f"    ✅ MAX OK, subprotocol={server_ws.subprotocol!r}")
            await asyncio.gather(
                pipe(client_ws, server_ws, "C→S"),
                pipe(server_ws, client_ws, "S→C"),
            )
    except websockets.InvalidStatusCode as e:
        log(f"    ❌ {e.status_code}")
    except Exception as e:
        log(f"    ❌ {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        try: await client_ws.close()
        except: pass

# ─────────────── Патч JS ───────────────

def patch_local(new_url):
    """Меняет wss://.../websocket на новый URL в локальном файле."""
    try:
        with open(LOCAL_JS, "r", encoding="utf-8", errors="surrogateescape") as f:
            text = f.read()
    except FileNotFoundError:
        log("→ Локальный JS не найден, пропускаю")
        return False
    new_text, n = URL_PATTERN.subn(new_url, text, count=1)
    if n == 0 or new_text == text:
        return False
    with open(LOCAL_JS, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(new_text)
    log(f"✅ Локальный JS обновлён → {new_url}")
    return True

def patch_github(new_url):
    """Патч через GitHub API. Требует GITHUB_TOKEN."""
    if not GITHUB_TOKEN:
        return False
    try:
        import requests, base64
    except ImportError:
        log("→ Нет requests (pip install requests), GitHub-патч пропущен")
        return False
    headers = {"Authorization": f"token {GITHUB_TOKEN}",
               "Accept": "application/vnd.github.v3+json"}
    api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    r = requests.get(api, headers=headers,
                     params={"ref": GITHUB_BRANCH}, timeout=15)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8", errors="surrogateescape")
    new_content, n = URL_PATTERN.subn(new_url, content, count=1)
    if n == 0 or new_content == content:
        return False
    body = {"message": f"auto: ws → {new_url}",
            "content": base64.b64encode(new_content.encode("utf-8", errors="surrogateescape")).decode("ascii"),
            "sha": data["sha"], "branch": GITHUB_BRANCH}
    r2 = requests.put(api, headers=headers, json=body, timeout=20)
    r2.raise_for_status()
    log(f"✅ GitHub обновлён → {new_url}")
    return True

# ─────────────── localhost.run watcher ───────────────

async def ssh_tunnel_watcher():
    """
    Поднимает ssh -R 80:localhost:8765 nokey@localhost.run,
    читает его stderr, ловит https://*.lhr.life,
    патчит локальный JS и GitHub.
    """
    while True:
        log("→ Поднимаю localhost.run...")
        proc = await asyncio.create_subprocess_exec(
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-R", f"80:localhost:{LISTEN_PORT}",
            "nokey@localhost.run",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        current_url = None
        try:
            async for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").rstrip()
                log(f"[ssh] {line}")
                m = LHR_URL_RE.search(line)
                if m and m.group(0) != current_url:
                    current_url = m.group(0)
                    ws_url = current_url.replace("https://", "wss://") + "/websocket"
                    log(f"→ Новый URL: {ws_url}")
                    patch_local(ws_url)
                    try:
                        patch_github(ws_url)
                    except Exception as e:
                        log(f"→ GitHub-патч ошибка: {e}")
            await proc.wait()
        except asyncio.CancelledError:
            proc.terminate()
            raise
        except Exception as e:
            log(f"→ ssh упал: {e}")
            if proc.returncode is None:
                proc.terminate()
        log("→ Туннель закрылся, перезапуск через 10 сек...")
        await asyncio.sleep(10)

# ─────────────── main ───────────────

async def main():
    # Прокси в фоне
    async with websockets.serve(
        handler, LISTEN_HOST, LISTEN_PORT,
        ping_interval=PING_INTERVAL, max_size=None, max_queue=32,
    ):
        log(f"ws-прокси на ws://{LISTEN_HOST}:{LISTEN_PORT}/websocket")
        # Туннель в фоне
        tunnel_task = asyncio.create_task(ssh_tunnel_watcher())
        try:
            await asyncio.Future()
        finally:
            tunnel_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("→ Остановлено")