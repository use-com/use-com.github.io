try:
    import asyncio, base64, os, struct, ssl
    import websockets
    import tls_client

    o = b"wss://api.oneme.ru/websocket"
    n = b"wss://localhost:8765/websocket"

    def ed(OLD, NEW):
        p = os.path.join(".", "_app", "immutable", "chunks", "BWj-8FBy.js")
        with open(p, "rb") as fh:
            data = fh.read()

        if OLD not in data:
            print("Строка уже заменена или не найдена. Текущее содержимое рядом с 'websocket':")
            idx = data.find(b"websocket")
            if idx >= 0:
                print(data[max(0, idx-60):idx+20].decode("utf-8", errors="replace"))
        else:
            new = data.replace(OLD, NEW)
            with open(p, "wb") as fh:
                fh.write(new)
            print(f"Патч применён: {p}")
            print(f"Заменено: {data.count(OLD)} вхождений")

    ed(o, n)






    import asyncio, ssl, websockets, traceback

    ORIGIN = "https://web.max.ru"
    TARGET = "wss://api.oneme.ru/websocket"
    UA = "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"

    HEADERS = {
        "User-Agent": UA,
        "Accept-Language": "ru,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    def log(*a): print(*a, flush=True)

    async def pipe(src, dst, label):
        try:
            async for msg in src:
                log(f"[{label}] {len(msg)} байт")
                await dst.send(msg)
        except websockets.ConnectionClosed as e:
            log(f"[{label}] закрыт code={e.code} reason={e.reason!r}")
        except Exception as e:
            log(f"[{label}] ошибка: {type(e).__name__}: {e}")

    async def handler(client_ws):
        log(f"\n>>> КЛИЕНТ подключился. origin={client_ws.request.headers.get('Origin')}")
        log(f"    subprotocols от клиента: {client_ws.subprotocol}")
        try:
            async with websockets.connect(
                TARGET,
                origin=ORIGIN,
                user_agent_header=UA,
                additional_headers=HEADERS,
                subprotocols=["graphql-ws"],   # MAX может требовать
                extensions=[],                 # ОТКЛЮЧАЕМ permessage-deflate!
                compression=None,              # двойная страховка
                ping_interval=None,            # не шлём ping'и
                open_timeout=15,
                close_timeout=5,
            ) as server_ws:
                log(f"    ✅ Подключились к MAX. subprotocol={server_ws.subprotocol!r}")
                await asyncio.gather(
                    pipe(client_ws, server_ws, "C→S"),
                    pipe(server_ws, client_ws, "S→C"),
                )
        except websockets.InvalidStatusCode as e:
            log(f"    ❌ 4xx на хендшейке: {e.status_code}")
            log(f"    headers от MAX: {dict(e.headers) if hasattr(e,'headers') else '?'}")
        except Exception as e:
            log(f"    ❌ {type(e).__name__}: {e}")
            traceback.print_exc()
        finally:
            try: await client_ws.close()
            except: pass

    async def main():
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain("srv.crt", "srv.key")
        async with websockets.serve(handler, "::", 8765, ssl=ctx):
            log("Прокси на wss://127.0.0.1:8765/websocket")
            await asyncio.Future()

    asyncio.run(main())
except KeyboardInterrupt:
    ed(n, o)