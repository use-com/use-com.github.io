import os

fixed = 0
for root, _, files in os.walk('.'):
    if '.git' in root:
        continue
    for f in files:
        if f.endswith(('.css', '.js', '.mjs')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='surrogateescape') as fh:
                src = fh.read()
            new = src.replace('\r\n', '').replace('\n', '').replace('\r', '')
            if new != src:
                with open(p, 'w', encoding='utf-8', errors='surrogateescape') as fh:
                    fh.write(new)
                print('Cleaned:', p)
                fixed += 1

print('Total:', fixed)