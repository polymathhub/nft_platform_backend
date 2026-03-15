import os
import urllib.request
CDN_BASE = 'https://unpkg.com/@tonconnect/ui@latest/dist/'
TARGET_DIR = os.path.join('app', 'static', 'vendor', 'tonconnect')
FILES = ['tonconnect-ui.js', 'tonconnect-ui.css']
os.makedirs(TARGET_DIR, exist_ok=True)
for f in FILES:
    url = CDN_BASE + f
    dest = os.path.join(TARGET_DIR, f)
    try:
        print(f'Downloading {url}...')
        with urllib.request.urlopen(url, timeout=10) as r:
            if r.status == 200:
                data = r.read()
                with open(dest, 'wb') as fh:
                    fh.write(data)
                print(f'Wrote {dest}')
            else:
                print(f'Failed to download {url}: HTTP {r.status}')
    except Exception as e:
        print(f'Error fetching {url}: {e}')
print('\nDone. If files saved, commit them to repository to ensure availability in Telegram WebApp.')
