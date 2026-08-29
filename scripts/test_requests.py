import requests
import time
from uuid import uuid4

BASE = "http://127.0.0.1:8000"


def pretty(resp):
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text


email = f"user-{uuid4().hex[:8]}@example.com"
print('Registering test user...')
reg = requests.post(
    f"{BASE}/api/auth/register",
    json={"email": email, "password": "testpass", "full_name": "Test User"},
)
print('Register:', pretty(reg))

login = requests.post(f"{BASE}/api/auth/login", json={"username": email, "password": "testpass"})
print('Login:', pretty(login))
if login.status_code != 200:
    raise SystemExit(f"Login failed: {pretty(login)}")

token = login.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Create a request
print('Creating request...')
req = requests.post(
    f"{BASE}/api/requests/",
    json={"student_id": "STD-001", "request_type": "transcript", "title": "Transcript for scholarship", "description": "Please process"},
    headers=headers,
)
print('Create:', pretty(req))

# List requests (retry a few times in case server reloads)
print('Listing requests...')
for i in range(5):
    listr = requests.get(f"{BASE}/api/requests/", headers=headers)
    if listr.status_code == 200:
        break
    print('List attempt', i, 'status', listr.status_code)
    time.sleep(0.5)
print('List:', pretty(listr))

# Update first request if exists
if listr.status_code == 200 and listr.json():
    rid = listr.json()[0]['id']
    print('Patching request', rid)
    patch = requests.patch(
        f"{BASE}/api/requests/{rid}",
        json={"status": "IN_PROGRESS", "assigned_to": "admin"},
        headers=headers,
    )
    print('Patch:', pretty(patch))

    # Get the request
    getr = requests.get(f"{BASE}/api/requests/{rid}", headers=headers)
    print('Get:', pretty(getr))
