"""Test the export endpoints."""
import urllib.request
import urllib.parse
import json
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
login_data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(
    "http://localhost:5000/api/v1/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = opener.open(req)
print("Login:", resp.status, json.loads(resp.read()))

# Test each download endpoint
for endpoint in ["overall", "faculty", "batch", "room"]:
    url = f"http://localhost:5000/api/v1/export/download/{endpoint}"
    try:
        req2 = urllib.request.Request(url)
        resp2 = opener.open(req2)
        ct = resp2.headers.get("Content-Type", "unknown")
        size = len(resp2.read())
        print(f"Download {endpoint}: status={resp2.status}, content-type={ct}, size={size} bytes")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Download {endpoint}: status={e.code}, error={body[:200]}")
