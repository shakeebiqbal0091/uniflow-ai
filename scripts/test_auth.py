import requests

BASE = "http://127.0.0.1:8000"

def pretty(resp):
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

# Register
print('Registering user...')
reg = requests.post(f"{BASE}/api/auth/register", json={"email":"test@example.com","password":"testpass","full_name":"Test User"})
print('Register:', pretty(reg))

# Login
print('Logging in...')
login = requests.post(f"{BASE}/api/auth/login", json={"username":"test@example.com","password":"testpass"})
print('Login:', pretty(login))
if login.status_code != 200:
    raise SystemExit('Login failed')

token = login.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Call protected
print('Calling protected /me...')
me = requests.get(f"{BASE}/api/protected/me", headers=headers)
print('Me:', pretty(me))
