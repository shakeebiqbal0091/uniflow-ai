import requests
BASE = "http://127.0.0.1:8000"
resp = requests.get(f"{BASE}/api/requests/")
print('status', resp.status_code)
print('headers', resp.headers)
print('text', resp.text)
print('allowed', resp.headers.get('allow'))
