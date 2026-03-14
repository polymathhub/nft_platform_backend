import urllib.request
url='https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.js'
try:
    r=urllib.request.urlopen(url, timeout=15)
    print('JSDELIV_OK', r.getcode())
except Exception as e:
    print('JSDELIV_ERR', e)
