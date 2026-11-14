import asyncio, ssl, websockets, sys

ORIGIN = "https://web.max.ru"
TARGET = "wss://api.oneme.ru/websocket"
UA = "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"

async def test():
    ctx = ssl.create_default_context()
    # не проверяем сертификат — нам важен сам факт соединения, а не проверка
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"→ подключаюсь к {TARGET}")
    try:
        async with websockets.connect(
            TARGET,
            origin=ORIGIN,
            user_agent_header=UA,
            subprotocols=["graphql-ws"],
            additional_headers={
                "Accept-Language": "ru,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            ssl=ctx,
            open_timeout=10,
            ping_interval=None,   # отключаем ping, чтобы тест был чистым
        ) as ws:
            print("✅ Хендшейк прошёл")
            print(f"   subprotocol: {ws.subprotocol!r}")
            print(f"   response headers: {dict(ws.response_headers)}")
            try:
                # ждём первого сообщения от MAX (auth-челлендж и т.п.)
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"   первое сообщение ({len(msg)} байт): {msg[:80]!r}")
            except asyncio.TimeoutError:
                print("   (сервер молчит 5 сек — это нормально для WS без handshake)")
    except websockets.InvalidStatusCode as e:
        print(f"❌ 403/4xx на хендшейке: {e.status_code}")
        print(f"   response headers: {dict(e.headers)}")
    except ConnectionResetError as e:
        print(f"❌ ConnectionResetError — сервер рвёт TCP до/во время TLS")
        print("   Скорее всего блок по JA3 (TLS-фингерпринт Python не как у Chrome)")
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")

asyncio.run(test())