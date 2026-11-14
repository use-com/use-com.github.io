OLD = "wss://hair-drainage-decorative-screening.trycloudflare.com/websocket"
NEW = "ws://scooter-resonance.tun.ply.gg"

p = "_app/immutable/chunks/BWj-8FBy.js"
with open(p, "r", encoding="utf-8", errors="surrogateescape") as f:
    data = f.read()

if OLD in data:
    data = data.replace(OLD, NEW, 1)
    with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(data)
    print("Патч применён")
else:
    print("Уже пропатчено или строка не найдена")