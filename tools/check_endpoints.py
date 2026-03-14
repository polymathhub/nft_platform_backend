import json
import urllib.request
import urllib.error

endpoints = {
    'manifest': 'https://nftplatformbackend-production-9081.up.railway.app/tonconnect-manifest.json',
    'unpkg_tonconnect': 'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.js',
    'telegram_auth': 'https://nftplatformbackend-production-9081.up.railway.app/api/v1/auth/telegram/login'
}

def fetch(url, method='GET', data=None):
    try:
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header('Content-Type','application/json')
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode('utf-8', errors='replace')
            return (r.getcode(), content)
    except urllib.error.HTTPError as e:
        return (e.code, str(e))
    except Exception as e:
        return (None, str(e))

if __name__ == '__main__':
    for k,u in endpoints.items():
        print('===', k, u)
        if k=='telegram_auth':
            status, content = fetch(u, method='POST', data=b'{}')
        else:
            status, content = fetch(u)
        print('status:', status)
        out = content[:1000] if content else ''
        print('body snippet:', out)
        print()
