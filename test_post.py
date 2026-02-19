import json, urllib.request
payload={"blockchain": "ethereum", "wallet_type": "custodial", "init_data": "user={\"id\":12345,\"username\":\"tester\"}"}
data=json.dumps(payload).encode('utf-8')
req=urllib.request.Request('http://localhost:8001/web-app/create-wallet', data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('STATUS', resp.status)
        print(resp.read().decode())
except Exception as e:
    print('ERROR', repr(e))
