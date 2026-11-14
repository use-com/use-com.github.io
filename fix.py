import os

print('Current dir:', os.getcwd())
print()

total_js = 0
for root, _, files in os.walk('.'):
    if '.git' in root:
        continue
    for f in files:
        if f.endswith(('.js', '.mjs')):
            p = os.path.join(root, f)
            with open(p, 'rb') as fh:
                data = fh.read()
            total_js += 1
            nl = data.count(b'\n')
            crlf = data.count(b'\r\n')
            print(f'{p}  size={len(data)}  \\n={nl}  \\r\\n={crlf}')

print()
print('Total .js files:', total_js)